"""
System routes - System information and statistics endpoints.
"""

from fastapi import APIRouter, Depends
from app.controllers.system import SystemController
from core.auth import get_current_user

router = APIRouter(prefix="/system", tags=["system"])
system_controller = SystemController()


# System info
router.add_api_route(
    "/info",
    system_controller.get_system_info,
    methods=["GET"],
    dependencies=[Depends(get_current_user)],
)

# System stats
router.add_api_route(
    "/stats",
    system_controller.get_quick_stats,
    methods=["GET"],
    dependencies=[Depends(get_current_user)],
)

# Host script
router.add_api_route(
    "/host-script",
    system_controller.get_host_details_via_script,
    methods=["GET"],
    dependencies=[Depends(get_current_user)],
)
