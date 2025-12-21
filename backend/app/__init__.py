"""
Inicialización de la aplicación - Registro de drivers
"""

from core.dns_driver import DNSDriverFactory
from app.integrations.cloudflare.dns_driver import CloudflareDNSDriver
from app.integrations.namecheap.dns_driver import NamecheapDNSDriver

# Registrar drivers DNS disponibles
DNSDriverFactory.register_driver("cloudflare", CloudflareDNSDriver)
DNSDriverFactory.register_driver("namecheap", NamecheapDNSDriver)

# TODO: Registrar otros drivers cuando estén disponibles
# DNSDriverFactory.register_driver("route53", Route53DNSDriver)
# DNSDriverFactory.register_driver("dnsmadeeasy", DNSMadeEasyDriver)

__all__ = ["DNSDriverFactory"]
