"""
Tunnel Agent Service - Lógica de negocio de túneles Cloudflare

Maneja la creación y gestión de túneles usando cloudflared:
- Quick Tunnels (temporales, URL automática)
- Named Tunnels (persistentes, dominio personalizado)
- Gestión de rutas DNS
- Configuración de ingress

Usa DockerService para operaciones de contenedores
Usa CloudflareDriver para operaciones con Cloudflare API
"""

import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

from app.integrations.cloudflare.tunnel_driver import CloudflaredHTTPDriver as CloudflareDriver
from app.infrastructure.docker_service import docker_service
from core.settings import settings

logger = logging.getLogger(__name__)

# Estado global del túnel Named
tunnel_state = {
    "name": "localrun-tunnel",
    "id": None,
    "token": None,
    "status_message": "Initializing...",
    "error": None,
}

# Reglas de ingress para Named Tunnels
managed_rules: Dict[str, Dict] = {}


class TunnelAgentService:
    """Servicio para gestión de túneles Cloudflare"""

    def __init__(self):
        """Inicializar servicio de túneles"""
        self.docker = docker_service
        self.quick_tunnels: Dict[int, Dict] = {}  # Quick tunnels por puerto
        self._cf_driver: Optional[CloudflareDriver] = None  # Driver de Cloudflare (lazy init)

    def _get_cf_driver(self, api_token: str) -> CloudflareDriver:
        """
        Obtener instancia del driver de Cloudflare (lazy init)

        Args:
            api_token: Token de API de Cloudflare

        Returns:
            CloudflareDriver: Instancia del driver
        """
        if not self._cf_driver or self._cf_driver.api_token != api_token:
            self._cf_driver = CloudflareDriver(api_token)
        return self._cf_driver

    def get_account_id(self, api_token: str) -> str:
        """
        Obtener account_id desde Cloudflare API usando el driver

        Args:
            api_token: Token de API de Cloudflare

        Returns:
            str: Account ID

        Raises:
            Exception: Si no se puede obtener el account_id
        """
        driver = self._get_cf_driver(api_token)
        return driver.get_account_id()

    # ========== Quick Tunnels (Temporales) ==========

    async def create_quick_tunnel(self, port: int, host: str = "localhost", protocol: str = "http") -> str:
        """
        Crear un Quick Tunnel individual con URL automática

        Args:
            port: Puerto local a exponer
            host: Host local (default: localhost)
            protocol: Protocolo (http, tcp, etc.)

        Returns:
            URL pública del túnel
        """
        container_name = f"cloudflared-quick-{port}"

        # Verificar si ya existe
        existing = self.docker.get_container(container_name)
        if existing and existing.status == "running":
            logger.info(f"Quick Tunnel ya existe para puerto {port}")
            url = self._extract_quick_url(existing)
            if url:
                self.quick_tunnels[port] = {
                    "container": existing,
                    "url": url,
                    "port": port,
                    "status": "running",
                }
                return url

        # Configurar comando
        if host == "localhost":
            host = "host.docker.internal"

        if protocol.lower() == "tcp":
            command = ["tunnel", "--url", f"tcp://{host}:{port}", "--no-autoupdate"]
        else:
            command = ["tunnel", "--url", f"http://{host}:{port}", "--no-autoupdate"]

        # Crear contenedor
        try:
            container = self.docker.create_container(
                image="cloudflare/cloudflared:latest",
                name=container_name,
                command=command,
                network="bridge",
                extra_hosts={"host.docker.internal": "host-gateway"},
                labels={
                    "managed-by": "localrun-agent",
                    "tunnel-type": "quick",
                    "port": str(port),
                },
                restart_policy={"Name": "unless-stopped"},
                mem_limit="32m",
                cpu_quota=20000,
            )

            logger.info(f"Quick Tunnel creado: {container_name}")

            # Esperar y obtener URL
            time.sleep(3)
            url = self._extract_quick_url(container)

            if not url:
                url = f"https://quick-tunnel-{port}.trycloudflare.com"
                logger.warning(f"URL no detectada, usando fallback: {url}")

            self.quick_tunnels[port] = {
                "container": container,
                "url": url,
                "port": port,
                "status": "running",
            }

            return url

        except Exception as e:
            logger.error(f"Error creando Quick Tunnel: {e}")
            # Limpiar si hay error
            self.docker.remove_container(container_name, force=True)
            if port in self.quick_tunnels:
                del self.quick_tunnels[port]
            raise

    async def stop_quick_tunnel(self, port: int) -> bool:
        """
        Detener y eliminar Quick Tunnel

        Args:
            port: Puerto del túnel

        Returns:
            True si se detuvo correctamente
        """
        container_name = f"cloudflared-quick-{port}"

        # Eliminar contenedor
        success = self.docker.remove_container(container_name, force=True)

        # Limpiar registro
        if port in self.quick_tunnels:
            del self.quick_tunnels[port]

        if success:
            logger.info(f"Quick Tunnel detenido: puerto {port}")

        return success

    def _extract_quick_url(self, container, max_wait: int = 30) -> Optional[str]:
        """
        Extraer URL del túnel desde los logs

        Args:
            container: Contenedor Docker
            max_wait: Tiempo máximo de espera

        Returns:
            URL del túnel o None
        """
        start_time = time.time()

        while time.time() - start_time < max_wait:
            logs = self.docker.get_container_logs(container.name, tail=100)
            if not logs:
                time.sleep(2)
                continue

            # Buscar patrón de URL
            for line in logs.split("\n"):
                if "https://" in line and "trycloudflare.com" in line:
                    match = re.search(r"https://[a-zA-Z0-9.-]+\.trycloudflare\.com", line)
                    if match:
                        url = match.group(0)
                        logger.info(f"URL detectada: {url}")
                        return url

            time.sleep(2)

        logger.warning(f"No se detectó URL después de {max_wait}s")
        return None

    # ========== Named Tunnels (Persistentes) ==========

    async def ensure_named_tunnel_initialized(
        self, api_token: str, account_id: str, tunnel_name: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Asegurar que el Named Tunnel esté inicializado

        Args:
            api_token: Token de API de Cloudflare
            account_id: ID de cuenta de Cloudflare
            tunnel_name: Nombre del túnel (opcional)

        Returns:
            Dict con tunnel_id y token
        """
        if tunnel_state.get("id") and tunnel_state.get("token"):
            logger.debug(f"Túnel ya inicializado: {tunnel_state['id']}")
            return {"tunnel_id": tunnel_state["id"], "token": tunnel_state["token"]}

        if not tunnel_name:
            tunnel_name = tunnel_state["name"]

        # Buscar túnel existente
        tunnel_id, token = await self._find_tunnel(api_token, account_id, tunnel_name)

        # Crear si no existe
        if not tunnel_id:
            tunnel_id, token = await self._create_tunnel(api_token, account_id, tunnel_name)

        if tunnel_id and token:
            tunnel_state["id"] = tunnel_id
            tunnel_state["name"] = tunnel_name
            tunnel_state["token"] = token
            tunnel_state["status_message"] = "Tunnel initialized"
            tunnel_state["error"] = None

            logger.info(f"Named Tunnel inicializado: {tunnel_id}")
            return {"tunnel_id": tunnel_id, "token": token}

        raise RuntimeError("No se pudo inicializar el Named Tunnel")

    async def create_named_tunnel_route(
        self,
        tunnel_id: str,
        hostname: str,
        port: int,
        protocol: str = "http",
    ) -> bool:
        """
        Crear ruta de ingress para Named Tunnel

        Args:
            tunnel_id: ID del túnel
            hostname: Hostname completo (ej: api.example.com)
            port: Puerto local
            protocol: Protocolo (http, tcp, etc.)

        Returns:
            True si se creó correctamente
        """
        # Configurar service según protocolo
        if protocol.lower() in ["tcp", "ssh"]:
            service = f"tcp://host.docker.internal:{port}"
        else:
            service = f"http://host.docker.internal:{port}"

        # Agregar a managed_rules
        rule_key = f"{hostname}_{protocol}"
        managed_rules[rule_key] = {
            "hostname": hostname,
            "service": service,
            "port": port,
            "protocol": protocol,
            "status": "active",
            "source": "localrun-agent",
        }

        # Actualizar configuración del túnel
        success = await self._update_tunnel_config(tunnel_id)

        if success:
            logger.info(f"Ruta creada: {hostname} -> {service}")

        return success

    async def delete_named_tunnel_route(self, tunnel_id: str, hostname: str, protocol: str = "http") -> bool:
        """
        Eliminar ruta de ingress para Named Tunnel

        Args:
            tunnel_id: ID del túnel
            hostname: Hostname completo
            protocol: Protocolo

        Returns:
            True si se eliminó correctamente
        """
        rule_key = f"{hostname}_{protocol}"

        if rule_key in managed_rules:
            del managed_rules[rule_key]
            logger.info(f"Ruta eliminada: {rule_key}")

            # Actualizar configuración
            return await self._update_tunnel_config(tunnel_id)

        logger.warning(f"Ruta no encontrada: {rule_key}")
        return True

    async def start_named_tunnel_container(self, token: str) -> bool:
        """
        Iniciar contenedor cloudflared para Named Tunnel

        Args:
            token: Token del túnel

        Returns:
            True si se inició correctamente
        """
        container_name = f"cloudflared-agent-{tunnel_state['name']}"

        # Verificar si ya existe
        existing = self.docker.get_container(container_name)
        if existing:
            if existing.status == "running":
                logger.info(f"Contenedor ya está corriendo: {container_name}")
                return True

            # Intentar iniciar existente
            if self.docker.start_container(container_name):
                logger.info(f"Contenedor existente iniciado: {container_name}")
                return True

            # Si falla, eliminar y recrear
            self.docker.remove_container(container_name, force=True)

        # Crear nuevo contenedor
        try:
            command = ["tunnel", "--no-autoupdate", "run", "--token", token]

            container = self.docker.create_container(
                image="cloudflare/cloudflared:latest",
                name=container_name,
                command=command,
                network="localrun_default",
                extra_hosts={"host.docker.internal": "host-gateway"},
                labels={
                    "managed-by": "localrun",
                    "localrun-tunnel": "true",
                    "tunnel-type": "named",
                },
                restart_policy={"Name": "unless-stopped"},
            )

            logger.info(f"Contenedor Named Tunnel creado: {container_name}")
            return True

        except Exception as e:
            logger.error(f"Error creando contenedor Named Tunnel: {e}")
            return False

    # ========== API de Cloudflare ==========

    async def _find_tunnel(
        self, api_token: str, account_id: str, tunnel_name: str
    ) -> tuple[Optional[str], Optional[str]]:
        """Buscar túnel existente por nombre usando CloudflareDriver"""
        try:
            driver = self._get_cf_driver(api_token)
            tunnels = await driver.list_tunnels(account_id, name=tunnel_name)

            for tunnel in tunnels:
                if tunnel.get("name") == tunnel_name and not tunnel.get("deleted_at"):
                    tunnel_id = tunnel["id"]
                    token = await driver.get_tunnel_token(account_id, tunnel_id)
                    logger.info(f"Túnel existente encontrado: {tunnel_name}")
                    return tunnel_id, token

            return None, None

        except Exception as e:
            logger.error(f"Error buscando túnel: {e}")
            return None, None

    async def _create_tunnel(
        self, api_token: str, account_id: str, tunnel_name: str
    ) -> tuple[Optional[str], Optional[str]]:
        """Crear nuevo túnel usando CloudflareDriver"""
        try:
            driver = self._get_cf_driver(api_token)
            tunnel = await driver.create_tunnel(account_id, tunnel_name)

            if tunnel and tunnel.get("id"):
                tunnel_id = tunnel["id"]
                token = await driver.get_tunnel_token(account_id, tunnel_id)

                logger.info(f"Túnel creado: {tunnel_name} (ID: {tunnel_id})")

                # Guardar credenciales
                self._save_tunnel_credentials(tunnel_id, account_id, token)

                return tunnel_id, token

            return None, None

        except Exception as e:
            logger.error(f"Error creando túnel: {e}")
            return None, None

    async def _update_tunnel_config(self, tunnel_id: str) -> bool:
        """Actualizar configuración de ingress del túnel usando CloudflareDriver"""
        # Obtener credenciales
        from sqlmodel import select

        from app.models.provider import Provider
        from core.database import get_db

        db = next(get_db())
        statement = select(Provider).where(Provider.key == "cloudflare")
        provider = db.exec(statement).first()

        if not provider or not provider.credentials.get("api_token"):
            logger.error("No se encontraron credenciales de Cloudflare")
            return False

        api_token = provider.credentials["api_token"]

        # Usar método get_account_id
        try:
            account_id = self.get_account_id(api_token)
        except Exception as e:
            logger.error(f"Error obteniendo account_id: {e}")
            return False

        # Construir ingress
        ingress = []
        for rule_key, rule_info in managed_rules.items():
            hostname = rule_info.get("hostname")
            service = rule_info.get("service")

            if hostname and service:
                ingress.append({"hostname": hostname, "service": service})

        # Usar driver para actualizar config
        try:
            driver = self._get_cf_driver(api_token)
            return await driver.update_tunnel_config(account_id, tunnel_id, ingress)

        except Exception as e:
            logger.error(f"Error actualizando configuración: {e}")
            return False

    def _save_tunnel_credentials(self, tunnel_id: str, account_id: str, token: str):
        """Guardar credenciales del túnel en storage"""
        storage_path = settings.get_storage_path("cloudflared")
        tunnel_file = f"{storage_path}/{tunnel_id}.json"

        # Extraer secret del token
        secret = token.split(":")[-1] if ":" in token else token

        tunnel_data = {
            "t": tunnel_id,
            "a": account_id,
            "s": secret,
        }

        os.makedirs(storage_path, exist_ok=True)
        with open(tunnel_file, "w") as f:
            json.dump(tunnel_data, f)

        logger.info(f"Credenciales guardadas: {tunnel_file}")

    # ========== Operaciones de Listado ==========

    def list_quick_tunnels(self) -> List[Dict[str, Any]]:
        """Listar Quick Tunnels activos"""
        containers = self.docker.list_containers_by_label("tunnel-type", "quick")

        tunnels = []
        for container in containers:
            port_str = container.labels.get("port", "")
            if port_str.isdigit():
                port = int(port_str)
                url = self._extract_quick_url(container, max_wait=5)

                tunnels.append(
                    {
                        "port": port,
                        "url": url or f"https://quick-tunnel-{port}.trycloudflare.com",
                        "status": container.status,
                        "container_id": container.id[:12],
                        "container_name": container.name,
                    }
                )

        return tunnels

    def list_named_tunnel_routes(self) -> List[Dict[str, Any]]:
        """Listar rutas de Named Tunnel"""
        routes = []

        for rule_key, rule_info in managed_rules.items():
            routes.append(
                {
                    "rule_key": rule_key,
                    "hostname": rule_info.get("hostname"),
                    "service": rule_info.get("service"),
                    "port": rule_info.get("port"),
                    "protocol": rule_info.get("protocol"),
                    "status": rule_info.get("status"),
                }
            )

        return routes

    def get_named_tunnel_container_status(self) -> Optional[str]:
        """Obtener estado del contenedor Named Tunnel"""
        container_name = f"cloudflared-agent-{tunnel_state['name']}"
        return self.docker.get_container_status(container_name)

    # ========== Cleanup ==========

    async def cleanup_all_tunnels(self) -> Dict[str, int]:
        """
        Limpiar todos los túneles

        Returns:
            Dict con conteo de túneles eliminados
        """
        quick_cleaned = 0
        named_cleaned = 0

        # Limpiar Quick Tunnels
        quick_ports = list(self.quick_tunnels.keys())
        for port in quick_ports:
            if await self.stop_quick_tunnel(port):
                quick_cleaned += 1

        # Limpiar Named Tunnel routes
        named_cleaned = len(managed_rules)
        managed_rules.clear()

        if tunnel_state.get("id"):
            await self._update_tunnel_config(tunnel_state["id"])

        logger.info(f"Cleanup: {quick_cleaned} Quick, {named_cleaned} Named")

        return {
            "quick_tunnels": quick_cleaned,
            "named_routes": named_cleaned,
        }

    # ========== Sync & Diagnostics ==========

    async def sync_service_states(self, services: List, repo) -> Dict[str, Any]:
        """
        Sincronizar estado de servicios entre BD y túneles reales

        Args:
            services: Lista de servicios de la BD
            repo: ServiceRepository para actualizar estados

        Returns:
            Dict con resultados de la sincronización
        """
        sync_results = []

        # Obtener túneles activos
        quick_tunnels = self.list_quick_tunnels()
        named_routes = self.list_named_tunnel_routes()

        for service in services:
            old_status = service.status
            is_actually_running = False

            # Verificar si está realmente corriendo
            if service.is_quick_service:
                # Buscar en Quick Tunnels
                for tunnel in quick_tunnels:
                    if tunnel["port"] == service.port:
                        is_actually_running = True
                        break
            else:
                # Buscar en Named Tunnel routes
                hostname = f"{service.subdomain}.{service.domain}"
                for route in named_routes:
                    if route["hostname"] == hostname and route["port"] == service.port:
                        is_actually_running = True
                        break

            # Importar ServiceStatus aquí para evitar importación circular
            from app.enums.service import ServiceStatus

            # Sincronizar estado
            if is_actually_running and service.status != ServiceStatus.RUNNING.value:
                repo.update_status(service, ServiceStatus.RUNNING)
                sync_results.append(
                    {
                        "id": service.id,
                        "name": service.name,
                        "old_status": old_status,
                        "new_status": ServiceStatus.RUNNING.value,
                        "synced": True,
                    }
                )

            elif not is_actually_running and service.status == ServiceStatus.RUNNING.value:
                repo.update_status(service, ServiceStatus.STOPPED)
                sync_results.append(
                    {
                        "id": service.id,
                        "name": service.name,
                        "old_status": old_status,
                        "new_status": ServiceStatus.STOPPED.value,
                        "synced": True,
                    }
                )

        synced_count = len([r for r in sync_results if r.get("synced")])

        return {
            "message": f"Sincronización completada: {synced_count} cambios",
            "results": sync_results,
        }

    async def get_diagnostics(self, services: List, repo) -> Dict[str, Any]:
        """
        Obtener diagnósticos del sistema de servicios

        Args:
            services: Lista de servicios de la BD
            repo: ServiceRepository para obtener estadísticas

        Returns:
            Dict con diagnósticos completos
        """
        # Túneles activos
        quick_tunnels = self.list_quick_tunnels()
        named_routes = self.list_named_tunnel_routes()
        named_container_status = self.get_named_tunnel_container_status()

        # Importar ServiceStatus aquí
        from app.enums.service import ServiceStatus

        # Correlaciones
        correlations = []
        inconsistencies = []

        for service in services:
            correlation = {
                "service_id": service.id,
                "name": service.name,
                "port": service.port,
                "type": "named" if service.is_named_service else "quick",
                "db_status": service.status,
                "tunnel_found": False,
                "issue": None,
            }

            # Verificar túnel
            if service.is_quick_service:
                for tunnel in quick_tunnels:
                    if tunnel["port"] == service.port:
                        correlation["tunnel_found"] = True
                        correlation["tunnel_status"] = tunnel["status"]
                        break
            else:
                hostname = f"{service.subdomain}.{service.domain}"
                for route in named_routes:
                    if route["hostname"] == hostname:
                        correlation["tunnel_found"] = True
                        correlation["route_status"] = route["status"]
                        break

            # Detectar inconsistencias
            if service.status == ServiceStatus.RUNNING.value and not correlation["tunnel_found"]:
                correlation["issue"] = "BD dice 'running' pero túnel no existe"
                inconsistencies.append(correlation.copy())

            elif service.status == ServiceStatus.STOPPED.value and correlation["tunnel_found"]:
                correlation["issue"] = "BD dice 'stopped' pero túnel existe"
                inconsistencies.append(correlation.copy())

            correlations.append(correlation)

        # Obtener estadísticas desde repo (asumiendo que services[0] tiene user_id)
        stats = (
            repo.get_statistics(services[0].user_id)
            if services
            else {
                "total": 0,
                "enabled": 0,
                "disabled": 0,
                "running": 0,
                "stopped": 0,
                "error": 0,
            }
        )

        return {
            "database": {
                "total_services": stats["total"],
                "by_status": {
                    "running": stats["running"],
                    "stopped": stats["stopped"],
                    "error": stats["error"],
                },
                "by_type": {
                    "enabled": stats["enabled"],
                    "disabled": stats["disabled"],
                },
            },
            "infrastructure": {
                "quick_tunnels": len(quick_tunnels),
                "named_routes": len(named_routes),
                "named_container_status": named_container_status,
            },
            "correlations": correlations,
            "inconsistencies": inconsistencies,
            "summary": {
                "total_services": len(services),
                "total_tunnels": len(quick_tunnels) + len(named_routes),
                "inconsistencies_count": len(inconsistencies),
                "properly_synced": len(correlations) - len(inconsistencies),
            },
        }


# Instancia singleton
tunnel_agent_service = TunnelAgentService()
