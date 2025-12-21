"""
Tunnel Service - Service Locator for Tunnel Drivers

Resolves the appropriate tunnel driver based on provider and protocol.
"""

import logging
from typing import Any

from app.enums import TunnelProvider, TunnelProtocol

logger = logging.getLogger(__name__)


class TunnelService:
    """Service Locator for tunnel drivers"""

    @staticmethod
    def resolve(provider: TunnelProvider, protocol: TunnelProtocol) -> Any:
        """
        Resolve and return the appropriate tunnel driver.

        Args:
            provider: TunnelProvider enum (CLOUDFLARE, NGROK, PINGGY)
            protocol: TunnelProtocol enum (HTTP, HTTPS, TCP, UDP)

        Returns:
            Instance of the appropriate driver

        Raises:
            ValueError: If provider/protocol combination is not supported

        Example:
            >>> driver = TunnelService.resolve(TunnelProvider.CLOUDFLARE, TunnelProtocol.TCP)
            >>> tunnel_info = await driver.start_tunnel(config)
        """
        logger.debug(f"Resolving driver for {provider.value} + {protocol.value}")

        # Cloudflare drivers
        if provider == TunnelProvider.CLOUDFLARE:
            from app.integrations.cloudflare.tunnel_driver import CloudflaredHTTPDriver
            return CloudflaredHTTPDriver()

        # Ngrok drivers
        elif provider == TunnelProvider.NGROK:
            if protocol in [TunnelProtocol.HTTP, TunnelProtocol.HTTPS]:
                from app.integrations.ngrok.http_driver import NgrokHTTPDriver
                return NgrokHTTPDriver()
            elif protocol == TunnelProtocol.TCP:
                from app.integrations.ngrok.tcp_driver import NgrokTCPDriver
                return NgrokTCPDriver()

        # Pinggy drivers
        elif provider == TunnelProvider.PINGGY:
            from app.integrations.pinggy.pinggy_driver import PinggyDriver
            return PinggyDriver()

        # Unsupported combination
        raise ValueError(
            f"No driver available for provider '{provider.value}' with protocol '{protocol.value}'"
        )

    @staticmethod
    def get_supported_combinations() -> dict:
        """
        Get all supported provider/protocol combinations.

        Returns:
            Dict mapping providers to their supported protocols
        """
        return {
            TunnelProvider.CLOUDFLARE: [
                TunnelProtocol.HTTP,
                TunnelProtocol.HTTPS,
                TunnelProtocol.TCP,
            ],
            TunnelProvider.NGROK: [
                TunnelProtocol.HTTP,
                TunnelProtocol.HTTPS,
                TunnelProtocol.TCP,
            ],
            TunnelProvider.PINGGY: [
                TunnelProtocol.HTTP,
                TunnelProtocol.HTTPS,
                TunnelProtocol.TCP,
            ],
        }

    @staticmethod
    def is_supported(provider: TunnelProvider, protocol: TunnelProtocol) -> bool:
        """
        Check if a provider/protocol combination is supported.

        Args:
            provider: TunnelProvider enum
            protocol: TunnelProtocol enum

        Returns:
            True if supported, False otherwise
        """
        supported = TunnelService.get_supported_combinations()
        return provider in supported and protocol in supported[provider]


    async def start_quick_tunnel(self, service: Any, db: Any = None) -> tuple[str, str]:
        """Start a quick tunnel for the given service."""
        from core.tunnel_driver import TunnelConfig

        provider = self._get_provider_enum(service.provider_key)
        protocol = self._get_protocol_enum(service.protocol)
        
        driver = self.resolve(provider, protocol)
        
        config = TunnelConfig(
            port=service.port,
            protocol=service.protocol,
            host=service.host or "localhost",
            service_id=str(service.id),  # Add service ID for container labeling
            healthcheck_enabled=service.healthcheck_enabled,
            healthcheck_path=service.healthcheck_path,
            healthcheck_timeout=service.healthcheck_timeout,
            healthcheck_expected_status=service.healthcheck_expected_status,
        )
        
        info = await driver.create_tunnel(config)
        return info.public_url, info.process_id

    async def start_named_tunnel(self, service: Any, db: Any = None) -> tuple[str, str]:
        """Start a named tunnel for the given service."""
        from core.tunnel_driver import TunnelConfig

        provider = self._get_provider_enum(service.provider_key)
        protocol = self._get_protocol_enum(service.protocol)
        
        driver = self.resolve(provider, protocol)
        
        config = TunnelConfig(
            port=service.port,
            protocol=service.protocol,
            host=service.host or "localhost",
            domain=service.domain,
            subdomain=service.subdomain,
            service_id=str(service.id),
            healthcheck_enabled=service.healthcheck_enabled,
            healthcheck_path=service.healthcheck_path,
            healthcheck_timeout=service.healthcheck_timeout,
            healthcheck_expected_status=service.healthcheck_expected_status,
        )
        
        info = await driver.create_tunnel(config)
        return info.public_url, info.process_id

    async def stop_quick_tunnel(self, service: Any) -> bool:
        """Stop a quick tunnel."""
        provider = self._get_provider_enum(service.provider_key)
        protocol = self._get_protocol_enum(service.protocol)
        
        driver = self.resolve(provider, protocol)
        return await driver.stop_tunnel(service.port, service_id=str(service.id))


    async def stop_named_tunnel(self, service: Any, db: Any = None) -> bool:
        """Stop a named tunnel."""
        provider = self._get_provider_enum(service.provider_key)
        protocol = self._get_protocol_enum(service.protocol)
        
        driver = self.resolve(provider, protocol)
        return await driver.stop_tunnel(service.port)

    async def get_diagnostics(self, services: list, repo: Any) -> dict:
        """Get diagnostics for tunnel system."""
        # Simple diagnostics for now, aggregating from drivers if needed
        # Assuming cloudflare is main provider for now
        from app.integrations.cloudflare.tunnel_driver import CloudflaredHTTPDriver
        driver = CloudflaredHTTPDriver()
        return driver.get_provider_info()

    # Helpers
    def _get_provider_enum(self, key: str) -> TunnelProvider:
        key = key.lower()
        if key == "cloudflare": return TunnelProvider.CLOUDFLARE
        if key == "ngrok": return TunnelProvider.NGROK
        if key == "pinggy": return TunnelProvider.PINGGY
        raise ValueError(f"Unknown provider key: {key}")

    def _get_protocol_enum(self, key: str) -> TunnelProtocol:
        key = key.lower()
        if key in ["http", "https"]: return TunnelProtocol.HTTP
        if key == "tcp": return TunnelProtocol.TCP
        if key == "udp": return TunnelProtocol.UDP
        if key == "ssh": return TunnelProtocol.SSH
        raise ValueError(f"Unknown protocol key: {key}")

# Singleton instance
tunnel_service = TunnelService()
