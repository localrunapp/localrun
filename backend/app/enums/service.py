from enum import Enum


class ServiceProtocol(str, Enum):
    """Protocolos soportados para servicios"""

    HTTP = "http"
    HTTPS = "https"
    TCP = "tcp"
    UDP = "udp"
    SSH = "ssh"
    WEBSOCKET = "websocket"


class ServiceStatus(str, Enum):
    """Estados de un servicio"""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"
    STOPPING = "stopping"
