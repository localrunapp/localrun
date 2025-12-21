"""
DNS Record models - SQLModel (Laravel Eloquent style)
"""

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

from app.enums.dns import DNSRecordType


class DNSRecord(SQLModel, table=True):
    """
    DNS Record model - Laravel equivalent: App/Models/DNSRecord
    """

    __tablename__ = "dns_records"

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # DNS info
    record_type: str = Field(max_length=10)  # DNSRecordType enum value
    name: str = Field(max_length=255)  # subdomain.example.com
    content: str = Field(max_length=500)  # IP or target
    proxied: bool = Field(default=False)
    ttl: int = Field(default=3600)

    # Provider reference
    provider_record_id: Optional[str] = Field(default=None, max_length=255)  # ID from DNS provider

    # Relationships
    service_id: int = Field(foreign_key="services.id", index=True)
    dns_provider_id: int = Field(foreign_key="providers.id", index=True)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def __repr__(self):
        return f"<DNSRecord(id={self.id}, name='{self.name}', type='{self.record_type}')>"
