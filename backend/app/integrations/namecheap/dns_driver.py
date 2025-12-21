"""
Namecheap DNS driver
"""

import hashlib
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree as ET

import httpx

from core.dns_driver import DNSDriver
from core.logger import setup_logger

logger = setup_logger(__name__)


class NamecheapDNSDriver(DNSDriver):
    """Namecheap DNS provider using XML API"""

    BASE_URL = "https://api.namecheap.com/xml.response"

    def __init__(self, api_user: Optional[str] = None, api_key: Optional[str] = None, username: Optional[str] = None):
        self.api_user = api_user
        self.api_key = api_key
        self.username = username or api_user
        logger.debug("Namecheap DNS driver initialized")

    async def create_record(
        self,
        zone_id: str,
        record_type: str,
        name: str,
        content: str,
        credentials: Dict[str, Any],
        ttl: int = 1800,
        proxied: bool = False,
    ) -> Dict[str, Any]:
        """Create DNS record"""
        api_user = credentials.get("api_user", self.api_user)
        api_key = credentials.get("api_key", self.api_key)
        username = credentials.get("username", self.username)

        temp_driver = NamecheapDNSDriver(api_user, api_key, username)
        return await temp_driver._add_record(zone_id, record_type, name, content, ttl)

    async def update_record(
        self,
        zone_id: str,
        record_id: str,
        content: str,
        credentials: Dict[str, Any],
        ttl: Optional[int] = None,
        proxied: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Update DNS record - Namecheap doesn't support direct updates, need to replace all records"""
        api_user = credentials.get("api_user", self.api_user)
        api_key = credentials.get("api_key", self.api_key)
        username = credentials.get("username", self.username)

        temp_driver = NamecheapDNSDriver(api_user, api_key, username)

        # Get all current records
        records = await temp_driver._get_hosts(zone_id)

        # Find and update the specific record
        updated = False
        for record in records:
            if record.get("id") == record_id:
                record["Address"] = content
                if ttl:
                    record["TTL"] = ttl
                updated = True
                break

        if not updated:
            raise ValueError(f"Record {record_id} not found")

        # Set all records back (Namecheap API limitation)
        await temp_driver._set_hosts(zone_id, records)

        return {"id": record_id, "content": content, "ttl": ttl or 1800}

    async def delete_record(self, zone_id: str, record_id: str, credentials: Dict[str, Any]) -> None:
        """Delete DNS record"""
        api_user = credentials.get("api_user", self.api_user)
        api_key = credentials.get("api_key", self.api_key)
        username = credentials.get("username", self.username)

        temp_driver = NamecheapDNSDriver(api_user, api_key, username)

        # Get all current records
        records = await temp_driver._get_hosts(zone_id)

        # Filter out the record to delete
        filtered_records = [r for r in records if r.get("id") != record_id]

        if len(filtered_records) == len(records):
            raise ValueError(f"Record {record_id} not found")

        # Set remaining records
        await temp_driver._set_hosts(zone_id, filtered_records)

    async def list_records(
        self, zone_id: str, credentials: Dict[str, Any], record_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List DNS records"""
        api_user = credentials.get("api_user", self.api_user)
        api_key = credentials.get("api_key", self.api_key)
        username = credentials.get("username", self.username)

        temp_driver = NamecheapDNSDriver(api_user, api_key, username)
        records = await temp_driver._get_hosts(zone_id)

        if record_type:
            records = [r for r in records if r.get("type") == record_type]

        return records

    async def list_zones(self, credentials: Dict[str, Any]) -> List[Dict[str, Any]]:
        """List DNS zones (domains)"""
        api_user = credentials.get("api_user", self.api_user)
        api_key = credentials.get("api_key", self.api_key)
        username = credentials.get("username", self.username)

        logger.info("Listing Namecheap domains")

        async with httpx.AsyncClient() as client:
            params = {
                "ApiUser": api_user,
                "ApiKey": api_key,
                "UserName": username,
                "Command": "namecheap.domains.getList",
                "ClientIp": await self._get_client_ip(),
                "PageSize": 100,
            }

            resp = await client.get(self.BASE_URL, params=params)
            resp.raise_for_status()

            root = ET.fromstring(resp.text)

            # Check for errors
            if root.get("Status") == "ERROR":
                errors = root.findall(".//Error")
                error_msg = errors[0].text if errors else "Unknown error"
                raise Exception(f"Namecheap API error: {error_msg}")

            # Parse domains
            domains = []
            domain_list = root.findall(".//Domain")

            for domain in domain_list:
                domain_name = domain.get("Name")
                domains.append(
                    {
                        "id": domain_name,  # Use domain name as ID
                        "name": domain_name,
                        "status": "active" if domain.get("IsExpired") == "false" else "expired",
                        "name_servers": [],  # Would need separate API call to get NS
                    }
                )

            logger.info(f"Found {len(domains)} Namecheap domains")
            return domains

    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Validate credentials"""
        try:
            api_user = credentials.get("api_user")
            api_key = credentials.get("api_key")

            if not api_user or not api_key:
                return False

            temp_driver = NamecheapDNSDriver(api_user, api_key)
            await temp_driver.list_zones(credentials)
            return True
        except Exception as e:
            logger.error(f"Namecheap credential validation failed: {e}")
            return False

    # ========== Namecheap-specific methods ==========

    async def _get_client_ip(self) -> str:
        """Get public IP for API calls (Namecheap requires it)"""
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://api.ipify.org?format=text")
            return resp.text.strip()

    async def _get_hosts(self, domain: str) -> List[Dict[str, Any]]:
        """Get all DNS records for a domain"""
        # Split domain into SLD and TLD
        parts = domain.split(".")
        if len(parts) < 2:
            raise ValueError(f"Invalid domain format: {domain}")

        sld = ".".join(parts[:-1])
        tld = parts[-1]

        async with httpx.AsyncClient() as client:
            params = {
                "ApiUser": self.api_user,
                "ApiKey": self.api_key,
                "UserName": self.username,
                "Command": "namecheap.domains.dns.getHosts",
                "ClientIp": await self._get_client_ip(),
                "SLD": sld,
                "TLD": tld,
            }

            resp = await client.get(self.BASE_URL, params=params)
            resp.raise_for_status()

            root = ET.fromstring(resp.text)

            if root.get("Status") == "ERROR":
                errors = root.findall(".//Error")
                error_msg = errors[0].text if errors else "Unknown error"
                raise Exception(f"Namecheap API error: {error_msg}")

            records = []
            hosts = root.findall(".//host")

            for idx, host in enumerate(hosts):
                record_type = host.get("Type", "A")
                name = host.get("Name", "@")
                address = host.get("Address", "")
                ttl = int(host.get("TTL", "1800"))

                # Generate unique ID (Namecheap doesn't provide IDs)
                record_id = hashlib.md5(f"{name}:{record_type}:{address}:{idx}".encode()).hexdigest()[:16]

                records.append(
                    {
                        "id": record_id,
                        "zone_id": domain,
                        "zone_name": domain,
                        "name": f"{name}.{domain}" if name != "@" else domain,
                        "type": record_type,
                        "content": address,
                        "ttl": ttl,
                        "proxied": False,
                        "Name": name,  # Keep for internal use
                        "Address": address,
                        "TTL": ttl,
                    }
                )

            return records

    async def _set_hosts(self, domain: str, records: List[Dict[str, Any]]) -> None:
        """Set all DNS records for a domain (replaces existing)"""
        parts = domain.split(".")
        if len(parts) < 2:
            raise ValueError(f"Invalid domain format: {domain}")

        sld = ".".join(parts[:-1])
        tld = parts[-1]

        params = {
            "ApiUser": self.api_user,
            "ApiKey": self.api_key,
            "UserName": self.username,
            "Command": "namecheap.domains.dns.setHosts",
            "ClientIp": await self._get_client_ip(),
            "SLD": sld,
            "TLD": tld,
        }

        # Add each record as numbered parameters
        for idx, record in enumerate(records, start=1):
            params[f"HostName{idx}"] = record.get("Name", "@")
            params[f"RecordType{idx}"] = record.get("type", "A")
            params[f"Address{idx}"] = record.get("Address", record.get("content", ""))
            params[f"TTL{idx}"] = str(record.get("TTL", record.get("ttl", 1800)))

        async with httpx.AsyncClient() as client:
            resp = await client.post(self.BASE_URL, params=params)
            resp.raise_for_status()

            root = ET.fromstring(resp.text)

            if root.get("Status") == "ERROR":
                errors = root.findall(".//Error")
                error_msg = errors[0].text if errors else "Unknown error"
                raise Exception(f"Namecheap API error: {error_msg}")

    async def _add_record(
        self, domain: str, record_type: str, name: str, content: str, ttl: int = 1800
    ) -> Dict[str, Any]:
        """Add a new DNS record"""
        # Get existing records
        records = await self._get_hosts(domain)

        # Extract hostname from full name
        hostname = name.replace(f".{domain}", "") if name.endswith(domain) else name
        if hostname == domain:
            hostname = "@"

        # Generate ID for new record
        record_id = hashlib.md5(f"{hostname}:{record_type}:{content}".encode()).hexdigest()[:16]

        # Add new record
        new_record = {
            "id": record_id,
            "Name": hostname,
            "type": record_type,
            "Address": content,
            "TTL": ttl,
        }

        records.append(new_record)

        # Set all records
        await self._set_hosts(domain, records)

        return {
            "id": record_id,
            "zone_id": domain,
            "name": f"{hostname}.{domain}" if hostname != "@" else domain,
            "type": record_type,
            "content": content,
            "ttl": ttl,
            "proxied": False,
        }
