"""
Tunnel Protocol Enum
"""

from enum import Enum


class TunnelProtocol(str, Enum):
    """Supported tunnel protocols"""
    
    HTTP = "http"
    HTTPS = "https"
    TCP = "tcp"
    UDP = "udp"
