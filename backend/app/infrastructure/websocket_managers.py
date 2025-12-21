"""
WebSocket Managers for Server Operations
Handles WebSocket connections for stats broadcasting and terminal sessions.
"""

from fastapi import WebSocket
from typing import Dict, List, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)


class ServerStatsManager:
    """
    Manages WebSocket connections for per-server stats broadcasting.
    """

    def __init__(self):
        # Map of server_id -> list of WebSocket connections
        self.connections: Dict[str, List[WebSocket]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, server_id: str, websocket: WebSocket):
        """Register a WebSocket connection for a specific server."""
        await websocket.accept()
        async with self.lock:
            if server_id not in self.connections:
                self.connections[server_id] = []
            self.connections[server_id].append(websocket)
        logger.info(
            f"Stats WebSocket connected for server {server_id}. Total: {len(self.connections[server_id])}"
        )

    def disconnect(self, server_id: str, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if server_id in self.connections and websocket in self.connections[server_id]:
            self.connections[server_id].remove(websocket)
            if not self.connections[server_id]:
                del self.connections[server_id]
        logger.info(f"Stats WebSocket disconnected for server {server_id}")

    async def broadcast(self, server_id: str, message: dict):
        """Broadcast stats to all clients subscribed to this server."""
        if server_id not in self.connections:
            return

        disconnected = []
        async with self.lock:
            for connection in self.connections[server_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to client: {e}")
                    disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(server_id, conn)


class ServerTerminalManager:
    """
    Manages terminal WebSocket connections per server.
    Bridges frontend clients with agent terminals.
    """

    def __init__(self):
        # Map of server_id -> {"client": WebSocket, "agent": WebSocket}
        self.sessions: Dict[str, Dict[str, Optional[WebSocket]]] = {}
        self.lock = asyncio.Lock()

    async def connect_client(self, server_id: str, websocket: WebSocket):
        """Connect a frontend client to a server's terminal."""
        await websocket.accept()
        async with self.lock:
            if server_id not in self.sessions:
                self.sessions[server_id] = {"client": None, "agent": None}
            self.sessions[server_id]["client"] = websocket
        logger.info(f"Terminal client connected for server {server_id}")

    async def connect_agent(self, server_id: str, websocket: WebSocket):
        """Connect an agent to provide terminal for this server."""
        await websocket.accept()
        async with self.lock:
            if server_id not in self.sessions:
                self.sessions[server_id] = {"client": None, "agent": None}
            self.sessions[server_id]["agent"] = websocket
        logger.info(f"Terminal agent connected for server {server_id}")

    def disconnect_client(self, server_id: str):
        """Disconnect client."""
        if server_id in self.sessions:
            self.sessions[server_id]["client"] = None

    def disconnect_agent(self, server_id: str):
        """Disconnect agent."""
        if server_id in self.sessions:
            self.sessions[server_id]["agent"] = None

    async def send_to_agent(self, server_id: str, message: dict):
        """Send message from client to agent."""
        if server_id in self.sessions and self.sessions[server_id]["agent"]:
            try:
                await self.sessions[server_id]["agent"].send_json(message)
            except Exception as e:
                logger.error(f"Error sending to agent: {e}")

    async def send_to_client(self, server_id: str, message: dict):
        """Send message from agent to client."""
        if server_id in self.sessions and self.sessions[server_id]["client"]:
            try:
                await self.sessions[server_id]["client"].send_json(message)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")


# Singleton instances
stats_manager = ServerStatsManager()
terminal_manager = ServerTerminalManager()
