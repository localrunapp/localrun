"""
Restart Service Use Case

Business logic for restarting a tunnel service.
"""

import logging
import uuid
from sqlmodel import Session

from app.models.service import Service
from app.use_cases.services.stop_service import StopServiceUseCase
from app.use_cases.services.start_service import StartServiceUseCase

logger = logging.getLogger(__name__)


class RestartServiceUseCase:
    """
    Use Case: Restart a service (stop + start).
    
    Responsibilities:
    - Orchestrate stop and start operations
    - Return updated service
    """
    
    def __init__(
        self,
        stop_service_use_case: StopServiceUseCase,
        start_service_use_case: StartServiceUseCase,
    ):
        """
        Initialize use case.
        
        Args:
            stop_service_use_case: Use case for stopping service
            start_service_use_case: Use case for starting service
        """
        self.stop_use_case = stop_service_use_case
        self.start_use_case = start_service_use_case
    
    async def execute(
        self,
        service_id: uuid.UUID,
        user_id: int,
        db: Session,
    ) -> Service:
        """
        Execute the use case.
        
        Args:
            service_id: ID of service to restart
            user_id: ID of the user restarting the service
            db: Database session for tunnel operations
            
        Returns:
            Updated service with running status
            
        Raises:
            HTTPException: If service not found or restart fails
        """
        logger.info(f"Restarting service {service_id} for user {user_id}")
        
        # 1. Stop service
        await self.stop_use_case.execute(service_id, user_id, db)
        
        # 2. Start service
        service = await self.start_use_case.execute(service_id, user_id, db)
        
        logger.info(f"Service restarted successfully: ID {service_id}")
        
        return service
