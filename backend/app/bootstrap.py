"""
Application Bootstrap

Orchestrates all startup tasks using use cases.
"""


import logging
import os
from typing import Dict, Any

from sqlmodel import Session

from core.database import get_db
from core.settings import settings
from database.seeders import seed_database
from app.use_cases.system import (
    sync_tunnel_states_use_case,
    auto_detect_host_ip_use_case,
    start_health_checker_use_case,
    stop_health_checker_use_case,
    stop_managed_containers_use_case,
)

logger = logging.getLogger(__name__)


def is_hot_reload() -> bool:
    """Check if running in hot reload mode"""
    return os.environ.get("HOT_RELOAD", "false").lower() == "true"


def get_or_create_system_user(db: Session):
    """Get or create system user for internal operations"""
    from core.auth import create_system_user
    return create_system_user()


async def bootstrap_application() -> Dict[str, Any]:
    """
    Bootstrap application on startup.
    
    Orchestrates all initialization tasks using use cases:
    1. Database seeding (first run only)
    2. System user creation
    3. Tunnel state synchronization (use case)
    4. Host IP auto-detection (use case)
    5. Background services startup (use case)
    
    Returns:
        dict: Bootstrap results
    """
    results = {}
    
    # Get database session
    db = next(get_db())
    
    # 1. Seed database (creates initial data)
    try:
        initial_password = seed_database()
        results["initial_password"] = initial_password
        results["is_first_run"] = bool(initial_password)
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    # 2. Get/create system user
    results["system_user"] = get_or_create_system_user(db)
    
    # 3. Sync tunnel states (use case - skip in hot reload)
    if not is_hot_reload():
        results["sync_result"] = await sync_tunnel_states_use_case(
            db, results["system_user"]
        )
    
    # 4. Auto-detect host IP (use case)
    results["host_ip"] = await auto_detect_host_ip_use_case(db)
    
    # 5. Start background services (use case)
    start_health_checker_use_case()
    
    return results


async def shutdown_application():
    """
    Graceful application shutdown using use cases.
    
    Stops all background services and managed containers.
    """
    if is_hot_reload():
        logger.debug("Hot reload mode: Skipping shutdown tasks")
        return
    
    try:
        # Stop health checker (use case)
        await stop_health_checker_use_case()
        
        # Stop Quick Tunnel in production
        if not settings.is_development() and settings.quick_tunnel_enabled:
            logger.info("Shutting down Quick Tunnel...")
            from core.quick_tunnel import quick_tunnel
            await quick_tunnel.stop()
        
        # Stop all managed containers (use case)
        await stop_managed_containers_use_case()
        
        logger.info("Graceful shutdown complete")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")
