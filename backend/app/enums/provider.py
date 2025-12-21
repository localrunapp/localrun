from enum import Enum


class ProviderType(str, Enum):
    """Provider types available in the system"""

    CLOUDFLARE = "cloudflare"
    NGROK = "ngrok"
