"""
Enums - Separation of concerns
"""

from enum import Enum


class TunnelProtocol(str, Enum):
    """Tunnel protocols supported"""

    HTTP = "http"
    HTTPS = "https"
    TCP = "tcp"
    UDP = "udp"
    SSH = "ssh"
    WEBSOCKET = "websocket"


class TunnelStatus(str, Enum):
    """Tunnel lifecycle states"""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class DriverType(str, Enum):
    """Driver categories"""

    DNS = "dns"
    TUNNEL = "tunnel"
    BASTION = "bastion"
