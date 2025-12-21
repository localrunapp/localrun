"""
Service Repository - Capa de acceso a datos para servicios

Maneja todas las operaciones de base de datos relacionadas con servicios,
incluyendo CRUD, queries, y operaciones de estado.
"""

import logging
import uuid
from typing import List, Optional
from datetime import datetime

from sqlmodel import Session, select
from fastapi import HTTPException

from app.models.service import Service
from app.enums.service import ServiceStatus, ServiceProtocol
from app.models.provider import Provider
from app.models.user import User

logger = logging.getLogger(__name__)


class ServiceRepository:
    """Repository para gestionar servicios en base de datos"""

    def __init__(self, db: Session):
        """
        Inicializar repository con sesión de BD.

        Args:
            db: Sesión de SQLModel
        """
        self.db = db

    # ========== CRUD Básico ==========

    def get_by_id(self, service_id: uuid.UUID, user_id: int) -> Optional[Service]:
        """
        Obtener servicio por ID y usuario.

        Args:
            service_id: ID del servicio
            user_id: ID del usuario propietario

        Returns:
            Service si existe, None si no
        """
        statement = select(Service).where(Service.id == service_id, Service.user_id == user_id)
        return self.db.exec(statement).first()

    def get_by_port(self, port: int, host: str, user_id: int, provider_key: str) -> Optional[Service]:
        """
        Buscar servicio por puerto, host y proveedor.

        Args:
            port: Puerto del servicio
            host: Host del servicio
            user_id: ID del usuario
            provider_key: Clave del proveedor

        Returns:
            Service si existe, None si no
        """
        statement = select(Service).where(
            Service.user_id == user_id, Service.port == port, Service.host == host, Service.provider_key == provider_key
        )
        return self.db.exec(statement).first()

    def get_by_port_and_host(self, port: int, host: str, user_id: int) -> Optional[Service]:
        """
        Buscar servicio por puerto y host (sin filtro de proveedor).

        Args:
            port: Puerto del servicio
            host: Host del servicio
            user_id: ID del usuario

        Returns:
            Service si existe, None si no
        """
        statement = select(Service).where(Service.user_id == user_id, Service.port == port, Service.host == host)
        return self.db.exec(statement).first()

    def list_all(
        self,
        user_id: int,
        enabled: Optional[bool] = None,
        provider: Optional[str] = None,
        protocol: Optional[str] = None,
    ) -> List[Service]:
        """
        Listar servicios con filtros opcionales.

        Args:
            user_id: ID del usuario
            enabled: Filtrar por habilitado/deshabilitado
            provider: Filtrar por proveedor
            protocol: Filtrar por protocolo

        Returns:
            Lista de servicios
        """
        statement = select(Service).where(Service.user_id == user_id)

        if enabled is not None:
            statement = statement.where(Service.enabled == enabled)

        if provider:
            statement = statement.where(Service.provider_key == provider)

        if protocol:
            statement = statement.where(Service.protocol == protocol)

        return list(self.db.exec(statement).all())

    def list_enabled(self, user_id: int) -> List[Service]:
        """
        Listar servicios habilitados que no están corriendo.

        Args:
            user_id: ID del usuario

        Returns:
            Lista de servicios habilitados detenidos
        """
        statement = select(Service).where(
            Service.user_id == user_id, Service.enabled == True, Service.status != ServiceStatus.RUNNING.value
        )
        return list(self.db.exec(statement).all())

    def list_running(self, user_id: int) -> List[Service]:
        """
        Listar servicios actualmente corriendo.

        Args:
            user_id: ID del usuario

        Returns:
            Lista de servicios en ejecución
        """
        statement = select(Service).where(Service.user_id == user_id, Service.status == ServiceStatus.RUNNING.value)
        return list(self.db.exec(statement).all())

    def create(self, service: Service) -> Service:
        """
        Crear nuevo servicio en BD.

        Args:
            service: Instancia de Service a crear

        Returns:
            Service creado con ID asignado
        """
        self.db.add(service)
        self.db.commit()
        self.db.refresh(service)
        logger.info(f"Servicio creado en BD: {service.name} (ID: {service.id})")
        return service

    def update(self, service: Service) -> Service:
        """
        Actualizar servicio existente.

        Args:
            service: Servicio con cambios

        Returns:
            Service actualizado
        """
        service.updated_at = datetime.utcnow()
        self.db.add(service)
        self.db.commit()
        self.db.refresh(service)
        logger.info(f"Servicio actualizado en BD: {service.name} (ID: {service.id})")
        return service

    def delete(self, service: Service) -> None:
        """
        Eliminar servicio de BD.

        Args:
            service: Servicio a eliminar
        """
        service_name = service.name
        service_id = service.id
        self.db.delete(service)
        self.db.commit()
        logger.info(f"Servicio eliminado de BD: {service_name} (ID: {service_id})")

    # ========== Operaciones de Estado ==========

    def update_status(self, service: Service, status: ServiceStatus) -> Service:
        """
        Actualizar estado del servicio.

        Args:
            service: Servicio a actualizar
            status: Nuevo estado

        Returns:
            Service actualizado
        """
        old_status = service.status
        service.status = status.value
        service.updated_at = datetime.utcnow()

        if status == ServiceStatus.RUNNING:
            service.started_at = datetime.utcnow()

        self.db.add(service)
        self.db.commit()
        self.db.refresh(service)

        logger.info(f"Estado de servicio actualizado: {service.name} ({old_status} -> {status.value})")
        return service

    def mark_as_running(self, service: Service, public_url: str, process_id: str) -> Service:
        """
        Marcar servicio como corriendo con URL pública.

        Args:
            service: Servicio a actualizar
            public_url: URL pública del túnel
            process_id: ID del proceso/túnel

        Returns:
            Service actualizado
        """
        service.status = ServiceStatus.RUNNING.value
        service.public_url = public_url
        service.process_id = process_id
        service.started_at = datetime.utcnow()
        service.error_message = None
        service.updated_at = datetime.utcnow()

        self.db.add(service)
        self.db.commit()
        self.db.refresh(service)

        logger.info(f"Servicio marcado como running: {service.name} -> {public_url}")
        return service

    def mark_as_stopped(self, service: Service) -> Service:
        """
        Marcar servicio como detenido.

        Args:
            service: Servicio a actualizar

        Returns:
            Service actualizado
        """
        service.status = ServiceStatus.STOPPED.value
        service.public_url = None
        service.process_id = None
        service.updated_at = datetime.utcnow()

        self.db.add(service)
        self.db.commit()
        self.db.refresh(service)

        logger.info(f"Servicio marcado como stopped: {service.name}")
        return service

    def mark_as_error(self, service: Service, error_message: str) -> Service:
        """
        Marcar servicio con error.

        Args:
            service: Servicio a actualizar
            error_message: Mensaje de error

        Returns:
            Service actualizado
        """
        service.status = ServiceStatus.ERROR.value
        service.error_message = error_message
        service.updated_at = datetime.utcnow()

        self.db.add(service)
        self.db.commit()
        self.db.refresh(service)

        logger.error(f"Servicio marcado con error: {service.name} - {error_message}")
        return service

    def enable(self, service: Service) -> Service:
        """
        Habilitar servicio.

        Args:
            service: Servicio a habilitar

        Returns:
            Service actualizado
        """
        service.enabled = True
        service.updated_at = datetime.utcnow()

        self.db.add(service)
        self.db.commit()
        self.db.refresh(service)

        logger.info(f"Servicio habilitado: {service.name}")
        return service

    def disable(self, service: Service) -> Service:
        """
        Deshabilitar servicio.

        Args:
            service: Servicio a deshabilitar

        Returns:
            Service actualizado
        """
        service.enabled = False
        service.updated_at = datetime.utcnow()

        # Si está corriendo, cambiar a stopped
        if service.status == ServiceStatus.RUNNING.value:
            service.status = ServiceStatus.STOPPED.value
            service.public_url = None
            service.process_id = None

        self.db.add(service)
        self.db.commit()
        self.db.refresh(service)

        logger.info(f"Servicio deshabilitado: {service.name}")
        return service

    # ========== Validaciones ==========

    def validate_provider_exists(self, provider_key: str) -> Provider:
        """
        Validar que el proveedor existe y está activo.

        Args:
            provider_key: Clave del proveedor

        Returns:
            Provider encontrado

        Raises:
            HTTPException: Si el proveedor no existe o está inactivo
        """
        statement = select(Provider).where(Provider.key == provider_key, Provider.is_active == True)
        provider = self.db.exec(statement).first()

        if not provider:
            raise HTTPException(status_code=400, detail=f"Proveedor '{provider_key}' no existe o está inactivo")

        return provider

    def validate_port_available(
        self, port: int, host: str, user_id: int, exclude_service_id: Optional[int] = None
    ) -> None:
        """
        Validar que el puerto/host está disponible para el usuario.

        Args:
            port: Puerto a validar
            host: Host a validar
            user_id: ID del usuario
            exclude_service_id: ID de servicio a excluir (para updates)

        Raises:
            HTTPException: Si el puerto ya está en uso
        """
        statement = select(Service).where(Service.user_id == user_id, Service.port == port, Service.host == host)

        if exclude_service_id:
            statement = statement.where(Service.id != exclude_service_id)

        existing = self.db.exec(statement).first()

        if existing:
            raise HTTPException(status_code=400, detail=f"Ya existe un servicio en {host}:{port}")

    # ========== Queries Especializadas ==========

    def get_running_by_port(self, port: int, provider_key: str, user_id: int) -> Optional[Service]:
        """
        Buscar servicio corriendo por puerto y proveedor.

        Args:
            port: Puerto del servicio
            provider_key: Clave del proveedor
            user_id: ID del usuario

        Returns:
            Service si está corriendo, None si no
        """
        statement = select(Service).where(
            Service.user_id == user_id,
            Service.port == port,
            Service.provider_key == provider_key,
            Service.status == ServiceStatus.RUNNING.value,
        )
        return self.db.exec(statement).first()

    def count_by_status(self, user_id: int, status: ServiceStatus) -> int:
        """
        Contar servicios por estado.

        Args:
            user_id: ID del usuario
            status: Estado a contar

        Returns:
            Cantidad de servicios en ese estado
        """
        statement = select(Service).where(Service.user_id == user_id, Service.status == status.value)
        return len(list(self.db.exec(statement).all()))

    def get_statistics(self, user_id: int) -> dict:
        """
        Obtener estadísticas de servicios del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Dict con estadísticas
        """
        all_services = self.list_all(user_id)

        return {
            "total": len(all_services),
            "enabled": len([s for s in all_services if s.enabled]),
            "disabled": len([s for s in all_services if not s.enabled]),
            "running": len([s for s in all_services if s.status == ServiceStatus.RUNNING.value]),
            "stopped": len([s for s in all_services if s.status == ServiceStatus.STOPPED.value]),
            "error": len([s for s in all_services if s.status == ServiceStatus.ERROR.value]),
            "by_provider": self._count_by_provider(all_services),
            "by_protocol": self._count_by_protocol(all_services),
        }

    def _count_by_provider(self, services: List[Service]) -> dict:
        """Contar servicios por proveedor."""
        counts = {}
        for service in services:
            provider = service.provider_key
            counts[provider] = counts.get(provider, 0) + 1
        return counts

    def _count_by_protocol(self, services: List[Service]) -> dict:
        """Contar servicios por protocolo."""
        counts = {}
        for service in services:
            protocol = service.protocol
            counts[protocol] = counts.get(protocol, 0) + 1
        return counts

    def get_cloudflare_provider(self) -> Provider:
        """Obtener provider de Cloudflare desde BD"""
        statement = select(Provider).where(
            Provider.key == "cloudflare",
            Provider.is_active,
        )
        provider = self.db.exec(statement).first()

        if not provider:
            raise ValueError("Proveedor Cloudflare no configurado")

        return provider
