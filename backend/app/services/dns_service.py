"""
DNS Service - Service Locator for DNS Drivers

Resolves the appropriate DNS driver based on provider.
"""

import logging
from typing import Any

from app.enums import DNSProvider

logger = logging.getLogger(__name__)


class DNSService:
    """Service Locator for DNS drivers"""

    @staticmethod
    def resolve(provider: DNSProvider) -> Any:
        """
        Resolve and return the appropriate DNS driver.

        Args:
            provider: DNSProvider enum (CLOUDFLARE, NAMECHEAP, ROUTE53)

        Returns:
            Instance of the appropriate DNS driver

        Raises:
            ValueError: If provider is not supported

        Example:
            >>> driver = DNSService.resolve(DNSProvider.CLOUDFLARE)
            >>> zones = await driver.list_zones(credentials)
        """
        logger.debug(f"Resolving DNS driver for {provider.value}")

        # Cloudflare DNS
        if provider == DNSProvider.CLOUDFLARE:
            from app.integrations.cloudflare.dns_driver import CloudflareDNSDriver
            return CloudflareDNSDriver()

        # Namecheap DNS
        elif provider == DNSProvider.NAMECHEAP:
            from app.integrations.namecheap.dns_driver import NamecheapDNSDriver
            return NamecheapDNSDriver()

        # Route53 DNS
        elif provider == DNSProvider.ROUTE53:
            # TODO: Implement Route53 driver
            raise NotImplementedError(f"Route53 driver not yet implemented")

        # Unsupported provider
        raise ValueError(f"No DNS driver available for provider '{provider.value}'")

    @staticmethod
    def get_supported_providers() -> list:
        """
        Get all supported DNS providers.

        Returns:
            List of supported DNSProvider enums
        """
        return [
            DNSProvider.CLOUDFLARE,
            DNSProvider.NAMECHEAP,
            # DNSProvider.ROUTE53,  # TODO: Uncomment when implemented
        ]

    @staticmethod
    def is_supported(provider: DNSProvider) -> bool:
        """
        Check if a DNS provider is supported.

        Args:
            provider: DNSProvider enum

        Returns:
            True if supported, False otherwise
        """
        return provider in DNSService.get_supported_providers()


# Singleton instance (optional, can use static methods directly)
dns_service = DNSService()
