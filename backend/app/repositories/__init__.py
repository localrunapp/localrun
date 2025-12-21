"""
Repositories - Capa de acceso a datos

Los repositories encapsulan la lógica de acceso a datos y queries,
separándola de la lógica de negocio en los controllers.
"""

from .service_repository import ServiceRepository

__all__ = ["ServiceRepository"]
