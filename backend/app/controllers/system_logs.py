"""
System Logs Controller
Handles system-wide log retrieval, filtering, and real-time streaming via WebSocket.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query as QueryParam, Depends
from typing import List, Optional, Dict, Any
import logging
import asyncio
import json

from app.repositories.log_repository import log_manager
from app.schemas.log_schemas import (
    LogQueryParams,
    PaginatedLogsResponse,
    LogStatsResponse,
    LogEntry as LogEntrySchema,
    PaginationMeta
)


logger = logging.getLogger(__name__)

router = APIRouter()


class LogsWebSocketManager:
    """Manages WebSocket connections for real-time log streaming."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        async with self.lock:
            self.active_connections.append(websocket)
        logger.info(f"Logs WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Logs WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, log_entry: Dict[str, Any]):
        """Broadcast a new log entry to all connected clients."""
        if not self.active_connections:
            return
        
        disconnected = []
        async with self.lock:
            for connection in self.active_connections:
                try:
                    await connection.send_json({
                        "type": "log_entry",
                        "data": log_entry
                    })
                except Exception as e:
                    logger.error(f"Error broadcasting log to client: {e}")
                    disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)


# Global WebSocket manager
ws_manager = LogsWebSocketManager()


class SystemLogsController:
    """Controller for system log operations."""
    
    def __init__(self):
        self.ws_manager = ws_manager
    
    async def log_and_broadcast(
        self,
        severity: str,
        module: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        store: bool = True,
        console: bool = True,
        # Legacy parameters for backward compatibility
        category: Optional[str] = None,
        level: Optional[str] = None,
        server_id: Optional[str] = None,
        server_name: Optional[str] = None,
    ):
        """
        Log an entry and broadcast it to WebSocket clients.
        
        This is the main method to use throughout the application.
        
        Args:
            severity: Log severity (info, warning, error, debug)
            module: Module/category of the log
            message: Log message
            metadata: Optional metadata dict
            store: If True, saves to database (default: True)
            console: If True, outputs to console (default: True)
            
            # Legacy parameters (deprecated, use metadata instead):
            category: Use 'module' instead
            level: Use 'severity' instead
            server_id: Pass in metadata dict
            server_name: Pass in metadata dict
        """
        from core.logger import log
        
        # Handle legacy parameters
        if category is not None:
            module = category
        if level is not None:
            severity = level
        
        # Merge legacy server fields into metadata
        if metadata is None:
            metadata = {}
        if server_id is not None:
            metadata["server_id"] = server_id
        if server_name is not None:
            metadata["server_name"] = server_name
        
        # Use unified logging
        log_id = log(
            severity=severity,
            module=module,
            message=message,
            metadata=metadata,
            store=store,
            console=console,
        )
        
        # Broadcast to WebSocket clients only if stored in DB
        if store and log_id:
            logs = log_manager.get_logs(limit=1)
            if logs:
                await self.ws_manager.broadcast(logs[0])
        
        return log_id


# Global controller instance
system_logs_controller = SystemLogsController()


# REST Endpoints

@router.get("/system/logs", response_model=PaginatedLogsResponse)
async def get_logs(
    search: Optional[str] = QueryParam(None, description="Search term (searches in all fields)"),
    categories: Optional[str] = QueryParam(None, description="Comma-separated categories to filter"),
    levels: Optional[str] = QueryParam(None, description="Comma-separated levels to filter"),
    server_id: Optional[str] = QueryParam(None, description="Filter by server ID"),
    sort_by: str = QueryParam("timestamp", description="Field to sort by"),
    sort_order: str = QueryParam("desc", description="Sort order (asc/desc)"),
    page: int = QueryParam(1, ge=1, description="Page number"),
    page_size: int = QueryParam(50, ge=1, le=500, description="Items per page")
):
    """
    Get logs with advanced filtering, search, sorting, and pagination.
    
    **Query parameters:**
    - `search`: Search term to find in message, server_name, category, level, or metadata
    - `categories`: Comma-separated list of categories (e.g., "backend,services")
    - `levels`: Comma-separated list of levels (e.g., "error,warning")
    - `server_id`: Filter by specific server ID
    - `sort_by`: Field to sort by (timestamp, category, level, server_name, message, server_id)
    - `sort_order`: Sort order (asc or desc)
    - `page`: Page number (1-indexed)
    - `page_size`: Number of items per page (max 500)
    
    **Returns:**
    - `items`: List of log entries for the current page
    - `pagination`: Metadata including total count, page info, and navigation flags
    - `filters`: Applied filters for reference
    """
    # Parse comma-separated values
    categories_list = [c.strip() for c in categories.split(",")] if categories else None
    levels_list = [l.strip() for l in levels.split(",")] if levels else None
    
    # Get paginated results
    result = log_manager.get_logs_paginated(
        search=search,
        categories=categories_list,
        levels=levels_list,
        server_id=server_id,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size
    )
    
    return result



@router.get("/system/logs/recent")
async def get_recent_logs(
    minutes: int = QueryParam(5, description="Number of minutes to look back")
):
    """
    Get logs from the last N minutes.
    
    Query parameters:
    - minutes: Number of minutes to look back (default: 5)
    """
    logs = log_manager.get_recent_logs(minutes=minutes)
    
    return {
        "logs": logs,
        "count": len(logs),
        "minutes": minutes
    }


@router.get("/system/logs/stats", response_model=LogStatsResponse)
async def get_log_stats():
    """
    Get statistics about stored logs.
    
    **Returns:**
    - `total_logs`: Total number of log entries
    - `by_category`: Count of logs per category
    - `by_level`: Count of logs per level
    - `oldest_log`: Timestamp of oldest log entry
    - `newest_log`: Timestamp of newest log entry
    """
    stats = log_manager.get_stats()
    return stats



@router.delete("/system/logs")
async def clear_logs():
    """Clear all logs (admin only - add auth later)."""
    count = log_manager.clear_all_logs()
    
    # Log this action
    await system_logs_controller.log_and_broadcast(
        module="backend",
        severity="warning",
        message=f"All logs cleared ({count} entries removed)",
        metadata={"count": count}
    )
    
    return {
        "message": "All logs cleared",
        "count": count
    }


# WebSocket Endpoint

@router.websocket("/system/logs/stream")
async def websocket_logs_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time log streaming.
    Clients connect here to receive new logs as they are created.
    """
    logger.info(f"Logs WebSocket connection attempt from {websocket.client}")
    await ws_manager.connect(websocket)
    
    try:
        # Send initial recent logs
        recent_logs = log_manager.get_recent_logs(minutes=5)
        await websocket.send_json({
            "type": "initial_logs",
            "data": recent_logs
        })
        
        # Keep connection alive and handle client messages
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                # Handle ping/pong
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                
                # Handle filter updates (future feature)
                elif message.get("type") == "update_filters":
                    # Client-side filtering for now
                    pass
                    
            except json.JSONDecodeError:
                logger.warning("Received non-JSON message on logs WebSocket")
                
    except WebSocketDisconnect:
        logger.info(f"Logs WebSocket disconnected: {websocket.client}")
        ws_manager.disconnect(websocket)
