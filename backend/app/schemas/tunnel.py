"""
Tunnel schemas - DTOs for API requests/responses
"""

from typing import Optional, Dict, Any

from pydantic import BaseModel, Field

from app.enums import TunnelProtocol


class TunnelCreateRequest(BaseModel):
    """
    Request to create a new tunnel.
    """

    name: str = Field(..., min_length=3, max_length=255, description="Tunnel name")
    provider_key: str = Field(..., description="Provider key to use for this tunnel")
    protocol: TunnelProtocol = Field(..., description="Tunnel protocol")
    port: int = Field(..., ge=1, le=65535, description="Port to expose")
    host: str = Field(default="localhost", description="Host")
    domain: Optional[str] = Field(None, description="Custom domain (optional)")
    subdomain: Optional[str] = Field(None, description="Subdomain (optional)")
    dns_provider_key: Optional[str] = Field(None, description="DNS provider key (optional)")
    config: Optional[Dict[str, Any]] = Field(None, description="Tunnel configuration (tunnel_mode, hostname, etc.)")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Mi App Puerto 3006",
                "provider_key": "cloudflare",
                "protocol": "http",
                "port": 3006,
                "host": "localhost",
            }
        }


class TunnelResponse(BaseModel):
    """
    Tunnel response schema.
    """

    id: int
    name: str
    provider_key: str
    protocol: str
    port: int
    host: str
    status: str
    public_url: Optional[str] = None
    domain: Optional[str] = None
    subdomain: Optional[str] = None
    dns_provider_key: Optional[str] = None
    process_id: Optional[int] = None
    error_message: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    created_at: str
    started_at: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Mi App Puerto 3006",
                "provider_key": "cloudflare",
                "protocol": "http",
                "port": 3006,
                "host": "localhost",
                "status": "stopped",
                "public_url": None,
                "created_at": "2024-01-01T00:00:00",
            }
        }


class TunnelUpdateRequest(BaseModel):
    """
    Request to update tunnel.
    """

    name: Optional[str] = Field(None, min_length=3, max_length=255)
    port: Optional[int] = Field(None, ge=1, le=65535)
    host: Optional[str] = None


class TunnelStatusResponse(BaseModel):
    """
    Tunnel status response.
    """

    id: int
    status: str
    public_url: Optional[str] = None
    process_id: Optional[int] = None
    error_message: Optional[str] = None
    started_at: Optional[str] = None
