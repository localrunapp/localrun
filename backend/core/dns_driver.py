"""
Core DNS driver interface
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class DNSDriver(ABC):
    """
    Base interface for DNS management drivers.
    Manages DNS records across different providers: Cloudflare, Route53, DNSMadeEasy, etc.
    """

    @abstractmethod
    async def create_record(
        self,
        zone_id: str,
        record_type: str,
        name: str,
        content: str,
        credentials: Dict[str, Any],
        ttl: int = 1,
        proxied: bool = False,
    ) -> Dict[str, Any]:
        """
        Create DNS record.

        Args:
            zone_id: DNS zone ID
            record_type: A, AAAA, CNAME, TXT, MX, SRV
            name: Record name
            content: Record value
            credentials: Provider credentials
            ttl: Time to live
            proxied: Proxy through provider (Cloudflare only)

        Returns:
            {"id": str, "type": str, "name": str, "content": str}
        """
        pass

    @abstractmethod
    async def update_record(
        self,
        zone_id: str,
        record_id: str,
        content: str,
        credentials: Dict[str, Any],
        ttl: Optional[int] = None,
        proxied: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Update DNS record"""
        pass

    @abstractmethod
    async def delete_record(self, zone_id: str, record_id: str, credentials: Dict[str, Any]) -> None:
        """Delete DNS record"""
        pass

    @abstractmethod
    async def list_records(
        self, zone_id: str, credentials: Dict[str, Any], record_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List DNS records"""
        pass

    @abstractmethod
    async def list_zones(self, credentials: Dict[str, Any]) -> List[Dict[str, Any]]:
        """List DNS zones available to this API token"""
        pass

    @abstractmethod
    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Validate credentials"""
        pass


class DNSDriverFactory:
    """Factory para crear drivers DNS"""

    _drivers = {}

    @classmethod
    def register_driver(cls, provider_name: str, driver_class):
        """Registra un driver DNS para un proveedor"""
        cls._drivers[provider_name] = driver_class

    @classmethod
    def get_driver(cls, provider_name: str) -> DNSDriver:
        """
        Obtiene un driver DNS para el proveedor especificado.

        Args:
            provider_name: Nombre del proveedor ("cloudflare", "route53", "dnsmadeeasy")

        Returns:
            DNSDriver: Instancia del driver DNS

        Raises:
            ValueError: Si el proveedor no está soportado
        """
        if provider_name not in cls._drivers:
            raise ValueError(f"Unsupported DNS provider: {provider_name}")

        driver_class = cls._drivers[provider_name]
        return driver_class()

    @classmethod
    def list_providers(cls) -> List[str]:
        """Lista todos los proveedores DNS registrados"""
        return list(cls._drivers.keys())
