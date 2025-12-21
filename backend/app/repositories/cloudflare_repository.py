"""
Cloudflare Repository - Acceso a Cloudflare API

Responsabilidades:
- Llamadas HTTP a Cloudflare API (tunnels, DNS, routes, config)
- Manejo de autenticación con API token
- Transformación de respuestas de API a modelos internos

NO maneja:
- Lógica de negocio → Services
- Operaciones de Docker → Infrastructure Services
- Operaciones de BD → ServiceRepository
"""

import logging
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class CloudflareRepository:
    """Repository para interactuar con Cloudflare API"""

    CF_API = "https://api.cloudflare.com/client/v4"

    def __init__(self, api_token: str, account_id: str):
        """
        Inicializar repository con credenciales.

        Args:
            api_token: Token de API de Cloudflare
            account_id: ID de cuenta de Cloudflare
        """
        self.api_token = api_token
        self.account_id = account_id

    def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Realizar petición a Cloudflare API.

        Args:
            method: Método HTTP (GET, POST, PUT, DELETE)
            endpoint: Endpoint de la API (ej: /accounts/{id}/tunnels)
            json_data: Datos JSON para el body
            params: Query parameters

        Returns:
            Respuesta de la API

        Raises:
            Exception: Si la petición falla
        """
        url = f"{self.CF_API}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                json=json_data,
                params=params,
                timeout=30,
            )
            response.raise_for_status()

            data = response.json()

            if not data.get("success", False):
                errors = data.get("errors", [])
                error_msg = ", ".join([e.get("message", str(e)) for e in errors])
                raise Exception(f"Cloudflare API error: {error_msg}")

            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Cloudflare API request failed: {e}")
            raise Exception(f"Error en petición a Cloudflare: {str(e)}")

    # ========== Tunnel Operations ==========

    def find_tunnel_by_name(self, tunnel_name: str) -> Optional[Dict[str, Any]]:
        """
        Buscar túnel por nombre.

        Args:
            tunnel_name: Nombre del túnel

        Returns:
            Dict con datos del túnel o None si no existe
        """
        endpoint = f"/accounts/{self.account_id}/cfd_tunnel"
        params = {"name": tunnel_name, "is_deleted": "false"}

        try:
            response = self._request("GET", endpoint, params=params)
            tunnels = response.get("result", [])

            for tunnel in tunnels:
                if tunnel.get("name") == tunnel_name:
                    logger.info(f"Túnel encontrado: {tunnel_name} (ID: {tunnel['id']})")
                    return tunnel

            logger.info(f"Túnel no encontrado: {tunnel_name}")
            return None

        except Exception as e:
            logger.error(f"Error buscando túnel {tunnel_name}: {e}")
            return None

    def create_tunnel(self, tunnel_name: str) -> tuple[str, str]:
        """
        Crear nuevo túnel.

        Args:
            tunnel_name: Nombre del túnel

        Returns:
            Tupla (tunnel_id, token)

        Raises:
            Exception: Si falla la creación
        """
        endpoint = f"/accounts/{self.account_id}/cfd_tunnel"
        data = {"name": tunnel_name, "config_src": "cloudflare"}

        try:
            response = self._request("POST", endpoint, json_data=data)
            result = response.get("result", {})

            tunnel_id = result.get("id")
            token = result.get("token")

            if not tunnel_id or not token:
                raise Exception("No se recibió tunnel_id o token en la respuesta")

            logger.info(f"Túnel creado: {tunnel_name} (ID: {tunnel_id})")
            return tunnel_id, token

        except Exception as e:
            logger.error(f"Error creando túnel {tunnel_name}: {e}")
            raise

    def get_tunnel_token(self, tunnel_id: str) -> str:
        """
        Obtener token de un túnel existente.

        Args:
            tunnel_id: ID del túnel

        Returns:
            Token del túnel

        Raises:
            Exception: Si falla la obtención
        """
        endpoint = f"/accounts/{self.account_id}/cfd_tunnel/{tunnel_id}/token"

        try:
            response = self._request("GET", endpoint)
            token = response.get("result")

            if not token:
                raise Exception("No se recibió token en la respuesta")

            logger.info(f"Token obtenido para túnel {tunnel_id}")
            return token

        except Exception as e:
            logger.error(f"Error obteniendo token del túnel {tunnel_id}: {e}")
            raise

    def delete_tunnel(self, tunnel_id: str) -> bool:
        """
        Eliminar túnel.

        Args:
            tunnel_id: ID del túnel

        Returns:
            True si se eliminó correctamente

        Raises:
            Exception: Si falla la eliminación
        """
        endpoint = f"/accounts/{self.account_id}/cfd_tunnel/{tunnel_id}"

        try:
            self._request("DELETE", endpoint)
            logger.info(f"Túnel eliminado: {tunnel_id}")
            return True

        except Exception as e:
            logger.error(f"Error eliminando túnel {tunnel_id}: {e}")
            raise

    # ========== Tunnel Configuration ==========

    def update_tunnel_config(self, tunnel_id: str, ingress_rules: List[Dict]) -> bool:
        """
        Actualizar configuración de ingress del túnel.

        Args:
            tunnel_id: ID del túnel
            ingress_rules: Lista de reglas de ingress

        Returns:
            True si se actualizó correctamente

        Raises:
            Exception: Si falla la actualización
        """
        endpoint = f"/accounts/{self.account_id}/cfd_tunnel/{tunnel_id}/configurations"

        # Siempre agregar catch-all al final
        if not any(rule.get("service") == "http_status:404" for rule in ingress_rules):
            ingress_rules.append({"service": "http_status:404"})

        config_data = {"config": {"ingress": ingress_rules}}

        try:
            self._request("PUT", endpoint, json_data=config_data)
            logger.info(f"Configuración actualizada para túnel {tunnel_id}: {len(ingress_rules)} reglas")
            return True

        except Exception as e:
            logger.error(f"Error actualizando config del túnel {tunnel_id}: {e}")
            raise

    def get_tunnel_config(self, tunnel_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener configuración actual del túnel.

        Args:
            tunnel_id: ID del túnel

        Returns:
            Configuración del túnel o None

        Raises:
            Exception: Si falla la obtención
        """
        endpoint = f"/accounts/{self.account_id}/cfd_tunnel/{tunnel_id}/configurations"

        try:
            response = self._request("GET", endpoint)
            return response.get("result", {})

        except Exception as e:
            logger.error(f"Error obteniendo config del túnel {tunnel_id}: {e}")
            return None

    # ========== DNS Operations ==========

    def list_zones(self) -> List[Dict[str, Any]]:
        """
        Listar zonas DNS de la cuenta.

        Returns:
            Lista de zonas
        """
        endpoint = "/zones"

        try:
            response = self._request("GET", endpoint)
            return response.get("result", [])

        except Exception as e:
            logger.error(f"Error listando zonas: {e}")
            return []

    def get_zone_id(self, domain: str) -> Optional[str]:
        """
        Obtener zone_id de un dominio.

        Args:
            domain: Dominio (ej: example.com)

        Returns:
            Zone ID o None
        """
        zones = self.list_zones()

        for zone in zones:
            if zone.get("name") == domain:
                return zone.get("id")

        logger.warning(f"Zona no encontrada para dominio: {domain}")
        return None

    def create_dns_record(
        self,
        zone_id: str,
        record_type: str,
        name: str,
        content: str,
        proxied: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Crear registro DNS.

        Args:
            zone_id: ID de la zona
            record_type: Tipo de registro (A, CNAME, etc.)
            name: Nombre del registro
            content: Contenido del registro
            proxied: Si debe pasar por proxy de Cloudflare

        Returns:
            Registro creado o None

        Raises:
            Exception: Si falla la creación
        """
        endpoint = f"/zones/{zone_id}/dns_records"
        data = {
            "type": record_type,
            "name": name,
            "content": content,
            "proxied": proxied,
        }

        try:
            response = self._request("POST", endpoint, json_data=data)
            result = response.get("result", {})
            logger.info(f"DNS record creado: {name} -> {content}")
            return result

        except Exception as e:
            logger.error(f"Error creando DNS record {name}: {e}")
            raise

    def find_dns_record(self, zone_id: str, name: str) -> Optional[Dict[str, Any]]:
        """
        Buscar registro DNS por nombre.

        Args:
            zone_id: ID de la zona
            name: Nombre del registro

        Returns:
            Registro encontrado o None
        """
        endpoint = f"/zones/{zone_id}/dns_records"
        params = {"name": name}

        try:
            response = self._request("GET", endpoint, params=params)
            records = response.get("result", [])

            if records:
                return records[0]

            return None

        except Exception as e:
            logger.error(f"Error buscando DNS record {name}: {e}")
            return None

    def delete_dns_record(self, zone_id: str, record_id: str) -> bool:
        """
        Eliminar registro DNS.

        Args:
            zone_id: ID de la zona
            record_id: ID del registro

        Returns:
            True si se eliminó correctamente

        Raises:
            Exception: Si falla la eliminación
        """
        endpoint = f"/zones/{zone_id}/dns_records/{record_id}"

        try:
            self._request("DELETE", endpoint)
            logger.info(f"DNS record eliminado: {record_id}")
            return True

        except Exception as e:
            logger.error(f"Error eliminando DNS record {record_id}: {e}")
            raise

    # ========== Utility Methods ==========

    def verify_token(self) -> bool:
        """
        Verificar que el token sea válido.

        Returns:
            True si el token es válido
        """
        endpoint = "/user/tokens/verify"

        try:
            response = self._request("GET", endpoint)
            return response.get("success", False)

        except Exception:
            return False
