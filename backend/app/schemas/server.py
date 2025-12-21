"""
Server schemas for API requests and responses.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ServerBase(BaseModel):
    """Base server schema"""

    name: str = Field(..., min_length=1, max_length=255, description="Server name")
    host: str = Field(..., min_length=1, max_length=255, description="IP address or hostname")
    description: Optional[str] = Field(None, max_length=500, description="Optional description")


class ServerCreate(ServerBase):
    """Schema for creating a server"""

    pass


class ServerUpdate(BaseModel):
    """Schema for updating a server"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    host: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)


class ServerResponse(ServerBase):
    """Schema for server response"""

    id: str
    is_local: bool
    is_reachable: bool
    last_check: Optional[datetime]
    os_type: Optional[str]
    detected_services: Optional[str]
    agent_status: str = Field(default="not_installed", description="CLI agent status")
    network_ip: Optional[str] = None
    # user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ServerWithServices(ServerResponse):
    """Server response with detected services parsed"""

    services: list[dict] = Field(default_factory=list)


class ServerDetailResponse(ServerResponse):
    """Detailed server response with agent status and discovered services"""
    
    # Agent status
    agent_installed: bool = Field(description="Whether CLI agent has ever connected")
    agent_connected: bool = Field(description="Whether CLI agent is currently connected (real-time)")
    agent_last_seen: Optional[datetime] = Field(None, description="Last time agent was seen")
    
    # Discovered services (parsed)
    discovered_services: list[dict] = Field(default_factory=list, description="Services discovered by CLI agent")
    
    class Config:
        from_attributes = True


class ConnectivityCheckResponse(BaseModel):
    """Response for connectivity check"""

    reachable: bool
    latency_ms: Optional[float] = None
    error: Optional[str] = None


class DetectedService(BaseModel):
    """Detected service information"""

    port: int
    protocol: str
    service_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    version: Optional[str] = None
    banner: Optional[str] = None


class NetworkScanResult(BaseModel):
    """Result from network scan"""

    host: str
    hostname: Optional[str] = None
    is_reachable: bool
    os_type: Optional[str] = None
    open_ports: list[DetectedService] = Field(default_factory=list)


class ServerStatus(BaseModel):
    """Server status response."""
    server_id: str
    name: str
    agent_status: str  # "installed", "connected", "disconnected", "not_installed"
    is_reachable: bool
    last_check: Optional[datetime] = None
    os_type: Optional[str] = None
    cpu_cores: Optional[int] = None
    memory_gb: Optional[float] = None


class StatsEntry(BaseModel):
    """Single stats entry."""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_gb: float
    disk_percent: float
    disk_gb: float
    network_ip: Optional[str] = None


class PortTestRequest(BaseModel):
    """Request model for port testing"""
    port: int
    protocol: str = "tcp"

