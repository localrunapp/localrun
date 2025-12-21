"""
Update Service Use Case

Business logic for updating an existing service.
"""

import logging
import uuid
from fastapi import HTTPException

from app.models.service import Service
from app.models.provider import Provider
from app.schemas.service import ServiceUpdateRequest

logger = logging.getLogger(__name__)


class UpdateServiceUseCase:
    """
    Use Case: Update an existing service.
    
    Responsibilities:
    - Validate service exists and belongs to user
    - Validate provider if changed
    - Validate port availability if changed
    - Update service using Active Record
    - Return updated service
    """
    
    async def execute(
        self,
        service_id: uuid.UUID,
        service_data: ServiceUpdateRequest,
        user_id: int,
    ) -> Service:
        """
        Execute the use case.
        
        Args:
            service_id: ID of service to update
            service_data: Update request data
            user_id: ID of the user updating the service
            
        Returns:
            Updated service
            
        Raises:
            HTTPException: If service not found or validation fails
        """
        logger.info(f"Updating service {service_id} for user {user_id}")
        
        # 1. Get existing service
        service = Service.find(service_id)
        if not service or service.user_id != user_id:
            raise HTTPException(status_code=404, detail="Servicio no encontrado")
        
        # 2. Validate provider if changed
        if service_data.provider_key:
            provider = Provider.first_where(key=service_data.provider_key, is_active=True)
            if not provider:
                raise HTTPException(
                    status_code=400,
                    detail=f"Proveedor '{service_data.provider_key}' no existe o está inactivo"
                )
        
        # 3. Validate port availability if port or host changed
        if service_data.port or service_data.host:
            new_port = service_data.port or service.port
            new_host = service_data.host or service.host
            
            existing = Service.first_where(
                user_id=user_id,
                port=new_port,
                host=new_host
            )
            if existing and existing.id != service_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"Ya existe un servicio en {new_host}:{new_port}"
                )
        
        # 4. Update service fields
        update_data = service_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "protocol" and value:
                setattr(service, field, value.value)
            else:
                setattr(service, field, value)
        
        # 5. Save using Active Record
        service.save()
        
        logger.info(f"Service updated successfully: {service.name} (ID: {service.id})")
        
        return service
