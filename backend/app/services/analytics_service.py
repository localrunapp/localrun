"""
Analytics Service - Gestión de métricas y analytics con TinyDB
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from tinydb import TinyDB, Query
from pathlib import Path
import geoip2.database
from user_agents import parse as parse_user_agent


class AnalyticsService:
    """Servicio para almacenar y consultar analytics de túneles"""

    def __init__(self, db_path: str = "database/analytics.json"):
        """
        Inicializar servicio de analytics

        Args:
            db_path: Ruta al archivo TinyDB
        """
        # Crear directorio si no existe
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.db = TinyDB(db_path)
        self.requests_table = self.db.table("requests")
        self.sessions_table = self.db.table("sessions")

        # GeoIP reader (opcional, requiere base de datos)
        self.geoip_reader = None
        try:
            geoip_db_path = Path("database/GeoLite2-Country.mmdb")
            if geoip_db_path.exists():
                self.geoip_reader = geoip2.database.Reader(str(geoip_db_path))
        except Exception:
            pass

    def log_request(
        self,
        tunnel_id: str,
        ip: str,
        user_agent: str,
        method: str,
        path: str,
        status_code: int,
        response_time_ms: float,
        referer: Optional[str] = None,
        accept_language: Optional[str] = None,
        request_size_bytes: int = 0,
        response_size_bytes: int = 0,
    ) -> Dict:
        """
        Registrar un request HTTP

        Args:
            tunnel_id: ID del túnel
            ip: IP del cliente
            user_agent: User-Agent header
            method: HTTP method (GET, POST, etc.)
            path: Request path
            status_code: HTTP status code
            response_time_ms: Tiempo de respuesta en ms
            referer: Referer header
            accept_language: Accept-Language header

        Returns:
            Dict con el registro creado
        """
        # Parse User-Agent
        ua = parse_user_agent(user_agent)

        # GeoIP lookup
        geo_data = self._get_geo_data(ip)

        # Crear registro
        record = {
            "tunnel_id": tunnel_id,
            "timestamp": datetime.utcnow().isoformat(),
            "ip": ip,
            "method": method,
            "path": path,
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "request_size_bytes": request_size_bytes,
            "response_size_bytes": response_size_bytes,
            "referer": referer,
            "accept_language": accept_language,
            # User-Agent parsed
            "browser": {
                "family": ua.browser.family,
                "version": ua.browser.version_string,
            },
            "os": {
                "family": ua.os.family,
                "version": ua.os.version_string,
            },
            "device": {
                "family": ua.device.family,
                "brand": ua.device.brand,
                "model": ua.device.model,
                "is_mobile": ua.is_mobile,
                "is_tablet": ua.is_tablet,
                "is_pc": ua.is_pc,
                "is_bot": ua.is_bot,
            },
            # GeoIP
            "geo": geo_data,
        }

        # Insertar en DB
        self.requests_table.insert(record)

        return record

    def _get_geo_data(self, ip: str) -> Dict:
        """Obtener datos geográficos de una IP"""
        if not self.geoip_reader:
            return {"country": "Unknown", "country_code": "XX"}

        try:
            response = self.geoip_reader.country(ip)
            return {
                "country": response.country.name or "Unknown",
                "country_code": response.country.iso_code or "XX",
            }
        except Exception:
            return {"country": "Unknown", "country_code": "XX"}

    def get_tunnel_stats(self, tunnel_id: str, hours: int = 24) -> Dict:
        """
        Obtener estadísticas de un túnel

        Args:
            tunnel_id: ID del túnel
            hours: Horas hacia atrás para analizar

        Returns:
            Dict con estadísticas
        """
        Request = Query()
        since = datetime.utcnow() - timedelta(hours=hours)

        # Filtrar requests del túnel en el período
        requests = self.requests_table.search(
            (Request.tunnel_id == tunnel_id) & (Request.timestamp >= since.isoformat())
        )

        if not requests:
            return self._empty_stats()

        # Calcular estadísticas
        total_requests = len(requests)

        # Por país y código
        countries = {}
        country_codes = {}
        for req in requests:
            geo = req.get("geo", {})
            country = geo.get("country", "Unknown")
            code = geo.get("country_code", "XX")
            
            countries[country] = countries.get(country, 0) + 1
            if code != "XX":
                country_codes[code] = country_codes.get(code, 0) + 1

        # Por navegador
        browsers = {}
        for req in requests:
            browser = req.get("browser", {}).get("family", "Unknown")
            browsers[browser] = browsers.get(browser, 0) + 1

        # Por dispositivo
        devices = {"mobile": 0, "tablet": 0, "desktop": 0, "bot": 0}
        for req in requests:
            device = req.get("device", {})
            if device.get("is_bot"):
                devices["bot"] += 1
            elif device.get("is_mobile"):
                devices["mobile"] += 1
            elif device.get("is_tablet"):
                devices["tablet"] += 1
            else:
                devices["desktop"] += 1

        # Por status code
        status_codes = {}
        for req in requests:
            code = str(req.get("status_code", 0))
            status_codes[code] = status_codes.get(code, 0) + 1

        # Tiempo de respuesta promedio
        response_times = [r.get("response_time_ms", 0) for r in requests]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        # Top paths
        paths = {}
        for req in requests:
            path = req.get("path", "/")
            paths[path] = paths.get(path, 0) + 1
        top_paths = sorted(paths.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "tunnel_id": tunnel_id,
            "period_hours": hours,
            "total_requests": total_requests,
            "avg_response_time_ms": round(avg_response_time, 2),
            "countries": countries,
            "country_codes": country_codes,
            "browsers": browsers,
            "devices": devices,
            "status_codes": status_codes,
            "top_paths": dict(top_paths),
        }

    def _empty_stats(self) -> Dict:
        """Retornar estadísticas vacías"""
        return {
            "total_requests": 0,
            "avg_response_time_ms": 0,
            "countries": {},
            "browsers": {},
            "devices": {"mobile": 0, "tablet": 0, "desktop": 0, "bot": 0},
            "status_codes": {},
            "top_paths": {},
        }

    def get_realtime_stats(self, tunnel_id: str, minutes: int = 5) -> Dict:
        """Obtener estadísticas en tiempo real (últimos N minutos)"""
        Request = Query()
        since = datetime.utcnow() - timedelta(minutes=minutes)

        requests = self.requests_table.search(
            (Request.tunnel_id == tunnel_id) & (Request.timestamp >= since.isoformat())
        )

        return {
            "tunnel_id": tunnel_id,
            "period_minutes": minutes,
            "requests_count": len(requests),
            "requests_per_minute": len(requests) / minutes if minutes > 0 else 0,
        }

    def cleanup_old_data(self, days: int = 30):
        """Limpiar datos antiguos"""
        Request = Query()
        cutoff = datetime.utcnow() - timedelta(days=days)

        removed = self.requests_table.remove(Request.timestamp < cutoff.isoformat())

        return {"removed_count": len(removed) if removed else 0}
