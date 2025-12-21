"""
Enable Service Use Case

Business logic for enabling a service.
"""

import logging
import uuid
from typing import Dict, Any
from fastapi import HTTPException

from app.models.service import Service

logger = logging.getLogger(__name__)


class EnableServiceUseCase:
    """
    Use Case: Enable a service.
    
    Responsibilities:
    - Validate service exists and belongs to user
    - Enable service using Active Record
    - Return success message
    """
    
    async def execute(
        self,
        service_id: uuid.UUID,
        user_id: int,
    ) -> Dict[str, Any]:
        """
        Execute the use case.
        
        Args:
            service_id: ID of service to enable
            user_id: ID of the user enabling the service
            
        Returns:
            Success message with service name
            
        Raises:
            HTTPException: If service not found
        """
        logger.info(f"Enabling service {service_id} for user {user_id}")
        
        # Get service
        service = Service.find(service_id)
        if not service or service.user_id != user_id:
            raise HTTPException(status_code=404, detail="Servicio no encontrado")
        
        # Enable service using Active Record
        service.update(enabled=True)
        
        logger.info(f"Service enabled: {service.name} (ID: {service_id})")
        
        return {
            "success": True,
            "message": f"Servicio '{service.name}' habilitado",
        }
