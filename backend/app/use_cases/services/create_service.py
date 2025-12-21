"""
Create Service Use Case

Business logic for creating a new tunnel service.
"""

import logging
from fastapi import HTTPException

from app.models.service import Service
from app.models.provider import Provider
from app.enums.service import ServiceStatus
from app.schemas.service import ServiceCreateRequest

logger = logging.getLogger(__name__)


class CreateServiceUseCase:
    """
    Use Case: Create a new tunnel service.
    
    Responsibilities:
    - Validate input data
    - Verify provider exists
    - Verify port is available
    - Create service in database using Active Record
    - Return created service
    """
    
    async def execute(
        self,
        service_data: ServiceCreateRequest,
        user_id: int,
    ) -> Service:
        """
        Execute the use case.
        
        Args:
            service_data: Service creation request data
            user_id: ID of the user creating the service
            
        Returns:
            Created service
            
        Raises:
            HTTPException: If validation fails or creation errors
        """
        logger.info(f"Creating service: {service_data.name} for user {user_id}")
        
        # 1. Validate provider exists and is active
        provider = Provider.first_where(key=service_data.provider_key, is_active=True)
        if not provider:
            raise HTTPException(
                status_code=400,
                detail=f"Proveedor '{service_data.provider_key}' no existe o está inactivo"
            )
        
        # 2. Validate port is available
        existing = Service.first_where(
            user_id=user_id,
            port=service_data.port,
            host=service_data.host
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Ya existe un servicio en {service_data.host}:{service_data.port}"
            )
        
        # 3. Create service using Active Record
        service = Service.create(
            name=service_data.name,
            protocol=service_data.protocol.value,
            port=service_data.port,
            host=service_data.host,
            server_id=service_data.server_id,
            domain=service_data.domain,
            subdomain=service_data.subdomain,
            provider_key=service_data.provider_key,
            dns_provider_key=service_data.dns_provider_key,
            tunnel_password=service_data.tunnel_password,
            enable_analytics=service_data.enable_analytics,
            enabled=service_data.enabled,
            user_id=user_id,
            status=ServiceStatus.STOPPED.value,
        )
        
        logger.info(f"Service created successfully: {service.name} (ID: {service.id})")
        
        return service
