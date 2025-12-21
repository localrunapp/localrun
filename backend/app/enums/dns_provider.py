"""
DNS Provider Enum
"""

from enum import Enum


class DNSProvider(str, Enum):
    """Supported DNS providers"""
    
    CLOUDFLARE = "cloudflare"
    NAMECHEAP = "namecheap"
    ROUTE53 = "route53"
