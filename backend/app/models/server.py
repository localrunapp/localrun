"""
Server model for managing remote machines in the local network.
"""

from datetime import datetime
from typing import Optional
import uuid
from sqlmodel import Field
from core.database_model import DatabaseModel


class Server(DatabaseModel, table=True):
    """
    Server model to manage remote machines in the local network.
    Each server represents a machine that can host services.
    """

    __tablename__ = "servers"

    # Identification
    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()), primary_key=True, description="UUID of the server"
    )
    name: str = Field(max_length=255, index=True, description="Server name (e.g., 'Raspberry Pi', 'NAS')")

    # Network configuration
    host: str = Field(max_length=255, index=True, description="IP address or hostname (e.g., '192.168.1.100')")
    description: Optional[str] = Field(default=None, max_length=500, description="Optional description")

    # Status
    is_local: bool = Field(default=False, description="True if this is localhost/127.0.0.1")
    is_reachable: bool = Field(default=True, description="Connectivity status")
    last_check: Optional[datetime] = Field(default=None, description="Last connectivity check")

    # Metadata
    os_type: Optional[str] = Field(default=None, max_length=50, description="Detected OS (Linux, macOS, Windows)")
    os_version: Optional[str] = Field(default=None, max_length=50, description="Kernel/OS Version")
    cpu_cores: Optional[int] = Field(default=None, description="Number of CPU cores")
    memory_gb: Optional[float] = Field(default=None, description="Total RAM in GB")
    network_ip: Optional[str] = Field(default=None, max_length=50, description="Local network IP")
    detected_services: Optional[str] = Field(default=None, max_length=1000, description="JSON with detected services")
    
    # Scanning status
    scanning_status: Optional[str] = Field(default="idle", max_length=20, description="Scan status: idle, scanning, completed, failed")
    last_scan_started: Optional[datetime] = Field(default=None, description="When the last scan started")
    last_scan_completed: Optional[datetime] = Field(default=None, description="When the last scan completed")
    
    # CLI Agent status
    agent_status: str = Field(
        default="not_installed",
        max_length=20,
        description="CLI agent status: not_installed, installed, connected, disconnected"
    )

    # Relationships
    # user_id removed to make servers global
    # user_id: int = Field(foreign_key="users.id", index=True)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Model configuration"""

        from_attributes = True
        json_schema_extra = {
            "example": {
                "name": "Raspberry Pi",
                "host": "192.168.1.100",
                "description": "Pi-hole + Home Assistant",
                "is_local": False,
                "is_reachable": True,
                "os_type": "Linux",
            }
        }

    def __repr__(self):
        """String representation"""
        status = "🟢" if self.is_reachable else "🔴"
        return f"Server(id={self.id}, name='{self.name}', host='{self.host}' {status})"

    @property
    def is_localhost(self) -> bool:
        """Check if this server is localhost"""
        return self.host in ["localhost", "127.0.0.1", "::1"] or self.is_local
