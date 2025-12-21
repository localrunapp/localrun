"""
Sync Service States Use Case

Business logic for synchronizing service states between database and running tunnels.
"""

import logging
from typing import Dict, Any, List

from sqlmodel import Session
from app.models.service import Service
from app.services.tunnel_service import TunnelService
from app.repositories.service_repository import ServiceRepository

logger = logging.getLogger(__name__)


class SyncServiceStatesUseCase:
    """
    Use Case: Sync service states between DB and actual tunnels.
    
    Responsibilities:
    - Get all services
    - Delegate sync to tunnel service
    - Return sync results
    """
    
    def __init__(self, tunnel_service: TunnelService):
        """
        Initialize use case.
        
        Args:
            tunnel_service: Service for tunnel operations
        """
        self.tunnel_service = tunnel_service
    
    async def execute(
        self,
        user_id: int,
        db: Session,
    ) -> Dict[str, Any]:
        """
        Execute the use case.
        
        Args:
            user_id: ID of the user requesting sync
            db: Database session for operations
            
        Returns:
            Sync results from tunnel service
        """
        logger.info(f"Syncing service states for user {user_id}")
        
        # Get all services
        repo = ServiceRepository(db)
        services = repo.list_all(user_id)
        
        # Delegate to tunnel service
        result = await self.tunnel_service.sync_service_states(services, repo)
        
        logger.info(f"Sync completed for user {user_id}")
        
        return result
