"""
Provider schemas - DTOs for API requests/responses
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProviderCreateRequest(BaseModel):
    """
    Request to register a new provider with credentials.
    Laravel equivalent: App/Http/Requests/ProviderStoreRequest
    """

    name: str = Field(..., min_length=3, max_length=255, description="User-defined name")
    provider: str = Field(..., description="Provider name (cloudflare, ngrok)")
    credentials: Dict[str, Any] = Field(..., description="Provider credentials")
    enable_protocols: List[str] = Field(default=[], description="Protocols to enable immediately")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "My Cloudflare Account",
                "provider": "cloudflare",
                "credentials": {"api_token": "abc123...", "account_id": "xyz789..."},
                "enable_protocols": ["http", "https", "dns"],
            }
        }


class ProviderResponse(BaseModel):
    """
    Provider response schema.
    Laravel equivalent: App/Http/Resources/ProviderResource
    """

    id: int
    name: str
    provider: str
    available_protocols: List[str]  # What this provider CAN do
    enabled_drivers: List[Dict[str, Any]]  # What's currently enabled
    is_active: bool
    created_at: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "My Cloudflare Account",
                "provider": "cloudflare",
                "available_protocols": ["http", "https", "tcp", "udp", "websocket", "ssh", "dns"],
                "enabled_drivers": [
                    {"id": 1, "protocol": "http", "is_active": True},
                    {"id": 2, "protocol": "https", "is_active": True},
                    {"id": 3, "protocol": "dns", "is_active": True},
                ],
                "is_active": True,
                "created_at": "2024-01-01T00:00:00",
            }
        }


class DriverEnableRequest(BaseModel):
    """Request to enable a protocol driver"""

    protocol: str = Field(..., description="Protocol to enable (http, https, tcp, etc)")
    config: Optional[Dict[str, Any]] = Field(default={}, description="Protocol-specific configuration")

    class Config:
        json_schema_extra = {"example": {"protocol": "http", "config": {"auto_https": True, "compression": True}}}


class DriverResponse(BaseModel):
    """Driver response schema"""

    id: int
    protocol: str
    is_active: bool
    provider_id: int
    provider_name: str
    config: Dict[str, Any]
    created_at: str
