"""
Provider schemas - DTOs for API requests/responses
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ProviderCreateRequest(BaseModel):
    """
    Request to register a new provider.
    Laravel equivalent: App/Http/Requests/ProviderStoreRequest
    """

    name: str = Field(..., min_length=3, max_length=255, description="User-defined name")
    types: list[str] = Field(..., description="Provider types (cloudflare_tunnel, cloudflare_dns, etc)")
    credentials: Dict[str, Any] = Field(..., description="Provider credentials")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "My Cloudflare Account",
                "types": ["cloudflare_tunnel", "cloudflare_dns"],
                "credentials": {"token": "eyJhIjoiYWJjMTIzIiwidCI6ImRlZjQ1NiIsInMiOiJnaGk3ODkifQ=="},
            }
        }


class ProviderResponse(BaseModel):
    """
    Provider response schema.
    Laravel equivalent: App/Http/Resources/ProviderResource
    """

    id: int
    name: str
    types: list[str]  # Provider types this account supports
    protocols: list[str]  # Protocols this provider supports
    features: list[str]
    is_active: bool = True
    created_at: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "My Cloudflare Account",
                "types": ["cloudflare_tunnel", "cloudflare_dns"],
                "protocols": ["http", "https", "tcp", "udp", "websocket", "ssh", "dns"],
                "features": ["zero_trust", "automatic_dns", "ddos_protection"],
                "is_active": True,
                "created_at": "2024-01-01T00:00:00",
            }
        }


class ProviderUpdateRequest(BaseModel):
    """
    Request to update provider.
    """

    name: Optional[str] = Field(None, min_length=3, max_length=255)
    credentials: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
