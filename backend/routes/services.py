"""
Services routes - Service management and tunnel operations endpoints.
"""

from fastapi import APIRouter, Depends
from typing import Any, Dict, List
from app.controllers.services import ServicesController
from app.schemas.service import (
    ServiceResponse,
    ServiceListResponse,
    ServiceAgentResponse,
)
from core.auth import get_current_user

router = APIRouter(prefix="/services", tags=["services"])
services_controller = ServicesController()


# ========== CRUD Operations ==========

# List services
router.add_api_route(
    "",
    services_controller.list_services,
    methods=["GET"],
    response_model=List[ServiceResponse],
)

# Create service
router.add_api_route(
    "",
    services_controller.create_service,
    methods=["POST"],
    status_code=201,
    response_model=ServiceResponse,
)

# Get service
router.add_api_route(
    "/{service_id}",
    services_controller.get_service,
    methods=["GET"],
    response_model=ServiceResponse,
)

# Update service
router.add_api_route(
    "/{service_id}",
    services_controller.update_service,
    methods=["PUT"],
    response_model=ServiceResponse,
)

# Delete service
router.add_api_route(
    "/{service_id}",
    services_controller.delete_service,
    methods=["DELETE"],
    response_model=Dict[str, Any],
)

# Enable service
router.add_api_route(
    "/{service_id}/enable",
    services_controller.enable_service,
    methods=["PUT"],
    response_model=Dict[str, Any],
)

# Disable service
router.add_api_route(
    "/{service_id}/disable",
    services_controller.disable_service,
    methods=["PUT"],
    response_model=Dict[str, Any],
)


# ========== Runtime Operations (Static routes first) ==========

# List active services
router.add_api_route(
    "/active",
    services_controller.list_active_services,
    methods=["GET"],
    response_model=List[ServiceResponse],
    dependencies=[Depends(get_current_user)],
)

# Start all enabled services
router.add_api_route(
    "/start-all",
    services_controller.start_enabled_services,
    methods=["POST"],
    dependencies=[Depends(get_current_user)],
)

# Stop all services
router.add_api_route(
    "/stop-all",
    services_controller.stop_all_services,
    methods=["POST"],
    dependencies=[Depends(get_current_user)],
)

# Sync service states
router.add_api_route(
    "/sync",
    services_controller.sync_service_states,
    methods=["POST"],
    dependencies=[Depends(get_current_user)],
)

# Get diagnostics
router.add_api_route(
    "/diagnostics",
    services_controller.get_diagnostics,
    methods=["GET"],
    dependencies=[Depends(get_current_user)],
)

# Reconcile services with running containers
router.add_api_route(
    "/reconcile",
    services_controller.reconcile_services,
    methods=["POST"],
    response_model=Dict[str, Any],
)

# ========== Provider Information ==========

# Get supported providers
router.add_api_route(
    "/providers/available",
    services_controller.get_supported_providers,
    methods=["GET"],
    response_model=Dict[str, Any],
    dependencies=[Depends(get_current_user)],
)

# Get provider status
router.add_api_route(
    "/providers/{provider}/status",
    services_controller.get_provider_status,
    methods=["GET"],
    dependencies=[Depends(get_current_user)],
)

# Cleanup provider
router.add_api_route(
    "/providers/{provider}/cleanup",
    services_controller.cleanup_provider,
    methods=["POST"],
    dependencies=[Depends(get_current_user)],
)


# ========== Service Operations (Routes with parameters) ==========

# Start service
router.add_api_route(
    "/{service_id}/start",
    services_controller.start_service,
    methods=["POST"],
    response_model=ServiceResponse,
    dependencies=[Depends(get_current_user)],
)

# Stop service
router.add_api_route(
    "/{service_id}/stop",
    services_controller.stop_service,
    methods=["POST"],
    dependencies=[Depends(get_current_user)],
)

# Restart service
router.add_api_route(
    "/{service_id}/restart",
    services_controller.restart_service,
    methods=["POST"],
    response_model=ServiceResponse,
    dependencies=[Depends(get_current_user)],
)
