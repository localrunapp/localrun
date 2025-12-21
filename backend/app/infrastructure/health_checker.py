"""
Server Health Check Service
Periodically pings servers to check network reachability.
Independent of CLI agent connections.
"""

import asyncio
import logging
from typing import Dict
from sqlmodel import Session
from datetime import datetime

from core.database import engine
from app.repositories.server_repository import server_repository
from core.network import NetworkUtils

logger = logging.getLogger(__name__)


class ServerHealthChecker:
    """
    Background service that periodically checks server reachability via ping.
    This is independent of CLI agent connections.
    """
    
    def __init__(self, check_interval: int = 60):
        """
        Initialize health checker.
        
        Args:
            check_interval: Seconds between health checks (default: 60)
        """
        self.check_interval = check_interval
        self.network = NetworkUtils()
        self.running = False
        self.task = None
    
    async def check_server_health(self, server_id: str, host: str) -> bool:
        """
        Check if a server is reachable via ping.
        
        Args:
            server_id: Server ID
            host: Server host/IP to ping
            
        Returns:
            True if reachable, False otherwise
        """
        try:
            # Skip localhost - always reachable
            if host in ['127.0.0.1', 'localhost', '::1']:
                return True
            
            # Ping the server
            is_reachable, latency = await self.network.check_connectivity(host)
            
            if is_reachable:
                logger.debug(f"Server {server_id} ({host}) is reachable (latency: {latency}ms)")
            else:
                logger.warning(f"Server {server_id} ({host}) is unreachable")
            
            return is_reachable
            
        except Exception as e:
            logger.error(f"Error checking health for server {server_id}: {e}")
            return False
    
    async def check_all_servers(self):
        """Check health of all registered servers."""
        try:
            with Session(engine) as session:
                # Get all servers
                servers = server_repository.get_all(session)
                
                if not servers:
                    return
                
                logger.debug(f"Checking health of {len(servers)} servers...")
                
                # Check each server
                for server in servers:
                    is_reachable = await self.check_server_health(server.id, server.host)
                    
                    # Update database
                    if server.is_reachable != is_reachable:
                        logger.info(f"Server {server.name} ({server.host}) status changed: {server.is_reachable} -> {is_reachable}")
                        server.is_reachable = is_reachable
                        server.last_check = datetime.utcnow()
                        session.add(server)
                
                session.commit()
                
        except Exception as e:
            logger.error(f"Error in health check cycle: {e}")
    
    async def run(self):
        """Run the health checker loop."""
        self.running = True
        logger.info(f"Server health checker started (interval: {self.check_interval}s)")
        
        while self.running:
            try:
                await self.check_all_servers()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                logger.info("Health checker cancelled")
                break
            except Exception as e:
                logger.error(f"Error in health checker loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    def start(self):
        """Start the health checker as a background task."""
        if self.task is None or self.task.done():
            self.task = asyncio.create_task(self.run())
            logger.info("Health checker task created")
    
    async def stop(self):
        """Stop the health checker."""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Health checker stopped")


# Global health checker instance
health_checker = ServerHealthChecker(check_interval=60)  # Check every 60 seconds
