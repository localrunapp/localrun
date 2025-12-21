"""
Logs and monitoring controller
"""

from typing import Dict, Any

from fastapi import HTTPException, WebSocket
import asyncio

from app.models.user import User
from core.storage import storage
from core.logger import setup_logger

logger = setup_logger(__name__)


class LogsController:
    """Controller for logs and monitoring operations."""

    async def get_tunnel_logs(self, tunnel_id: str, lines: int, current_user: User) -> Dict[str, Any]:
        """
        Get recent logs for a tunnel.

        Args:
            tunnel_id: Tunnel ID
            lines: Number of log lines to retrieve
            current_user: Authenticated user

        Returns:
            Tunnel logs data
        """
        logger.info(f"Fetching {lines} log lines for tunnel {tunnel_id}")

        tunnel = await storage.get_tunnel(tunnel_id)

        if not tunnel or tunnel.user_id != current_user.id:
            logger.warning(f"Tunnel not found: {tunnel_id}")
            raise HTTPException(status_code=404, detail="Tunnel not found")

        # TODO: Implement log collection from supervisor
        logger.info(f"Log retrieval not yet implemented for tunnel {tunnel_id}")

        return {"tunnel_id": tunnel_id, "logs": []}

    async def websocket_logs(self, websocket: WebSocket, tunnel_id: str) -> None:
        """
        WebSocket endpoint for real-time logs.

        Args:
            websocket: WebSocket connection
            tunnel_id: Tunnel ID
        """
        await websocket.accept()
        logger.info(f"WebSocket connection opened for tunnel {tunnel_id}")

        # TODO: Implement WebSocket authentication
        # TODO: Stream logs in real-time from supervisor

        try:
            while True:
                await asyncio.sleep(1)
                await websocket.send_json({"tunnel_id": tunnel_id, "logs": ["[INFO] Tunnel running..."]})
        except Exception as e:
            logger.warning(f"WebSocket connection closed for tunnel {tunnel_id}: {e}")
            await websocket.close()
