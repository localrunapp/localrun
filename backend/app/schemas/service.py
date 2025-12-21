from typing import List, Dict, Optional
import uuid
from app.enums.service import ServiceProtocol
from datetime import datetime
from pydantic import BaseModel, Field


class ServiceCreateRequest(BaseModel):
    """Crear nuevo servicio expuesto"""

    name: str = Field(..., min_length=1, max_length=255)
    protocol: ServiceProtocol
    port: int = Field(..., ge=1, le=65535)
    host: str = Field(default="localhost", max_length=255)
    server_id: Optional[str] = Field(default=None, description="Optional server ID (if using remote server)")
    domain: Optional[str] = Field(default=None, max_length=255)
    subdomain: Optional[str] = Field(default=None, max_length=255)
    provider_key: str = Field(..., min_length=1, max_length=50)
    dns_provider_key: Optional[str] = Field(default=None, max_length=50)
    tunnel_password: Optional[str] = Field(default=None, max_length=100)
    enable_analytics: bool = Field(default=False, description="Enable traffic analytics")
    enabled: bool = Field(default=True)
    
    # Healthcheck configuration
    healthcheck_enabled: bool = Field(default=True, description="Enable healthcheck for this service")
    healthcheck_path: str = Field(default="/", max_length=255, description="Path to check")
    healthcheck_timeout: int = Field(default=5, ge=1, le=30, description="Timeout in seconds")
    healthcheck_expected_status: int = Field(default=200, ge=100, le=599, description="Expected HTTP status code")


class ServiceUpdateRequest(BaseModel):
    """Actualizar servicio existente"""

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    protocol: Optional[ServiceProtocol] = None
    port: Optional[int] = Field(default=None, ge=1, le=65535)
    host: Optional[str] = Field(default=None, max_length=255)
    server_id: Optional[str] = Field(default=None, description="Optional server ID")
    domain: Optional[str] = Field(default=None, max_length=255)
    subdomain: Optional[str] = Field(default=None, max_length=255)
    provider_key: Optional[str] = Field(default=None, min_length=1, max_length=50)
    dns_provider_key: Optional[str] = Field(default=None, max_length=50)
    tunnel_password: Optional[str] = Field(default=None, max_length=100)
    enable_analytics: Optional[bool] = None
    enabled: Optional[bool] = None
    
    # Healthcheck configuration
    healthcheck_enabled: Optional[bool] = None
    healthcheck_path: Optional[str] = Field(default=None, max_length=255)
    healthcheck_timeout: Optional[int] = Field(default=None, ge=1, le=30)
    healthcheck_expected_status: Optional[int] = Field(default=None, ge=100, le=599)


class ServiceResponse(BaseModel):
    """Respuesta de servicio"""

    id: uuid.UUID
    name: str
    protocol: str
    port: int
    host: str
    server_id: Optional[str] = None
    domain: Optional[str]
    subdomain: Optional[str]
    enabled: bool
    status: str
    public_url: Optional[str]
    provider_key: str
    dns_provider_key: Optional[str]
    tunnel_password: Optional[str]
    enable_analytics: bool
    user_id: int
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    
    # Healthcheck fields
    healthcheck_enabled: bool
    healthcheck_path: str
    healthcheck_timeout: int
    healthcheck_expected_status: int
    healthcheck_status: str
    healthcheck_last_check: Optional[datetime]
    healthcheck_last_error: Optional[str]
    healthcheck_consecutive_failures: int

    # Campos computados
    full_domain: Optional[str] = None
    local_endpoint: str = ""
    is_named_service: bool = False
    is_quick_service: bool = True
    expected_container_name: str = ""

    class Config:
        from_attributes = True


# === Runtime DTOs ===


class ServiceAgentRequest(BaseModel):
    """Request para activar un servicio."""

    port: int = Field(..., ge=1, le=65535, description="Puerto del host a exponer")
    protocol: str = Field("http", description="Protocolo (http/https)")
    provider: str = Field("cloudflare", description="Proveedor del servicio")
    subdomain: Optional[str] = Field(None, description="Subdominio personalizado (si el proveedor lo soporta)")
    domain: Optional[str] = Field(None, description="Dominio personalizado (si el proveedor lo soporta)")
    region: Optional[str] = Field(None, description="Región del servidor (para ngrok)")


class ServiceAgentResponse(BaseModel):
    """Response cuando se activa un servicio."""

    service_id: str
    port: int
    public_url: str
    provider: str
    status: str
    local_target: str
    # Campos adicionales para Named Services
    tunnel_url: Optional[str] = None
    cname_target: Optional[str] = None
    setup_instructions: Optional[Dict] = None


class ServiceListResponse(BaseModel):
    """Response para listar servicios activos."""

    services: List[ServiceAgentResponse]
    total: int
    providers: List[str]
