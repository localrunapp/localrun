"""
Service model for tunnel configurations.
"""

from datetime import datetime
from typing import Optional
import uuid
from sqlmodel import Field
from core.database_model import DatabaseModel
from app.enums.service import ServiceStatus


class Service(DatabaseModel, table=True):
    """
    Modelo para servicios expuestos

    Cada servicio representa un endpoint específico que se expone al exterior:
    - Puerto específico (ej: 3000, 5437)
    - Protocolo específico (HTTP, TCP, etc.)
    - Dominio específico (api.example.com, db.example.com)
    """

    __tablename__ = "services"

    # Identificación
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255, index=True)

    # Configuración del servicio
    protocol: str = Field(max_length=20, index=True)  # ServiceProtocol
    port: int = Field(ge=1, le=65535, index=True)
    host: str = Field(default="localhost", max_length=255)

    # DNS y dominio
    domain: Optional[str] = Field(default=None, max_length=255)
    subdomain: Optional[str] = Field(default=None, max_length=255)
    dns_record_id: Optional[str] = Field(default=None, max_length=100)  # ID del registro DNS creado

    # Configuración de proveedor
    provider_key: str = Field(max_length=50, index=True)
    dns_provider_key: Optional[str] = Field(default=None, max_length=50)
    tunnel_password: Optional[str] = Field(default=None, max_length=100)
    enable_analytics: bool = Field(default=False, description="Enable traffic analytics through tunnel agent")

    # Estado del servicio
    enabled: bool = Field(default=True, index=True)
    status: str = Field(default=ServiceStatus.STOPPED.value, max_length=20, index=True)

    # URLs y proceso
    public_url: Optional[str] = Field(default=None, max_length=500)
    process_id: Optional[str] = Field(default=None, max_length=100)
    error_message: Optional[str] = Field(default=None, max_length=1000)

    # Relaciones
    user_id: int = Field(foreign_key="users.id", index=True)
    server_id: Optional[str] = Field(
        default=None, foreign_key="servers.id", index=True, description="Optional remote server UUID"
    )

    # Healthcheck configuration
    healthcheck_enabled: bool = Field(default=True, description="Enable healthcheck for this service")
    healthcheck_path: str = Field(default="/", max_length=255, description="Path to check")
    healthcheck_timeout: int = Field(default=5, ge=1, le=30, description="Timeout in seconds")
    healthcheck_expected_status: int = Field(default=200, ge=100, le=599, description="Expected HTTP status code")

    # Healthcheck status (managed by tunnel-agent)
    healthcheck_status: str = Field(default="unknown", max_length=20, description="Current health: unknown, healthy, unhealthy")
    healthcheck_last_check: Optional[datetime] = Field(default=None, description="Last healthcheck timestamp")
    healthcheck_last_error: Optional[str] = Field(default=None, max_length=500, description="Last error message if unhealthy")
    healthcheck_consecutive_failures: int = Field(default=0, description="Consecutive failure count")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(default=None)

    class Config:
        """Configuración del modelo"""

        # Para compatibilidad con FastAPI
        from_attributes = True

        # Ejemplo de uso en JSON schema
        json_schema_extra = {
            "example": {
                "name": "API Backend",
                "protocol": "http",
                "port": 3000,
                "host": "localhost",
                "domain": "example.com",
                "subdomain": "api",
                "provider_key": "cloudflare",
                "dns_provider_key": "cloudflare",
                "enabled": True,
                "status": "stopped",
            }
        }

    def __repr__(self):
        """Representación string del servicio"""
        return f"Service(id={self.id}, name='{self.name}', {self.protocol}://{self.host}:{self.port})"

    @property
    def full_domain(self) -> Optional[str]:
        """Obtiene el dominio completo del servicio"""
        if self.domain and self.subdomain:
            return f"{self.subdomain}.{self.domain}"
        return None

    @property
    def local_endpoint(self) -> str:
        """Obtiene el endpoint local del servicio"""
        return f"{self.protocol}://{self.host}:{self.port}"

    @property
    def is_named_service(self) -> bool:
        """Verifica si es un servicio Named (con dominio personalizado)"""
        return bool(self.domain and self.subdomain)

    @property
    def is_quick_service(self) -> bool:
        """Verifica si es un servicio Quick (sin dominio personalizado)"""
        return not self.is_named_service

    def get_expected_container_name(self) -> str:
        """Obtiene el nombre esperado del contenedor según el tipo de servicio"""
        if self.is_quick_service:
            return f"cloudflared-quick-{self.port}"
        return "cloudflared-agent"  # Named services usan contenedor compartido

    def update_status(
        self,
        status: ServiceStatus,
        public_url: Optional[str] = None,
        process_id: Optional[str] = None,
        error_message: Optional[str] = None,
    ):
        """Actualiza el estado del servicio"""
        self.status = status.value
        self.updated_at = datetime.utcnow()

        if status == ServiceStatus.RUNNING:
            self.started_at = datetime.utcnow()
            self.error_message = None  # Limpiar error al correr
            if public_url:
                self.public_url = public_url
            if process_id:
                self.process_id = process_id
        elif status == ServiceStatus.STOPPED:
            self.public_url = None
            self.process_id = None
            if error_message is None:
                self.error_message = None  # Solo limpiar si no hay nuevo error
        elif status == ServiceStatus.ERROR:
            self.error_message = error_message
            self.public_url = None
            self.process_id = None

        # Actualizar error_message si se proporciona
        if error_message is not None:
            self.error_message = error_message
