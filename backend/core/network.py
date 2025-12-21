"""
Network utilities for server discovery and connectivity checks.
"""

import asyncio
import ipaddress
import platform
import socket
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

# TODO: service_detector.py was lost during reorganization - needs to be recreated or removed
# from core.service_detector import service_detector, ServiceInfo
from core.logger import setup_logger

logger = setup_logger(__name__)


def is_localhost_connection(client_ip: str, db) -> bool:
    """
    Detect if connection comes from localhost CLI-agent.
    
    Context: Backend ALWAYS runs in Docker, CLI ALWAYS on host.
    Backend sees host as Docker gateway IP.
    
    Args:
        client_ip: IP address of the client making the request
        db: Database session to query localhost server
        
    Returns:
        True if connection is from localhost, False otherwise
    """
    from sqlmodel import select
    from app.models.server import Server
    
    # Get localhost server from database
    localhost_server = db.exec(
        select(Server).where(Server.is_local == True)
    ).first()
    
    if not localhost_server:
        return False
    
    # Compare client IP with localhost server's network_ip
    # This is the Docker gateway IP (e.g., 172.17.0.1)
    return client_ip == localhost_server.network_ip


@dataclass
class ServiceInfo:
    """Service information for detected services"""
    port: int
    service_name: str
    version: Optional[str] = None
    banner: Optional[str] = None


@dataclass
class NetworkScanResult:
    """Result from scanning a host"""

    host: str
    hostname: Optional[str]
    is_reachable: bool
    os_type: Optional[str]
    open_ports: list[ServiceInfo]


class NetworkUtils:
    """Network utilities for server management"""

    def __init__(self, timeout: int = 3):
        self.timeout = timeout

    async def check_connectivity(self, host: str, port: Optional[int] = None) -> tuple[bool, Optional[float]]:
        """
        Check connectivity to a host and optionally a specific port.

        Args:
            host: Target host IP or hostname
            port: Optional port to check

        Returns:
            Tuple of (is_reachable, latency_ms)
        """
        import time

        try:
            start = time.time()

            if port:
                # Check specific port
                reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=self.timeout)
                writer.close()
                await writer.wait_closed()
            else:
                # Just ping (try to resolve hostname)
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, socket.gethostbyname, host)

            latency = (time.time() - start) * 1000  # Convert to ms
            return True, latency

        except Exception as e:
            logger.debug(f"Connectivity check failed for {host}:{port or 'N/A'}: {e}")
            return False, None

    async def scan_ports(self, host: str, ports: list[int]) -> list[ServiceInfo]:
        """
        Scan multiple ports on a host and detect services.

        Args:
            host: Target host
            ports: List of ports to scan

        Returns:
            List of detected services
        """
        detected_services = []

        # Check ports in parallel
        tasks = [ServiceInfo_detector.check_port(host, port) for port in ports]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # For open ports, detect service
        for port, is_open in zip(ports, results):
            if is_open is True:
                try:
                    service_info = await ServiceInfo_detector.detect_service(host, port)
                    detected_services.append(service_info)
                    logger.info(
                        f"Detected: {host}:{port} -> {service_info.service_name} (confidence: {service_info.confidence})"
                    )
                except Exception as e:
                    logger.debug(f"Service detection failed for {host}:{port}: {e}")

        return detected_services

    async def scan_host(self, host: str, common_ports: bool = True) -> NetworkScanResult:
        """
        Scan a single host for open ports and services.

        Args:
            host: Target host IP
            common_ports: If True, scan common ports. If False, scan all ports (slow)

        Returns:
            NetworkScanResult with findings
        """
        # Common ports to scan
        if common_ports:
            ports = [
                21,
                22,
                23,
                25,
                53,
                80,
                110,
                143,
                443,
                445,
                3000,
                3306,
                3389,
                5000,
                5432,
                5900,
                6379,
                8000,
                8080,
                8123,
                8443,
                8888,
                9000,
                9090,
                27017,
                32400,
            ]
        else:
            ports = list(range(1, 65536))  # All ports (very slow!)

        # Check if host is reachable
        is_reachable, _ = await self.check_connectivity(host)

        if not is_reachable:
            return NetworkScanResult(host=host, hostname=None, is_reachable=False, os_type=None, open_ports=[])

        # Try to get hostname
        hostname = await self._get_hostname(host)

        # Scan ports
        open_ports = await self.scan_ports(host, ports)

        # Try to detect OS (basic)
        os_type = await self._detect_os(host, open_ports)

        return NetworkScanResult(
            host=host, hostname=hostname, is_reachable=True, os_type=os_type, open_ports=open_ports
        )

    async def scan_network(self, network: str = "192.168.1.0/24", max_hosts: int = 254) -> list[NetworkScanResult]:
        """
        Scan an entire network for active hosts.

        Args:
            network: Network in CIDR notation (e.g., '192.168.1.0/24')
            max_hosts: Maximum number of hosts to scan

        Returns:
            List of NetworkScanResult for reachable hosts
        """
        try:
            net = ipaddress.ip_network(network, strict=False)
        except ValueError as e:
            logger.error(f"Invalid network: {network}: {e}")
            return []

        # Get all hosts in network
        hosts = list(net.hosts())[:max_hosts]
        logger.info(f"Scanning {len(hosts)} hosts in {network}...")

        # Quick ping check first (parallel)
        reachable_hosts = []
        tasks = [self.check_connectivity(str(host)) for host in hosts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for host, result in zip(hosts, results):
            if isinstance(result, tuple) and result[0]:
                reachable_hosts.append(str(host))

        logger.info(f"Found {len(reachable_hosts)} reachable hosts")

        # Scan each reachable host
        scan_results = []
        for host in reachable_hosts:
            try:
                result = await self.scan_host(host)
                if result.is_reachable and result.open_ports:
                    scan_results.append(result)
                    logger.info(f"Host {host}: {len(result.open_ports)} services detected")
            except Exception as e:
                logger.error(f"Error scanning {host}: {e}")

        return scan_results

    async def _get_hostname(self, host: str) -> Optional[str]:
        """Get hostname for an IP address"""
        try:
            loop = asyncio.get_event_loop()
            hostname = await loop.run_in_executor(None, socket.gethostbyaddr, host)
            return hostname[0] if hostname else None
        except:
            return None

    async def _detect_os(self, host: str, services: list[ServiceInfo]) -> Optional[str]:
        """
        Basic OS detection based on open services.
        This is a simple heuristic, not accurate.
        """
        # Check for Windows-specific services
        windows_ports = {3389, 445, 135, 139}
        if any(s.port in windows_ports for s in services):
            return "Windows"

        # Check for macOS-specific services
        macos_ports = {548, 5900}  # AFP, VNC
        if any(s.port in macos_ports for s in services):
            return "macOS"

        # Check for Linux-specific patterns
        if any(s.port == 22 for s in services):  # SSH is common on Linux
            return "Linux"

        return None

    def get_local_ip(self) -> str:
        """Get local IP address of this machine"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def get_local_network(self) -> str:
        """
        Get local network in CIDR notation.
        Assumes /24 subnet.
        """
        local_ip = self.get_local_ip()
        if local_ip == "127.0.0.1":
            return "192.168.1.0/24"  # Default fallback

        # Convert to network (assume /24)
        parts = local_ip.split(".")
        network = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
        return network


# Singleton instance
network_utils = NetworkUtils()
