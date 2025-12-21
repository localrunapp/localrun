"""
Providers routes - Provider configuration endpoints.
"""

from fastapi import APIRouter, Depends
from app.controllers.providers import ProvidersController
from core.auth import get_current_user

router = APIRouter(prefix="/providers", tags=["providers"])
providers_controller = ProvidersController()


# List all providers
router.add_api_route(
    "",
    providers_controller.list_providers,
    methods=["GET"],
    dependencies=[Depends(get_current_user)],
)

# Get provider config
router.add_api_route(
    "/{provider_key}",
    providers_controller.get_provider_config,
    methods=["GET"],
    dependencies=[Depends(get_current_user)],
)

# Update provider config
router.add_api_route(
    "/{provider_key}",
    providers_controller.update_provider_config,
    methods=["POST", "PUT"],
    dependencies=[Depends(get_current_user)],
)

# Delete provider config
router.add_api_route(
    "/{provider_key}",
    providers_controller.delete_provider_config,
    methods=["DELETE"],
    dependencies=[Depends(get_current_user)],
)

# Enable protocol
router.add_api_route(
    "/{provider_key}/protocols/{protocol}/enable",
    providers_controller.enable_protocol,
    methods=["POST"],
    dependencies=[Depends(get_current_user)],
)

# Disable protocol
router.add_api_route(
    "/{provider_key}/protocols/{protocol}/disable",
    providers_controller.disable_protocol,
    methods=["POST"],
    dependencies=[Depends(get_current_user)],
)

# Test Cloudflare token
router.add_api_route(
    "/cloudflare/test",
    providers_controller.test_cloudflare_token,
    methods=["POST"],
    dependencies=[Depends(get_current_user)],
)
