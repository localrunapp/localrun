"""
Metrics Controller - Gestión centralizada de métricas de servidores y analytics
"""

import json
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException

from app.models.server import Server
from app.repositories.server_stats_repository import server_stats_repository
from app.services.analytics_service import AnalyticsService
from app.schemas.metrics import (
    AggregateMetrics,
    MetricAlert,
    MetricsAlerts,
    MetricsHistoryEntry,
    ServerComparison,
    ServerMetricsDetail,
    ServerMetricsHistory,
    ServerMetricsSummary,
    ServersMetricsOverview,
    ServerTunnelAnalytics,
)

logger = logging.getLogger(__name__)


class MetricsController:
    """
    Controller para métricas de servidores.
    Centraliza acceso a stats de TinyDB y proporciona vistas agregadas.
    Integra analytics de tráfico de túneles/proxies.
    """

    def __init__(self):
        self.stats_repo = server_stats_repository
        self.analytics_service = AnalyticsService()
        # Umbrales para alertas
        self.thresholds = {
            "cpu": {"warning": 70.0, "critical": 90.0},
            "memory": {"warning": 80.0, "critical": 95.0},
            "disk": {"warning": 85.0, "critical": 95.0},
        }

    def _calculate_health_status(
        self, cpu: Optional[float], memory: Optional[float], disk: Optional[float]
    ) -> str:
        """
        Calcular estado de salud basado en métricas.

        Returns:
            str: "healthy", "warning", "critical", "unknown"
        """
        if cpu is None and memory is None and disk is None:
            return "unknown"

        # Critical si alguna métrica está en nivel crítico
        if (
            (cpu and cpu >= self.thresholds["cpu"]["critical"])
            or (memory and memory >= self.thresholds["memory"]["critical"])
            or (disk and disk >= self.thresholds["disk"]["critical"])
        ):
            return "critical"

        # Warning si alguna métrica está en nivel warning
        if (
            (cpu and cpu >= self.thresholds["cpu"]["warning"])
            or (memory and memory >= self.thresholds["memory"]["warning"])
            or (disk and disk >= self.thresholds["disk"]["warning"])
        ):
            return "warning"

        return "healthy"

    async def get_server_metrics_summary(self, server_id: str) -> ServerMetricsSummary:
        """
        Obtener resumen de métricas de un servidor.

        Args:
            server_id: ID del servidor

        Returns:
            ServerMetricsSummary con las últimas métricas
        """
        # Obtener servidor
        server = Server.find(server_id)
        if not server:
            raise HTTPException(status_code=404, detail="Server not found")

        # Obtener última métrica de TinyDB
        latest_stats = self.stats_repo.get_latest(server_id)

        # Verificar si el agente está conectado (últimos 30 segundos)
        agent_connected = False
        last_update = None

        if latest_stats and "timestamp" in latest_stats:
            try:
                last_update = datetime.fromisoformat(latest_stats["timestamp"])
                time_diff = datetime.utcnow() - last_update
                agent_connected = time_diff.total_seconds() < 30
            except (ValueError, KeyError, TypeError):
                pass

        # Extraer métricas
        cpu_percent = latest_stats.get("cpu_percent") if latest_stats else None
        memory_percent = latest_stats.get("memory_percent") if latest_stats else None
        disk_percent = latest_stats.get("disk_percent") if latest_stats else None

        # Calcular estado de salud
        health_status = self._calculate_health_status(
            cpu_percent, memory_percent, disk_percent
        )

        return ServerMetricsSummary(
            server_id=server_id,
            server_name=server.name,
            os_type=server.os_type,
            agent_connected=agent_connected,
            last_update=last_update,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_gb=latest_stats.get("memory_gb") if latest_stats else None,
            disk_percent=disk_percent,
            disk_gb=latest_stats.get("disk_gb") if latest_stats else None,
            network_ip=latest_stats.get("network_ip") if latest_stats else None,
            health_status=health_status,
        )

    async def get_server_metrics_detail(self, server_id: str) -> ServerMetricsDetail:
        """
        Obtener métricas detalladas de un servidor.

        Args:
            server_id: ID del servidor

        Returns:
            ServerMetricsDetail con información completa
        """
        # Obtener resumen base
        summary = await self.get_server_metrics_summary(server_id)

        # Obtener servidor para info adicional
        server = Server.find(server_id)
        if not server:
            raise HTTPException(status_code=404, detail="Server not found")

        # Parsear servicios detectados
        services = []
        services_count = 0
        if server.detected_services:
            try:
                services = json.loads(server.detected_services)
                services_count = len(services)
            except (json.JSONDecodeError, TypeError):
                pass

        # Crear respuesta detallada
        return ServerMetricsDetail(
            **summary.model_dump(),
            host=server.host,
            is_local=server.is_local,
            cpu_cores=server.cpu_cores,
            memory_total_gb=server.memory_gb,
            services_count=services_count,
            services=services,
        )

    async def get_server_metrics_history(
        self, server_id: str, hours: float = 24
    ) -> ServerMetricsHistory:
        """
        Obtener histórico de métricas de un servidor.

        Args:
            server_id: ID del servidor
            hours: Horas de histórico (default: 24)

        Returns:
            ServerMetricsHistory con histórico y estadísticas
        """
        # Verificar que el servidor existe
        server = Server.find(server_id)
        if not server:
            raise HTTPException(status_code=404, detail="Server not found")

        # Obtener stats de TinyDB
        stats = self.stats_repo.get_stats(server_id, hours)
        
        # Ordenar por timestamp ascendente (antiguo -> nuevo) para gráficos
        stats.sort(key=lambda x: x.get("timestamp", ""))

        # Convertir a entries
        entries = []
        cpu_values = []
        memory_values = []
        disk_values = []

        for stat in stats:
            try:
                entry = MetricsHistoryEntry(
                    timestamp=stat.get("timestamp", ""),
                    cpu_percent=stat.get("cpu_percent", 0.0),
                    memory_percent=stat.get("memory_percent", 0.0),
                    memory_gb=stat.get("memory_gb", 0.0),
                    disk_percent=stat.get("disk_percent", 0.0),
                    disk_gb=stat.get("disk_gb", 0.0),
                    disk_read_ops=stat.get("disk_read_ops", 0.0),
                    disk_write_ops=stat.get("disk_write_ops", 0.0),
                    network_ip=stat.get("network_ip"),
                )
                entries.append(entry)

                # Recopilar valores para estadísticas
                cpu_values.append(entry.cpu_percent)
                memory_values.append(entry.memory_percent)
                disk_values.append(entry.disk_percent)
            except (ValueError, KeyError, TypeError) as e:
                logger.warning("Error parsing stats entry: %s", e)
                continue

        # Calcular estadísticas
        avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else None
        max_cpu = max(cpu_values) if cpu_values else None
        avg_memory = sum(memory_values) / len(memory_values) if memory_values else None
        max_memory = max(memory_values) if memory_values else None
        avg_disk = sum(disk_values) / len(disk_values) if disk_values else None

        return ServerMetricsHistory(
            server_id=server_id,
            server_name=server.name,
            period_hours=hours,
            total_entries=len(entries),
            entries=entries,
            avg_cpu=avg_cpu,
            max_cpu=max_cpu,
            avg_memory=avg_memory,
            max_memory=max_memory,
            avg_disk=avg_disk,
        )

    async def get_all_servers_metrics(self) -> ServersMetricsOverview:
        """
        Obtener vista general de métricas de todos los servidores.

        Returns:
            ServersMetricsOverview con resumen de todos los servidores
        """
        # Obtener todos los servidores
        servers = Server.all()

        servers_metrics = []
        healthy_count = 0
        warning_count = 0
        critical_count = 0
        connected_count = 0

        for server in servers:
            try:
                # Obtener métricas de cada servidor
                metrics = await self.get_server_metrics_summary(str(server.id))
                servers_metrics.append(metrics)

                # Contar por estado
                if metrics.agent_connected:
                    connected_count += 1

                if metrics.health_status == "healthy":
                    healthy_count += 1
                elif metrics.health_status == "warning":
                    warning_count += 1
                elif metrics.health_status == "critical":
                    critical_count += 1

            except HTTPException:
                # Server not found, skip
                continue
            except (ValueError, KeyError, TypeError) as e:
                logger.error("Error getting metrics for server %s: %s", server.id, e)
                continue

        return ServersMetricsOverview(
            total_servers=len(servers),
            connected_servers=connected_count,
            healthy_servers=healthy_count,
            warning_servers=warning_count,
            critical_servers=critical_count,
            servers=servers_metrics,
        )

    async def get_aggregate_metrics(self) -> AggregateMetrics:
        """
        Obtener métricas agregadas del sistema completo.

        Returns:
            AggregateMetrics con totales y promedios
        """
        servers = Server.all()

        total_servers = len(servers)
        active_servers = 0
        total_cpu_cores = 0
        total_memory_gb = 0.0
        total_disk_gb = 0.0

        cpu_values = []
        memory_values = []
        disk_values = []
        used_memory = 0.0
        used_disk = 0.0

        for server in servers:
            # Sumar recursos totales
            if server.cpu_cores:
                total_cpu_cores += server.cpu_cores
            if server.memory_gb:
                total_memory_gb += server.memory_gb

            # Obtener última métrica
            latest = self.stats_repo.get_latest(str(server.id))
            if not latest:
                continue

            # Verificar si está activo (últimos 5 minutos)
            try:
                last_update = datetime.fromisoformat(latest["timestamp"])
                time_diff = datetime.utcnow() - last_update
                if time_diff.total_seconds() < 300:  # 5 minutos
                    active_servers += 1

                    # Recopilar valores para promedios
                    if "cpu_percent" in latest:
                        cpu_values.append(latest["cpu_percent"])
                    if "memory_percent" in latest:
                        memory_values.append(latest["memory_percent"])
                    if "memory_gb" in latest:
                        used_memory += latest["memory_gb"]
                    if "disk_percent" in latest and "disk_gb" in latest:
                        disk_values.append(latest["disk_percent"])
                        # Calcular disco total basado en uso
                        if latest["disk_percent"] > 0:
                            total_disk_gb += latest["disk_gb"] / (
                                latest["disk_percent"] / 100
                            )
                        used_disk += latest["disk_gb"]
            except (ValueError, KeyError, TypeError, ZeroDivisionError):
                pass

        # Calcular promedios
        avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0.0
        avg_memory = sum(memory_values) / len(memory_values) if memory_values else 0.0
        avg_disk = sum(disk_values) / len(disk_values) if disk_values else 0.0

        return AggregateMetrics(
            timestamp=datetime.utcnow(),
            total_servers=total_servers,
            active_servers=active_servers,
            total_cpu_cores=total_cpu_cores,
            total_memory_gb=round(total_memory_gb, 2),
            total_disk_gb=round(total_disk_gb, 2),
            avg_cpu_percent=round(avg_cpu, 2),
            avg_memory_percent=round(avg_memory, 2),
            avg_disk_percent=round(avg_disk, 2),
            used_memory_gb=round(used_memory, 2),
            used_disk_gb=round(used_disk, 2),
        )

    async def get_metrics_alerts(self) -> MetricsAlerts:
        """
        Obtener alertas de métricas basadas en umbrales.

        Returns:
            MetricsAlerts con lista de alertas activas
        """
        servers = Server.all()
        alerts = []
        critical_count = 0
        warning_count = 0

        for server in servers:
            # Obtener última métrica
            latest = self.stats_repo.get_latest(str(server.id))
            if not latest:
                continue

            # Verificar si está activo (últimos 5 minutos)
            try:
                last_update = datetime.fromisoformat(latest["timestamp"])
                time_diff = datetime.utcnow() - last_update
                if time_diff.total_seconds() >= 300:  # Más de 5 minutos
                    continue
            except (ValueError, KeyError, TypeError):
                continue

            # Verificar CPU
            cpu = latest.get("cpu_percent")
            if cpu:
                if cpu >= self.thresholds["cpu"]["critical"]:
                    alerts.append(
                        MetricAlert(
                            server_id=str(server.id),
                            server_name=server.name,
                            metric="cpu",
                            value=cpu,
                            threshold=self.thresholds["cpu"]["critical"],
                            severity="critical",
                            timestamp=last_update,
                            message=f"CPU usage critical: {cpu:.1f}%",
                        )
                    )
                    critical_count += 1
                elif cpu >= self.thresholds["cpu"]["warning"]:
                    alerts.append(
                        MetricAlert(
                            server_id=str(server.id),
                            server_name=server.name,
                            metric="cpu",
                            value=cpu,
                            threshold=self.thresholds["cpu"]["warning"],
                            severity="warning",
                            timestamp=last_update,
                            message=f"CPU usage high: {cpu:.1f}%",
                        )
                    )
                    warning_count += 1

            # Verificar Memory
            memory = latest.get("memory_percent")
            if memory:
                if memory >= self.thresholds["memory"]["critical"]:
                    alerts.append(
                        MetricAlert(
                            server_id=str(server.id),
                            server_name=server.name,
                            metric="memory",
                            value=memory,
                            threshold=self.thresholds["memory"]["critical"],
                            severity="critical",
                            timestamp=last_update,
                            message=f"Memory usage critical: {memory:.1f}%",
                        )
                    )
                    critical_count += 1
                elif memory >= self.thresholds["memory"]["warning"]:
                    alerts.append(
                        MetricAlert(
                            server_id=str(server.id),
                            server_name=server.name,
                            metric="memory",
                            value=memory,
                            threshold=self.thresholds["memory"]["warning"],
                            severity="warning",
                            timestamp=last_update,
                            message=f"Memory usage high: {memory:.1f}%",
                        )
                    )
                    warning_count += 1

            # Verificar Disk
            disk = latest.get("disk_percent")
            if disk:
                if disk >= self.thresholds["disk"]["critical"]:
                    alerts.append(
                        MetricAlert(
                            server_id=str(server.id),
                            server_name=server.name,
                            metric="disk",
                            value=disk,
                            threshold=self.thresholds["disk"]["critical"],
                            severity="critical",
                            timestamp=last_update,
                            message=f"Disk usage critical: {disk:.1f}%",
                        )
                    )
                    critical_count += 1
                elif disk >= self.thresholds["disk"]["warning"]:
                    alerts.append(
                        MetricAlert(
                            server_id=str(server.id),
                            server_name=server.name,
                            metric="disk",
                            value=disk,
                            threshold=self.thresholds["disk"]["warning"],
                            severity="warning",
                            timestamp=last_update,
                            message=f"Disk usage high: {disk:.1f}%",
                        )
                    )
                    warning_count += 1

        # Ordenar por severidad (critical primero) y luego por timestamp
        alerts.sort(
            key=lambda x: (0 if x.severity == "critical" else 1, x.timestamp),
            reverse=True,
        )

        return MetricsAlerts(
            total_alerts=len(alerts),
            critical_count=critical_count,
            warning_count=warning_count,
            alerts=alerts,
        )

    async def compare_servers(self, server_ids: List[str]) -> ServerComparison:
        """
        Comparar métricas entre múltiples servidores.

        Args:
            server_ids: Lista de IDs de servidores a comparar

        Returns:
            ServerComparison con métricas de cada servidor
        """
        servers_metrics = []

        for server_id in server_ids:
            try:
                metrics = await self.get_server_metrics_summary(server_id)
                servers_metrics.append(metrics)
            except HTTPException:
                # Servidor no encontrado, skip
                continue
            except (ValueError, KeyError, TypeError) as e:
                logger.error("Error getting metrics for server %s: %s", server_id, e)
                continue
            except Exception as e:
                logger.error(f"Error getting metrics for server {server_id}: {e}")
                continue

        return ServerComparison(
            servers=servers_metrics, comparison_time=datetime.utcnow()
        )

    async def get_server_tunnel_analytics(
        self, server_id: str, hours: float = 24
    ) -> ServerTunnelAnalytics:
        """
        Obtener analytics de tráfico de túneles asociados a un servidor.

        Args:
            server_id: ID del servidor
            hours: Horas de histórico (default: 24)

        Returns:
            ServerTunnelAnalytics con métricas de tráfico
        """
        # Verificar que el servidor existe
        server = Server.find(server_id)
        if not server:
            raise HTTPException(status_code=404, detail="Server not found")

        # Obtener túneles del servidor
        from app.models.tunnel import Tunnel
        tunnels = Tunnel.query.filter_by(server_id=server_id).all()

        total_requests = 0
        total_bandwidth_mb = 0.0
        response_times = []
        all_paths = {}
        all_devices = {"mobile": 0, "tablet": 0, "desktop": 0, "bot": 0}
        all_browsers = {}
        all_countries = {}
        all_country_codes = {}

        # Agregar analytics de todos los túneles
        for tunnel in tunnels:
            try:
                stats = self.analytics_service.get_tunnel_stats(str(tunnel.id), hours)
                
                total_requests += stats.get("total_requests", 0)
                
                # Agregar tiempo de respuesta
                avg_rt = stats.get("avg_response_time_ms", 0)
                if avg_rt > 0:
                    response_times.append(avg_rt)
                
                # Agregar paths
                for path, count in stats.get("top_paths", {}).items():
                    all_paths[path] = all_paths.get(path, 0) + count
                
                # Agregar status codes
                for code, count in stats.get("status_codes", {}).items():
                    all_status_codes[code] = all_status_codes.get(code, 0) + count

                # Agregar devices
                for device, count in stats.get("devices", {}).items():
                    all_devices[device] = all_devices.get(device, 0) + count

                # Agregar browsers
                for browser, count in stats.get("browsers", {}).items():
                    all_browsers[browser] = all_browsers.get(browser, 0) + count

                # Agregar countries
                for country, count in stats.get("countries", {}).items():
                    all_countries[country] = all_countries.get(country, 0) + count

                # Agregar country_codes
                for code, count in stats.get("country_codes", {}).items():
                    all_country_codes[code] = all_country_codes.get(code, 0) + count
                
            except Exception as e:
                logger.warning(f"Error getting analytics for tunnel {tunnel.id}: {e}")
                continue

        # Calcular promedio de tiempo de respuesta
        avg_response_time = (
            sum(response_times) / len(response_times) if response_times else 0.0
        )

        # Ordenar top paths
        sorted_paths = dict(
            sorted(all_paths.items(), key=lambda x: x[1], reverse=True)[:10]
        )

        # Ordenar browsers y countries
        sorted_browsers = dict(
            sorted(all_browsers.items(), key=lambda x: x[1], reverse=True)[:10]
        )
        # Ordenar countries
        sorted_countries = dict(
            sorted(all_countries.items(), key=lambda x: x[1], reverse=True)[:10]
        )
        # Ordenar country codes
        sorted_country_codes = dict(
            sorted(all_country_codes.items(), key=lambda x: x[1], reverse=True)[:10]
        )

        return ServerTunnelAnalytics(
            server_id=server_id,
            server_name=server.name,
            period_hours=hours,
            total_requests=total_requests,
            total_bandwidth_mb=round(total_bandwidth_mb, 2),
            avg_response_time_ms=round(avg_response_time, 2),
            top_paths=sorted_paths,
            devices=all_devices,
            browsers=sorted_browsers,
            countries=sorted_countries,
            country_codes=sorted_country_codes, # Use the sorted country codes
            status_codes=all_status_codes,
        )


# Singleton instance
metrics_controller = MetricsController()
