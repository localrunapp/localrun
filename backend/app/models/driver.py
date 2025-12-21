"""
Driver model - SQLModel (Enabled protocol capabilities)
"""

from datetime import datetime
from typing import Optional

from sqlmodel import Column, Field, JSON, SQLModel


class Driver(SQLModel, table=True):
    """
    Driver model - Represents an enabled protocol for a provider.
    Laravel equivalent: App/Models/Driver

    Example: Provider "Cloudflare" enables drivers: HTTP, HTTPS, DNS, WebSocket
    """

    __tablename__ = "drivers"

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Driver info
    protocol: str = Field(max_length=50)  # http, https, tcp, udp, websocket, ssh, dns
    is_active: bool = Field(default=True)

    # Configuration (protocol-specific settings)
    config: dict = Field(default={}, sa_column=Column(JSON))

    # Relationships
    provider_id: int = Field(foreign_key="providers.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def __repr__(self):
        return f"<Driver(id={self.id}, protocol='{self.protocol}', provider_id={self.provider_id})>"
