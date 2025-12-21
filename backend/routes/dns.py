"""
DNS routes - DNS management endpoints.
"""

from fastapi import APIRouter, Depends
from app.controllers.dns import DNSController
from core.auth import get_current_user

router = APIRouter(prefix="/dns", tags=["dns"])
dns_controller = DNSController()


# Test DNS provider
router.add_api_route(
    "/{provider_key}/test",
    dns_controller.test_dns_provider,
    methods=["GET"],
    dependencies=[Depends(get_current_user)],
)

# List DNS zones
router.add_api_route(
    "/{provider_key}/zones",
    dns_controller.list_dns_zones,
    methods=["GET"],
    dependencies=[Depends(get_current_user)],
)

# List DNS records
router.add_api_route(
    "/{provider_key}/zones/{zone_id}/records",
    dns_controller.list_dns_records,
    methods=["GET"],
    dependencies=[Depends(get_current_user)],
)

# Get DNS record
router.add_api_route(
    "/{provider_key}/zones/{zone_id}/records/{record_id}",
    dns_controller.get_dns_record,
    methods=["GET"],
    dependencies=[Depends(get_current_user)],
)

# Create DNS record
router.add_api_route(
    "/{provider_key}/zones/{zone_id}/records",
    dns_controller.create_dns_record,
    methods=["POST"],
    status_code=201,
    dependencies=[Depends(get_current_user)],
)

# Delete DNS record
router.add_api_route(
    "/{provider_key}/zones/{zone_id}/records/{record_id}",
    dns_controller.delete_dns_record,
    methods=["DELETE"],
    dependencies=[Depends(get_current_user)],
)

# Create DNS for service
router.add_api_route(
    "/{provider_key}/zones/{zone_id}/service/{service_id}",
    dns_controller.create_dns_for_service,
    methods=["POST"],
    status_code=201,
    dependencies=[Depends(get_current_user)],
)
