"""
Drivers controller - Discover available drivers by protocol
"""

from typing import Any, Dict, List

from core.logger import setup_logger

logger = setup_logger(__name__)


# Driver registry - maps protocol + provider to driver class
DRIVER_REGISTRY = {
    "http": {
        "cloudflare": {
            "class": "app.drivers.http.cloudflared.CloudflaredHTTPDriver",
            "name": "Cloudflare HTTP Tunnel",
            "credentials_required": ["token"],
            "features": ["zero_trust", "automatic_dns", "ddos_protection"],
            "free_tier": True,
        },
        "ngrok": {
            "class": "app.drivers.http.ngrok.NgrokHTTPDriver",
            "name": "Ngrok HTTP Tunnel",
            "credentials_required": ["authtoken"],
            "features": ["custom_domains", "basic_auth", "oauth"],
            "free_tier": True,
        },
    },
    "https": {
        "cloudflare": {
            "class": "app.drivers.http.cloudflared.CloudflaredHTTPDriver",
            "name": "Cloudflare HTTPS Tunnel",
            "credentials_required": ["token"],
            "features": ["zero_trust", "automatic_ssl", "ddos_protection"],
            "free_tier": True,
        },
        "ngrok": {
            "class": "app.drivers.http.ngrok.NgrokHTTPDriver",
            "name": "Ngrok HTTPS Tunnel",
            "credentials_required": ["authtoken"],
            "features": ["custom_domains", "automatic_ssl", "basic_auth"],
            "free_tier": True,
        },
    },
    "tcp": {
        "cloudflare": {
            "class": "app.drivers.tcp.cloudflared.CloudflaredTCPDriver",
            "name": "Cloudflare TCP Tunnel",
            "credentials_required": ["token"],
            "features": ["any_tcp_port", "zero_trust"],
            "free_tier": True,
        },
        "ngrok": {
            "class": "app.drivers.tcp.ngrok.NgrokTCPDriver",
            "name": "Ngrok TCP Tunnel",
            "credentials_required": ["authtoken"],
            "features": ["any_tcp_port"],
            "free_tier": False,
            "requires_plan": "paid",
        },
    },
    "udp": {
        "cloudflare": {
            "class": "app.drivers.udp.cloudflared.CloudflaredUDPDriver",
            "name": "Cloudflare UDP Tunnel",
            "credentials_required": ["token"],
            "features": ["udp_support", "zero_trust"],
            "free_tier": True,
            "notes": "Experimental feature",
        }
    },
    "websocket": {
        "cloudflare": {
            "class": "app.drivers.http.cloudflared.CloudflaredHTTPDriver",
            "name": "Cloudflare WebSocket Tunnel",
            "credentials_required": ["token"],
            "features": ["websocket_support", "automatic_upgrade"],
            "free_tier": True,
        },
        "ngrok": {
            "class": "app.drivers.http.ngrok.NgrokHTTPDriver",
            "name": "Ngrok WebSocket Tunnel",
            "credentials_required": ["authtoken"],
            "features": ["websocket_support", "automatic_upgrade"],
            "free_tier": True,
        },
    },
    "ssh": {
        "cloudflare": {
            "class": "app.drivers.ssh.cloudflared.CloudflaredSSHDriver",
            "name": "Cloudflare SSH Tunnel",
            "credentials_required": ["token"],
            "features": ["ssh_support", "zero_trust", "browser_rendering"],
            "free_tier": True,
        }
    },
    "dns": {
        "cloudflare": {
            "class": "app.drivers.dns.cloudflare.CloudflareDNSDriver",
            "name": "Cloudflare DNS",
            "credentials_required": ["api_token", "zone_id"],
            "features": ["automatic_dns", "proxied_records", "ddos_protection"],
            "supported_record_types": ["A", "AAAA", "CNAME", "TXT", "MX", "SRV"],
            "free_tier": True,
        }
    },
}


class DriversController:
    """
    Controller for drivers discovery.
    Laravel equivalent: App/Http/Controllers/DriversController
    """

    async def list_drivers(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        List all available drivers organized by protocol.
        Each protocol can have multiple provider implementations.

        Returns:
            Dictionary with protocols as keys and their available drivers
        """
        logger.info("Listing available drivers by protocol")

        result = {}
        for protocol, providers in DRIVER_REGISTRY.items():
            result[protocol] = []
            for provider_name, driver_info in providers.items():
                result[protocol].append(
                    {
                        "provider": provider_name,
                        "type": f"{provider_name}_{protocol}",
                        "driver_class": driver_info["class"],
                        **{k: v for k, v in driver_info.items() if k != "class"},
                    }
                )

        return result

    async def get_protocol_drivers(self, protocol: str) -> List[Dict[str, Any]]:
        """
        Get all drivers available for a specific protocol.

        Args:
            protocol: Protocol name (http, https, tcp, udp, websocket, ssh, dns)

        Returns:
            List of drivers supporting that protocol
        """
        logger.info(f"Getting drivers for protocol: {protocol}")

        all_drivers = await self.list_drivers()
        return all_drivers.get(protocol.lower(), [])

    async def get_driver_info(self, provider: str, protocol: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific driver.

        Args:
            provider: Provider name (cloudflare, ngrok)
            protocol: Protocol name (http, tcp, etc.)

        Returns:
            Driver detailed information
        """
        logger.info(f"Getting driver info: {provider}/{protocol}")

        driver_info = DRIVER_REGISTRY.get(protocol, {}).get(provider)

        if driver_info:
            return {"provider": provider, "protocol": protocol, "type": f"{provider}_{protocol}", **driver_info}

        return {"error": "Driver not found"}

    def get_driver_instance(self, provider: str, protocol: str):
        """
        Get an instance of the specified driver.

        Args:
            provider: Provider name (cloudflare, ngrok)
            protocol: Protocol name (http, https, tcp, udp, websocket, ssh, dns)

        Returns:
            Driver instance

        Raises:
            ValueError: If driver not found or cannot be instantiated
        """
        logger.info(f"Creating driver instance: {provider}/{protocol}")

        driver_info = DRIVER_REGISTRY.get(protocol, {}).get(provider)

        if not driver_info:
            raise ValueError(f"Driver not found: {provider}/{protocol}")

        driver_class_path = driver_info["class"]

        try:
            # Import and instantiate the driver class
            # Example: "app.drivers.http.cloudflared.CloudflaredHTTPDriver"
            module_path, class_name = driver_class_path.rsplit(".", 1)

            # Dynamic import
            import importlib

            module = importlib.import_module(module_path)
            driver_class = getattr(module, class_name)

            # Instantiate and return
            return driver_class()

        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to instantiate driver {driver_class_path}: {str(e)}")
            raise ValueError(f"Failed to instantiate driver: {str(e)}")


# Create a singleton instance for easy access
drivers_controller = DriversController()
