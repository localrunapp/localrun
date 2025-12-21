"""
Services Controller - HTTP Layer for Service Management

Responsibilities:
- Handle HTTP requests/responses
- Transform DTOs to/from domain models
- Delegate business logic to use cases
- Return appropriate HTTP status codes

Does NOT contain business logic - all logic is in use cases.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, Query
from sqlmodel import Session

from app.services.dns_service import dns_service
from app.services.tunnel_service import tunnel_service
from app.models.service import Service
from app.enums.service import ServiceStatus
from app.models.user import User
from app.repositories.service_repository import ServiceRepository
from app.schemas.service import (
    ServiceCreateRequest,
    ServiceResponse,
    ServiceUpdateRequest,
)
from core.auth import get_current_user
from core.database import get_db

# Import use cases
from app.use_cases.services import (
    CreateServiceUseCase,
    UpdateServiceUseCase,
    DeleteServiceUseCase,
    EnableServiceUseCase,
    DisableServiceUseCase,
    StartServiceUseCase,
    StopServiceUseCase,
    RestartServiceUseCase,
    ListServicesUseCase,
    GetServiceUseCase,
    StartAllServicesUseCase,
    StopAllServicesUseCase,
    SyncServiceStatesUseCase,
)
from app.use_cases.services.reconcile_services import ReconcileServicesUseCase


logger = logging.getLogger(__name__)


class ServicesController:
    """Controller para gestión de servicios (HTTP layer)"""

    def __init__(self):
        self.tunnel_service = tunnel_service

    def _enrich_service_response(self, service: Service) -> ServiceResponse:
        """Enriquecer respuesta con campos computados"""
        response = ServiceResponse.model_validate(service)
        response.full_domain = service.full_domain
        response.local_endpoint = service.local_endpoint
        response.is_named_service = service.is_named_service
        response.is_quick_service = service.is_quick_service
        response.expected_container_name = service.get_expected_container_name()
        return response

    # ========== CRUD Operations ==========

    async def list_services(
        self,
        enabled: Optional[bool] = Query(default=None),
        provider: Optional[str] = Query(default=None),
        protocol: Optional[str] = Query(default=None),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> List[ServiceResponse]:
        """Listar servicios con filtros opcionales"""
        try:
            # Delegate to use case (no repository needed)
            use_case = ListServicesUseCase()
            services = await use_case.execute(
                user_id=current_user.id,
                enabled=enabled,
                provider=provider,
                protocol=protocol,
            )

            return [self._enrich_service_response(s) for s in services]

        except Exception as e:
            logger.error(f"Error listando servicios: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def create_service(
        self,
        service_data: ServiceCreateRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> ServiceResponse:
        """Crear nuevo servicio"""
        try:
            # Delegate to use case (no repository needed)
            use_case = CreateServiceUseCase()
            service = await use_case.execute(service_data, current_user.id)

            return self._enrich_service_response(service)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creando servicio: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_service(
        self,
        service_id: uuid.UUID,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> ServiceResponse:
        """Obtener servicio por ID"""
        try:
            # Delegate to use case (no repository needed)
            use_case = GetServiceUseCase()
            service = await use_case.execute(service_id, current_user.id)

            return self._enrich_service_response(service)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo servicio {service_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def update_service(
        self,
        service_id: uuid.UUID,
        service_data: ServiceUpdateRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> ServiceResponse:
        """Actualizar servicio existente"""
        try:
            # Delegate to use case (no repository needed)
            use_case = UpdateServiceUseCase()
            service = await use_case.execute(service_id, service_data, current_user.id)

            return self._enrich_service_response(service)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error actualizando servicio {service_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_service(
        self,
        service_id: uuid.UUID,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Dict[str, Any]:
        """Eliminar servicio (detiene túnel primero si está corriendo)"""
        try:
            # Delegate to use case
            use_case = DeleteServiceUseCase(
                ServiceRepository(db),
                self.tunnel_service,
            )
            return await use_case.execute(service_id, current_user.id, db)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error eliminando servicio {service_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def enable_service(
        self,
        service_id: uuid.UUID,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Dict[str, Any]:
        """Habilitar servicio"""
        try:
            # Delegate to use case (no repository needed)
            use_case = EnableServiceUseCase()
            return await use_case.execute(service_id, current_user.id)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error habilitando servicio {service_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def disable_service(
        self,
        service_id: uuid.UUID,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Dict[str, Any]:
        """Deshabilitar servicio"""
        try:
            # Delegate to use case (no repository needed)
            use_case = DisableServiceUseCase()
            return await use_case.execute(service_id, current_user.id)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deshabilitando servicio {service_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ========== Runtime Operations ==========

    async def start_service(
        self,
        service_id: uuid.UUID,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> ServiceResponse:
        """Iniciar túnel para un servicio"""
        try:
            # Delegate to use case
            use_case = StartServiceUseCase(
                ServiceRepository(db),
                self.tunnel_service,
            )
            service = await use_case.execute(service_id, current_user.id, db)

            return self._enrich_service_response(service)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error iniciando servicio {service_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def stop_service(
        self,
        service_id: uuid.UUID,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Dict[str, Any]:
        """Detener túnel de un servicio"""
        try:
            # Delegate to use case
            use_case = StopServiceUseCase(
                ServiceRepository(db),
                self.tunnel_service,
            )
            return await use_case.execute(service_id, current_user.id, db)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deteniendo servicio {service_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def restart_service(
        self,
        service_id: uuid.UUID,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> ServiceResponse:
        """Reiniciar servicio (stop + start)"""
        try:
            # Delegate to use case
            stop_use_case = StopServiceUseCase(
                ServiceRepository(db),
                self.tunnel_service,
            )
            start_use_case = StartServiceUseCase(
                ServiceRepository(db),
                self.tunnel_service,
            )
            restart_use_case = RestartServiceUseCase(stop_use_case, start_use_case)
            service = await restart_use_case.execute(service_id, current_user.id, db)

            return self._enrich_service_response(service)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error reiniciando servicio {service_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ========== Bulk Operations ==========

    async def list_active_services(
        self,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> List[ServiceResponse]:
        """Listar todos los servicios actualmente corriendo"""
        try:
            repo = ServiceRepository(db)
            services = repo.list_running(current_user.id)

            return [self._enrich_service_response(s) for s in services]

        except Exception as e:
            logger.error(f"Error listando servicios activos: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def start_enabled_services(
        self,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Dict[str, Any]:
        """Iniciar todos los servicios habilitados (alias de start_all_services)"""
        return await self.start_all_services(current_user, db)

    async def start_all_services(
        self,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Dict[str, Any]:
        """Iniciar todos los servicios habilitados"""
        try:
            # Delegate to use case
            start_use_case = StartServiceUseCase(
                ServiceRepository(db),
                self.tunnel_service,
            )
            use_case = StartAllServicesUseCase(start_use_case)
            return await use_case.execute(current_user.id, db)

        except Exception as e:
            logger.error(f"Error iniciando servicios: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def stop_all_services(
        self,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Dict[str, Any]:
        """Detener todos los servicios en ejecución"""
        try:
            # Delegate to use case
            stop_use_case = StopServiceUseCase(
                ServiceRepository(db),
                self.tunnel_service,
            )
            use_case = StopAllServicesUseCase(stop_use_case)
            return await use_case.execute(current_user.id, db)

        except Exception as e:
            logger.error(f"Error deteniendo servicios: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ========== Sync & Diagnostics ==========

    async def sync_service_states(
        self,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Dict[str, Any]:
        """Sincronizar estado de servicios entre BD y túneles reales"""
        try:
            # Delegate to use case
            use_case = SyncServiceStatesUseCase(self.tunnel_service)
            return await use_case.execute(current_user.id, db)

        except Exception as e:
            logger.error(f"Error en sincronización: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_diagnostics(
        self,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Dict[str, Any]:
        """Obtener diagnósticos del sistema de servicios"""
        try:
            repo = ServiceRepository(db)
            services = repo.list_all(current_user.id)

            # Delegar a tunnel_service
            return await self.tunnel_service.get_diagnostics(services, repo)

        except Exception as e:
            logger.error(f"Error obteniendo diagnósticos: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def reconcile_services(
        self,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Dict[str, Any]:
        """
        Reconcile service states with running Docker containers.
        Updates services that have running containers but show error/stopped status.
        """
        try:
            use_case = ReconcileServicesUseCase(db)
            result = await use_case.execute(current_user.id)
            
            logger.info(
                f"Reconciliation completed for user {current_user.id}: "
                f"{result['reconciled']} services updated"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error during service reconciliation: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to reconcile services: {str(e)}"
            )

    # ========== Provider Information ==========

    async def get_supported_providers(
        self,
        current_user: User = Depends(get_current_user),
    ) -> Dict[str, Any]:
        """Listar proveedores de túneles disponibles"""
        return {
            "providers": [
                {
                    "name": "Cloudflare Tunnels",
                    "key": "cloudflare",
                    "supports_quick": True,
                    "supports_named": True,
                    "supports_dns": True,
                },
                {
                    "name": "Pinggy",
                    "key": "pinggy",
                    "supports_quick": True,
                    "supports_named": True,
                    "supports_dns": True,
                }
            ]
        }

    async def get_provider_status(
        self,
        provider: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Dict[str, Any]:
        """Estado detallado de un proveedor específico"""
        try:
            if provider != "cloudflare":
                raise HTTPException(status_code=404, detail=f"Proveedor '{provider}' no soportado")

            repo = ServiceRepository(db)

            # Obtener provider de BD
            try:
                cf_provider = repo.get_cloudflare_provider()
                configured = True
                tunnel_name = cf_provider.tunnel_name
            except ValueError:
                configured = False
                tunnel_name = None

            # Información de infraestructura
            quick_tunnels = self.tunnel_service.list_quick_tunnels()
            named_routes = self.tunnel_service.list_named_tunnel_routes()
            container_status = self.tunnel_service.get_named_tunnel_container_status()

            return {
                "provider": "cloudflare",
                "configured": configured,
                "tunnel_name": tunnel_name,
                "infrastructure": {
                    "quick_tunnels_count": len(quick_tunnels),
                    "named_routes_count": len(named_routes),
                    "container_status": container_status,
                },
                "quick_tunnels": quick_tunnels,
                "named_routes": named_routes,
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo estado del proveedor: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def cleanup_provider(
        self,
        provider: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Dict[str, Any]:
        """Limpiar todos los túneles de un proveedor"""
        try:
            if provider != "cloudflare":
                raise HTTPException(status_code=404, detail=f"Proveedor '{provider}' no soportado")

            # Detener todos los servicios primero
            stop_result = await self.stop_all_services(current_user, db)

            return {
                "success": True,
                "message": f"Proveedor '{provider}' limpiado",
                "services_stopped": stop_result,
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error limpiando proveedor: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ========== DNS Operations ==========

    async def create_dns_record(
        self,
        service_id: uuid.UUID,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Dict[str, Any]:
        """
        Crear registro DNS para un servicio (Named Service).

        Esta es una operación EXPLÍCITA que el usuario debe ejecutar.
        NO se crea automáticamente al iniciar el servicio.
        """
        try:
            repo = ServiceRepository(db)
            service = repo.get_by_id(service_id, current_user.id)

            if not service:
                raise HTTPException(status_code=404, detail="Servicio no encontrado")

            if not service.is_named_service:
                raise HTTPException(
                    status_code=400,
                    detail="Solo Named Services requieren DNS (domain + subdomain)",
                )

            # Obtener tunnel_id (necesario para el CNAME target)
            tunnel_id = "localrun-tunnel"  # TODO: obtener desde provider config

            success = await dns_service.create_dns_record(service, tunnel_id, db)

            if success:
                return {
                    "success": True,
                    "message": f"DNS record creado: {service.full_domain}",
                    "hostname": service.full_domain,
                }

            raise HTTPException(status_code=500, detail="Error creando DNS record")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creando DNS para servicio {service_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_dns_record(
        self,
        service_id: uuid.UUID,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Dict[str, Any]:
        """
        Eliminar registro DNS de un servicio.

        Esta es una operación EXPLÍCITA que el usuario debe ejecutar.
        NO se elimina automáticamente al detener/eliminar el servicio.
        """
        try:
            repo = ServiceRepository(db)
            service = repo.get_by_id(service_id, current_user.id)

            if not service:
                raise HTTPException(status_code=404, detail="Servicio no encontrado")

            if not service.is_named_service:
                raise HTTPException(
                    status_code=400,
                    detail="Solo Named Services tienen DNS",
                )

            success = await dns_service.delete_dns_record(service, db)

            if success:
                return {
                    "success": True,
                    "message": f"DNS record eliminado: {service.full_domain}",
                }

            raise HTTPException(status_code=500, detail="Error eliminando DNS record")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error eliminando DNS para servicio {service_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def verify_dns_record(
        self,
        service_id: uuid.UUID,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Dict[str, Any]:
        """Verificar si existe registro DNS para un servicio"""
        try:
            repo = ServiceRepository(db)
            service = repo.get_by_id(service_id, current_user.id)

            if not service:
                raise HTTPException(status_code=404, detail="Servicio no encontrado")

            if not service.is_named_service:
                return {
                    "exists": False,
                    "message": "Este servicio no requiere DNS",
                }

            result = await dns_service.verify_dns_record(service, db)

            return result or {"exists": False}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error verificando DNS para servicio {service_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ========== Helper Methods ==========

    async def _stop_service_tunnel(self, service: Service, db: Session):
        """Detener túnel de un servicio (Quick o Named)"""
        if service.is_quick_service:
            await self.tunnel_service.stop_quick_tunnel(service)
        else:
            # Named Tunnel: eliminar ruta
            await self.tunnel_service.stop_named_tunnel(service, db)


# Instancia del controller
services_controller = ServicesController()
