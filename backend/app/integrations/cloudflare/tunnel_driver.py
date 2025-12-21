"""
DockFlare-inspired Cloudflare tunnel management
Direct copy of DockFlare's tunnel_manager.py approach
"""

import json
import os
import requests
import time
import subprocess
import signal
import asyncio
from typing import Any, Dict, List, Optional

import docker
from docker.errors import APIError, NotFound

from core.tunnel_driver import (
    AbstractTunnelDriver,
    TunnelConfig,
    TunnelInfo,
    TunnelStatus,
    TunnelCreationException,
    TunnelNotFoundException,
    TunnelProviderException,
)
from core.logger import setup_logger
from core.settings import settings

logger = setup_logger(__name__)

# Global state exactly like DockFlare
tunnel_state = {
    "name": "localrun-tunnel",
    "id": None,
    "token": None,
    "status_message": "Initializing...",
    "error": None,
}

cloudflared_agent_state = {"container_status": "unknown", "last_action_status": None}

# Managed rules (like DockFlare's managed_rules)
managed_rules: Dict[str, Dict] = {}

# Docker client
try:
    docker_client = docker.from_env()
    docker_client.ping()
except Exception as e:
    logger.error(f"Failed to connect to Docker: {e}")
    docker_client = None


class CloudflaredHTTPDriver(AbstractTunnelDriver):
    """
    DockFlare-inspired Cloudflare tunnel driver.

    Copies DockFlare's approach:
    - Single master tunnel per account
    - Dynamic ingress rules via API
    - One cloudflared process managed directly
    - State management like DockFlare
    """

    def __init__(self):
        super().__init__("cloudflare")
        self.quick_tunnels = {}  # Para Quick tunnels independientes

    CF_API = "https://api.cloudflare.com/client/v4"

    # Implementación de métodos abstractos requeridos
    def supports_protocol(self, protocol: str) -> bool:
        """Cloudflare soporta HTTP, HTTPS, TCP, UDP, SSH, Bastion"""
        return protocol.lower() in ["http", "https", "tcp", "udp", "ssh", "bastion"]

    def supports_named_tunnels(self) -> bool:
        """Cloudflare sí soporta Named Tunnels persistentes"""
        return True

    # Implementación de métodos abstractos usando el patrón DockFlare
    async def create_tunnel(self, config: TunnelConfig) -> TunnelInfo:
        """Crea un túnel Cloudflare exponiendo un puerto del host"""
        try:
            port = config.port
            protocol = config.protocol

            # Determinar tipo de túnel basado en configuración
            is_named_tunnel = (
                hasattr(config, "domain") and config.domain and hasattr(config, "subdomain") and config.subdomain
            )

            if is_named_tunnel:
                # Inicializar túnel si es necesario (SOLO para Named Tunnels)
                await self._ensure_tunnel_initialized()

                # Named Tunnel: usar dominio personalizado con túnel maestro
                hostname = f"{config.subdomain}.{config.domain}"
                # Configurar service según protocolo
                if config.protocol.lower() in ["tcp", "ssh"]:
                    service = f"tcp://host.docker.internal:{port}"
                else:
                    service = f"http://host.docker.internal:{port}"

                # Agregar a managed_rules para túnel maestro
                rule_key = f"{hostname}_{protocol}"
                managed_rules[rule_key] = {
                    "hostname": hostname,
                    "service": service,
                    "port": port,
                    "protocol": protocol,
                    "status": "active",
                    "source": "localrun-agent",
                }

                # Actualizar configuración del túnel maestro
                if not self.update_cloudflare_config():
                    raise Exception("Failed to update tunnel configuration")

                # Asegurar que el contenedor cloudflared esté corriendo
                if not self.start_cloudflared_container():
                    raise Exception("Failed to start cloudflared container")

                # NOTA: La creación de rutas DNS se maneja por servicio en start(), no aquí
                tunnel_id = tunnel_state.get("id")

                public_url = f"https://{hostname}"
                tunnel_url = f"{tunnel_id}.cfargotunnel.com"

            # Obtener Process ID
            process_id = None
            if is_named_tunnel:
                main_container = self.get_cloudflared_container()
                if main_container:
                    process_id = main_container.id[:12]
            else:
                # Quick Tunnel: crear túnel independiente con URL automática
                public_url = await self._create_quick_tunnel(config.host, port, config.protocol, config)

                hostname = public_url.replace("https://", "")
                
                # Obtener ID del contenedor recién creado
                if port in self.quick_tunnels:
                    quick_data = self.quick_tunnels[port]
                    if quick_data.get("container"):
                        process_id = quick_data["container"].id[:12]

                # Configurar service según protocolo
                if config.protocol.lower() in ["tcp", "ssh"]:
                    service = f"tcp://host.docker.internal:{port}"
                else:
                    service = f"http://host.docker.internal:{port}"

            # Crear TunnelInfo
            metadata = {
                "tunnel_type": "named" if is_named_tunnel else "quick",
                "hostname": hostname,
                "service": service,
                "rule_key": f"{hostname}_{protocol}" if is_named_tunnel else None,
            }

            # Para Named Tunnels, agregar información del CNAME
            if is_named_tunnel:
                metadata["tunnel_id"] = tunnel_id
                metadata["tunnel_url"] = tunnel_url
                metadata["cname_target"] = tunnel_url
                metadata["subdomain"] = config.subdomain
                metadata["domain"] = config.domain
                metadata["dns_auto_managed"] = True  # Indicar que las rutas DNS se manejan automáticamente
                metadata["setup_instructions"] = {
                    "cname_record": {
                        "name": config.subdomain,
                        "target": tunnel_url,
                        "type": "CNAME",
                        "description": f"DNS automático activado: {config.subdomain} -> {tunnel_url}",
                    }
                }

            tunnel_info = TunnelInfo(
                tunnel_id=tunnel_id[:12] if is_named_tunnel else f"quick-{port}",
                public_url=public_url,
                local_target=f"localhost:{port}",
                port=port,
                status=TunnelStatus.RUNNING,
                provider="cloudflare",
                protocol=config.protocol,
                process_id=process_id,
                metadata=metadata,
            )

            # Registrar túnel activo
            self.active_tunnels[port] = tunnel_info

            tunnel_type = "Named" if is_named_tunnel else "Quick"
            logger.info(f"{tunnel_type} Tunnel creado: {public_url} -> localhost:{port}")
            return tunnel_info

        except Exception as e:
            logger.error(f"Error creando túnel Cloudflare: {e}")
            raise TunnelCreationException(f"Error creando túnel: {e}", provider="cloudflare")

    async def _create_quick_tunnel(self, host: str, port: int, protocol: str = "http", config: Optional[TunnelConfig] = None) -> str:
        """Crear un Quick Tunnel individual independiente"""
        try:
            # Nombre del contenedor con short service ID para unicidad
            service_id = config.service_id or "unknown"
            short_id = service_id[:8] if len(service_id) > 8 else service_id
            container_name = f"cloudflared-quick-{port}-{short_id}"

            # Verificar si ya existe un contenedor con este nombrerto
            try:
                existing_container = docker_client.containers.get(container_name)
                if existing_container.status == "running":
                    logger.info(f"Quick Tunnel ya existe para puerto {port}, usando existente")
                    quick_url = self.get_quick_tunnel_url(existing_container, port)
                    if quick_url:
                        self.quick_tunnels[port] = {
                            "container": existing_container,
                            "public_url": quick_url,
                            "host": host,
                            "port": port,
                            "status": "running",
                        }
                        return quick_url
            except docker.errors.NotFound:
                pass

            # Crear contenedor individual para este Quick Tunnel
            if host == "localhost":
                host = "host.docker.internal"

            # Clean up any existing container with the same name (orphaned from previous runs)
            try:
                existing_container = docker_client.containers.get(container_name)
                logger.warning(f"Found existing Cloudflare container {container_name}, removing it")
                try:
                    existing_container.stop(timeout=2)
                except Exception:
                    pass  # Already stopped
                existing_container.remove(force=True)
                logger.info(f"Removed orphaned Cloudflare container {container_name}")
            except docker.errors.NotFound:
                # No existing container, this is expected
                pass
            except Exception as e:
                logger.warning(f"Error cleaning up existing Cloudflare container: {e}")

            # Preparar variables de entorno para tunnel-agent
            environment = {
                "TUNNEL_PORT": str(port),
                "TARGET_HOST": host,  # Use processed host (localhost -> host.docker.internal, or actual IP)
                "TUNNEL_ID": f"cloudflare-{port}",
            }
            
            # Agregar métricas si están habilitadas (usar getattr para campos opcionales)
            enable_analytics = getattr(config, 'enable_analytics', False) if config else False
            backend_url = getattr(config, 'backend_url', None) if config else None
            
            if enable_analytics and backend_url:
                environment["BACKEND_URL"] = backend_url
                environment["METRICS_INTERVAL"] = "10"
            
            # Agregar configuración de healthcheck
            if config:
                environment["HEALTHCHECK_ENABLED"] = str(config.healthcheck_enabled).lower()
                environment["HEALTHCHECK_PATH"] = config.healthcheck_path
                environment["HEALTHCHECK_TIMEOUT"] = str(config.healthcheck_timeout)
                environment["HEALTHCHECK_EXPECTED_STATUS"] = str(config.healthcheck_expected_status)
                environment["HEALTHCHECK_INTERVAL"] = "30"  # Fixed: 30 seconds
                environment["HEALTHCHECK_RETRIES"] = "3"    # Fixed: 3 retries
                environment["BACKEND_URL"] = f"http://host.docker.internal:{settings.app_port}"
                environment["SERVICE_ID"] = service_id

            container = docker_client.containers.run(
                "ghcr.io/localrunapp/cloudflared:latest",
                name=container_name,
                network="bridge",
                extra_hosts={"host.docker.internal": "host-gateway"},
                environment=environment,
                detach=True,
                remove=False,
                restart_policy={"Name": "unless-stopped"},
                labels={
                    "managed-by": "localrun-agent",
                    "tunnel-type": "quick",
                    "tunnel-provider": "cloudflare",
                    "tunnel-port": str(port),
                    "service-id": service_id,
                },
                # Límites de recursos para optimizar memoria/CPU
                mem_limit="32m",  # Límite de 32MB por contenedor
                memswap_limit="32m",  # Sin swap
                cpu_quota=20000,  # 0.2 CPU cores máximo
                cpu_period=100000,
            )

            logger.info(f"Quick Tunnel individual creado: {container_name} para puerto {port}")

            # Esperar y detectar la URL del túnel
            import time

            time.sleep(3)  # Esperar que el túnel se establezca

            # Intentar detectar la URL del Quick Tunnel
            quick_url = self.get_quick_tunnel_url(container, port)
            if not quick_url:
                quick_url = f"https://quick-tunnel-{port}.trycloudflare.com"  # URL fallback
                logger.warning(f"No se pudo detectar URL real, usando fallback: {quick_url}")

            # Guardar referencia del contenedor
            self.quick_tunnels[port] = {
                "container": container,
                "public_url": quick_url,
                "host": host,
                "port": port,
                "status": "running",
            }

            # También registrar en active_tunnels para compatibilidad
            self.active_tunnels[port] = container

            logger.info(f"Quick Tunnel individual creado: puerto {port} -> {quick_url}")
            return quick_url

        except Exception as e:
            # Limpiar si hay error
            if port in self.quick_tunnels:
                del self.quick_tunnels[port]
            logger.error(f"Error creando Quick Tunnel: {e}")
            raise

    async def _ensure_quick_agent_running(self):
        """Ya no necesario - cada túnel se crea individualmente"""
        pass

    def get_quick_agent_container(self):
        """Obtener cualquier contenedor Quick Tunnel corriendo (para detectar URLs)"""
        try:
            containers = docker_client.containers.list(filters={"label": "tunnel-type=quick", "status": "running"})
            if containers:
                return containers[0]  # Retornar el primer contenedor corriendo
            return None
        except Exception as e:
            logger.warning(f"Error obteniendo contenedores Quick: {e}")
            return None

    def get_quick_tunnel_url(self, container, port, max_wait=30):
        """Extraer URL del túnel Quick desde los logs"""
        try:
            import time
            import re

            start_time = time.time()

            while time.time() - start_time < max_wait:
                # Obtener logs recientes
                logs = container.logs(tail=100).decode("utf-8")

                # Buscar patrón de URL de Quick Tunnel
                # Buscar líneas que contengan "https://" y "trycloudflare.com"
                for line in logs.split("\n"):
                    if "https://" in line and "trycloudflare.com" in line:
                        # Usar regex para extraer URL completa
                        url_match = re.search(r"https://[a-zA-Z0-9.-]+\.trycloudflare\.com", line)
                        if url_match:
                            url = url_match.group(0)
                            logger.info(f"URL detectada: {url}")
                            return url

                time.sleep(2)

            logger.warning(f"No se pudo detectar URL después de {max_wait}s")
            return None

        except Exception as e:
            logger.error(f"Error extrayendo URL de Quick Tunnel: {e}")
            return None

    async def stop_tunnel(self, port: int, service_id: str = None) -> bool:
        """Detiene un túnel específico por service_id (preferido) o puerto (fallback)"""
        try:
            container = None
            
            # Method 1: Find by service-id label (most accurate for Quick Tunnels)
            if service_id:
                try:
                    containers = docker_client.containers.list(
                        filters={
                            "label": [
                                "managed-by=localrun-agent",
                                f"service-id={service_id}"
                            ]
                        }
                    )
                    if containers:
                        container = containers[0]
                        logger.info(f"Found Cloudflare container by service-id: {container.name}")
                except Exception as e:
                    logger.warning(f"Error finding Cloudflare container by service-id: {e}")
            
            # Method 2: Fallback - find by port and provider (for old containers)
            if not container:
                try:
                    containers = docker_client.containers.list(
                        filters={
                            "label": [
                                "managed-by=localrun-agent",
                                "tunnel-provider=cloudflare",
                                f"tunnel-port={port}"
                            ]
                        }
                    )
                    if containers:
                        container = containers[0]
                        logger.info(f"Found Cloudflare container by port: {container.name}")
                except Exception as e:
                    logger.warning(f"Error finding Cloudflare container by port: {e}")
            
            # If Quick Tunnel container found, remove it
            if container:
                try:
                    container.remove(force=True)
                    logger.info(f"Contenedor Quick Tunnel eliminado: {container.name}")

                    # Limpiar de registros
                    if port in self.quick_tunnels:
                        del self.quick_tunnels[port]
                    if port in self.active_tunnels:
                        del self.active_tunnels[port]

                    logger.info(f"Quick Tunnel en puerto {port} detenido")
                    return True
                except Exception as e:
                    logger.warning(f"Error eliminando contenedor Quick: {e}")
                    return False

            # Verificar si es Named Tunnel (no usa containers, usa config)
            if port in self.active_tunnels:
                tunnel_info = self.active_tunnels[port]
                rule_key = tunnel_info.metadata.get("rule_key")

                # Remover de managed_rules solo para Named Tunnels
                # NOTA: La gestión DNS se maneja por servicio en stop(), no aquí
                if rule_key and rule_key in managed_rules:
                    del managed_rules[rule_key]
                    logger.info(f"Regla eliminada: {rule_key}")

                    # Actualizar configuración del túnel
                    await self._update_tunnel_config()

                # Remover del registro local
                del self.active_tunnels[port]
                logger.info(f"Named Tunnel en puerto {port} detenido")
                return True

            logger.warning(f"No se encontró túnel activo en puerto {port}")
            return False

        except Exception as e:
            logger.error(f"Error deteniendo túnel para puerto {port}: {e}")
            return False

    async def get_tunnel_status(self, port: int) -> Optional[TunnelInfo]:
        """Obtiene el estado de un túnel específico"""
        return self.active_tunnels.get(port)

    async def list_active_tunnels(self) -> List[TunnelInfo]:
        """Lista todos los túneles activos detectando contenedores Docker reales"""
        try:
            active_tunnels = []

            # 1. Detectar Quick Tunnels - buscar contenedores cloudflared-quick-*
            containers = docker_client.containers.list(filters={"label": "managed-by=localrun-agent"})

            for container in containers:
                try:
                    labels = container.labels
                    tunnel_type = labels.get("tunnel-type", "")
                    port_str = labels.get("port", "")

                    if tunnel_type == "quick" and port_str.isdigit():
                        port = int(port_str)

                        # Intentar obtener URL del Quick Tunnel (con timeout corto)
                        quick_url = self.get_quick_tunnel_url(container, port, max_wait=5)

                        # Si no se puede detectar URL, usar placeholder con estado detectado
                        if not quick_url:
                            quick_url = f"https://quick-tunnel-{port}.trycloudflare.com"
                            logger.info(f"Usando URL placeholder para contenedor {container.name}: {quick_url}")

                        # Detectar protocolo del comando del contenedor
                        protocol = "http"  # default
                        try:
                            # Verificar comando o args del contenedor para detectar protocolo
                            container_info = container.attrs
                            cmd_args = container_info.get("Args", [])
                            if any("tcp://" in str(arg) for arg in cmd_args):
                                protocol = "tcp"
                        except:
                            pass

                        tunnel_info = TunnelInfo(
                            tunnel_id=f"quick-{port}",
                            public_url=quick_url,
                            local_target=f"localhost:{port}",
                            port=port,
                            status=TunnelStatus.RUNNING,
                            provider="cloudflare",
                            protocol=protocol,
                            process_id=container.id[:12],
                            metadata={
                                "tunnel_type": "quick",
                                "container_id": container.id,
                                "container_name": container.name,
                                "container_status": container.status,
                                "detection_method": "docker_container_labels",
                                "expected_container_name": f"cloudflared-quick-{port}",
                            },
                        )
                        active_tunnels.append(tunnel_info)

                        # Sincronizar con active_tunnels en memoria
                        self.active_tunnels[port] = tunnel_info

                except Exception as e:
                    logger.warning(f"Error procesando contenedor {container.name}: {e}")

            # 2. Detectar Named Tunnels - verificar managed_rules con contenedor principal
            main_container = self.get_cloudflared_container()
            if main_container and main_container.status == "running":
                for rule_key, rule_info in managed_rules.items():
                    if rule_info.get("source") == "localrun-agent":
                        port = rule_info.get("port")
                        hostname = rule_info.get("hostname")
                        protocol = rule_info.get("protocol", "http")

                        if port and hostname:
                            tunnel_info = TunnelInfo(
                                tunnel_id=rule_info.get("tunnel_id", f"named-{port}"),
                                public_url=f"https://{hostname}",
                                local_target=f"localhost:{port}",
                                port=port,
                                status=TunnelStatus.RUNNING,
                                provider="cloudflare",
                                protocol=protocol,
                                process_id=main_container.id[:12],
                                metadata={
                                    "tunnel_type": "named",
                                    "hostname": hostname,
                                    "rule_key": rule_key,
                                    "container_id": main_container.id,
                                    "container_name": main_container.name,
                                    "container_status": main_container.status,
                                    "detection_method": "managed_rules_with_container",
                                    "tunnel_id": rule_info.get("tunnel_id"),
                                    "service_url": rule_info.get("service"),
                                },
                            )
                            active_tunnels.append(tunnel_info)

                            # Sincronizar con active_tunnels en memoria
                            self.active_tunnels[port] = tunnel_info

            logger.info(f"Detectados {len(active_tunnels)} túneles activos")
            return active_tunnels

        except Exception as e:
            logger.error(f"Error listando túneles activos: {e}")
            return []

    async def cleanup(self) -> bool:
        """Limpia todos los túneles y recursos"""
        try:
            # Detener todos los túneles
            ports_to_stop = list(self.active_tunnels.keys())
            for port in ports_to_stop:
                await self.stop_tunnel(port)

            # Limpiar managed_rules de localrun-agent
            rules_to_remove = [k for k, v in managed_rules.items() if v.get("source") == "localrun-agent"]
            for rule_key in rules_to_remove:
                del managed_rules[rule_key]

            await self._update_tunnel_config()
            return True

        except Exception as e:
            logger.error(f"Error en cleanup: {e}")
            return False

    def get_provider_info(self) -> Dict[str, Any]:
        """Información del proveedor Cloudflare"""
        return {
            "name": "Cloudflare Tunnels",
            "version": "cloudflared",
            "tunnel_id": tunnel_state.get("id"),
            "tunnel_name": tunnel_state.get("name"),
            "status": tunnel_state.get("status_message", "unknown"),
            "container_status": cloudflared_agent_state.get("container_status", "unknown"),
            "active_rules": len([r for r in managed_rules.values() if r.get("source") == "localrun-agent"]),
            "supports_custom_domains": True,
            "supports_ssl": True,
        }

    async def _ensure_tunnel_initialized(self):
        """Asegura que el túnel esté inicializado usando el Provider"""
        if tunnel_state.get("id"):
            logger.debug(f"Túnel ya inicializado: {tunnel_state.get('id')}")
            return

        # Obtener provider de la BD
        try:
            from sqlmodel import select
            from app.models.provider import Provider
            from core.database import get_db

            db = next(get_db())
            statement = select(Provider).where(Provider.key == "cloudflare")
            provider = db.exec(statement).first()

            if not provider:
                raise Exception("Provider 'cloudflare' no configurado en la BD")

            if not provider.credentials.get("api_token"):
                raise Exception("API token no configurado en el provider")

            tunnel_name = provider.tunnel_name or f"localrun-tunnel-{int(time.time())}"

            # Buscar si el túnel ya existe en Cloudflare
            api_token = provider.credentials["api_token"]

            # Obtener account_id
            import httpx

            headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}

            async with httpx.AsyncClient() as client:
                # Get account_id from zones
                zones_resp = await client.get(f"{self.CF_API}/zones", headers=headers)
                zones_resp.raise_for_status()
                zones_data = zones_resp.json()

                if not zones_data.get("success") or not zones_data.get("result"):
                    raise Exception("No se pudo obtener account_id")

                account_id = zones_data["result"][0]["account"]["id"]

                # Buscar el túnel por nombre
                tunnels_resp = await client.get(f"{self.CF_API}/accounts/{account_id}/cfd_tunnel", headers=headers)
                tunnels_resp.raise_for_status()
                tunnels_data = tunnels_resp.json()

                if tunnels_data.get("success"):
                    # Buscar túnel con el nombre exacto
                    for t in tunnels_data.get("result", []):
                        if t.get("name") == tunnel_name and not t.get("deleted_at"):
                            tunnel_id = t["id"]
                            logger.info(f"Túnel existente encontrado: {tunnel_name} (ID: {tunnel_id})")

                            # Obtener token del túnel
                            token_resp = await client.get(
                                f"{self.CF_API}/accounts/{account_id}/cfd_tunnel/{tunnel_id}/token", headers=headers
                            )
                            token_resp.raise_for_status()
                            token_data = token_resp.json()

                            if token_data.get("success"):
                                tunnel_state["id"] = tunnel_id
                                tunnel_state["name"] = tunnel_name
                                tunnel_state["token"] = token_data["result"]
                                tunnel_state["status_message"] = "Tunnel loaded from API"
                                logger.info(f"Túnel inicializado desde API: {tunnel_id}")
                                return

                # Si no existe, crear uno nuevo
                logger.info(f"Túnel no encontrado, creando nuevo: {tunnel_name}")
                credentials = {"api_token": api_token, "account_id": account_id}
                tunnel_id, token = await self._create_new_tunnel(credentials, tunnel_name)

                tunnel_state["id"] = tunnel_id
                tunnel_state["name"] = tunnel_name
                tunnel_state["token"] = token
                tunnel_state["status_message"] = "New tunnel created"
                logger.info(f"Nuevo túnel creado: {tunnel_id}")

        except Exception as e:
            logger.error(f"Error inicializando túnel: {e}")
            raise Exception(f"No se pudo inicializar el túnel: {e}")

    async def _update_tunnel_config(self):
        """Actualiza la configuración del túnel con las reglas actuales (DockFlare method)"""
        # Reutilizar el método existente de DockFlare
        return self.update_cloudflare_config()

    def _get_credentials(self) -> Optional[Dict[str, str]]:
        """
        Get Cloudflare credentials from Provider (API token) or fallback to cert.pem
        Returns dict with 'api_token' and 'account_id'
        """
        # Try to get from Provider first (modern approach)
        try:
            from sqlmodel import Session, select
            from app.models.provider import Provider
            from core.database import get_db

            # Get database session
            db = next(get_db())

            statement = select(Provider).where(Provider.key == "cloudflare")
            provider = db.exec(statement).first()

            # Validate provider and credentials
            if not provider:
                logger.debug("Provider 'cloudflare' not found in database")
                raise Exception("Provider not found")

            if not isinstance(provider.credentials, dict):
                logger.warning(f"Provider credentials is not a dict: {type(provider.credentials)}")
                raise Exception("Invalid credentials format")

            if not provider.credentials.get("api_token"):
                logger.debug("No api_token in provider credentials")
                raise Exception("No API token")

            api_token = provider.credentials["api_token"]

            # Get account_id from zones endpoint
            import httpx

            headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}

            # Use sync httpx for this
            with httpx.Client() as client:
                zones_resp = client.get(f"{self.CF_API}/zones", headers=headers)
                zones_resp.raise_for_status()
                zones_data = zones_resp.json()

                if zones_data.get("success") and zones_data.get("result"):
                    account_id = zones_data["result"][0]["account"]["id"]
                    logger.info(f"Using API token from Provider (account: {account_id})")
                    return {"api_token": api_token, "account_id": account_id}
        except Exception as e:
            logger.warning(f"Could not get credentials from Provider: {e}")

        # Fallback to cert.pem (legacy approach)
        cert_data = self._extract_cert_data()
        if cert_data:
            logger.info("Using credentials from cert.pem (legacy)")
            return {"api_token": cert_data.api_token, "account_id": cert_data.account_id}

        logger.error("No valid Cloudflare credentials found")
        return None

    def _extract_cert_data(self) -> Optional[Dict[str, str]]:
        """Extract credentials from cert.pem (DockFlare style)"""
        # Try multiple cert.pem locations
        cert_paths = [
            os.path.expanduser("~/.cloudflared/cert.pem"),
            "/home/localrun/.cloudflared/cert.pem",  # Production container path
            settings.get_storage_path("cloudflared", "cert.pem"),  # Storage path
        ]

        cert_path = None
        for path in cert_paths:
            if os.path.exists(path):
                cert_path = path
                break

        if not cert_path:
            logger.error(f"cert.pem not found in paths: {cert_paths}")
            return None

        try:
            with open(cert_path, "r") as f:
                content = f.read()

            import base64

            inside = False
            base64_buffer = []

            for line in content.splitlines():
                line = line.strip()
                if line.startswith("-----BEGIN"):
                    inside = True
                    continue
                if line.startswith("-----END"):
                    break
                if inside:
                    base64_buffer.append(line)

            decoded = base64.b64decode("".join(base64_buffer))
            data = json.loads(decoded.decode("utf-8"))

            logger.info(f"Loaded Cloudflare credentials from: {cert_path}")
            # Return credentials dict directly
            return {
                "api_token": data.get("AccountTag"),
                "account_id": data.get("AccountID")
            }

        except Exception as e:
            logger.error(f"cert.pem decode failed: {e}")
            return None

    def cf_api_request(self, method: str, endpoint: str, json_data=None, params=None):
        """Cloudflare API request using credentials from Provider or cert.pem"""
        credentials = self._get_credentials()
        if not credentials:
            raise RuntimeError("No valid Cloudflare credentials")

        url = f"{self.CF_API}{endpoint}"
        headers = {"Authorization": f"Bearer {credentials['api_token']}", "Content-Type": "application/json"}

        response = requests.request(method, url, headers=headers, params=params, json=json_data)
        response.raise_for_status()

        data = response.json()
        if not data.get("success", False):
            raise RuntimeError(f"Cloudflare API error: {data.get('errors', [])}")

        return data

    def find_tunnel_via_api(self, name: str):
        """Find tunnel by name using API"""
        credentials = self._get_credentials()
        if not credentials:
            return None, None

        endpoint = f"/accounts/{credentials['account_id']}/cfd_tunnel"
        params = {"name": name, "is_deleted": "false"}

        try:
            response_data = self.cf_api_request("GET", endpoint, params=params)
            tunnels = response_data.get("result", [])

            if tunnels and isinstance(tunnels, list):
                for tunnel_entry in tunnels:
                    if tunnel_entry.get("name") == name:
                        tunnel_id = tunnel_entry.get("id")
                        if tunnel_id:
                            logger.info(f"Found existing tunnel '{name}' ID: {tunnel_id}")
                            token = self.get_tunnel_token_via_api(tunnel_id)
                            return tunnel_id, token

            logger.info(f"Tunnel '{name}' not found")
            return None, None

        except Exception as e:
            logger.error(f"Error finding tunnel {name}: {e}")
            tunnel_state["error"] = f"Failed to find tunnel: {e}"
            return None, None

    async def _create_new_tunnel(self, credentials: Dict[str, str], tunnel_name: Optional[str] = None):
        """Crear un nuevo túnel usando las credenciales"""
        if not tunnel_name:
            tunnel_name = f"localrun-tunnel-{int(time.time())}"

        tunnel_id, token = self.create_tunnel_via_api(tunnel_name)

        if not tunnel_id or not token:
            raise Exception("Failed to create new Cloudflare tunnel")

        # Guardar en storage como hace DockFlare
        storage_path = settings.get_storage_path("cloudflared")
        tunnel_file = f"{storage_path}/{tunnel_id}.json"

        # Crear el formato de storage que usa DockFlare
        tunnel_data = {
            "t": tunnel_id,
            "a": credentials["account_id"],  # account_id
            "s": token.split(":")[-1] if ":" in token else token,  # secret
        }

        os.makedirs(storage_path, exist_ok=True)
        with open(tunnel_file, "w") as f:
            json.dump(tunnel_data, f)

        logger.info(f"Tunnel credentials saved to: {tunnel_file}")
        return tunnel_id, token

    def get_tunnel_token_via_api(self, tunnel_id: str):
        """Get tunnel token"""
        credentials = self._get_credentials()
        if not credentials:
            return None

        endpoint = f"/accounts/{credentials['account_id']}/cfd_tunnel/{tunnel_id}/token"

        try:
            response_data = self.cf_api_request("GET", endpoint)
            return response_data.get("result")
        except Exception as e:
            logger.error(f"Failed to get tunnel token for {tunnel_id}: {e}")
            return None

    def create_tunnel_via_api(self, name: str):
        """Create tunnel"""
        credentials = self._get_credentials()
        if not credentials:
            return None, None

        endpoint = f"/accounts/{credentials['account_id']}/cfd_tunnel"
        data = {"name": name, "config_src": "cloudflare"}

        try:
            response_data = self.cf_api_request("POST", endpoint, json_data=data)
            result = response_data.get("result")

            if result:
                tunnel_id = result.get("id")
                logger.info(f"Created tunnel '{name}' with ID: {tunnel_id}")
                token = self.get_tunnel_token_via_api(tunnel_id)
                return tunnel_id, token

            return None, None

        except Exception as e:
            logger.error(f"Failed to create tunnel {name}: {e}")
            tunnel_state["error"] = f"Failed to create tunnel: {e}"
            return None, None

    def update_cloudflare_config(self):
        """Update tunnel ingress configuration"""
        if not tunnel_state.get("id"):
            logger.warning("Cannot update config, no tunnel ID")
            return False

        credentials = self._get_credentials()
        if not credentials:
            return False

        tunnel_id = tunnel_state["id"]

        # Build ingress from managed rules
        ingress = []

        for rule_key, rule_details in managed_rules.items():
            hostname = rule_details.get("hostname")
            service = rule_details.get("service")

            if hostname and service:
                ingress.append({"hostname": hostname, "service": service})

        # Always add catch-all
        ingress.append({"service": "http_status:404"})

        endpoint = f"/accounts/{credentials['account_id']}/cfd_tunnel/{tunnel_id}/configurations"
        config_data = {"config": {"ingress": ingress}}

        try:
            self.cf_api_request("PUT", endpoint, json_data=config_data)
            logger.info(f"Updated tunnel {tunnel_id} ingress with {len(ingress) - 1} services")
            return True
        except Exception as e:
            logger.error(f"Failed to update tunnel config: {e}")
            tunnel_state["error"] = f"Failed to update config: {e}"
            return False

    def initialize_tunnel(self):
        """Initialize tunnel (DockFlare style)"""
        tunnel_name = tunnel_state["name"]
        logger.info(f"Initializing tunnel: {tunnel_name}")

        tunnel_state["status_message"] = "Checking tunnel configuration..."
        tunnel_state["error"] = None

        try:
            # Try to find existing tunnel
            tunnel_id, token = self.find_tunnel_via_api(tunnel_name)

            # Create if not found
            if not tunnel_id and not tunnel_state.get("error"):
                tunnel_state["status_message"] = f"Tunnel '{tunnel_name}' not found. Creating..."
                tunnel_id, token = self.create_tunnel_via_api(tunnel_name)

            if tunnel_id and token:
                tunnel_state["id"] = tunnel_id
                tunnel_state["token"] = token
                tunnel_state["status_message"] = "Tunnel setup complete"
                tunnel_state["error"] = None
                logger.info(f"Tunnel '{tunnel_name}' initialized. ID: {tunnel_id}")
                return True

            tunnel_state["status_message"] = "Tunnel initialization failed"
            tunnel_state["error"] = "Failed to find/create tunnel or get token"
            logger.error(f"Tunnel init failed for '{tunnel_name}'")
            return False

        except Exception as e:
            logger.error(f"Exception during tunnel initialization: {e}")
            tunnel_state["error"] = f"Initialization error: {e}"
            tunnel_state["status_message"] = "Tunnel initialization failed"
            return False

    def get_cloudflared_container(self):
        """Get cloudflared container (DockFlare style)"""
        if not docker_client:
            return None

        container_name = f"cloudflared-agent-{tunnel_state['name']}"

        try:
            container = docker_client.containers.get(container_name)
            container.reload()
            return container
        except (NotFound, APIError):
            return None

    def start_cloudflared_container(self):
        """Start cloudflared container (DockFlare style)"""
        if not docker_client:
            cloudflared_agent_state["last_action_status"] = "Error: Docker client unavailable"
            return False

        if not tunnel_state.get("token"):
            cloudflared_agent_state["last_action_status"] = "Error: Tunnel token not available"
            return False

        container_name = f"cloudflared-agent-{tunnel_state['name']}"
        token = tunnel_state["token"]

        logger.info(f"Starting cloudflared container: {container_name}")
        cloudflared_agent_state["last_action_status"] = "Starting..."

        container = self.get_cloudflared_container()

        if container:
            if container.status == "running":
                msg = f"Container '{container_name}' is already running"
                logger.info(msg)
                cloudflared_agent_state["last_action_status"] = msg
                return True

            logger.info(f"Starting existing container '{container_name}'")
            try:
                container.start()
                msg = f"Started existing container '{container_name}'"
                cloudflared_agent_state["last_action_status"] = msg
                logger.info(msg)
                return True
            except Exception as e:
                logger.warning(f"Failed to start existing container, recreating: {e}")
                container.remove(force=True)
                container = None  # Create new container
        if not container:
            logger.info(f"Creating new cloudflared container: {container_name}")

            try:
                # Pull latest image
                docker_client.images.pull("cloudflare/cloudflared:latest")
            except Exception as e:
                logger.warning(f"Failed to pull image: {e}")

            # Container command - usar token como DockFlare original
            command_parts = ["tunnel", "--no-autoupdate", "run", "--token", token]

            try:
                # Use bridge network with extra_hosts like DockFlare
                network_name = "localrun_default"  # Usar la red del compose
                container_config = {
                    "image": "cloudflare/cloudflared:latest",
                    "command": command_parts,
                    "name": container_name,
                    "detach": True,
                    "restart_policy": {"Name": "unless-stopped"},
                    "labels": {"managed-by": "localrun", "localrun-tunnel": "true"},
                    "network": network_name,
                    "extra_hosts": {"host.docker.internal": "host-gateway"},
                }

                # Create container with bridge network and extra_hosts
                container = docker_client.containers.run(**container_config)

                msg = f"Successfully created container '{container_name}' ({container.id[:12]})"
                cloudflared_agent_state["last_action_status"] = msg
                logger.info(msg)

                # Update container status
                self.update_cloudflared_container_status()
                return True

            except Exception as e:
                msg = f"Failed to create container: {e}"
                logger.error(msg)
                logger.error(f"Container config was: {container_config}")
                logger.error(f"Token format: {token[:20]}...")
                cloudflared_agent_state["last_action_status"] = f"Error: {msg}"
                return False

        return False

    def update_cloudflared_container_status(self):
        """Update container status (DockFlare style)"""
        current_status = cloudflared_agent_state.get("container_status")

        container = self.get_cloudflared_container()
        new_status = "not_found"

        if container:
            try:
                container.reload()
                new_status = container.status
            except (NotFound, APIError) as e:
                new_status = "not_found"
                logger.warning(f"Error reloading container status: {e}")

        if current_status != new_status:
            logger.info(f"Container status changed: {current_status} -> {new_status}")
            cloudflared_agent_state["container_status"] = new_status

    async def start(self, port: int, credentials: Dict[str, Any], config: Optional[Dict[str, Any]] = None):
        """Start tunnel service (DockFlare approach)"""

        # Initialize tunnel if needed
        if not tunnel_state.get("id"):
            if not self.initialize_tunnel():
                raise RuntimeError("Failed to initialize tunnel")

        # Ensure cloudflared container is running
        if not self.start_cloudflared_container():
            raise RuntimeError("Failed to start cloudflared container")

        # Extract configuration (DockFlare approach)
        tunnel_config = config or {}
        protocol = tunnel_config.get("protocol", "http")
        host = tunnel_config.get("host", "localhost")

        # Map localhost to host.docker.internal like DockFlare
        if host in ["localhost", "127.0.0.1", "host"]:
            host = "host.docker.internal"

        service_url = f"{protocol}://{host}:{port}"

        # Generate hostname - support custom domains
        tunnel_id = tunnel_state["id"]
        if tunnel_config.get("domain") and tunnel_config.get("subdomain"):
            hostname = f"{tunnel_config['subdomain']}.{tunnel_config['domain']}"
        else:
            hostname = f"port-{port}-{tunnel_id[:8]}.cfargotunnel.com"

        # Add this service to managed rules
        rule_key = f"port-{port}-{host}"
        managed_rules[rule_key] = {
            "hostname": hostname,
            "service": service_url,
            "port": port,
            "host": host,
            "protocol": protocol,
            "source": "localrun",
            "tunnel_id": tunnel_id,  # Mantener para referencia
        }

        # Update tunnel configuration
        if not self.update_cloudflare_config():
            raise RuntimeError("Failed to update tunnel configuration")

        # NOTA: Gestión DNS se maneja en TunnelsController, no aquí

        public_url = f"https://{hostname}"
        container = self.get_cloudflared_container()
        container_id = container.id if container else "unknown"

        logger.info(f"Service started: {hostname} -> {service_url}")

        return {
            "public_url": public_url,
            "pid": container_id[:12] if container_id != "unknown" else "unknown",
            "process": {"tunnel_id": tunnel_id, "container_id": container_id, "rule_key": rule_key},
        }

    async def stop(self, process) -> None:
        """Stop service (remove from tunnel config)"""
        if isinstance(process, dict) and process.get("rule_key"):
            rule_key = process["rule_key"]
            if rule_key in managed_rules:
                # NOTA: Gestión DNS se maneja en TunnelsController, no aquí

                del managed_rules[rule_key]
                logger.info(f"Removed rule: {rule_key}")

                # Update tunnel configuration
                self.update_cloudflare_config()

    async def get_status(self, process) -> str:
        """Get service status"""
        if isinstance(process, dict) and process.get("container_id"):
            container = self.get_cloudflared_container()
            if container and container.status == "running":
                return "running"
        return "stopped"

    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Validate Cloudflare credentials"""
        cert_data = self._extract_cert_data()
        return cert_data is not None and cert_data.is_valid()

    def _check_cloudflared_cli(self) -> bool:
        """
        Verificar si cloudflared CLI está disponible en el sistema

        Returns:
            bool: True si cloudflared está disponible
        """
        try:
            import subprocess

            result = subprocess.run(["cloudflared", "--version"], capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except Exception:
            return False

    def get_container_details(self) -> Dict[str, Any]:
        """
        Obtener detalles de todos los contenedores relacionados con Localrun
        """
        try:
            containers_info = {
                "quick_tunnels": [],
                "named_tunnel_container": None,
                "total_containers": 0,
                "container_summary": {},
            }

            # Buscar todos los contenedores gestionados por localrun-agent
            containers = docker_client.containers.list(
                all=True,  # Incluir parados también
                filters={"label": "managed-by=localrun-agent"},
            )

            containers_info["total_containers"] = len(containers)

            for container in containers:
                labels = container.labels
                tunnel_type = labels.get("tunnel-type", "unknown")
                port = labels.get("port", "unknown")

                container_detail = {
                    "id": container.id[:12],
                    "name": container.name,
                    "status": container.status,
                    "tunnel_type": tunnel_type,
                    "port": port,
                    "created": container.attrs.get("Created", "unknown"),
                    "labels": labels,
                }

                if tunnel_type == "quick":
                    containers_info["quick_tunnels"].append(container_detail)
                elif container.name == "cloudflared-agent":
                    containers_info["named_tunnel_container"] = container_detail

                # Agregar al summary por tipo
                if tunnel_type not in containers_info["container_summary"]:
                    containers_info["container_summary"][tunnel_type] = {"count": 0, "running": 0, "stopped": 0}

                containers_info["container_summary"][tunnel_type]["count"] += 1
                if container.status == "running":
                    containers_info["container_summary"][tunnel_type]["running"] += 1
                else:
                    containers_info["container_summary"][tunnel_type]["stopped"] += 1

            return containers_info

        except Exception as e:
            logger.error(f"Error obteniendo detalles de contenedores: {e}")
            return {"error": str(e)}
