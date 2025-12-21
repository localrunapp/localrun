"""
List Services Use Case

Business logic for listing services with filters.
"""

import logging
from typing import List, Optional

from app.models.service import Service

logger = logging.getLogger(__name__)


class ListServicesUseCase:
    """
    Use Case: List services with optional filters.
    
    Responsibilities:
    - Query services from database using Active Record
    - Apply filters (enabled, provider, protocol, user)
    - Return list of services
    """
    
    async def execute(
        self,
        user_id: int,
        enabled: Optional[bool] = None,
        provider: Optional[str] = None,
        protocol: Optional[str] = None,
    ) -> List[Service]:
        """
        Execute the use case.
        
        Args:
            user_id: ID of the user listing services
            enabled: Filter by enabled/disabled status
            provider: Filter by provider key
            protocol: Filter by protocol
            
        Returns:
            List of services matching filters
        """
        logger.info(f"Listing services for user {user_id} with filters: enabled={enabled}, provider={provider}, protocol={protocol}")
        
        # Build filters
        filters = {"user_id": user_id}
        
        if enabled is not None:
            filters["enabled"] = enabled
        
        if provider:
            filters["provider_key"] = provider
        
        if protocol:
            filters["protocol"] = protocol
        
        # Query using Active Record
        services = Service.where(**filters)
        
        logger.info(f"Found {len(services)} services")
        
        return services
