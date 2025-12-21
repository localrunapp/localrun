"""
Analytics Controller - Endpoints para analytics y métricas
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.services.analytics_service import AnalyticsService


router = APIRouter(prefix="/analytics", tags=["Analytics"])

# Singleton del servicio
analytics_service = AnalyticsService()


class RequestLog(BaseModel):
    """Schema para log de request"""

    tunnel_id: str
    ip: str
    user_agent: str
    method: str
    path: str
    status_code: int
    response_time_ms: float
    request_size_bytes: Optional[int] = 0
    response_size_bytes: Optional[int] = 0
    referer: Optional[str] = None
    accept_language: Optional[str] = None


class AnalyticsResponse(BaseModel):
    """Schema para respuesta de analytics"""

    tunnel_id: str
    period_hours: int
    total_requests: int
    avg_response_time_ms: float
    countries: dict
    browsers: dict
    devices: dict
    status_codes: dict
    top_paths: dict


@router.post("/log")
async def log_request(log: RequestLog):
    """
    Registrar un request HTTP para analytics

    Este endpoint es llamado por el proxy/túnel cada vez que
    pasa un request HTTP.
    """
    try:
        record = analytics_service.log_request(
            tunnel_id=log.tunnel_id,
            ip=log.ip,
            user_agent=log.user_agent,
            method=log.method,
            path=log.path,
            status_code=log.status_code,
            response_time_ms=log.response_time_ms,
            referer=log.referer,
            accept_language=log.accept_language,
            request_size_bytes=log.request_size_bytes,
            response_size_bytes=log.response_size_bytes,
        )

        return {"status": "ok", "message": "Request logged", "timestamp": record["timestamp"]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def log_batch(batch: dict):
    """
    Registrar múltiples eventos de analytics en batch

    Mucho más eficiente que requests individuales.
    Usado por el analytics proxy.
    """
    try:
        events = batch.get("events", [])

        if not events:
            return {"status": "ok", "message": "No events to log"}

        # Log each event
        for event in events:
            analytics_service.log_request(
                tunnel_id=event.get("tunnel_id"),
                ip=event.get("ip"),
                user_agent=event.get("user_agent"),
                method=event.get("method"),
                path=event.get("path"),
                status_code=event.get("status_code"),
                response_time_ms=event.get("response_time_ms"),
                referer=event.get("referer"),
                accept_language=event.get("accept_language"),
                request_size_bytes=event.get("request_size_bytes", 0),
                response_size_bytes=event.get("response_size_bytes", 0),
            )

        return {"status": "ok", "message": f"Logged {len(events)} events"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tunnel/{tunnel_id}")
async def get_tunnel_analytics(tunnel_id: str, hours: int = 24) -> AnalyticsResponse:
    """
    Obtener analytics de un túnel

    Args:
        tunnel_id: ID del túnel
        hours: Horas hacia atrás (default: 24)

    Returns:
        Estadísticas detalladas del túnel
    """
    try:
        stats = analytics_service.get_tunnel_stats(tunnel_id, hours)
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tunnel/{tunnel_id}/realtime")
async def get_realtime_analytics(tunnel_id: str, minutes: int = 5):
    """
    Obtener analytics en tiempo real

    Args:
        tunnel_id: ID del túnel
        minutes: Minutos hacia atrás (default: 5)

    Returns:
        Estadísticas en tiempo real
    """
    try:
        stats = analytics_service.get_realtime_stats(tunnel_id, minutes)
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cleanup")
async def cleanup_old_analytics(days: int = 30):
    """
    Limpiar datos antiguos de analytics

    Args:
        days: Días de retención (default: 30)

    Returns:
        Número de registros eliminados
    """
    try:
        result = analytics_service.cleanup_old_data(days)
        return {"status": "ok", "message": f"Cleaned up analytics older than {days} days", **result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
