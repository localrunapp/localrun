"""
Config routes - Configuration endpoints.
"""

from fastapi import APIRouter
from app.controllers.config import ConfigController

router = APIRouter(prefix="/config", tags=["config"])
config_controller = ConfigController()


# Get config
router.add_api_route("", config_controller.get_config, methods=["GET"])
