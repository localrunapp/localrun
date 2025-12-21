import asyncio
import docker
import json
import logging
import os
import time
from typing import Dict, List, Optional, Any

from core.tunnel_driver import (
    AbstractTunnelDriver,
    TunnelConfig,
    TunnelInfo,
    TunnelStatus,
    TunnelCreationException,
    TunnelNotFoundException,
    TunnelProviderException,
)


class NgrokHTTPDriver(AbstractTunnelDriver):
    """
    Driver para ngrok que maneja túneles HTTP usando contenedores Docker.
    Siguiendo el patrón de DockFlare pero para ngrok.
    """

    def __init__(self, auth_token: Optional[str] = None, region: str = "us"):
        super().__init__("ngrok")
        self.auth_token = auth_token
        self.region = region
        self.docker_client = docker.from_env()
        self.container_prefix = "ngrok-tunnel"
        self.network_name = "localrun_default"  # Usar la misma red que el backend

        # Configuración de ngrok
        self.ngrok_image = "ghcr.io/localrunapp/ngrok:latest"

    async def create_tunnel(self, config: TunnelConfig) -> TunnelInfo:
        """
        Crea un túnel ngrok usando Docker.
        """
        try:
            port = config.port

            # Verificar si ya existe un túnel para este puerto
            if self.is_port_active(port):
                raise TunnelCreationException(f"Puerto {port} ya tiene un túnel activo", provider=self.provider_name)

            # Nombre único para el contenedor
            container_name = f"{self.container_prefix}-{port}"

            # Configurar comando ngrok
            ngrok_command = self._build_ngrok_command(config)

            # Variables de entorno
            environment = {}
            if self.auth_token:
                environment["NGROK_AUTHTOKEN"] = self.auth_token

            # Crear y ejecutar contenedor
            container = await self._create_ngrok_container(container_name, ngrok_command, environment, port)

            # Esperar a que ngrok esté listo y obtener URL pública
            public_url = await self._wait_for_ngrok_ready(container, port)

            # Crear información del túnel
            tunnel_info = TunnelInfo(
                tunnel_id=container.id[:12],
                public_url=public_url,
                local_target=f"host.docker.internal:{port}",
                port=port,
                status=TunnelStatus.RUNNING,
                provider=self.provider_name,
                metadata={
                    "container_name": container_name,
                    "container_id": container.id,
                    "region": self.region,
                    "protocol": config.protocol,
                },
            )

            # Registrar túnel activo
            self.active_tunnels[port] = tunnel_info

            logging.info(f"Túnel ngrok creado exitosamente: {public_url} -> localhost:{port}")
            return tunnel_info

        except Exception as e:
            logging.error(f"Error creando túnel ngrok para puerto {config.port}: {e}")
            raise TunnelCreationException(
                f"No se pudo crear túnel para puerto {config.port}: {str(e)}", provider=self.provider_name
            )

    async def stop_tunnel(self, port: int) -> bool:
        """
        Detiene un túnel ngrok por puerto.
        """
        try:
            if not self.is_port_active(port):
                return False

            tunnel_info = self.active_tunnels[port]
            container_name = tunnel_info.metadata.get("container_name")

            # Detener y remover contenedor
            try:
                container = self.docker_client.containers.get(container_name)
                container.stop(timeout=5)
                container.remove(force=True)
                logging.info(f"Contenedor ngrok {container_name} detenido y removido")
            except docker.errors.NotFound:
                logging.warning(f"Contenedor {container_name} no encontrado, probablemente ya fue removido")
            except Exception as e:
                logging.error(f"Error deteniendo contenedor {container_name}: {e}")
                return False

            # Remover del registro
            del self.active_tunnels[port]

            logging.info(f"Túnel ngrok para puerto {port} detenido exitosamente")
            return True

        except Exception as e:
            logging.error(f"Error deteniendo túnel ngrok para puerto {port}: {e}")
            return False

    async def get_tunnel_status(self, port: int) -> Optional[TunnelInfo]:
        """
        Obtiene el estado de un túnel específico.
        """
        if not self.is_port_active(port):
            return None

        tunnel_info = self.active_tunnels[port]

        # Verificar si el contenedor sigue corriendo
        try:
            container_name = tunnel_info.metadata.get("container_name")
            container = self.docker_client.containers.get(container_name)
            container.reload()

            if container.status == "running":
                tunnel_info.status = TunnelStatus.RUNNING
            else:
                tunnel_info.status = TunnelStatus.ERROR

        except docker.errors.NotFound:
            tunnel_info.status = TunnelStatus.ERROR

        return tunnel_info

    async def list_active_tunnels(self) -> List[TunnelInfo]:
        """
        Lista todos los túneles activos.
        """
        # Actualizar estado de todos los túneles
        active_tunnels = []
        for port in list(self.active_tunnels.keys()):
            tunnel_info = await self.get_tunnel_status(port)
            if tunnel_info and tunnel_info.status == TunnelStatus.RUNNING:
                active_tunnels.append(tunnel_info)
            elif tunnel_info and tunnel_info.status == TunnelStatus.ERROR:
                # Remover túneles que ya no están corriendo
                del self.active_tunnels[port]

        return active_tunnels

    async def cleanup(self) -> bool:
        """
        Detiene todos los túneles activos y limpia recursos.
        """
        success = True
        ports_to_stop = list(self.active_tunnels.keys())

        for port in ports_to_stop:
            if not await self.stop_tunnel(port):
                success = False

        return success

    def get_provider_info(self) -> Dict[str, Any]:
        """
        Retorna información específica del proveedor ngrok.
        """
        return {
            "name": "ngrok",
            "version": "3.x",
            "supports_auth": bool(self.auth_token),
            "supports_custom_domains": bool(self.auth_token),
            "supports_regions": True,
            "current_region": self.region,
            "container_image": self.ngrok_image,
            "max_connections_free": 1,
            "max_connections_paid": "unlimited",
        }

    def _build_ngrok_command(self, config: TunnelConfig) -> List[str]:
        """
        Construye el comando ngrok basado en la configuración.
        """
        port = config.port
        protocol = config.protocol

        # Comando base
        command = ["ngrok", protocol, f"host.docker.internal:{port}"]

        # Agregar región si está especificada
        if self.region:
            command.extend(["--region", self.region])

        # Agregar subdominio si está especificado y hay auth token
        if config.subdomain and self.auth_token:
            command.extend(["--subdomain", config.subdomain])

        # Agregar dominio personalizado si está especificado y hay auth token
        if config.domain and self.auth_token:
            command.extend(["--hostname", config.domain])

        return command

    async def _create_ngrok_container(
        self, container_name: str, command: List[str], environment: Dict[str, str], port: int
    ) -> docker.models.containers.Container:
        """
        Crea y ejecuta un contenedor ngrok.
        """
        try:
            # Asegurar que la imagen esté disponible
            try:
                self.docker_client.images.pull(self.ngrok_image)
            except Exception as e:
                logging.warning(f"No se pudo actualizar imagen ngrok: {e}")

            # Configuración del contenedor
            container_config = {
                "image": self.ngrok_image,
                "name": container_name,
                "command": command,
                "environment": environment,
                "network": self.network_name,
                "detach": True,
                "remove": False,
                "restart_policy": {"Name": "no"},
                "extra_hosts": {"host.docker.internal": "host-gateway"},
                "labels": {
                    "managed-by": "localrun-tunneling-agent",
                    "tunnel-provider": "ngrok",
                    "tunnel-port": str(port),
                },
            }

            # Crear y ejecutar contenedor
            container = self.docker_client.containers.run(**container_config)

            logging.info(f"Contenedor ngrok creado: {container_name} ({container.id[:12]})")
            return container

        except Exception as e:
            logging.error(f"Error creando contenedor ngrok: {e}")
            raise

    async def _wait_for_ngrok_ready(
        self, container: docker.models.containers.Container, port: int, timeout: int = 30
    ) -> str:
        """
        Espera a que ngrok esté listo y retorna la URL pública.
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Obtener logs del contenedor para buscar la URL
                logs = container.logs(tail=50).decode("utf-8")

                # Buscar URL pública en los logs
                public_url = self._extract_public_url_from_logs(logs)
                if public_url:
                    return public_url

                # Verificar que el contenedor sigue corriendo
                container.reload()
                if container.status != "running":
                    raise TunnelCreationException(
                        f"Contenedor ngrok se detuvo inesperadamente: {container.status}", provider=self.provider_name
                    )

                await asyncio.sleep(1)

            except Exception as e:
                logging.error(f"Error esperando ngrok: {e}")
                raise

        raise TunnelCreationException(
            f"Timeout esperando que ngrok esté listo para puerto {port}", provider=self.provider_name
        )

    def _extract_public_url_from_logs(self, logs: str) -> Optional[str]:
        """
        Extrae la URL pública de los logs de ngrok.
        """
        try:
            # Buscar líneas que contengan URLs públicas
            for line in logs.split("\n"):
                if "started tunnel" in line.lower() or "forwarding" in line.lower():
                    # Buscar URLs https
                    import re

                    url_pattern = r"https://[a-zA-Z0-9.-]+\.ngrok[a-zA-Z0-9.-]*"
                    matches = re.findall(url_pattern, line)
                    if matches:
                        return matches[0]

                    # Buscar URLs http como fallback
                    url_pattern = r"http://[a-zA-Z0-9.-]+\.ngrok[a-zA-Z0-9.-]*"
                    matches = re.findall(url_pattern, line)
                    if matches:
                        return matches[0]

        except Exception as e:
            logging.error(f"Error extrayendo URL de logs ngrok: {e}")

        return None
