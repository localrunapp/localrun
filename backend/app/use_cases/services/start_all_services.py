"""
Start All Services Use Case

Business logic for starting all enabled services.
"""

import logging
from typing import Dict, Any, List

from sqlmodel import Session
from app.use_cases.services.start_service import StartServiceUseCase

logger = logging.getLogger(__name__)


class StartAllServicesUseCase:
    """
    Use Case: Start all enabled services.
    
    Responsibilities:
    - Get all enabled services
    - Start each service individually
    - Handle individual errors gracefully
    - Return summary of results
    """
    
    def __init__(self, start_service_use_case: StartServiceUseCase):
        """
        Initialize use case.
        
        Args:
            start_service_use_case: Use case for starting individual services
        """
        self.start_use_case = start_service_use_case
    
    async def execute(
        self,
        user_id: int,
        db: Session,
    ) -> Dict[str, Any]:
        """
        Execute the use case.
        
        Args:
            user_id: ID of the user starting services
            db: Database session for operations
            
        Returns:
            Summary with started services and errors
        """
        logger.info(f"Starting all enabled services for user {user_id}")
        
        # Get enabled services that are not running
        from app.repositories.service_repository import ServiceRepository
        repo = ServiceRepository(db)
        services = repo.list_enabled(user_id)
        
        if not services:
            return {
                "message": "No hay servicios habilitados",
                "started": [],
            }
        
        results = []
        
        # Start each service
        for service in services:
            try:
                await self.start_use_case.execute(service.id, user_id, db)
                results.append({
                    "id": service.id,
                    "name": service.name,
                    "status": "started",
                })
                logger.info(f"Started service: {service.name}")
            except Exception as e:
                logger.error(f"Error starting {service.name}: {e}")
                results.append({
                    "id": service.id,
                    "name": service.name,
                    "status": "error",
                    "error": str(e),
                })
        
        successful = len([r for r in results if r["status"] == "started"])
        
        logger.info(f"Started {successful}/{len(results)} services")
        
        return {
            "message": f"{successful}/{len(results)} servicios iniciados",
            "started": results,
        }
