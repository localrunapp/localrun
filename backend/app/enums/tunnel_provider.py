"""
Tunnel Provider Enum
"""

from enum import Enum


class TunnelProvider(str, Enum):
    """Supported tunnel providers"""
    
    CLOUDFLARE = "cloudflare"
    NGROK = "ngrok"
    PINGGY = "pinggy"
