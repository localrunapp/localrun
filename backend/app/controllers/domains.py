"""
Domain controller for DNS zone management.
Handles CRUD operations for domains linked to DNS providers.
"""

from typing import List, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.models.domain import Domain
from app.models.provider import Provider
from core.database import get_db
from core.logger import setup_logger

logger = setup_logger(__name__)


# Request/Response models
class DomainCreateRequest(BaseModel):
    """Create domain request."""

    domain: str = Field(..., min_length=3, max_length=255, description="Domain name (e.g., 'example.com')")
    provider_id: int = Field(..., description="DNS provider ID")
    zone_id: str = Field(..., min_length=1, max_length=255, description="Zone ID from DNS provider")
    zone_name: Optional[str] = Field(None, max_length=255, description="Zone name if different from domain")
    auto_create_records: bool = Field(True, description="Auto-create DNS records for services")
    description: Optional[str] = Field(None, max_length=500)


class DomainUpdateRequest(BaseModel):
    """Update domain request."""

    active: Optional[bool] = None
    verified: Optional[bool] = None
    auto_create_records: Optional[bool] = None
    description: Optional[str] = Field(None, max_length=500)


class DomainResponse(BaseModel):
    """Domain response."""

    id: int
    domain: str
    provider_id: int
    provider_name: str
    zone_id: str
    zone_name: Optional[str]
    active: bool
    verified: bool
    auto_create_records: bool
    description: Optional[str]
    created_at: str
    updated_at: str
    last_verified_at: Optional[str]


class DomainController:
    """Controller for domain management."""

    def list_domains(self) -> List[DomainResponse]:
        """
        List all registered domains.
        Returns domains with their provider information.
        """
        db = next(get_db())

        try:
            statement = select(Domain, Provider).join(Provider)
            results = db.exec(statement).all()

            domains = []
            for domain, provider in results:
                domains.append(
                    DomainResponse(
                        id=domain.id,
                        domain=domain.domain,
                        provider_id=domain.provider_id,
                        provider_name=provider.key,
                        zone_id=domain.zone_id,
                        zone_name=domain.zone_name,
                        active=domain.active,
                        verified=domain.verified,
                        auto_create_records=domain.auto_create_records,
                        description=domain.description,
                        created_at=domain.created_at.isoformat(),
                        updated_at=domain.updated_at.isoformat(),
                        last_verified_at=domain.last_verified_at.isoformat() if domain.last_verified_at else None,
                    )
                )

            return domains
        finally:
            db.close()

    def get_domain(self, domain_id: int) -> DomainResponse:
        """Get a specific domain by ID."""
        db = next(get_db())

        try:
            statement = select(Domain, Provider).join(Provider).where(Domain.id == domain_id)
            result = db.exec(statement).first()

            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=f"Domain with ID {domain_id} not found"
                )

            domain, provider = result

            return DomainResponse(
                id=domain.id,
                domain=domain.domain,
                provider_id=domain.provider_id,
                provider_name=provider.name,
                zone_id=domain.zone_id,
                zone_name=domain.zone_name,
                active=domain.active,
                verified=domain.verified,
                auto_create_records=domain.auto_create_records,
                description=domain.description,
                created_at=domain.created_at.isoformat(),
                updated_at=domain.updated_at.isoformat(),
                last_verified_at=domain.last_verified_at.isoformat() if domain.last_verified_at else None,
            )
        finally:
            db.close()

    def create_domain(self, request: DomainCreateRequest) -> DomainResponse:
        """
        Register a new domain.
        Links domain to a DNS provider and stores zone configuration.
        """
        db = next(get_db())

        try:
            # Verify provider exists
            provider = db.get(Provider, request.provider_id)
            if not provider:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=f"Provider with ID {request.provider_id} not found"
                )

            # Check if domain already exists
            existing = db.exec(select(Domain).where(Domain.domain == request.domain)).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, detail=f"Domain '{request.domain}' already registered"
                )

            # Create domain
            domain = Domain(
                domain=request.domain,
                provider_id=request.provider_id,
                zone_id=request.zone_id,
                zone_name=request.zone_name or request.domain,
                auto_create_records=request.auto_create_records,
                description=request.description,
                active=True,
                verified=False,  # Needs verification
            )

            db.add(domain)
            db.commit()
            db.refresh(domain)

            logger.info(f"✅ Domain registered: {domain.domain} (Provider: {provider.key})")

            return DomainResponse(
                id=domain.id,
                domain=domain.domain,
                provider_id=domain.provider_id,
                provider_name=provider.key,
                zone_id=domain.zone_id,
                zone_name=domain.zone_name,
                active=domain.active,
                verified=domain.verified,
                auto_create_records=domain.auto_create_records,
                description=domain.description,
                created_at=domain.created_at.isoformat(),
                updated_at=domain.updated_at.isoformat(),
                last_verified_at=None,
            )
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create domain: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create domain: {str(e)}"
            )
        finally:
            db.close()

    def update_domain(self, domain_id: int, request: DomainUpdateRequest) -> DomainResponse:
        """Update domain configuration."""
        db = next(get_db())

        try:
            domain = db.get(Domain, domain_id)

            if not domain:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=f"Domain with ID {domain_id} not found"
                )

            # Update fields
            if request.active is not None:
                domain.active = request.active
            if request.verified is not None:
                domain.verified = request.verified
            if request.auto_create_records is not None:
                domain.auto_create_records = request.auto_create_records
            if request.description is not None:
                domain.description = request.description

            from datetime import datetime

            domain.updated_at = datetime.utcnow()

            db.add(domain)
            db.commit()
            db.refresh(domain)

            # Get provider for response
            provider = db.get(Provider, domain.provider_id)

            logger.info(f"✅ Domain updated: {domain.domain}")

            return DomainResponse(
                id=domain.id,
                domain=domain.domain,
                provider_id=domain.provider_id,
                provider_name=provider.key if provider else "Unknown",
                zone_id=domain.zone_id,
                zone_name=domain.zone_name,
                active=domain.active,
                verified=domain.verified,
                auto_create_records=domain.auto_create_records,
                description=domain.description,
                created_at=domain.created_at.isoformat(),
                updated_at=domain.updated_at.isoformat(),
                last_verified_at=domain.last_verified_at.isoformat() if domain.last_verified_at else None,
            )
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update domain: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update domain: {str(e)}"
            )
        finally:
            db.close()

    def delete_domain(self, domain_id: int) -> dict:
        """Delete a domain."""
        db = next(get_db())

        try:
            domain = db.get(Domain, domain_id)

            if not domain:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=f"Domain with ID {domain_id} not found"
                )

            domain_name = domain.domain

            db.delete(domain)
            db.commit()

            logger.info(f"✅ Domain deleted: {domain_name}")

            return {"success": True, "message": f"Domain '{domain_name}' deleted successfully"}
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete domain: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete domain: {str(e)}"
            )
        finally:
            db.close()

    async def verify_domain(self, domain_id: int) -> DomainResponse:
        """
        Verify domain with DNS provider.
        Checks if the zone exists and is accessible via provider API.
        """
        db = next(get_db())

        try:
            domain = db.get(Domain, domain_id)

            if not domain:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=f"Domain with ID {domain_id} not found"
                )

            # Get provider
            provider = db.get(Provider, domain.provider_id)
            if not provider:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=f"Provider with ID {domain.provider_id} not found"
                )

            # Verify with DNS provider
            from datetime import datetime

            from core.dns_driver import DNSDriverFactory

            try:
                driver = DNSDriverFactory.get_driver(provider.key)

                # Try to list zones to verify credentials and access
                zones = await driver.list_zones(provider.credentials)

                # Check if our zone exists
                zone_found = any(z.get("id") == domain.zone_id or z.get("name") == domain.domain for z in zones)

                if not zone_found:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Zone '{domain.zone_id}' not found in {provider.key} account",
                    )

                # Verification successful
                domain.verified = True
                domain.last_verified_at = datetime.utcnow()
                domain.updated_at = datetime.utcnow()

                logger.info(f"✅ Domain verified: {domain.domain} (Provider: {provider.key})")

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"DNS provider verification failed for {domain.domain}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Failed to verify with DNS provider: {str(e)}"
                )

            db.add(domain)
            db.commit()
            db.refresh(domain)

            return DomainResponse(
                id=domain.id,
                domain=domain.domain,
                provider_id=domain.provider_id,
                provider_name=provider.key,
                zone_id=domain.zone_id,
                zone_name=domain.zone_name,
                active=domain.active,
                verified=domain.verified,
                auto_create_records=domain.auto_create_records,
                description=domain.description,
                created_at=domain.created_at.isoformat(),
                updated_at=domain.updated_at.isoformat(),
                last_verified_at=domain.last_verified_at.isoformat() if domain.last_verified_at else None,
            )
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to verify domain: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to verify domain: {str(e)}"
            )
        finally:
            db.close()
