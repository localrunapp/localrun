"""
Domains routes - Domain management endpoints.
"""

from fastapi import APIRouter, Depends
from app.controllers.domains import DomainController
from core.auth import get_current_user

router = APIRouter(prefix="/domains", tags=["domains"])
domains_controller = DomainController()


# List domains
router.add_api_route(
    "", domains_controller.list_domains, methods=["GET"], dependencies=[Depends(get_current_user)]
)

# Create domain
router.add_api_route(
    "",
    domains_controller.create_domain,
    methods=["POST"],
    status_code=201,
    dependencies=[Depends(get_current_user)],
)

# Get domain
router.add_api_route(
    "/{domain_id}",
    domains_controller.get_domain,
    methods=["GET"],
    dependencies=[Depends(get_current_user)],
)

# Update domain
router.add_api_route(
    "/{domain_id}",
    domains_controller.update_domain,
    methods=["PUT", "PATCH"],
    dependencies=[Depends(get_current_user)],
)

# Delete domain
router.add_api_route(
    "/{domain_id}",
    domains_controller.delete_domain,
    methods=["DELETE"],
    dependencies=[Depends(get_current_user)],
)

# Verify domain
router.add_api_route(
    "/{domain_id}/verify",
    domains_controller.verify_domain,
    methods=["POST"],
    dependencies=[Depends(get_current_user)],
)
