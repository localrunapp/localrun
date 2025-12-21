"""
Drivers routes - Driver information endpoints.
"""

from fastapi import APIRouter
from app.controllers.drivers import DriversController

router = APIRouter(prefix="/drivers", tags=["drivers"])
drivers_controller = DriversController()


# List all drivers
router.add_api_route("", drivers_controller.list_drivers, methods=["GET"])

# Get drivers by protocol
router.add_api_route(
    "/protocol/{protocol}", drivers_controller.get_protocol_drivers, methods=["GET"]
)

# Get driver info
router.add_api_route("/{driver_type}", drivers_controller.get_driver_info, methods=["GET"])
