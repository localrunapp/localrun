"""
Stop All Services Use Case

Business logic for stopping all running services.
"""

import logging
from typing import Dict, Any

from sqlmodel import Session
from app.use_cases.services.stop_service import StopServiceUseCase

logger = logging.getLogger(__name__)


class StopAllServicesUseCase:
    """
    Use Case: Stop all running services.
    
    Responsibilities:
    - Get all running services
    - Stop each service individually
    - Handle individual errors gracefully
    - Return summary of results
    """
    
    def __init__(self, stop_service_use_case: StopServiceUseCase):
        """
        Initialize use case.
        
        Args:
            stop_service_use_case: Use case for stopping individual services
        """
        self.stop_use_case = stop_service_use_case
    
    async def execute(
        self,
        user_id: int,
        db: Session,
    ) -> Dict[str, Any]:
        """
        Execute the use case.
        
        Args:
            user_id: ID of the user stopping services
            db: Database session for operations
            
        Returns:
            Summary with stopped services and errors
        """
        logger.info(f"Stopping all running services for user {user_id}")
        
        # Get running services
        from app.repositories.service_repository import ServiceRepository
        repo = ServiceRepository(db)
        services = repo.list_running(user_id)
        
        if not services:
            return {
                "message": "No hay servicios corriendo",
                "stopped": [],
            }
        
        results = []
        
        # Stop each service
        for service in services:
            try:
                await self.stop_use_case.execute(service.id, user_id, db)
                results.append({
                    "id": service.id,
                    "name": service.name,
                    "status": "stopped",
                })
                logger.info(f"Stopped service: {service.name}")
            except Exception as e:
                logger.error(f"Error stopping {service.name}: {e}")
                results.append({
                    "id": service.id,
                    "name": service.name,
                    "status": "error",
                    "error": str(e),
                })
        
        successful = len([r for r in results if r["status"] == "stopped"])
        
        logger.info(f"Stopped {successful}/{len(results)} services")
        
        return {
            "message": f"{successful}/{len(results)} servicios detenidos",
            "stopped": results,
        }
