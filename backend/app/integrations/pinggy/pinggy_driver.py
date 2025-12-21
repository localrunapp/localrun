"""
Pinggy Tunnel Driver

Driver for Pinggy tunnels using ghcr.io/localrunapp/pinggy Docker image.
"""

import asyncio
import docker
import logging
import re
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

logger = logging.getLogger(__name__)


class PinggyDriver(AbstractTunnelDriver):
    """
    Driver for Pinggy tunnels using Docker containers.
    Uses the optimized tunnel-agent image from ghcr.io/localrunapp/pinggy
    """

    def __init__(self):
        super().__init__("pinggy")
        self.docker_client = docker.from_env()
        self.container_prefix = "pinggy-tunnel"
        self.pinggy_image = "ghcr.io/localrunapp/pinggy:latest"

    def supports_protocol(self, protocol: str) -> bool:
        """Pinggy supports HTTP, HTTPS, TCP"""
        return protocol.lower() in ["http", "https", "tcp"]

    def supports_named_tunnels(self) -> bool:
        """Pinggy supports named/custom domain tunnels with paid plan"""
        return True

    async def create_tunnel(self, config: TunnelConfig) -> TunnelInfo:
        """
        Creates a Pinggy tunnel using Docker container.
        """
        try:
            port = config.port
            host = config.host or "localhost"

            # Check if tunnel already exists for this port
            if self.is_port_active(port):
                raise TunnelCreationException(
                    f"Port {port} already has an active tunnel",
                    provider=self.provider_name
                )

            # Container name with short service ID for uniqueness
            service_id = config.service_id or "unknown"
            short_id = service_id[:8] if len(service_id) > 8 else service_id
            container_name = f"{self.container_prefix}-{port}-{short_id}"

            # Clean up any existing container with the same name (orphaned from previous runs)
            try:
                existing_container = self.docker_client.containers.get(container_name)
                logger.warning(f"Found existing container {container_name}, removing it")
                try:
                    existing_container.stop(timeout=2)
                except Exception:
                    pass  # Already stopped
                existing_container.remove(force=True)
                logger.info(f"Removed orphaned container {container_name}")
            except docker.errors.NotFound:
                # No existing container, this is expected
                pass
            except Exception as e:
                logger.warning(f"Error cleaning up existing container: {e}")

            # Prepare host for Docker
            if host == "localhost":
                host = "host.docker.internal"

            # Environment variables for tunnel-agent
            environment = {
                "TUNNEL_PORT": str(port),
                "TARGET_HOST": host,
                "TUNNEL_ID": f"pinggy-{port}",
            }

            # Create and run container
            container = await self._create_pinggy_container(
                container_name, environment, port, service_id
            )

            # Wait for Pinggy to be ready and get public URL
            public_url = await self._wait_for_pinggy_ready(container, port)

            # Create tunnel info
            tunnel_info = TunnelInfo(
                tunnel_id=container.id[:12],
                public_url=public_url,
                local_target=f"localhost:{port}",
                port=port,
                status=TunnelStatus.RUNNING,
                provider=self.provider_name,
                protocol=config.protocol,
                process_id=container.id[:12],
                metadata={
                    "container_name": container_name,
                    "container_id": container.id,
                    "protocol": config.protocol,
                    "tunnel_type": "quick",
                },
            )

            # Register active tunnel
            self.active_tunnels[port] = tunnel_info

            logger.info(f"Pinggy tunnel created: {public_url} -> localhost:{port}")
            return tunnel_info

        except Exception as e:
            logger.error(f"Error creating Pinggy tunnel for port {config.port}: {e}")
            raise TunnelCreationException(
                f"Failed to create tunnel for port {config.port}: {str(e)}",
                provider=self.provider_name
            )

    async def stop_tunnel(self, port: int, service_id: str = None) -> bool:
        """
        Stops a Pinggy tunnel by service_id (preferred) or port (fallback).
        Finds container by service-id label for accurate identification.
        """
        try:
            logger.info(f"Attempting to stop Pinggy tunnel - port: {port}, service_id: {service_id}")
            
            container = None
            
            # Method 1: Find by service-id label (most accurate)
            if service_id:
                try:
                    containers = self.docker_client.containers.list(
                        filters={
                            "label": [
                                "managed-by=localrun-agent",
                                f"service-id={service_id}"
                            ]
                        }
                    )
                    if containers:
                        container = containers[0]
                        logger.info(f"Found container by service-id: {container.name}")
                except Exception as e:
                    logger.warning(f"Error finding container by service-id: {e}")
            
            # Method 2: Fallback - find by port and provider
            if not container:
                try:
                    containers = self.docker_client.containers.list(
                        filters={
                            "label": [
                                "managed-by=localrun-agent",
                                "tunnel-provider=pinggy",
                                f"tunnel-port={port}"
                            ]
                        }
                    )
                    if containers:
                        container = containers[0]
                        logger.info(f"Found container by port: {container.name}")
                except Exception as e:
                    logger.warning(f"Error finding container by port: {e}")
            
            # If container found, stop and remove it
            if container:
                try:
                    logger.info(f"Stopping container {container.name}...")
                    container.stop(timeout=5)
                    logger.info(f"Container stopped, now removing...")
                    container.remove(force=True)
                    logger.info(f"Pinggy container {container.name} stopped and removed successfully")
                except Exception as e:
                    logger.error(f"Error stopping/removing container: {e}", exc_info=True)
                    return False
            else:
                logger.warning(f"No Pinggy container found for port {port}, service_id {service_id}")
                # Check if it's in our registry
                if port not in self.active_tunnels:
                    return False

            # Remove from registry if it exists
            if port in self.active_tunnels:
                del self.active_tunnels[port]
                logger.info(f"Removed port {port} from active_tunnels")

            logger.info(f"Pinggy tunnel for port {port} stopped successfully")
            return True

        except Exception as e:
            logger.error(f"Error stopping Pinggy tunnel for port {port}: {e}", exc_info=True)
            return False

    async def get_tunnel_status(self, port: int) -> Optional[TunnelInfo]:
        """
        Gets the status of a specific tunnel.
        """
        if not self.is_port_active(port):
            return None

        tunnel_info = self.active_tunnels[port]

        # Check if container is still running
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
        Lists all active tunnels.
        """
        active_tunnels = []
        for port in list(self.active_tunnels.keys()):
            tunnel_info = await self.get_tunnel_status(port)
            if tunnel_info and tunnel_info.status == TunnelStatus.RUNNING:
                active_tunnels.append(tunnel_info)
            elif tunnel_info and tunnel_info.status == TunnelStatus.ERROR:
                # Remove tunnels that are no longer running
                del self.active_tunnels[port]

        return active_tunnels

    async def cleanup(self) -> bool:
        """
        Stops all active tunnels and cleans up resources.
        """
        success = True
        ports_to_stop = list(self.active_tunnels.keys())

        for port in ports_to_stop:
            if not await self.stop_tunnel(port):
                success = False

        return success

    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """
        Validates Pinggy credentials (token for paid plans).
        For quick tunnels, no credentials needed.
        """
        # Quick tunnels don't need credentials
        if not credentials:
            return True
        
        # For named tunnels, validate token if provided
        token = credentials.get("token") or credentials.get("auth_token")
        if token:
            # Pinggy tokens are typically in format: pinggy_xxxxx
            return isinstance(token, str) and len(token) > 0
        
        return True

    def get_provider_info(self) -> Dict[str, Any]:
        """
        Returns Pinggy provider information.
        """
        return {
            "name": "Pinggy",
            "version": "latest",
            "supports_auth": True,
            "supports_custom_domains": True,
            "supports_regions": False,
            "container_image": self.pinggy_image,
            "tunnel_type": "SSH-based",
        }

    async def _create_pinggy_container(
        self, container_name: str, environment: Dict[str, str], port: int, service_id: str
    ) -> docker.models.containers.Container:
        """
        Creates and runs a Pinggy container.
        """
        try:
            # Pull image if needed
            try:
                self.docker_client.images.pull(self.pinggy_image)
            except Exception as e:
                logger.warning(f"Could not pull Pinggy image: {e}")

            # Container configuration
            container_config = {
                "image": self.pinggy_image,
                "name": container_name,
                "environment": environment,
                "network": "bridge",
                "detach": True,
                "remove": False,
                "restart_policy": {"Name": "unless-stopped"},
                "extra_hosts": {"host.docker.internal": "host-gateway"},
                "labels": {
                    "managed-by": "localrun-agent",
                    "tunnel-provider": "pinggy",
                    "tunnel-port": str(port),
                    "service-id": service_id,  # Add service ID for identification
                },
                # Resource limits
                "mem_limit": "32m",
                "memswap_limit": "32m",
                "cpu_quota": 20000,
                "cpu_period": 100000,
            }

            # Create and run container
            container = self.docker_client.containers.run(**container_config)

            logger.info(f"Pinggy container created: {container_name} ({container.id[:12]})")
            return container

        except Exception as e:
            logger.error(f"Error creating Pinggy container: {e}")
            raise

    async def _wait_for_pinggy_ready(
        self, container: docker.models.containers.Container, port: int, timeout: int = 30
    ) -> str:
        """
        Waits for Pinggy to be ready and returns the public URL.
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Get container logs to find the URL
                logs = container.logs(tail=50).decode("utf-8")

                # Extract public URL from logs
                public_url = self._extract_public_url_from_logs(logs)
                if public_url:
                    return public_url

                # Check container is still running
                container.reload()
                if container.status != "running":
                    raise TunnelCreationException(
                        f"Pinggy container stopped unexpectedly: {container.status}",
                        provider=self.provider_name
                    )

                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error waiting for Pinggy: {e}")
                raise

        raise TunnelCreationException(
            f"Timeout waiting for Pinggy to be ready for port {port}",
            provider=self.provider_name
        )

    def _extract_public_url_from_logs(self, logs: str) -> Optional[str]:
        """
        Extracts the public URL from Pinggy logs.
        Pinggy outputs URLs in format: https://xxxxx-xxx-xxx-xxx-xxx.a.free.pinggy.link
        """
        try:
            # Look for Pinggy URLs in logs
            for line in logs.split("\n"):
                # Match Pinggy free URL pattern (with dashes and dots)
                url_pattern = r"https?://[a-zA-Z0-9-]+\.a\.free\.pinggy\.link"
                matches = re.findall(url_pattern, line)
                if matches:
                    return matches[0]

                # Also try paid/pro URL pattern
                url_pattern_pro = r"https?://[a-zA-Z0-9-]+\.a\.pinggy\.link"
                matches = re.findall(url_pattern_pro, line)
                if matches:
                    return matches[0]

                # Also try TCP format if applicable
                tcp_pattern = r"tcp://[a-zA-Z0-9-]+\.a\.(?:free\.)?pinggy\.link:\d+"
                matches = re.findall(tcp_pattern, line)
                if matches:
                    return matches[0]

        except Exception as e:
            logger.error(f"Error extracting URL from Pinggy logs: {e}")

        return None
