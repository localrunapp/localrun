"""
Delete Service Use Case

Business logic for deleting a service.
"""

import logging
import uuid
from typing import Dict, Any

from app.models.service import Service
from app.enums.service import ServiceStatus
from app.repositories.service_repository import ServiceRepository
from app.services.tunnel_service import TunnelService
from fastapi import HTTPException
from sqlmodel import Session

logger = logging.getLogger(__name__)


class DeleteServiceUseCase:
    """
    Use Case: Delete a service.
    
    Responsibilities:
    - Validate service exists
    - Stop tunnel if running
    - Delete service from database
    - Return success message
    """
    
    def __init__(
        self,
        service_repository: ServiceRepository,
        tunnel_service: TunnelService,
    ):
        """
        Initialize use case.
        
        Args:
            service_repository: Repository for service data access
            tunnel_service: Service for tunnel operations
        """
        self.service_repo = service_repository
        self.tunnel_service = tunnel_service
    
    async def execute(
        self,
        service_id: uuid.UUID,
        user_id: int,
        db: Session,
    ) -> Dict[str, Any]:
        """
        Execute the use case.
        
        Args:
            service_id: ID of service to delete
            user_id: ID of the user deleting the service
            db: Database session for tunnel operations
            
        Returns:
            Success message with service name
            
        Raises:
            HTTPException: If service not found
        """
        logger.info(f"Deleting service {service_id} for user {user_id}")
        
        # 1. Get service
        service = self.service_repo.get_by_id(service_id, user_id)
        if not service:
            raise HTTPException(status_code=404, detail="Servicio no encontrado")
        
        service_name = service.name
        
        # 2. Stop tunnel if running
        if service.status == ServiceStatus.RUNNING.value:
            try:
                logger.info(f"Stopping tunnel for service {service_name} before deletion")
                await self._stop_tunnel(service, db)
            except Exception as e:
                logger.warning(f"Error stopping tunnel before deletion: {e}")
        
        # 3. Delete from database
        self.service_repo.delete(service)
        
        logger.info(f"Service deleted successfully: {service_name} (ID: {service_id})")
        
        return {
            "success": True,
            "message": f"Servicio '{service_name}' eliminado",
        }
    
    async def _stop_tunnel(self, service: Service, db: Session):
        """Stop tunnel based on service type."""
        if service.is_quick_service:
            await self.tunnel_service.stop_quick_tunnel(service)
        else:
            await self.tunnel_service.stop_named_tunnel(service, db)
