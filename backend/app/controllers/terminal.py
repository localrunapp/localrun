from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Optional
import logging
import json
import asyncio
import datetime
from sqlmodel import Session
from core.database import engine
from app.repositories.server_repository import server_repository
from app.models.server import Server

logger = logging.getLogger(__name__)

router = APIRouter()


from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import logging
import json
import asyncio
from app.infrastructure.websocket_managers import terminal_manager

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws/terminal/client")
async def websocket_client_endpoint(
    websocket: WebSocket,
    server_id: Optional[str] = Query(None)
):
    """
    Terminal client endpoint.
    Connects frontend to a server's terminal session.
    """
    # If no server_id provided, we might need a default or error
    # For now, let's assume if it's hitting this, it wants the "local" one or a specific one
    # If server_id is None, maybe we look for a "connected" local server?
    
    if not server_id:
        # Fallback for backward compatibility or local dev
        # Ideally frontend always sends server_id
        await websocket.close(code=1000, reason="Missing server_id")
        return

    await terminal_manager.connect_client(server_id, websocket)

    # Notify client of status
    # We check if agent is connected for this server
    if terminal_manager.sessions.get(server_id, {}).get("agent"):
        await websocket.send_text(json.dumps({"type": "status", "status": "online"}))
    else:
        await websocket.send_text(json.dumps({"type": "status", "status": "offline"}))

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                # Client sends: {"type": "input", "data": "..."} or {"type": "resize", ...}
                # Agent expects directly the message object or wrapped? 
                # servers_controller.handle_terminal_websocket iterates and forwards.
                
                # Check agent expectation in cli-agent code:
                # It receives {"type": "terminal_input", ...} or {"type": "terminal_resize", ...}
                
                msg_type = message.get("type")
                if msg_type == "input":
                    agent_message = {
                        "type": "terminal_input",
                        "data": message.get("data", "")
                    }
                    await terminal_manager.send_to_agent(server_id, agent_message)
                    
                elif msg_type == "resize":
                    agent_message = {
                        "type": "terminal_resize",
                        "cols": message.get("cols", 80),
                        "rows": message.get("rows", 24)
                    }
                    await terminal_manager.send_to_agent(server_id, agent_message)
                else:
                    await terminal_manager.send_to_agent(server_id, message)
                    
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        terminal_manager.disconnect_client(server_id)

