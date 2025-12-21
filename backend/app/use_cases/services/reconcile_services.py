"""
Reconcile services with running Docker containers
"""
import logging
from typing import Dict, Any, List
import docker
from sqlalchemy.orm import Session

from app.models.service import Service
from app.integrations.utils.url_extractor import extract_url_by_provider

logger = logging.getLogger(__name__)


class ReconcileServicesUseCase:
    """
    Reconciles service states with running Docker containers.
    Updates services that have running containers but show error/stopped status.
    """

    def __init__(self, db: Session):
        self.db = db
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.docker_client = None

    async def execute(self, user_id: int) -> Dict[str, Any]:
        """
        Execute reconciliation process.
        
        Args:
            user_id: User ID to reconcile services for
            
        Returns:
            Reconciliation report with updated services and orphaned containers
        """
        if not self.docker_client:
            return {
                "reconciled": 0,
                "updated_services": [],
                "orphaned_containers": [],
                "error": "Docker client not available"
            }

        try:
            # Get all running containers with localrun labels
            containers = self._get_localrun_containers()
            
            # Get all services for this user that might need reconciliation
            services = self._get_services_to_reconcile(user_id)
            
            # Match containers to services and update
            updated_services = []
            orphaned_containers = []
            
            for container in containers:
                result = await self._reconcile_container(container, services)
                if result["updated"]:
                    updated_services.append(result["service_info"])
                elif result["orphaned"]:
                    orphaned_containers.append(result["container_info"])
            
            # Commit all changes
            self.db.commit()
            
            return {
                "reconciled": len(updated_services),
                "updated_services": updated_services,
                "orphaned_containers": orphaned_containers
            }
            
        except Exception as e:
            logger.error(f"Error during reconciliation: {e}")
            self.db.rollback()
            return {
                "reconciled": 0,
                "updated_services": [],
                "orphaned_containers": [],
                "error": str(e)
            }

    def _get_localrun_containers(self) -> List:
        """Get all running containers managed by localrun"""
        try:
            return self.docker_client.containers.list(
                filters={"label": "managed-by=localrun-agent"}
            )
        except Exception as e:
            logger.error(f"Error listing containers: {e}")
            return []

    def _get_services_to_reconcile(self, user_id: int) -> List[Service]:
        """Get services that might need reconciliation (error or stopped status)"""
        return self.db.query(Service).filter(
            Service.user_id == user_id,
            Service.status.in_(["error", "stopped", "starting"])
        ).all()

    async def _reconcile_container(
        self, container, services: List[Service]
    ) -> Dict[str, Any]:
        """
        Reconcile a single container with services.
        
        Returns:
            Dict with 'updated', 'service_info', 'orphaned', 'container_info'
        """
        try:
            # Extract port and provider from container labels
            labels = container.labels
            port = labels.get("tunnel-port") or labels.get("port")
            provider = labels.get("tunnel-provider") or labels.get("provider")
            
            if not port:
                return {"updated": False, "orphaned": False}
            
            port = int(port)
            
            # Find matching service by port AND provider
            service = None
            for s in services:
                if s.port == port:
                    # If provider label exists, match it too
                    if provider and s.provider_key.lower() == provider.lower():
                        service = s
                        break
                    # If no provider label, just match by port (fallback)
                    elif not provider:
                        service = s
                        break
            
            if not service:
                return {
                    "updated": False,
                    "orphaned": True,
                    "container_info": {
                        "container_id": container.id[:12],
                        "port": port,
                        "provider": provider or "unknown",
                        "reason": "No matching service found"
                    }
                }
            
            # Get container logs and extract URL
            logs = container.logs(tail=100).decode("utf-8", errors="ignore")
            public_url = extract_url_by_provider(service.provider_key, logs)
            
            if not public_url:
                logger.warning(f"Could not extract URL for service {service.id} from container logs")
                # Still update status even without URL
                public_url = service.public_url or ""
            
            # Update service
            old_status = service.status
            service.status = "running"
            service.public_url = public_url
            
            logger.info(
                f"Reconciled service {service.id} ({service.provider_key}): "
                f"{old_status} -> running, URL: {public_url}"
            )
            
            return {
                "updated": True,
                "service_info": {
                    "id": service.id,
                    "name": service.name,
                    "provider": service.provider_key,
                    "old_status": old_status,
                    "new_status": "running",
                    "public_url": public_url,
                    "port": port
                },
                "orphaned": False
            }
            
        except Exception as e:
            logger.error(f"Error reconciling container {container.id[:12]}: {e}")
            return {"updated": False, "orphaned": False}
