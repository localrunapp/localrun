"""
Application Bootstrap

Orchestrates all startup tasks using use cases.
"""

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
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


def generate_or_load_reset_token() -> str:
    """
    Generate or load existing password reset token.
    Token persists across restarts in /app/storage/reset_token.json
    """
    token_file = Path("/app/storage/reset_token.json")
    token_file.parent.mkdir(parents=True, exist_ok=True)

    # Load existing token
    if token_file.exists():
        try:
            with open(token_file, "r") as f:
                data = json.load(f)
                return data["token"]
        except Exception as e:
            logger.warning(f"Could not load reset token, generating new: {e}")

    # Generate new token
    token = str(uuid.uuid4())
    data = {
        "token": token,
        "created_at": datetime.now().isoformat(),
        "last_used": None
    }

    try:
        with open(token_file, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Could not save reset token: {e}")

    return token


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
    3. Reset token generation
    4. Tunnel state synchronization (use case)
    5. Host IP auto-detection (use case)
    6. Background services startup (use case)
    
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
    
    # 2. Generate/load reset token
    results["reset_token"] = generate_or_load_reset_token()
    
    # 3. Get/create system user
    results["system_user"] = get_or_create_system_user(db)
    
    # 4. Sync tunnel states (use case - skip in hot reload)
    if not is_hot_reload():
        results["sync_result"] = await sync_tunnel_states_use_case(
            db, results["system_user"]
        )
    
    # 5. Auto-detect host IP (use case)
    results["host_ip"] = await auto_detect_host_ip_use_case(db)
    
    # 6. Start background services (use case)
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
