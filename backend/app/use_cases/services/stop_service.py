"""
Stop Service Use Case

Business logic for stopping a tunnel service.
"""

import logging
import uuid
from typing import Dict, Any
from sqlmodel import Session

from app.models.service import Service
from app.enums.service import ServiceStatus
from app.repositories.service_repository import ServiceRepository
from app.services.tunnel_service import TunnelService
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class StopServiceUseCase:
    """
    Use Case: Stop a tunnel for a service.
    
    Responsibilities:
    - Validate service exists
    - Check if running
    - Stop tunnel (quick or named)
    - Update service status in database
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
            service_id: ID of service to stop
            user_id: ID of the user stopping the service
            db: Database session for tunnel operations
            
        Returns:
            Success message with service name
            
        Raises:
            HTTPException: If service not found or stop fails
        """
        logger.info(f"Stopping service {service_id} for user {user_id}")
        
        # 1. Get service
        service = self.service_repo.get_by_id(service_id, user_id)
        if not service:
            raise HTTPException(status_code=404, detail="Servicio no encontrado")
        
        # 2. Check if already stopped
        if service.status != ServiceStatus.RUNNING.value:
            logger.info(f"Service already stopped: {service.name}")
            return {
                "success": True,
                "message": "Servicio ya estaba detenido",
            }
        
        # 3. Stop tunnel based on type
        await self._stop_tunnel(service, db)
        
        # 4. Update service status
        self.service_repo.mark_as_stopped(service)
        
        logger.info(f"Service stopped: {service.name}")
        
        return {
            "success": True,
            "message": f"Servicio '{service.name}' detenido",
        }
    
    async def _stop_tunnel(self, service: Service, db: Session):
        """Stop tunnel based on service type."""
        if service.is_quick_service:
            logger.info(f"Stopping quick tunnel for: {service.name}")
            await self.tunnel_service.stop_quick_tunnel(service)
        else:
            logger.info(f"Stopping named tunnel for: {service.name}")
            await self.tunnel_service.stop_named_tunnel(service, db)
