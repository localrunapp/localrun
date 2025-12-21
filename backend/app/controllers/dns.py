"""
DNS management controller - Orquesta operaciones DNS

Responsabilidades:
- Validar requests HTTP
- Coordinar repository
- Manejar errores HTTP
"""

from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.repositories.dns_repository import DNSRepository
from core.database import get_db
from core.logger import setup_logger

logger = setup_logger(__name__)


# === DTOs ===


class CreateDNSRecordRequest(BaseModel):
    """Solicitud para crear registro DNS"""

    record_type: str = Field("CNAME", description="Tipo de registro DNS")
    name: str = Field(..., description="Nombre del registro")
    content: str = Field(..., description="Contenido del registro")
    ttl: int = Field(3600, ge=1, le=86400, description="TTL en segundos")
    proxied: bool = Field(False, description="Habilitar proxy (solo Cloudflare)")


class DNSRecordResponse(BaseModel):
    """Respuesta de registro DNS"""

    id: str
    zone_id: str
    zone_name: Optional[str]
    name: str
    type: str
    content: str
    ttl: int
    proxied: bool
    created_on: Optional[str]
    modified_on: Optional[str]


class DNSZoneResponse(BaseModel):
    """Respuesta de zona DNS"""

    id: str
    name: str
    status: str
    name_servers: List[str]


class DNSController:
    """Controller para operaciones DNS - Orquesta DNSRepository"""

    async def test_dns_provider(self, provider_key: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
        """Probar conexión con proveedor DNS configurado"""
        logger.info(f"Probando conexión DNS con {provider_key}")

        try:
            repo = DNSRepository(db)

            # Validar conexión
            is_valid = await repo.validate_provider_connection(provider_key)

            if not is_valid:
                return {"status": "error", "message": "Credenciales inválidas"}

            # Listar zonas para verificar acceso
            zones = await repo.list_zones(provider_key)

            return {
                "status": "success",
                "provider": provider_key,
                "zones_found": len(zones),
                "message": f"Conexión exitosa - {len(zones)} zonas disponibles",
            }

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error probando proveedor DNS {provider_key}: {e}")
            return {"status": "error", "message": f"Error de conexión: {str(e)}"}

    async def list_dns_zones(self, provider_key: str, db: Session = Depends(get_db)) -> List[DNSZoneResponse]:
        """Listar zonas DNS disponibles"""
        logger.info(f"Listando zonas DNS para {provider_key}")

        try:
            repo = DNSRepository(db)
            zones_data = await repo.list_zones(provider_key)

            zones = [
                DNSZoneResponse(
                    id=zone["id"],
                    name=zone["name"],
                    status=zone.get("status", "active"),
                    name_servers=zone.get("name_servers", []),
                )
                for zone in zones_data
            ]

            logger.info(f"Obtenidas {len(zones)} zonas DNS")
            return zones

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error listando zonas DNS: {e}")
            raise HTTPException(status_code=500, detail=f"Error obteniendo zonas: {str(e)}")

    async def list_dns_records(
        self, provider_key: str, zone_id: str, db: Session = Depends(get_db)
    ) -> List[DNSRecordResponse]:
        """Listar registros DNS de una zona específica"""
        logger.info(f"Listando registros DNS para zona {zone_id}")

        try:
            repo = DNSRepository(db)
            records_data = await repo.list_records(provider_key, zone_id)

            records = [
                DNSRecordResponse(
                    id=record["id"],
                    zone_id=record.get("zone_id", zone_id),
                    zone_name=record.get("zone_name"),
                    name=record["name"],
                    type=record["type"],
                    content=record["content"],
                    ttl=record.get("ttl", 3600),
                    proxied=record.get("proxied", False),
                    created_on=record.get("created_on"),
                    modified_on=record.get("modified_on"),
                )
                for record in records_data
            ]

            logger.info(f"Obtenidos {len(records)} registros DNS")
            return records

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error listando registros DNS: {e}")
            raise HTTPException(status_code=500, detail=f"Error obteniendo registros: {str(e)}")

    async def get_dns_record(
        self, provider_key: str, zone_id: str, record_id: str, db: Session = Depends(get_db)
    ) -> DNSRecordResponse:
        """Obtener un registro DNS específico"""
        logger.info(f"Obteniendo registro DNS {record_id} de zona {zone_id}")

        try:
            repo = DNSRepository(db)
            record_data = await repo.get_record(provider_key, zone_id, record_id)

            if not record_data:
                raise HTTPException(status_code=404, detail=f"Registro DNS {record_id} no encontrado")

            record = DNSRecordResponse(
                id=record_data["id"],
                zone_id=record_data.get("zone_id", zone_id),
                zone_name=record_data.get("zone_name"),
                name=record_data["name"],
                type=record_data["type"],
                content=record_data["content"],
                ttl=record_data.get("ttl", 3600),
                proxied=record_data.get("proxied", False),
                created_on=record_data.get("created_on"),
                modified_on=record_data.get("modified_on"),
            )

            logger.info(f"Registro DNS obtenido: {record_id}")
            return record

        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error obteniendo registro DNS: {e}")
            raise HTTPException(status_code=500, detail=f"Error obteniendo registro: {str(e)}")

    async def create_dns_record(
        self, provider_key: str, zone_id: str, record_data: CreateDNSRecordRequest, db: Session = Depends(get_db)
    ) -> DNSRecordResponse:
        """Crear registro DNS usando driver y proveedor configurado"""
        logger.info(f"Creando registro DNS: {record_data.name} -> {record_data.content}")

        try:
            repo = DNSRepository(db)
            result = await repo.create_record(
                provider_key=provider_key,
                zone_id=zone_id,
                record_type=record_data.record_type,
                name=record_data.name,
                content=record_data.content,
                ttl=record_data.ttl,
                proxied=record_data.proxied,
            )

            dns_record = DNSRecordResponse(
                id=result["id"],
                zone_id=result.get("zone_id", zone_id),
                zone_name=result.get("zone_name"),
                name=result["name"],
                type=result["type"],
                content=result["content"],
                ttl=result.get("ttl", record_data.ttl),
                proxied=result.get("proxied", record_data.proxied),
                created_on=result.get("created_on"),
                modified_on=result.get("modified_on"),
            )

            logger.info(f"Registro DNS creado exitosamente: {result['id']}")
            return dns_record

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error creando registro DNS: {e}")
            raise HTTPException(status_code=500, detail=f"Error creando registro: {str(e)}")

    async def delete_dns_record(
        self, provider_key: str, zone_id: str, record_id: str, db: Session = Depends(get_db)
    ) -> Dict[str, str]:
        """Eliminar registro DNS usando driver y proveedor configurado"""
        logger.info(f"Eliminando registro DNS {record_id} de zona {zone_id}")

        try:
            repo = DNSRepository(db)
            await repo.delete_record(provider_key, zone_id, record_id)

            logger.info(f"Registro DNS eliminado exitosamente: {record_id}")
            return {"message": "Registro DNS eliminado exitosamente", "record_id": record_id, "zone_id": zone_id}

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error eliminando registro DNS: {e}")
            raise HTTPException(status_code=500, detail=f"Error eliminando registro: {str(e)}")

    async def create_dns_for_service(
        self, provider_key: str, zone_id: str, service_id: int, db: Session = Depends(get_db)
    ) -> DNSRecordResponse:
        """Crear registro DNS automáticamente para un servicio"""
        logger.info(f"Creando DNS para servicio {service_id} en zona {zone_id}")

        try:
            from app.models.service import Service
            from sqlmodel import select

            # Obtener el servicio
            statement = select(Service).where(Service.id == service_id)
            service = db.exec(statement).first()

            if not service:
                raise HTTPException(status_code=404, detail="Servicio no encontrado")

            # Validar que el servicio tiene dominio y subdominio
            if not service.domain or not service.subdomain:
                raise HTTPException(
                    status_code=400,
                    detail="El servicio debe tener dominio y subdominio configurados",
                )

            # Crear repository
            repo = DNSRepository(db)

            # Obtener información de la zona para validar el dominio
            zones = await repo.list_zones(provider_key)
            zone = next((z for z in zones if z["id"] == zone_id), None)

            if not zone:
                raise HTTPException(status_code=404, detail=f"Zona {zone_id} no encontrada")

            # Validar que el dominio del servicio coincide con la zona
            if service.domain != zone["name"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"El dominio del servicio ({service.domain}) no coincide con la zona ({zone['name']})",
                )

            # Obtener provider del servicio
            provider = repo.get_provider(service.provider_key)

            if not provider.tunnel_name:
                raise HTTPException(
                    status_code=400,
                    detail=f"Proveedor {service.provider_key} no tiene tunnel configurado",
                )

            # Obtener hostname del tunnel desde repository
            tunnel_hostname = await repo.get_tunnel_hostname(provider_key, provider.tunnel_name)

            if not tunnel_hostname:
                raise HTTPException(
                    status_code=404,
                    detail=f"No se encontró tunnel con nombre '{provider.tunnel_name}'",
                )

            # Crear el registro CNAME apuntando al tunnel
            full_hostname = f"{service.subdomain}.{service.domain}"

            logger.info(f"Creando DNS: {full_hostname} -> {tunnel_hostname}")

            result = await repo.create_record(
                provider_key=provider_key,
                zone_id=zone_id,
                record_type="CNAME",
                name=service.subdomain,
                content=tunnel_hostname,
                ttl=1,  # Auto
                proxied=True,
            )

            # Guardar el DNS record ID en el servicio
            service.dns_record_id = result["id"]
            service.dns_provider_key = provider_key
            db.add(service)
            db.commit()

            logger.info(f"DNS creado para servicio {service.name}: {full_hostname} -> {tunnel_hostname}")

            return DNSRecordResponse(
                id=result["id"],
                zone_id=zone_id,
                zone_name=zone["name"],
                name=result["name"],
                type=result["type"],
                content=result["content"],
                ttl=result.get("ttl", 1),
                proxied=result.get("proxied", True),
                created_on=result.get("created_on"),
                modified_on=result.get("modified_on"),
            )

        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error creando DNS para servicio: {e}")
            raise HTTPException(status_code=500, detail=f"Error creando DNS: {str(e)}")

    async def create_cname_for_tunnel(
        self, provider_key: str, zone_name: str, subdomain: str, tunnel_url: str, db: Session = Depends(get_db)
    ) -> DNSRecordResponse:
        """Crear registro CNAME para túnel automáticamente"""
        logger.info(f"Creando CNAME para túnel: {subdomain}.{zone_name} -> {tunnel_url}")

        try:
            repo = DNSRepository(db)

            # Primero encontrar la zona por nombre
            zones = await repo.list_zones(provider_key)
            target_zone = next((z for z in zones if z["name"] == zone_name), None)

            if not target_zone:
                raise HTTPException(status_code=404, detail=f"Zona DNS '{zone_name}' no encontrada")

            # Crear el registro CNAME
            result = await repo.create_record(
                provider_key=provider_key,
                zone_id=target_zone["id"],
                record_type="CNAME",
                name=subdomain,
                content=tunnel_url,
                ttl=1,  # Automático
                proxied=True,  # Habilitar proxy para túneles
            )

            record = DNSRecordResponse(
                id=result["id"],
                zone_id=target_zone["id"],
                zone_name=target_zone["name"],
                name=result["name"],
                type=result["type"],
                content=result["content"],
                ttl=result.get("ttl", 1),
                proxied=result.get("proxied", True),
                created_on=result.get("created_on"),
                modified_on=result.get("modified_on"),
            )

            logger.info(f"CNAME creado para túnel: {subdomain}.{zone_name} -> {tunnel_url}")
            return record

        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error creando CNAME para túnel: {e}")
            raise HTTPException(status_code=500, detail=f"Error creando CNAME: {str(e)}")

    def get_supported_providers(self) -> List[str]:
        """Listar proveedores DNS soportados"""
        from core.dns_driver import DNSDriverFactory

        return DNSDriverFactory.list_providers()
