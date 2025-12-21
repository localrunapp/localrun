"""
Core tunnel driver interfaces and base classes
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class TunnelStatus(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"


@dataclass
class TunnelInfo:
    """Información de un túnel activo"""

    tunnel_id: str
    public_url: str
    local_target: str
    port: int
    status: TunnelStatus
    provider: str
    protocol: str
    process_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TunnelConfig:
    """Configuración para crear un túnel - Universal para todos los protocolos"""

    port: int
    protocol: str = "http"  # "http", "https", "tcp", "udp", "ssh"
    provider: str = "cloudflare"  # "cloudflare", "ngrok", "pinggy"
    host: str = "localhost"

    # Modo túnel (solo Cloudflare tiene named)
    tunnel_mode: str = "quick"  # "quick" | "named"

    # Named tunnel config (solo Cloudflare)
    subdomain: Optional[str] = None
    domain: Optional[str] = None

    # Provider specific options
    auth_token: Optional[str] = None
    region: Optional[str] = None

    # ngrok specific
    ngrok_domain: Optional[str] = None  # Solo con plan pago

    # Service identification
    service_id: Optional[str] = None  # UUID of the service for container labeling
    
    # Healthcheck configuration
    healthcheck_enabled: bool = True
    healthcheck_path: str = "/"
    healthcheck_timeout: int = 5
    healthcheck_expected_status: int = 200

    # Metadata adicional
    metadata: Optional[Dict[str, Any]] = None


class TunnelCreationException(Exception):
    """Exception raised when tunnel creation fails"""

    def __init__(self, message: str, provider: str = None, protocol: str = None):
        self.message = message
        self.provider = provider
        self.protocol = protocol
        super().__init__(self.message)


class TunnelNotFoundException(Exception):
    """Exception raised when tunnel is not found"""

    def __init__(self, message: str, tunnel_id: str = None, port: int = None):
        self.message = message
        self.tunnel_id = tunnel_id
        self.port = port
        super().__init__(self.message)


class TunnelProviderException(Exception):
    """Exception raised when there's an issue with the tunnel provider"""

    def __init__(self, message: str, provider: str = None):
        self.message = message
        self.provider = provider
        super().__init__(self.message)


class AbstractTunnelDriver(ABC):
    """
    Clase base abstracta para todos los proveedores de túneles.
    Soporta múltiples protocolos: HTTP, TCP, UDP, SSH
    """

    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.active_tunnels: Dict[int, TunnelInfo] = {}

    @abstractmethod
    def supports_protocol(self, protocol: str) -> bool:
        """
        Indica si el proveedor soporta este protocolo.

        Args:
            protocol: "http", "https", "tcp", "udp", "ssh"

        Returns:
            bool: True si el protocolo es soportado
        """
        pass

    @abstractmethod
    def supports_named_tunnels(self) -> bool:
        """
        Indica si el proveedor soporta Named Tunnels persistentes.

        Returns:
            bool: True si soporta Named Tunnels
        """
        pass

    @abstractmethod
    async def create_tunnel(self, config: TunnelConfig) -> TunnelInfo:
        """
        Crea un nuevo túnel con la configuración especificada.
        Soporte universal para todos los protocolos.

        Args:
            config: Configuración del túnel a crear

        Returns:
            TunnelInfo: Información del túnel creado

        Raises:
            TunnelCreationException: Si no se puede crear el túnel
        """
        pass

    @abstractmethod
    async def stop_tunnel(self, port: int) -> bool:
        """
        Detiene un túnel activo por puerto.

        Args:
            port: Puerto del túnel a detener

        Returns:
            bool: True si se detuvo correctamente, False en caso contrario
        """
        pass

    @abstractmethod
    async def get_tunnel_status(self, port: int) -> Optional[TunnelInfo]:
        """
        Obtiene el estado de un túnel por puerto.

        Args:
            port: Puerto del túnel

        Returns:
            Optional[TunnelInfo]: Información del túnel o None si no existe
        """
        pass

    @abstractmethod
    async def list_active_tunnels(self) -> List[TunnelInfo]:
        """
        Lista todos los túneles activos.

        Returns:
            List[TunnelInfo]: Lista de túneles activos
        """
        pass

    @abstractmethod
    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """
        Valida las credenciales del proveedor.

        Args:
            credentials: Credenciales a validar

        Returns:
            bool: True si las credenciales son válidas
        """
        pass

    def get_supported_protocols(self) -> List[str]:
        """
        Lista de protocolos soportados por este driver.

        Returns:
            List[str]: Lista de protocolos soportados
        """
        protocols = ["http", "https", "tcp", "udp", "ssh"]
        return [p for p in protocols if self.supports_protocol(p)]

    def validate_config(self, config: TunnelConfig) -> bool:
        """
        Valida la configuración del túnel.

        Args:
            config: Configuración a validar

        Returns:
            bool: True si la configuración es válida

        Raises:
            TunnelCreationException: Si la configuración es inválida
        """
        if not self.supports_protocol(config.protocol):
            raise TunnelCreationException(
                f"{self.provider_name} doesn't support protocol: {config.protocol}",
                provider=self.provider_name,
                protocol=config.protocol,
            )

        if config.tunnel_mode == "named" and not self.supports_named_tunnels():
            raise TunnelCreationException(
                f"{self.provider_name} doesn't support Named Tunnels", provider=self.provider_name
            )

        if config.port < 1 or config.port > 65535:
            raise TunnelCreationException(
                f"Invalid port: {config.port}. Must be between 1-65535", provider=self.provider_name
            )

        return True

    def is_port_active(self, port: int) -> bool:
        """
        Check if a port has an active tunnel.

        Args:
            port: Port to check

        Returns:
            bool: True if port has an active tunnel
        """
        return port in self.active_tunnels

    async def cleanup(self) -> bool:
        """
        Cleanup all active tunnels.
        
        Returns:
            bool: True if cleanup was successful
        """
        success = True
        ports = list(self.active_tunnels.keys())
        for port in ports:
            if not await self.stop_tunnel(port):
                success = False
        return success
