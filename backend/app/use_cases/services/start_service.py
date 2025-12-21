"""
Start Service Use Case

Business logic for starting a tunnel service.
"""

import logging
import uuid
from sqlmodel import Session

from app.models.service import Service
from app.enums.service import ServiceStatus
from app.repositories.service_repository import ServiceRepository
from app.services.tunnel_service import TunnelService
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class StartServiceUseCase:
    """
    Use Case: Start a tunnel for a service.
    
    Responsibilities:
    - Validate service exists and is enabled
    - Check if already running
    - Start tunnel (quick or named)
    - Update service status in database
    - Return updated service
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
    ) -> Service:
        """
        Execute the use case.
        
        Args:
            service_id: ID of service to start
            user_id: ID of the user starting the service
            db: Database session for tunnel operations
            
        Returns:
            Updated service with running status
            
        Raises:
            HTTPException: If service not found, disabled, or start fails
        """
        logger.info(f"Starting service {service_id} for user {user_id}")
        
        # 1. Get service
        service = self.service_repo.get_by_id(service_id, user_id)
        if not service:
            raise HTTPException(status_code=404, detail="Servicio no encontrado")
        
        # 2. Validate service is enabled
        if not service.enabled:
            raise HTTPException(
                status_code=400,
                detail=f"Servicio '{service.name}' está deshabilitado",
            )
        
        # 3. Check if already running
        if service.status == ServiceStatus.RUNNING.value:
            logger.info(f"Service already running: {service.name}")
            return service
        
        try:
            # 4. Resolve correct Host IP based on Server
            if service.server_id:
                # Need to use ServerRepository to finding connection details
                from app.repositories.server_repository import ServerRepository
                server_repo = ServerRepository()
                server = server_repo.get_by_id(db, service.server_id)
                
                if server and not server.is_local and server.network_ip:
                    # For remote servers, use the network IP
                    logger.info(f"Using network IP {server.network_ip} for remote server {server.name}")
                    service.host = server.network_ip
                elif server and server.is_local:
                    # For local server, ensure we use 127.0.0.1 or localhost
                    logger.info(f"Using local IP for server {server.name}")
                    service.host = "127.0.0.1"

            # 5. Start tunnel based on type
            if service.is_quick_service:
                logger.info(f"Starting quick tunnel for: {service.name} (target: {service.host})")
                public_url, process_id = await self.tunnel_service.start_quick_tunnel(
                    service, db
                )
            else:
                logger.info(f"Starting named tunnel for: {service.name} (target: {service.host})")
                public_url, process_id = await self.tunnel_service.start_named_tunnel(
                    service, db
                )
            
            # 6. Update service status
            self.service_repo.mark_as_running(service, public_url, process_id)
            
            logger.info(f"Service started: {service.name} -> {public_url}")
            
            return service
            
        except Exception as e:
            logger.error(f"Error starting service {service.name}: {e}")
            # Mark as error in database
            try:
                self.service_repo.mark_as_error(service, str(e))
            except Exception:
                pass
            raise HTTPException(status_code=500, detail=str(e))
