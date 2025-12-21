"""
Provider models - SQLModel (Provider credentials only, no protocol info)
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlmodel import Column, Field, JSON, Relationship
from core.database_model import DatabaseModel

if TYPE_CHECKING:
    from .domain import Domain


class Provider(DatabaseModel, table=True):
    """
    Provider model - Simplified configuration
    One config per provider type (cloudflare, ngrok) for the entire system
    """

    __tablename__ = "providers"

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Provider key (unique): "cloudflare" | "ngrok"
    key: str = Field(max_length=50, unique=True, index=True)

    # Provider-level configuration
    tunnel_name: Optional[str] = Field(default=None, max_length=100, description="Unique tunnel name for this provider")

    # Protocol enablement (simple booleans)
    http: bool = Field(default=False, description="HTTP/HTTPS tunnels enabled")
    dns: bool = Field(default=False, description="DNS management enabled")
    tcp: bool = Field(default=False, description="TCP tunnels enabled")
    udp: bool = Field(default=False, description="UDP tunnels enabled")
    ssh: bool = Field(default=False, description="SSH tunnels enabled")
    websocket: bool = Field(default=False, description="WebSocket tunnels enabled")
    bastion: bool = Field(default=False, description="Bastion mode enabled")

    # Provider credentials: {"api_token": "...", "certificate": "...", "login_completed_at": "..."}
    credentials: dict = Field(default={}, sa_column=Column(JSON))

    # Protocol-specific configurations: {"http": {...}, "dns": {...}, "tcp": {...}}
    configs: dict = Field(default={}, sa_column=Column(JSON))

    # Status
    is_active: bool = Field(default=True)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    domains: List["Domain"] = Relationship(back_populates="provider")

    def __repr__(self):
        return f"<Provider(id={self.id}, key='{self.key}')>"
