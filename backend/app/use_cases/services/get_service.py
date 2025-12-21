"""
Get Service Use Case

Business logic for retrieving a single service.
"""

import logging
import uuid
from fastapi import HTTPException

from app.models.service import Service

logger = logging.getLogger(__name__)


class GetServiceUseCase:
    """
    Use Case: Get a single service by ID.
    
    Responsibilities:
    - Validate service exists and belongs to user
    - Return service
    """
    
    async def execute(
        self,
        service_id: uuid.UUID,
        user_id: int,
    ) -> Service:
        """
        Execute the use case.
        
        Args:
            service_id: ID of service to retrieve
            user_id: ID of the user requesting the service
            
        Returns:
            Service if found
            
        Raises:
            HTTPException: If service not found or doesn't belong to user
        """
        logger.info(f"Getting service {service_id} for user {user_id}")
        
        service = Service.find(service_id)
        
        if not service or service.user_id != user_id:
            raise HTTPException(status_code=404, detail="Servicio no encontrado")
        
        return service
