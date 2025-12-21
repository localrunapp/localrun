"""
Cloudflare DNS driver
"""

import httpx
from typing import List, Dict, Any, Optional

from core.dns_driver import DNSDriver
from core.logger import setup_logger

logger = setup_logger(__name__)


class CloudflareDNSDriver(DNSDriver):
    """Cloudflare DNS provider"""

    BASE_URL = "https://api.cloudflare.com/client/v4"

    def __init__(self, api_token: Optional[str] = None, zone_id: Optional[str] = None):
        self.api_token = api_token
        self.zone_id = zone_id
        if api_token:
            self.headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}
            if zone_id:
                logger.debug(f"Cloudflare DNS driver initialized for zone {zone_id}")
            else:
                logger.debug("Cloudflare DNS driver initialized without specific zone")
        else:
            self.headers = {"Content-Type": "application/json"}

    # ========== Interface DNSDriver Methods ==========

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
        """Create DNS record (Interface method)"""
        # Usar credenciales si se proporcionan, sino usar las del constructor
        api_token = credentials.get("api_token", self.api_token)

        # Crear una instancia temporal con las credenciales específicas
        temp_driver = CloudflareDNSDriver(api_token, zone_id)
        return await temp_driver.create_record_simple(record_type, name, content, proxied, ttl)

    async def update_record(
        self,
        zone_id: str,
        record_id: str,
        content: str,
        credentials: Dict[str, Any],
        ttl: Optional[int] = None,
        proxied: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Update DNS record (Interface method)"""
        api_token = credentials.get("api_token", self.api_token)
        temp_driver = CloudflareDNSDriver(api_token, zone_id)

        if proxied is None:
            proxied = False
        return await temp_driver.update_record_simple(record_id, content, proxied)

    async def delete_record(self, zone_id: str, record_id: str, credentials: Dict[str, Any]) -> None:
        """Delete DNS record (Interface method)"""
        api_token = credentials.get("api_token", self.api_token)
        temp_driver = CloudflareDNSDriver(api_token, zone_id)
        return await temp_driver.delete_record_simple(record_id)

    async def list_records(
        self, zone_id: str, credentials: Dict[str, Any], record_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List DNS records (Interface method)"""
        api_token = credentials.get("api_token", self.api_token)
        temp_driver = CloudflareDNSDriver(api_token, zone_id)
        return await temp_driver.list_records_simple()

    async def list_zones(self, credentials: Dict[str, Any]) -> List[Dict[str, Any]]:
        """List DNS zones (Interface method)"""
        api_token = credentials.get("api_token", self.api_token)
        temp_driver = CloudflareDNSDriver(api_token)
        return await temp_driver.list_zones_simple()

    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Validate credentials"""
        try:
            api_token = credentials.get("api_token")
            if not api_token:
                return False

            temp_driver = CloudflareDNSDriver(api_token)
            await temp_driver.list_zones_simple()
            return True
        except Exception:
            return False

    # ========== Simple Methods (backwards compatibility) ==========

    async def create_record_simple(
        self, record_type: str, name: str, content: str, proxied: bool = False, ttl: int = 3600
    ) -> Dict[str, Any]:
        """Create DNS record in Cloudflare"""
        logger.info(f"Creating DNS record: {name} ({record_type})")

        async with httpx.AsyncClient() as client:
            url = f"{self.BASE_URL}/zones/{self.zone_id}/dns_records"

            payload = {
                "type": record_type,
                "name": name,
                "content": content,
                "proxied": proxied,
                "ttl": ttl if not proxied else 1,  # Auto if proxied
            }

            logger.debug(f"Cloudflare API request: POST {url}")
            resp = await client.post(url, json=payload, headers=self.headers)
            resp.raise_for_status()

            data = resp.json()
            if not data.get("success"):
                logger.error(f"Cloudflare API error: {data.get('errors')}")
                raise Exception(f"Cloudflare API error: {data.get('errors')}")

            logger.info(f"DNS record created successfully: {data['result']['id']}")
            return data["result"]

    async def delete_record_simple(self, record_id: str) -> None:
        """Delete DNS record from Cloudflare"""
        async with httpx.AsyncClient() as client:
            url = f"{self.BASE_URL}/zones/{self.zone_id}/dns_records/{record_id}"
            resp = await client.delete(url, headers=self.headers)
            resp.raise_for_status()

    async def list_records_simple(self) -> List[Dict[str, Any]]:
        """List all DNS records in zone"""
        async with httpx.AsyncClient() as client:
            url = f"{self.BASE_URL}/zones/{self.zone_id}/dns_records"
            resp = await client.get(url, headers=self.headers)
            resp.raise_for_status()

            data = resp.json()
            if not data.get("success"):
                raise Exception(f"Cloudflare API error: {data.get('errors')}")

            return data["result"]

    async def list_zones_simple(self) -> List[Dict[str, Any]]:
        """List all DNS zones available to this API token"""
        logger.info("Listing available Cloudflare DNS zones")

        async with httpx.AsyncClient() as client:
            url = f"{self.BASE_URL}/zones"
            resp = await client.get(url, headers=self.headers)
            resp.raise_for_status()

            data = resp.json()
            if not data.get("success"):
                logger.error(f"Cloudflare API error: {data.get('errors')}")
                raise Exception(f"Cloudflare API error: {data.get('errors')}")

            zones = data["result"]
            logger.info(f"Found {len(zones)} DNS zones")
            return zones

    async def update_record_simple(self, record_id: str, content: str, proxied: bool = False) -> Dict[str, Any]:
        """Update existing DNS record"""
        async with httpx.AsyncClient() as client:
            url = f"{self.BASE_URL}/zones/{self.zone_id}/dns_records/{record_id}"

            payload = {"content": content, "proxied": proxied}

            resp = await client.patch(url, json=payload, headers=self.headers)
            resp.raise_for_status()

            data = resp.json()
            if not data.get("success"):
                raise Exception(f"Cloudflare API error: {data.get('errors')}")

            return data["result"]
