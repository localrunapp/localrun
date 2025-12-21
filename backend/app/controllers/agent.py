from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Request
from typing import Dict, Optional
from sqlmodel import Session, select
import logging
import json
import asyncio
import datetime
import uuid

from core.database import get_db, engine
from core.network import is_localhost_connection
from app.repositories.server_repository import server_repository
from app.models.server import Server
from app.controllers.system_logs import system_logs_controller
from app.schemas.agent import AgentHandshakeRequest, AgentHandshakeResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/agent/handshake", response_model=AgentHandshakeResponse)
async def agent_handshake(
    request: Request,
    handshake: AgentHandshakeRequest,
    db: Session = Depends(get_db)
):
    """
    Handshake endpoint for CLI-agents before WebSocket connection.
    
    Validates server ID and handles localhost ID reconciliation after database resets.
    
    **Returns:**
    - `status: "ok"` - Server found, proceed with WebSocket
    - `status: "id_mismatch"` - Localhost agent with old ID, update required
    - `status: "register_required"` - Remote agent with invalid ID, must register
    """
    agent_id = handshake.server_id
    client_ip = request.client.host
    
    logger.info(f"Handshake from {client_ip} with ID {agent_id[:8]}...")
    
    # Check if server exists
    server = db.get(Server, agent_id)
    
    if server:
        # Server found - all good
        logger.info(f"Handshake OK: Server {server.name} ({agent_id[:8]})")
        return AgentHandshakeResponse(
            status="ok",
            server_id=str(server.id),
            message=f"Server '{server.name}' found, proceed with WebSocket"
        )
    
    # Server not found - check if localhost
    if is_localhost_connection(client_ip, db):
        # This is localhost agent with wrong ID
        localhost_server = db.exec(
            select(Server).where(Server.is_local == True)
        ).first()
        
        if localhost_server:
            logger.warning(
                f"Localhost ID mismatch: agent has {agent_id[:8]}, "
                f"database has {localhost_server.id[:8]}"
            )
            
            # Log to system logs
            await system_logs_controller.log_and_broadcast(
                module="agents",
                severity="warning",
                message=f"Localhost agent ID reconciliation: {agent_id[:8]} → {localhost_server.id[:8]}",
                server_id=str(localhost_server.id),
                server_name="localhost",
                metadata={
                    "old_id": agent_id,
                    "new_id": str(localhost_server.id),
                    "client_ip": client_ip
                }
            )
            
            return AgentHandshakeResponse(
                status="id_mismatch",
                old_id=agent_id,
                server_id=str(localhost_server.id),
                message="Database was reset. Update your agent ID and reconnect."
            )
    
    # Remote agent with invalid ID - must register
    logger.info(f"Handshake: Unknown server {agent_id[:8]} from {client_ip}, registration required")
    
    return AgentHandshakeResponse(
        status="register_required",
        message="Server not found. Please register as a new agent."
    )



class AgentManager:
    """
    Manages control connections to CLI agents.
    Handles registration, configuration, and service discovery.
    """
    def __init__(self):
        # Map of server_id -> WebSocket connection
        self.agents: Dict[str, WebSocket] = {}
        # Map of server_id -> last activity timestamp
        self.last_activity: Dict[str, datetime.datetime] = {}
        self.lock = asyncio.Lock()
        # TTL for agent connections (15 seconds)
        self.agent_ttl_seconds = 15

    async def connect_agent(self, server_id: str, websocket: WebSocket):
        """Register an agent connection."""
        async with self.lock:
            self.agents[server_id] = websocket
            self.last_activity[server_id] = datetime.datetime.utcnow()
        logger.info(f"Agent {server_id} connected to control channel")
        
        # Log to system logs
        await system_logs_controller.log_and_broadcast(
            module="websocket",
            severity="info",
            message="Agent connected to control channel",
            server_id=server_id,
            metadata={"channel": "control"}
        )

    async def disconnect_agent(self, server_id: str):
        """Remove an agent connection."""
        async with self.lock:
            if server_id in self.agents:
                del self.agents[server_id]
            if server_id in self.last_activity:
                del self.last_activity[server_id]
        logger.info(f"Agent {server_id} disconnected from control channel")
        
        # Log to system logs
        await system_logs_controller.log_and_broadcast(
            module="websocket",
            severity="warning",
            message="Agent disconnected from control channel",
            server_id=server_id,
            metadata={"channel": "control"}
        )
    
    async def update_activity(self, server_id: str):
        """Update last activity timestamp for an agent (keepalive)."""
        async with self.lock:
            if server_id in self.agents:
                self.last_activity[server_id] = datetime.datetime.utcnow()
    
    def is_agent_connected(self, server_id: str) -> bool:
        """Check if an agent is currently connected (within TTL)."""
        if server_id not in self.agents or server_id not in self.last_activity:
            return False
        
        # Check if last activity is within TTL
        time_since_activity = datetime.datetime.utcnow() - self.last_activity[server_id]
        return time_since_activity.total_seconds() < self.agent_ttl_seconds
    
    def get_connected_agents(self) -> Dict[str, datetime.datetime]:
        """Get all connected agents with their last activity time."""
        connected = {}
        now = datetime.datetime.utcnow()
        for server_id, last_seen in self.last_activity.items():
            time_since = now - last_seen
            if time_since.total_seconds() < self.agent_ttl_seconds:
                connected[server_id] = last_seen
        return connected

    async def send_to_agent(self, server_id: str, message: dict):
        """Send a message to a specific agent."""
        if server_id in self.agents:
            try:
                await self.agents[server_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending to agent {server_id}: {e}")

    async def broadcast_to_all(self, message: dict):
        """Send a message to all connected agents."""
        async with self.lock:
            for server_id, ws in list(self.agents.items()):
                try:
                    await ws.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error broadcasting to agent {server_id}: {e}")


manager = AgentManager()


@router.websocket("/ws/agent")
async def websocket_agent_control(websocket: WebSocket):
    """
    Agent control channel.
    Handles registration, config updates, and service discovery.
    """
    current_server_id: Optional[str] = None
    keepalive_task = None
    
    async def send_keepalive():
        """Background task to send periodic pings and update activity"""
        while True:
            try:
                await asyncio.sleep(5)  # Send ping every 5 seconds
                if current_server_id:
                    # Send WebSocket ping (protocol level)
                    await websocket.send_json({"type": "ping"})
                    # Update activity on successful send
                    await manager.update_activity(current_server_id)
            except Exception as e:
                logger.error(f"Keepalive error for {current_server_id}: {e}")
                break
    
    try:
        await websocket.accept()
        
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                msg_type = message.get("type")
                
                # Handle registration
                if msg_type == "register":
                    server_id = message.get("server_id")
                    system_info = message.get("system_info", {})
                    is_localhost_agent = message.get("is_localhost", False)  # Agent tells us if it's localhost
                    client_host = websocket.client.host
                    
                    if not server_id:
                        logger.warning("Registration attempt without server_id")
                        await system_logs_controller.log_and_broadcast(
                            module="agents",
                            severity="warning",
                            message="Agent registration failed: missing server_id",
                            metadata={"client_host": client_host}
                        )
                        continue
                    
                    try:
                        with Session(engine) as session:
                            # If agent says it's localhost, force the localhost server ID
                            if is_localhost_agent:
                                local_server = server_repository.get_localhost(session)
                                if local_server:
                                    if local_server.id != server_id:
                                        logger.info(f"Localhost agent with wrong ID ({server_id}). Sending correct ID: {local_server.id}")
                                        await system_logs_controller.log_and_broadcast(
                                            module="agents",
                                            severity="warning",
                                            message=f"Localhost agent ID mismatch - correcting from {server_id[:8]} to {local_server.id[:8]}",
                                            server_id=local_server.id,
                                            server_name="localhost",
                                            metadata={
                                                "old_id": server_id,
                                                "new_id": local_server.id,
                                                "client_host": client_host
                                            }
                                        )
                                        await websocket.send_text(json.dumps({
                                            "type": "config_update",
                                            "config": {"server_id": local_server.id}
                                        }))
                                        continue
                                    else:
                                        # Correct ID, just update
                                        local_ip = message.get("local_ip")
                                        logger.info(f"Localhost agent reconnected from {client_host}, local IP: {local_ip}")
                                        local_server.is_reachable = True
                                        local_server.last_check = datetime.datetime.utcnow()
                                        local_server.os_type = system_info.get('platform', local_server.os_type)
                                        local_server.network_ip = local_ip  # Update with actual local IP
                                        local_server.agent_status = "connected"  # Set agent status
                                        
                                        session.add(local_server)
                                        session.commit()
                                        
                                        current_server_id = local_server.id
                                        await manager.connect_agent(local_server.id, websocket)
                                        
                                        # Start keepalive background task
                                        if not keepalive_task:
                                            keepalive_task = asyncio.create_task(send_keepalive())
                                        
                                        # Log successful registration
                                        await system_logs_controller.log_and_broadcast(
                                            module="agents",
                                            severity="info",
                                            message="Localhost agent registered successfully",
                                            server_id=local_server.id,
                                            server_name="localhost",
                                            metadata={
                                                "os": system_info.get('platform'),
                                                "local_ip": local_ip,
                                                "client_host": client_host
                                            }
                                        )
                                        
                                        await websocket.send_text(json.dumps({
                                            "type": "registration_success",
                                            "server_id": local_server.id
                                        }))
                                        
                                        await websocket.send_text(json.dumps({
                                            "type": "start_service_discovery"
                                        }))
                                        continue

                            server = server_repository.get_by_id(session, server_id)
                            if server:
                                # Conflict Detection: Check if OS matches
                                existing_os = server.os_type
                                incoming_os = system_info.get('platform')
                                
                                if existing_os and incoming_os and existing_os != incoming_os:
                                    logger.warning(f"Conflict detected! Server {server_id} is {existing_os} but agent is {incoming_os}. Forcing new ID.")
                                    
                                    # Log OS conflict
                                    await system_logs_controller.log_and_broadcast(
                                        module="agents",
                                        severity="error",
                                        message=f"OS conflict detected - {existing_os} vs {incoming_os}",
                                        server_id=server_id,
                                        server_name=server.name,
                                        metadata={
                                            "existing_os": existing_os,
                                            "incoming_os": incoming_os,
                                            "action": "forcing_new_id"
                                        }
                                    )
                                    
                                    # Generate new ID
                                    new_server_id = str(uuid.uuid4())
                                    
                                    # Send config update to agent
                                    await websocket.send_text(json.dumps({
                                        "type": "config_update",
                                        "config": {"server_id": new_server_id}
                                    }))
                                    continue

                                logger.info(f"Agent re-connected: {server.name}")
                                server.is_reachable = True
                                server.last_check = datetime.datetime.utcnow()
                                server.agent_status = "connected"  # Set agent status
                                
                                # Update metadata
                                local_ip = message.get("local_ip")
                                server.name = f"{system_info.get('hostname', server.name)}"
                                server.os_type = system_info.get('platform', server.os_type)
                                server.description = f"Agent connected via {client_host}"
                                server.network_ip = local_ip  # Update with actual local IP
                                
                                session.add(server)
                                session.commit()
                                
                                # Register this connection
                                current_server_id = server.id
                                await manager.connect_agent(server.id, websocket)
                                
                                # Start keepalive background task
                                if not keepalive_task:
                                    keepalive_task = asyncio.create_task(send_keepalive())
                                
                                # Log reconnection
                                await system_logs_controller.log_and_broadcast(
                                    module="agents",
                                    severity="info",
                                    message="Remote agent reconnected",
                                    server_id=server.id,
                                    server_name=server.name,
                                    metadata={
                                        "os": system_info.get('platform'),
                                        "hostname": system_info.get('hostname'),
                                        "local_ip": local_ip,
                                        "client_host": client_host
                                    }
                                )
                                
                                # Handshake: Confirm registration
                                await websocket.send_text(json.dumps({
                                    "type": "registration_success",
                                    "server_id": server.id
                                }))
                                
                                # Handshake: Request service discovery
                                await websocket.send_text(json.dumps({
                                    "type": "start_service_discovery"
                                }))
                            else:
                                logger.info(f"New agent registering: {server_id}")
                                local_ip = message.get("local_ip")
                                new_server = Server(
                                    id=server_id,
                                    name=f"{system_info.get('hostname', 'Agent')} ({server_id[:8]})" if not is_localhost_agent else "localhost",
                                    host=client_host,
                                    description=f"Auto-registered via CLI. Platform: {system_info.get('platform')}",
                                    is_local=is_localhost_agent,  # ✅ Use the flag from agent
                                    is_reachable=True,
                                    last_check=datetime.datetime.utcnow(),
                                    os_type=system_info.get('platform'),
                                    network_ip=local_ip,  # Set actual local IP
                                    agent_status="connected",  # Set agent status
                                    cpu_cores=None,
                                    memory_gb=None
                                )
                                session.add(new_server)
                                session.commit()
                                
                                # Register this connection
                                current_server_id = new_server.id
                                await manager.connect_agent(new_server.id, websocket)
                                
                                # Start keepalive background task
                                if not keepalive_task:
                                    keepalive_task = asyncio.create_task(send_keepalive())
                                
                                # Log new agent registration
                                await system_logs_controller.log_and_broadcast(
                                    module="agents",
                                    severity="info",
                                    message=f"New agent registered: {new_server.name}",
                                    server_id=new_server.id,
                                    server_name=new_server.name,
                                    metadata={
                                        "os": system_info.get('platform'),
                                        "hostname": system_info.get('hostname'),
                                        "local_ip": local_ip,
                                        "client_host": client_host,
                                        "is_localhost": is_localhost_agent
                                    }
                                )
                                
                                # Handshake: Confirm registration
                                await websocket.send_text(json.dumps({
                                    "type": "registration_success",
                                    "server_id": new_server.id
                                }))
                                
                                # Handshake: Request service discovery
                                await websocket.send_text(json.dumps({
                                    "type": "start_service_discovery"
                                }))
                    except Exception as e:
                        logger.error(f"Error registering agent: {e}")

                # Handle service discovery results
                elif msg_type == "service_discovery_result":
                    server_id = message.get("server_id")
                    services_data = message.get("data")
                    
                    if server_id and services_data:
                        try:
                            with Session(engine) as session:
                                server = server_repository.get_by_id(session, server_id)
                                if server:
                                    # Update services
                                    server.detected_services = json.dumps(services_data)
                                    
                                    # Update scan status
                                    server.scanning_status = "completed"
                                    server.last_scan_completed = datetime.datetime.utcnow()
                                    
                                    session.add(server)
                                    session.commit()
                                    logger.info(f"Updated services for server {server.name}")
                                    
                                    # Broadcast scan completion via WebSocket
                                    from app.infrastructure.websocket_managers import stats_manager
                                    await stats_manager.broadcast(
                                        server_id,
                                        {
                                            "type": "scan_status",
                                            "status": "completed",
                                            "completed_at": server.last_scan_completed.isoformat(),
                                            "services": services_data
                                        }
                                    )
                        except Exception as e:
                            logger.error(f"Error updating services: {e}")
                
                # Handle ping/pong for keepalive
                elif msg_type == "ping":
                    # Update activity timestamp
                    if current_server_id:
                        await manager.update_activity(current_server_id)
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    
            except json.JSONDecodeError:
                logger.warning("Received non-JSON message on agent control channel")
                
    except WebSocketDisconnect:
        # Cancel keepalive task
        if keepalive_task:
            keepalive_task.cancel()
            try:
                await keepalive_task
            except asyncio.CancelledError:
                pass
        
        if current_server_id:
            await manager.disconnect_agent(current_server_id)
            # Mark server as unreachable
            try:
                with Session(engine) as session:
                    server = server_repository.get_by_id(session, current_server_id)
                    if server:
                        server.is_reachable = False
                        server.agent_status = "disconnected"  # Set agent status
                        server.last_check = datetime.datetime.utcnow()
                        session.add(server)
                        session.commit()
                        
                        # Notify frontend clients about agent disconnection
                        from app.infrastructure.websocket_managers import stats_manager
                        logger.info(f"Broadcasting agent disconnect for {current_server_id}")
                        await stats_manager.broadcast(
                            current_server_id,
                            {
                                "type": "agent_status_change",
                                "agent_status": "disconnected",
                                "timestamp": datetime.datetime.utcnow().isoformat()
                            }
                        )
                        logger.info(f"Agent disconnect notification sent for {current_server_id}")
            except Exception as e:
                logger.error(f"Error marking server unreachable: {e}")


@router.websocket("/agent/servers/{server_id}/stats")
async def websocket_agent_stats(server_id: str, websocket: WebSocket):
    """
    Agent stats channel for a specific server.
    Agent sends stats here, backend stores and broadcasts to frontend.
    """
    await websocket.accept()
    
    # Validate that server exists
    try:
        with Session(engine) as session:
            server = server_repository.get_by_id(session, server_id)
            if not server:
                logger.warning(f"Stats connection rejected: server {server_id} not found in database")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Server not registered. Please reconnect to control channel first."
                }))
                await websocket.close()
                return
    except Exception as e:
        logger.error(f"Error validating server {server_id}: {e}")
        await websocket.close()
        return
    
    logger.info(f"Agent stats channel connected for server {server_id}")
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                stats = json.loads(data)
                
                # Import here to avoid circular dependency
                from app.controllers.servers import servers_controller
                
                # Add stats to storage and broadcast
                await servers_controller.add_server_stats(server_id, stats)
                
            except json.JSONDecodeError:
                logger.warning(f"Received non-JSON stats from agent {server_id}")
            except Exception as e:
                logger.error(f"Error processing stats from agent {server_id}: {e}")
                
    except WebSocketDisconnect:
        logger.info(f"Agent stats channel disconnected for server {server_id}")


@router.websocket("/agent/servers/{server_id}/terminal")
async def websocket_agent_terminal(server_id: str, websocket: WebSocket):
    """
    Agent terminal channel for a specific server.
    Agent provides terminal I/O here, backend bridges with frontend.
    """
    # Import here to avoid circular dependency
    from app.controllers.servers import servers_controller
    
    await servers_controller.terminal_manager.connect_agent(server_id, websocket)
    logger.info(f"Agent terminal channel connected for server {server_id}")
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                # Forward to frontend client
                await servers_controller.terminal_manager.send_to_client(server_id, message)
            except json.JSONDecodeError:
                logger.warning(f"Received non-JSON terminal data from agent {server_id}")
                
    except WebSocketDisconnect:
        servers_controller.terminal_manager.disconnect_agent(server_id)
        logger.info(f"Agent terminal channel disconnected for server {server_id}")
