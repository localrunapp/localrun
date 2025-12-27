"""
Servers Controller
Handles all server-related operations including CRUD, stats, status, and terminal sessions.
"""

from fastapi import WebSocket, WebSocketDisconnect, HTTPException, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import logging
import json
import asyncio
import os
from app.services.server_service import server_service

from sqlmodel import Session
from core.database import engine
from core.auth import get_current_user

# Repositories
from app.repositories.server_repository import server_repository
from app.repositories.server_stats_repository import server_stats_repository

# Infrastructure
from app.infrastructure.websocket_managers import stats_manager, terminal_manager

# Models
from app.models.server import Server

# Schemas
from app.schemas.server import (
    ServerCreate,
    ServerUpdate,
    ServerStatus,
    StatsEntry,
    ServerResponse,
    ServerWithServices,
    ServerDetailResponse,
    DetectedService,
    ConnectivityCheckResponse,
)

# Services (imported in __init__ to avoid circular dependency)
# from app.services.server_service import server_service

# Controllers (imported where needed to avoid circular dependency)
# from app.controllers.agent import manager as agent_manager
# from app.controllers.system import manager

logger = logging.getLogger(__name__)


# ========== Controller ==========


class ServersController:
    """
    Main controller for all server operations.
    Handles CRUD, stats, terminal sessions, and agent commands.
    """

    def __init__(self):
        # Use imported singletons
        self.stats_storage = server_stats_repository
        self.stats_manager = stats_manager
        self.terminal_manager = terminal_manager
        
        # Throttling: Track last DB save per server (server_id -> timestamp)
        self.last_db_save: Dict[str, datetime] = {}
        self.db_save_interval_seconds = 60  # Save to DB once per minute

    # ===== CRUD Operations =====

    async def create_server(self, server_data: ServerCreate) -> ServerResponse:
        """
        Create a new server.

        Register a new server in the system with name, host, and optional description.

        - **name**: Server name (e.g., 'Raspberry Pi')
        - **host**: IP address or hostname (e.g., '192.168.1.100')
        - **description**: Optional description
        """
        try:
            server = Server.create(**server_data.dict())
            return ServerResponse.model_validate(server)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error creating server: {e}")
            raise HTTPException(status_code=500, detail="Failed to create server")

    async def get_server(self, server_id: str) -> Server:
        """Get a specific server (internal use only)."""
        server = Server.find(server_id)
        if not server:
            raise HTTPException(status_code=404, detail="Server not found")
        return server

    async def get_server_by_id(self, server_id: str) -> ServerWithServices:
        """
        Get server by ID.

        Retrieve a specific server with its detected services parsed.
        """
        try:
            server = Server.find(server_id)
            if not server:
                raise ValueError("Server not found")

            # Parse detected services
            services = []
            if server.detected_services:
                try:
                    services = json.loads(server.detected_services)
                except:
                    pass

            response = ServerWithServices.model_validate(server)
            response.services = services
            return response
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Error getting server: {e}")
            raise HTTPException(status_code=500, detail="Failed to get server")

    async def get_server_detail(self, server_id: str) -> ServerDetailResponse:
        """
        Get detailed server information.

        Returns server info including:
        - Real-time CLI agent connection status
        - Agent last seen timestamp
        - Discovered services from CLI agent
        """
        try:
            from app.controllers.agent import manager as agent_manager

            server = Server.find(server_id)
            if not server:
                raise ValueError("Server not found")

            # Parse detected services
            discovered_services = []
            if server.detected_services:
                try:
                    discovered_services = json.loads(server.detected_services)
                except:
                    pass

            # Check real-time agent connection status
            agent_connected = agent_manager.is_agent_connected(server_id)
            agent_installed = server.last_check is not None

            # Get last seen time
            agent_last_seen = None
            if server_id in agent_manager.last_activity:
                agent_last_seen = agent_manager.last_activity[server_id]

            # Build response
            response = ServerDetailResponse.model_validate(server)
            response.agent_installed = agent_installed
            response.agent_connected = agent_connected
            response.agent_last_seen = agent_last_seen
            response.discovered_services = discovered_services

            return response
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Error getting server detail: {e}")
            raise HTTPException(status_code=500, detail="Failed to get server detail")

    async def get_all_servers(self, only_reachable: bool = False) -> list[ServerWithServices]:
        """
        Get all servers.

        Retrieve all servers, optionally filtered by reachability status.

        - **only_reachable**: If true, only return servers that are currently reachable
        """
        try:
            if only_reachable:
                servers = Server.where(is_reachable=True)
            else:
                servers = Server.all()

            # Parse detected services for each
            results = []
            for server in servers:
                services = []
                if server.detected_services:
                    try:
                        services = json.loads(server.detected_services)
                    except:
                        pass

                response = ServerWithServices.model_validate(server)
                response.services = services
                results.append(response)

            return results
        except Exception as e:
            logger.error(f"Error getting servers: {e}")
            raise HTTPException(status_code=500, detail="Failed to get servers")

    async def update_server(self, server_id: str, server_data: ServerUpdate) -> ServerResponse:
        """
        Update server information.

        Update server name, host, or description.
        """
        try:
            server = Server.find(server_id)
            if not server:
                raise ValueError("Server not found")
            
            server.update(**server_data.dict(exclude_unset=True))
            return ServerResponse.model_validate(server)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Error updating server: {e}")
            raise HTTPException(status_code=500, detail="Failed to update server")

    async def delete_server(self, server_id: str) -> dict:
        """
        Delete server.

        Permanently remove a server from the system.
        """
        try:
            server = Server.find(server_id)
            if not server:
                raise ValueError("Server not found")
            
            server.delete()
            return {"message": "Server deleted successfully", "server_id": server_id}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error deleting server: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete server")

    # ===== Connectivity & Scanning =====

    async def check_connectivity(self, server_id: str, port: Optional[int] = None) -> ConnectivityCheckResponse:
        """
        Check server connectivity.

        Test if a server is reachable and measure latency.

        - **port**: Optional port to test (default: ping)
        """
        try:
            server = Server.find(server_id)
            if not server:
                raise ValueError("Server not found")
            
            # TODO: Implement actual connectivity check logic
            # For now, return basic response
            return ConnectivityCheckResponse(
                is_reachable=server.is_reachable,
                latency=0,
                message="Connectivity check completed"
            )
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Error checking connectivity: {e}")
            raise HTTPException(status_code=500, detail="Failed to check connectivity")

    async def scan(self, server_id: str) -> dict:
        """
        Scan server for services.

        Triggers service discovery on the server via CLI agent.
        Updates scanning status in DB and broadcasts via WebSocket.
        Server must be connected (is_reachable = True).
        """
        try:
            server = Server.find(server_id)
            if not server:
                raise ValueError("Server not found")
            
            if not server.is_reachable:
                raise HTTPException(status_code=400, detail="Server is not connected")

            from app.controllers.agent import manager as agent_manager

            # Update DB status to "scanning" using Active Record
            server.scanning_status = "scanning"
            server.last_scan_started = datetime.utcnow()
            server.save()

            # Broadcast WebSocket notification
            await self.stats_manager.broadcast(
                server_id,
                {
                    "type": "scan_status",
                    "status": "scanning",
                    "started_at": server.last_scan_started.isoformat(),
                },
            )

            # Send scan command to agent
            await agent_manager.send_to_agent(
                server_id, {"type": "start_service_discovery"}
            )

            return {
                "message": "Service discovery triggered",
                "server_id": server_id,
                "status": "scanning",
            }
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Error triggering scan: {e}")
            raise HTTPException(status_code=500, detail="Failed to trigger scan")

    # ===== Agent Commands =====

    async def test_port(self, server_id: str, port: int, protocol: str = "tcp") -> dict:
        """
        Test port accessibility.

        Test if a specific port is accessible on the server via CLI agent.
        Server must be connected (is_reachable = True).

        - **port**: Port number to test
        - **protocol**: Protocol (tcp or http)
        """
        try:
            server = Server.find(server_id)
            if not server:
                raise ValueError("Server not found")
            
            if not server.is_reachable:
                raise HTTPException(status_code=400, detail="Server is not connected")

            from app.controllers.agent import manager as agent_manager

            await agent_manager.send_to_agent(
                server_id, {"type": "test_port", "port": port, "protocol": protocol}
            )

            return {
                "success": True,
                "message": f"Port test command sent for {protocol}:{port}",
                "server_id": server_id,
                "port": port,
                "protocol": protocol,
            }
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Error testing port: {e}")
            raise HTTPException(status_code=500, detail="Failed to test port")

    # ===== Stats =====

    async def get_server_stats_history(
        self, server_id: str, hours: int = 168
    ) -> List[StatsEntry]:
        """Get historical stats for a server."""
        # Verify server exists
        await self.get_server(server_id)

        stats = self.stats_storage.get_stats(server_id, hours)
        return [StatsEntry(**s) for s in stats]

    async def get_server_stats_latest(self, server_id: str) -> Optional[StatsEntry]:
        """Get the latest stats for a server."""
        # Verify server exists
        await self.get_server(server_id)

        latest = self.stats_storage.get_latest(server_id)
        if not latest:
            return None
        return StatsEntry(**latest)

    async def add_server_stats(self, server_id: str, stats: Dict[str, Any]):
        """
        Add stats for a server (called by agent).
        
        - Always broadcasts to WebSocket subscribers in real-time
        - Only saves to DB once per minute to prevent saturation
        """
        # Verify server exists
        await self.get_server(server_id)
        
        # Check if we should save to DB (throttling)
        now = datetime.utcnow()
        should_save_to_db = False
        
        if server_id not in self.last_db_save:
            # First time for this server - save
            should_save_to_db = True
        else:
            # Check if enough time has passed
            time_since_last_save = (now - self.last_db_save[server_id]).total_seconds()
            if time_since_last_save >= self.db_save_interval_seconds:
                should_save_to_db = True
        
        # Save to DB only if throttle allows
        if should_save_to_db:
            self.stats_storage.add_stats(server_id, stats)
            self.last_db_save[server_id] = now
            logger.debug(f"Stats saved to DB for server {server_id}")
        else:
            logger.debug(f"Stats skipped DB save for server {server_id} (throttled)")

        # ALWAYS broadcast to WebSocket subscribers (real-time)
        await self.stats_manager.broadcast(
            server_id, {"type": "stats_update", "server_id": server_id, "data": stats}
        )

    # ===== WebSocket Handlers =====

    async def handle_stats_websocket(self, server_id: str, websocket: WebSocket):
        """WebSocket handler for real-time server stats."""
        await self.stats_manager.connect(server_id, websocket)
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
        except WebSocketDisconnect:
            self.stats_manager.disconnect(server_id, websocket)

    async def handle_terminal_websocket(self, server_id: str, websocket: WebSocket):
        """WebSocket handler for terminal sessions."""
        await self.terminal_manager.connect_client(server_id, websocket)
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                await self.terminal_manager.send_to_agent(server_id, message)
        except WebSocketDisconnect:
            self.terminal_manager.disconnect_client(server_id)


# Singleton instance
servers_controller = ServersController()
