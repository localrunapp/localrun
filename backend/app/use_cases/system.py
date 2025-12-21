"""
System Use Cases

Use cases for system-level operations like synchronization and auto-detection.
"""

import logging
from typing import Optional, Dict, Any

from sqlmodel import Session

logger = logging.getLogger(__name__)


async def sync_tunnel_states_use_case(db: Session, system_user) -> Optional[Dict]:
    """
    Synchronize tunnel states with actual infrastructure.
    
    Use case that orchestrates tunnel state synchronization by calling
    the services controller.
    
    Args:
        db: Database session
        system_user: System user for internal operations
        
    Returns:
        Sync results or None if skipped
    """
    try:
        from app.controllers.services import services_controller
        
        logger.info("Synchronizing tunnel states...")
        sync_result = await services_controller.sync_service_states(
            current_user=system_user,
            db=db
        )
        logger.info(f"Sync completed: {sync_result}")
        return sync_result
    except Exception as e:
        logger.warning(f"Sync error: {e}")
        return None


async def auto_detect_host_ip_use_case(db: Session) -> Optional[str]:
    """
    Auto-detect and update localhost server IP from Docker.
    
    Use case that detects the host IP and updates the localhost server
    configuration in the database.
    
    Args:
        db: Database session
        
    Returns:
        Detected host IP or None if detection failed
    """
    try:
        from app.controllers.system import system_controller
        from app.repositories.server_repository import server_repository

        host_ip = system_controller._get_host_ip_from_docker()
        if host_ip:
            localhost_server = server_repository.get_localhost(db)
            if localhost_server:
                localhost_server.network_ip = host_ip
                server_repository.update(db, localhost_server)
                logger.info(f"Auto-detected host IP: {host_ip}")
                return host_ip
    except Exception as e:
        logger.warning(f"Could not auto-detect host IP: {e}")
    
    return None


def start_health_checker_use_case():
    """
    Start background health checker service.
    
    Use case that starts the health checker infrastructure service.
    """
    from app.infrastructure.health_checker import health_checker
    
    health_checker.start()
    logger.info("Health checker started")


async def stop_health_checker_use_case():
    """
    Stop background health checker service.
    
    Use case that stops the health checker infrastructure service.
    """
    from app.infrastructure.health_checker import health_checker
    
    await health_checker.stop()
    logger.info("Health checker stopped")


async def stop_managed_containers_use_case():
    """
    Stop all containers managed by LocalRun.
    
    Use case that stops and removes all Docker containers managed
    by the LocalRun platform.
    """
    from app.infrastructure.docker_service import docker_service

    logger.info("Stopping managed containers...")
    containers = docker_service.list_containers_by_label("managed-by", "localrun")
    
    for container in containers:
        try:
            logger.info(f"Stopping: {container.name}")
            docker_service.stop_container(container.name)
            docker_service.remove_container(container.name)
        except Exception as e:
            logger.warning(f"Error stopping {container.name}: {e}")
