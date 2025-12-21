"""
Server service - Business logic for server management.
"""

import json
from typing import Optional
from sqlmodel import Session

from app.models.server import Server
from app.repositories.server_repository import server_repository
from core.network import network_utils
from core.network import ServiceInfo
from app.schemas.server import (
    ServerCreate,
    ServerUpdate,
    ConnectivityCheckResponse,
    NetworkScanResult as NetworkScanResultSchema,
    DetectedService,
)
from core.logger import setup_logger

logger = setup_logger(__name__)


class ServerService:
    """Service for server management operations"""

    def __init__(self):
        self.repo = server_repository
        self.network = network_utils

    async def create_server(self, db: Session, server_data: ServerCreate) -> Server:
        """
        Create a new server.

        Args:
            db: Database session
            server_data: Server creation data

        Returns:
            Created server

        Raises:
            ValueError: If server with same host already exists
        """
        # Check if server already exists
        existing = self.repo.get_by_host(db, server_data.host)
        if existing:
            raise ValueError(f"Server with host '{server_data.host}' already exists")

        # Check if it's localhost
        is_local = server_data.host in ["localhost", "127.0.0.1", "::1"]

        # Create server
        server = Server(
            name=server_data.name, host=server_data.host, description=server_data.description, is_local=is_local
        )

        # Check connectivity and detect services
        await self._update_server_info(db, server)

        return self.repo.create(db, server)

    async def update_server(self, db: Session, server_id: str, server_data: ServerUpdate) -> Server:
        """Update server"""
        server = self.repo.get_by_id(db, server_id)
        if not server:
            raise ValueError(f"Server {server_id} not found")

        # Update fields
        if server_data.name is not None:
            server.name = server_data.name
        if server_data.host is not None:
            # Check if new host already exists
            existing = self.repo.get_by_host(db, server_data.host)
            if existing and existing.id != server_id:
                raise ValueError(f"Server with host '{server_data.host}' already exists")
            server.host = server_data.host
            server.is_local = server_data.host in ["localhost", "127.0.0.1", "::1"]
        if server_data.description is not None:
            server.description = server_data.description

        # Re-check connectivity if host changed
        if server_data.host is not None:
            await self._update_server_info(db, server)

        return self.repo.update(db, server)

    def delete_server(self, db: Session, server_id: str) -> bool:
        """Delete server"""
        server = self.repo.get_by_id(db, server_id)
        if not server:
            raise ValueError(f"Server {server_id} not found")

        # Don't allow deleting localhost
        if server.is_local:
            raise ValueError("Cannot delete localhost server")

        return self.repo.delete(db, server)

    def get_server(self, db: Session, server_id: str) -> Server:
        """Get server by ID"""
        server = self.repo.get_by_id(db, server_id)
        if not server:
            raise ValueError(f"Server {server_id} not found")
        return server

    def get_all_servers(self, db: Session, only_reachable: bool = False) -> list[Server]:
        """Get all servers"""
        return self.repo.get_all(db, only_reachable)

    async def check_connectivity(
        self, db: Session, server_id: str, port: Optional[int] = None
    ) -> ConnectivityCheckResponse:
        """
        Check connectivity to a server.

        Args:
            db: Database session
            server_id: Server ID
            port: Optional specific port to check

        Returns:
            ConnectivityCheckResponse
        """
        server = self.repo.get_by_id(db, server_id)
        if not server:
            raise ValueError(f"Server {server_id} not found")

        try:
            is_reachable, latency = await self.network.check_connectivity(server.host, port)

            # Update server status
            self.repo.update_connectivity(db, server, is_reachable)

            return ConnectivityCheckResponse(reachable=is_reachable, latency_ms=latency)
        except Exception as e:
            logger.error(f"Connectivity check failed: {e}")
            return ConnectivityCheckResponse(reachable=False, error=str(e))

    async def scan_server(self, db: Session, server_id: str) -> list[DetectedService]:
        """
        Scan server for open ports and services.

        Args:
            db: Database session
            server_id: Server ID

        Returns:
            List of detected services
        """
        server = self.repo.get_by_id(db, server_id)
        if not server:
            raise ValueError(f"Server {server_id} not found")

        # Scan host
        scan_result = await self.network.scan_host(server.host)

        # Update server info
        detected_services = [
            {
                "port": s.port,
                "protocol": s.protocol,
                "service_name": s.service_name,
                "confidence": s.confidence,
                "version": s.version,
                "banner": s.banner,
            }
            for s in scan_result.open_ports
        ]

        self.repo.update_connectivity(
            db,
            server,
            scan_result.is_reachable,
            detected_services=json.dumps(detected_services),
            os_type=scan_result.os_type,
        )

        # Convert to schema
        return [
            DetectedService(
                port=s.port,
                protocol=s.protocol,
                service_name=s.service_name,
                confidence=s.confidence,
                version=s.version,
                banner=s.banner,
            )
            for s in scan_result.open_ports
        ]

    async def scan_network(self, db: Session, network: Optional[str] = None) -> list[NetworkScanResultSchema]:
        """
        Scan network for active hosts.

        Args:
            db: Database session
            network: Optional network CIDR (defaults to local network)

        Returns:
            List of scan results
        """
        if not network:
            network = self.network.get_local_network()

        logger.info(f"Scanning network: {network}")
        scan_results = await self.network.scan_network(network)

        # Convert to schema
        results = []
        for result in scan_results:
            services = [
                DetectedService(
                    port=s.port,
                    protocol=s.protocol,
                    service_name=s.service_name,
                    confidence=s.confidence,
                    version=s.version,
                    banner=s.banner,
                )
                for s in result.open_ports
            ]

            results.append(
                NetworkScanResultSchema(
                    host=result.host,
                    hostname=result.hostname,
                    is_reachable=result.is_reachable,
                    os_type=result.os_type,
                    open_ports=services,
                )
            )

        return results

    async def _update_server_info(self, db: Session, server: Server):
        """Update server connectivity and detected services"""
        try:
            # Quick connectivity check
            is_reachable, _ = await self.network.check_connectivity(server.host)

            if is_reachable:
                # Scan for services
                scan_result = await self.network.scan_host(server.host)

                detected_services = [
                    {
                        "port": s.port,
                        "protocol": s.protocol,
                        "service_name": s.service_name,
                        "confidence": s.confidence,
                        "version": s.version,
                    }
                    for s in scan_result.open_ports
                ]

                server.is_reachable = True
                server.detected_services = json.dumps(detected_services) if detected_services else None
                server.os_type = scan_result.os_type
            else:
                server.is_reachable = False

        except Exception as e:
            logger.error(f"Error updating server info: {e}")
            server.is_reachable = False

    def ensure_localhost(self, db: Session) -> Server:
        """Ensure localhost server exists"""
        return self.repo.get_localhost(db)


# Singleton instance
server_service = ServerService()
