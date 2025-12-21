"""
DNS Repository - Capa de acceso a datos y drivers DNS

Responsabilidades:
- Obtener providers configurados
- Interactuar con drivers DNS
- Validar credenciales
- Operaciones CRUD de registros DNS
"""

import logging
from typing import Any, Dict, List, Optional

from sqlmodel import Session, select

from app.models.provider import Provider
from core.dns_driver import DNSDriverFactory

logger = logging.getLogger(__name__)


class DNSRepository:
    """Repository para gestionar operaciones DNS"""

    def __init__(self, db: Session):
        """
        Inicializar repository con sesión de BD

        Args:
            db: Sesión de SQLModel
        """
        self.db = db
        self._drivers = {}

    # ========== Provider Operations ==========

    def get_provider(self, provider_key: str) -> Provider:
        """
        Obtener provider configurado

        Args:
            provider_key: Clave del provider (ej: cloudflare)

        Returns:
            Provider configurado

        Raises:
            ValueError: Si el provider no existe o no está activo
        """
        statement = select(Provider).where(
            Provider.key == provider_key,
            Provider.is_active,
        )
        provider = self.db.exec(statement).first()

        if not provider:
            raise ValueError(f"Proveedor '{provider_key}' no configurado")

        if not provider.dns:
            raise ValueError(f"DNS no habilitado para proveedor '{provider_key}'")

        if not provider.credentials.get("api_token"):
            raise ValueError(f"API token no configurado para '{provider_key}'")

        return provider

    def get_provider_credentials(self, provider_key: str) -> Dict[str, Any]:
        """
        Obtener credenciales del provider

        Args:
            provider_key: Clave del provider

        Returns:
            Dict con credenciales
        """
        provider = self.get_provider(provider_key)
        return provider.credentials

    # ========== Driver Operations ==========

    def get_driver(self, provider_key: str, credentials: Dict[str, Any]):
        """
        Obtener driver DNS (con cache)

        Args:
            provider_key: Clave del provider
            credentials: Credenciales del provider

        Returns:
            Driver DNS
        """
        cache_key = f"{provider_key}_{hash(str(credentials))}"

        if cache_key not in self._drivers:
            try:
                driver = DNSDriverFactory.get_driver(provider_key)
                self._drivers[cache_key] = driver
                logger.debug(f"Driver DNS creado para {provider_key}")
            except ValueError as e:
                logger.error(f"Proveedor DNS no soportado: {provider_key}")
                raise ValueError(f"Proveedor DNS no soportado: {provider_key}") from e

        return self._drivers[cache_key]

    # ========== DNS Operations ==========

    async def validate_provider_connection(self, provider_key: str) -> bool:
        """
        Validar conexión con provider DNS

        Args:
            provider_key: Clave del provider

        Returns:
            True si la conexión es válida
        """
        try:
            credentials = self.get_provider_credentials(provider_key)
            driver = self.get_driver(provider_key, credentials)
            return await driver.validate_credentials(credentials)
        except Exception as e:
            logger.error(f"Error validando provider {provider_key}: {e}")
            return False

    async def list_zones(self, provider_key: str) -> List[Dict[str, Any]]:
        """
        Listar zonas DNS disponibles

        Args:
            provider_key: Clave del provider

        Returns:
            Lista de zonas DNS
        """
        credentials = self.get_provider_credentials(provider_key)
        driver = self.get_driver(provider_key, credentials)
        return await driver.list_zones(credentials)

    async def list_records(
        self, provider_key: str, zone_id: str, record_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Listar registros DNS de una zona

        Args:
            provider_key: Clave del provider
            zone_id: ID de la zona
            record_type: Tipo de registro para filtrar (opcional)

        Returns:
            Lista de registros DNS
        """
        credentials = self.get_provider_credentials(provider_key)
        driver = self.get_driver(provider_key, credentials)
        return await driver.list_records(zone_id, credentials, record_type)

    async def get_record(self, provider_key: str, zone_id: str, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener un registro DNS específico

        Args:
            provider_key: Clave del provider
            zone_id: ID de la zona
            record_id: ID del registro

        Returns:
            Registro DNS o None si no existe
        """
        records = await self.list_records(provider_key, zone_id)
        return next((r for r in records if r["id"] == record_id), None)

    async def create_record(
        self,
        provider_key: str,
        zone_id: str,
        record_type: str,
        name: str,
        content: str,
        ttl: int = 3600,
        proxied: bool = False,
    ) -> Dict[str, Any]:
        """
        Crear registro DNS

        Args:
            provider_key: Clave del provider
            zone_id: ID de la zona
            record_type: Tipo de registro (A, CNAME, etc.)
            name: Nombre del registro
            content: Contenido del registro
            ttl: TTL en segundos
            proxied: Habilitar proxy (solo Cloudflare)

        Returns:
            Registro DNS creado
        """
        credentials = self.get_provider_credentials(provider_key)
        driver = self.get_driver(provider_key, credentials)

        return await driver.create_record(
            zone_id=zone_id,
            record_type=record_type,
            name=name,
            content=content,
            credentials=credentials,
            ttl=ttl,
            proxied=proxied,
        )

    async def delete_record(self, provider_key: str, zone_id: str, record_id: str) -> None:
        """
        Eliminar registro DNS

        Args:
            provider_key: Clave del provider
            zone_id: ID de la zona
            record_id: ID del registro
        """
        credentials = self.get_provider_credentials(provider_key)
        driver = self.get_driver(provider_key, credentials)
        await driver.delete_record(zone_id, record_id, credentials)

    # ========== Helper Methods ==========

    def get_zone_by_name(
        self, provider_key: str, zone_name: str, zones: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Buscar zona por nombre

        Args:
            provider_key: Clave del provider
            zone_name: Nombre de la zona
            zones: Lista de zonas

        Returns:
            Zona encontrada o None
        """
        return next((z for z in zones if z["name"] == zone_name), None)

    async def get_tunnel_hostname(self, provider_key: str, tunnel_name: str) -> Optional[str]:
        """
        Obtener hostname del túnel desde Cloudflare

        Args:
            provider_key: Clave del provider (debe ser cloudflare)
            tunnel_name: Nombre del túnel

        Returns:
            Hostname del túnel (UUID.cfargotunnel.com) o None
        """
        if provider_key != "cloudflare":
            raise ValueError("Solo soportado para Cloudflare")

        try:
            from app.integrations.cloudflare.tunnel_driver import CloudflareDriver

            credentials = self.get_provider_credentials(provider_key)
            driver = CloudflareDriver(credentials["api_token"])

            # Obtener account_id
            account_id = driver.get_account_id()

            # Listar túneles
            tunnels = await driver.list_tunnels(account_id, name=tunnel_name)

            # Buscar túnel exacto que no esté eliminado
            for tunnel in tunnels:
                if tunnel.get("name") == tunnel_name and not tunnel.get("deleted_at"):
                    tunnel_id = tunnel["id"]
                    logger.info(f"Túnel encontrado: {tunnel_name} (UUID: {tunnel_id})")
                    return f"{tunnel_id}.cfargotunnel.com"

            logger.warning(f"Túnel '{tunnel_name}' no encontrado")
            return None

        except Exception as e:
            logger.error(f"Error obteniendo hostname del túnel: {e}")
            return None
