"""
Metrics Schemas - Schemas para métricas de servidores y analytics
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ========== Server Metrics Schemas ==========


class ServerMetricsSummary(BaseModel):
    """Resumen de métricas de un servidor"""
    
    server_id: str
    server_name: str
    os_type: Optional[str] = None
    agent_connected: bool
    last_update: Optional[datetime] = None
    
    # Últimas métricas
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    memory_gb: Optional[float] = None
    disk_percent: Optional[float] = None
    disk_gb: Optional[float] = None
    network_ip: Optional[str] = None
    
    # Estado de salud
    health_status: str = Field(
        default="unknown",
        description="Health status: healthy, warning, critical, unknown"
    )


class ServerMetricsDetail(ServerMetricsSummary):
    """Métricas detalladas de un servidor"""
    
    # Info adicional del servidor
    host: str
    is_local: bool
    cpu_cores: Optional[int] = None
    memory_total_gb: Optional[float] = None
    
    # Servicios detectados
    services_count: int = 0
    services: List[Dict[str, Any]] = Field(default_factory=list)


class MetricsHistoryEntry(BaseModel):
    """Entrada de histórico de métricas"""
    
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_gb: float
    disk_percent: float
    disk_gb: float
    disk_read_ops: float = 0.0
    disk_write_ops: float = 0.0
    network_ip: Optional[str] = None


class ServerMetricsHistory(BaseModel):
    """Histórico de métricas de un servidor"""
    
    server_id: str
    server_name: str
    period_hours: float
    total_entries: int
    entries: List[MetricsHistoryEntry]
    
    # Estadísticas del período
    avg_cpu: Optional[float] = None
    max_cpu: Optional[float] = None
    avg_memory: Optional[float] = None
    max_memory: Optional[float] = None
    avg_disk: Optional[float] = None


class ServersMetricsOverview(BaseModel):
    """Vista general de métricas de todos los servidores"""
    
    total_servers: int
    connected_servers: int
    healthy_servers: int
    warning_servers: int
    critical_servers: int
    
    servers: List[ServerMetricsSummary]


# ========== Aggregate Metrics Schemas ==========


class AggregateMetrics(BaseModel):
    """Métricas agregadas del sistema completo"""
    
    timestamp: datetime
    total_servers: int
    active_servers: int
    
    # Recursos totales
    total_cpu_cores: int = 0
    total_memory_gb: float = 0.0
    total_disk_gb: float = 0.0
    
    # Uso agregado
    avg_cpu_percent: float = 0.0
    avg_memory_percent: float = 0.0
    avg_disk_percent: float = 0.0
    
    # Uso total
    used_memory_gb: float = 0.0
    used_disk_gb: float = 0.0


# ========== Alerts Schemas ==========


class MetricAlert(BaseModel):
    """Alerta de métrica"""
    
    server_id: str
    server_name: str
    metric: str = Field(description="cpu, memory, disk")
    value: float
    threshold: float
    severity: str = Field(description="warning, critical")
    timestamp: datetime
    message: str


class MetricsAlerts(BaseModel):
    """Lista de alertas de métricas"""
    
    total_alerts: int
    critical_count: int
    warning_count: int
    alerts: List[MetricAlert]


# ========== Comparison Schemas ==========


class ServerComparison(BaseModel):
    """Comparación de métricas entre servidores"""
    
    servers: List[ServerMetricsSummary]
    comparison_time: datetime


# ========== Analytics Integration Schemas ==========


class ServerTunnelAnalytics(BaseModel):
    """Analytics de túneles asociados a un servidor"""
    
    server_id: str
    server_name: str
    period_hours: float
    
    # Métricas de tráfico
    total_requests: int = 0
    total_bandwidth_mb: float = 0.0
    avg_response_time_ms: float = 0.0
    
    # Top paths
    top_paths: Dict[str, int] = Field(default_factory=dict)
    
    # Detailed stats
    devices: Dict[str, int] = Field(default_factory=dict)
    browsers: Dict[str, int] = Field(default_factory=dict)
    countries: Dict[str, int] = Field(default_factory=dict)
    country_codes: Dict[str, int] = Field(default_factory=dict)
    
    # Status codes
    status_codes: Dict[str, int] = Field(default_factory=dict)
