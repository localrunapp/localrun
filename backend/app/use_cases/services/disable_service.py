"""
Disable Service Use Case

Business logic for disabling a service.
"""

import logging
import uuid
from typing import Dict, Any
from fastapi import HTTPException

from app.models.service import Service
from app.enums.service import ServiceStatus

logger = logging.getLogger(__name__)


class DisableServiceUseCase:
    """
    Use Case: Disable a service.
    
    Responsibilities:
    - Validate service exists and belongs to user
    - Disable service using Active Record
    - If running, mark as stopped
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
            service_id: ID of service to disable
            user_id: ID of the user disabling the service
            
        Returns:
            Success message with service name
            
        Raises:
            HTTPException: If service not found
        """
        logger.info(f"Disabling service {service_id} for user {user_id}")
        
        # Get service
        service = Service.find(service_id)
        if not service or service.user_id != user_id:
            raise HTTPException(status_code=404, detail="Servicio no encontrado")
        
        # Disable service and stop if running
        updates = {"enabled": False}
        if service.status == ServiceStatus.RUNNING.value:
            updates.update({
                "status": ServiceStatus.STOPPED.value,
                "public_url": None,
                "process_id": None,
            })
        
        service.update(**updates)
        
        logger.info(f"Service disabled: {service.name} (ID: {service_id})")
        
        return {
            "success": True,
            "message": f"Servicio '{service.name}' deshabilitado",
        }
