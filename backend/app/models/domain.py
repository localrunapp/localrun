"""
Domain model for DNS zone management.
Represents registered domains linked to DNS providers.
"""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, Relationship
from core.database_model import DatabaseModel


class Domain(DatabaseModel, table=True):
    """
    Domain/DNS Zone model.
    Links domains to DNS providers and stores zone configuration.
    """

    __tablename__ = "domains"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Domain info
    domain: str = Field(index=True, unique=True, max_length=255, description="Full domain name (e.g., 'example.com')")

    # Provider linkage
    provider_id: int = Field(foreign_key="providers.id", description="DNS provider managing this domain")

    # Zone configuration (provider-specific)
    zone_id: str = Field(
        max_length=255, description="Zone ID from DNS provider (Cloudflare Zone ID, Route53 Hosted Zone, etc.)"
    )

    zone_name: Optional[str] = Field(
        default=None, max_length=255, description="Zone name if different from domain (some providers use this)"
    )

    # Status
    active: bool = Field(default=True, description="Whether this domain is active for use")

    verified: bool = Field(default=False, description="Whether domain ownership has been verified")

    auto_create_records: bool = Field(
        default=True, description="Automatically create DNS records when creating services"
    )

    # Metadata
    description: Optional[str] = Field(
        default=None, max_length=500, description="Optional description or notes about this domain"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_verified_at: Optional[datetime] = Field(
        default=None, description="Last time domain was verified with provider"
    )

    # Relationships
    provider: Optional["Provider"] = Relationship(back_populates="domains")

    class Config:
        json_schema_extra = {
            "example": {
                "domain": "example.com",
                "provider_id": 1,
                "zone_id": "abc123def456",
                "zone_name": "example.com",
                "active": True,
                "verified": True,
                "auto_create_records": True,
                "description": "Production domain",
            }
        }
