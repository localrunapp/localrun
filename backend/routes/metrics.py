"""
Metrics Routes - Rutas para métricas de servidores y analytics
"""

from typing import List

from fastapi import APIRouter, Depends, Query

from app.controllers.metrics import metrics_controller
from app.schemas.metrics import (
    AggregateMetrics,
    MetricsAlerts,
    ServerComparison,
    ServerMetricsDetail,
    ServerMetricsHistory,
    ServerMetricsSummary,
    ServersMetricsOverview,
    ServerTunnelAnalytics,
)
from core.auth import get_current_user

# Create router
router = APIRouter(prefix="/metrics", tags=["Metrics"])


# ========== Server Metrics Endpoints ==========


@router.get("/servers", response_model=ServersMetricsOverview)
async def get_all_servers_metrics(
    _current_user=Depends(get_current_user),
):
    """
    Obtener vista general de métricas de todos los servidores.

    Retorna un resumen de métricas de todos los servidores incluyendo:
    - Total de servidores
    - Servidores conectados
    - Conteo por estado de salud (healthy, warning, critical)
    - Métricas individuales de cada servidor
    """
    return await metrics_controller.get_all_servers_metrics()


@router.get("/servers/{server_id}", response_model=ServerMetricsDetail)
async def get_server_metrics_detail(
    server_id: str,
    _current_user=Depends(get_current_user),
):
    """
    Obtener métricas detalladas de un servidor específico.

    Retorna información completa del servidor incluyendo:
    - Métricas actuales (CPU, memoria, disco)
    - Información del sistema (OS, cores, RAM total)
    - Servicios detectados
    - Estado del agente
    - Estado de salud
    """
    return await metrics_controller.get_server_metrics_detail(server_id)


@router.get("/servers/{server_id}/summary", response_model=ServerMetricsSummary)
async def get_server_metrics_summary(
    server_id: str,
    _current_user=Depends(get_current_user),
):
    """
    Obtener resumen de métricas de un servidor.

    Retorna un resumen rápido con las últimas métricas del servidor.
    Más ligero que el endpoint de detail.
    """
    return await metrics_controller.get_server_metrics_summary(server_id)


@router.get("/servers/{server_id}/history", response_model=ServerMetricsHistory)
async def get_server_metrics_history(
    server_id: str,
    hours: float = Query(default=24, ge=0.1, le=336, description="Horas de histórico (0.1-336)"),
    _current_user=Depends(get_current_user),
):
    """
    Obtener histórico de métricas de un servidor.

    Retorna el histórico de métricas del servidor con estadísticas agregadas:
    - Lista completa de entradas (CPU, memoria, disco por timestamp)
    - Estadísticas del período (promedios, máximos)

    **Parámetros:**
    - **hours**: Horas de histórico (default: 24, máximo: 336)
    """
    return await metrics_controller.get_server_metrics_history(server_id, hours)


@router.get("/servers/{server_id}/analytics", response_model=ServerTunnelAnalytics)
async def get_server_tunnel_analytics(
    server_id: str,
    hours: float = Query(default=24, ge=0.1, le=336, description="Horas de histórico (0.1-336)"),
    _current_user=Depends(get_current_user),
):
    """
    Obtener analytics de tráfico de túneles asociados a un servidor.

    Retorna métricas de tráfico agregadas de todos los túneles del servidor:
    - Total de requests HTTP
    - Tiempo de respuesta promedio
    - Ancho de banda total (MB)
    - Top paths más accedidos
    - Distribución de status codes

    Los datos provienen de los proxies reversos instalados en cada túnel
    que envían analytics al backend.

    **Parámetros:**
    - **hours**: Horas de histórico (default: 24, máximo: 336)
    """
    return await metrics_controller.get_server_tunnel_analytics(server_id, hours)


# ========== Aggregate & System Metrics ==========


@router.get("/aggregate", response_model=AggregateMetrics)
async def get_aggregate_metrics(
    _current_user=Depends(get_current_user),
):
    """
    Obtener métricas agregadas del sistema completo.

    Retorna métricas consolidadas de todos los servidores:
    - Total de recursos (CPU cores, RAM, disco)
    - Uso promedio de recursos
    - Uso total (memoria y disco)
    - Servidores activos
    """
    return await metrics_controller.get_aggregate_metrics()


@router.get("/alerts", response_model=MetricsAlerts)
async def get_metrics_alerts(
    _current_user=Depends(get_current_user),
):
    """
    Obtener alertas de métricas.

    Retorna alertas basadas en umbrales predefinidos:
    - **CPU**: Warning ≥70%, Critical ≥90%
    - **Memory**: Warning ≥80%, Critical ≥95%
    - **Disk**: Warning ≥85%, Critical ≥95%

    Solo incluye servidores con datos recientes (últimos 5 minutos).
    """
    return await metrics_controller.get_metrics_alerts()


# ========== Comparison ==========


@router.post("/compare", response_model=ServerComparison)
async def compare_servers(
    server_ids: List[str],
    _current_user=Depends(get_current_user),
):
    """
    Comparar métricas entre múltiples servidores.

    Retorna las métricas actuales de los servidores especificados
    para facilitar comparación side-by-side.

    **Body:**
    ```json
    ["server-id-1", "server-id-2", "server-id-3"]
    ```
    """
    return await metrics_controller.compare_servers(server_ids)
