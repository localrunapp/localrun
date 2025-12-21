import socket

from core.settings import settings
from core.logger import setup_logger

logger = setup_logger(__name__)


class ConfigController:
    """System configuration management."""

    def _get_private_ip(self) -> str:
        """Get private IP address of the host."""
        try:
            # Create a socket to determine the local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "localhost"

    async def get_config(self):
        """
        Get public system configuration.
        Frontend uses this to know backend URLs, Quick Tunnel status, etc.
        """
        # Quick Tunnel info
        quick_tunnel_available = not settings.is_development() and settings.quick_tunnel_enabled
        quick_tunnel_message = None

        if settings.is_development():
            quick_tunnel_message = "Quick Tunnel disabled in development mode"
        elif not settings.quick_tunnel_enabled:
            quick_tunnel_message = "Quick Tunnel disabled in settings"
        elif settings.quick_tunnel_url:
            quick_tunnel_message = "Temporary URL - Configure permanent tunnel in admin panel"
        else:
            quick_tunnel_message = "Quick Tunnel starting..."

        # Get private IP
        private_ip = self._get_private_ip()

        # Build access URLs
        access_urls = {
            "localhost": f"http://localhost:{settings.app_port}",
            "private_ip": f"http://{private_ip}:{settings.app_port}",
        }

        # Add quick tunnel URL only in production
        if quick_tunnel_available and settings.quick_tunnel_url:
            access_urls["quick_tunnel"] = settings.quick_tunnel_url

        return {
            "app_name": settings.app_name,
            "app_env": settings.app_env,
            "backend_url": f"http://{settings.app_host}:{settings.app_port}",
            "access_urls": access_urls,
            "quick_tunnel": {
                "available": quick_tunnel_available,
                "enabled": settings.quick_tunnel_enabled,
                "url": settings.quick_tunnel_url if quick_tunnel_available else None,
                "message": quick_tunnel_message,
            },
            "version": "1.0.0",
        }
