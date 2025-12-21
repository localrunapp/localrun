"""
Provider management controller - Simplified singleton model
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, status
from sqlmodel import Session, select

from app.models.provider import Provider
from app.models.user import User
from core.auth import get_current_user
from core.database import get_db
from core.logger import setup_logger

logger = setup_logger(__name__)

# Provider definitions (fixed config per provider key)
PROVIDER_DEFINITIONS = {
    "cloudflare": {
        "name": "Cloudflare",
        "available_protocols": {
            "http": {"name": "HTTP/HTTPS Tunnels", "description": "Expose HTTP services"},
            "dns": {"name": "DNS Management", "description": "Manage DNS records"},
            "tcp": {"name": "TCP Tunnels", "description": "Expose TCP services"},
            "udp": {"name": "UDP Tunnels", "description": "Expose UDP services"},
            "ssh": {"name": "SSH Tunnels", "description": "SSH over tunnels"},
            "websocket": {"name": "WebSocket Tunnels", "description": "WebSocket support"},
        },
    },
    "ngrok": {
        "name": "Ngrok",
        "available_protocols": {
            "http": {"name": "HTTP/HTTPS Tunnels", "description": "Expose HTTP services"},
            "tcp": {"name": "TCP Tunnels", "description": "Expose TCP services"},
            "websocket": {"name": "WebSocket Tunnels", "description": "WebSocket support"},
        },
    },
    "namecheap": {
        "name": "Namecheap",
        "available_protocols": {
            "dns": {"name": "DNS Management", "description": "Manage DNS records"},
        },
    },
}


class ProvidersController:
    """Provider management controller"""

    def _get_or_create_provider(self, key: str, db: Session) -> Provider:
        """Get existing provider or create new one for the given key"""
        statement = select(Provider).where(Provider.key == key)
        provider = db.exec(statement).first()

        if not provider:
            default_configs = {}
            if key in ["ngrok", "cloudflare"]:
                default_configs["anonymous_tunnels"] = True

            provider = Provider(key=key, credentials={}, configs=default_configs)
            db.add(provider)
            db.commit()
            db.refresh(provider)
            logger.info(f"Created new provider: {key}")

        return provider

    # ========== List All Providers ==========
    async def list_providers(
        self, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
    ) -> List[Dict[str, Any]]:
        """List all provider configurations"""
        logger.info("Listing all provider configurations")

        result = []

        # Get all configured providers from database
        statement = select(Provider).where(Provider.is_active == True)
        providers = db.exec(statement).all()

        # Add system-defined providers that might not be configured yet
        configured_keys = {p.key for p in providers}
        for key in PROVIDER_DEFINITIONS.keys():
            if key not in configured_keys:
                provider = Provider(key=key, credentials={})
                providers.append(provider)

        for provider in providers:
            provider_def = PROVIDER_DEFINITIONS.get(provider.key, {"name": provider.key.title()})

            result.append(
                {
                    "key": provider.key,
                    "name": provider_def.get("name", provider.key.title()),
                    "http": provider.http,
                    "dns": provider.dns,
                    "tcp": provider.tcp,
                    "udp": provider.udp,
                    "ssh": provider.ssh,
                    "websocket": provider.websocket,
                    "bastion": provider.bastion,
                    "configs": provider.configs,
                    "has_credentials": bool(provider.credentials),
                    "is_active": provider.is_active,
                    "created_at": provider.created_at.isoformat() if provider.id else None,
                }
            )

        return result

    # ========== Generic Provider Methods ==========
    async def get_provider_config(
        self, provider_key: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
    ) -> Dict[str, Any]:
        """Get provider configuration by key"""
        logger.info(f"Getting config for provider: {provider_key}")

        if provider_key not in PROVIDER_DEFINITIONS:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")

        provider = self._get_or_create_provider(provider_key, db)
        provider_def = PROVIDER_DEFINITIONS[provider_key]

        # Enmascarar credenciales sensibles (mostrar primeros 4 y últimos 4 caracteres)
        masked_credentials = {}
        if provider.credentials:
            for key, value in provider.credentials.items():
                if isinstance(value, str) and len(value) > 8:
                    # Mostrar primeros 4 y últimos 4 caracteres, rellenar el medio con asteriscos
                    middle_length = len(value) - 8
                    masked_credentials[key] = f"{value[:4]}{'*' * middle_length}{value[-4:]}"
                elif isinstance(value, str):
                    # Si es muy corto, enmascarar completamente manteniendo el largo
                    masked_credentials[key] = "*" * len(value) if value else None
                else:
                    masked_credentials[key] = value

        return {
            "key": provider.key,
            "name": provider_def["name"],
            "tunnel_name": provider.tunnel_name,
            "http": provider.http,
            "dns": provider.dns,
            "tcp": provider.tcp,
            "udp": provider.udp,
            "ssh": provider.ssh,
            "websocket": provider.websocket,
            "bastion": provider.bastion,
            "configs": provider.configs,
            "credentials": masked_credentials,
            "is_active": provider.is_active,
            "created_at": provider.created_at.isoformat(),
        }

    async def update_provider_config(
        self,
        provider_key: str,
        request: Dict[str, Any],
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Dict[str, Any]:
        """Update provider configuration"""
        logger.info(f"Updating config for provider: {provider_key}")

        if provider_key not in PROVIDER_DEFINITIONS:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")

        provider = self._get_or_create_provider(provider_key, db)

        # Update credentials if provided
        if "credentials" in request:
            # Replace credentials completely if it's a dict, otherwise update
            if isinstance(request["credentials"], dict):
                provider.credentials = request["credentials"]
            else:
                provider.credentials.update(request["credentials"])
            logger.info(f"Updated credentials for {provider_key}")

        # Update tunnel_name if provided
        if "tunnel_name" in request:
            provider.tunnel_name = request["tunnel_name"]

        # Update protocol configurations (usando campos directos)
        for protocol in ["http", "dns", "tcp", "udp", "ssh", "websocket", "bastion"]:
            if protocol in request:
                protocol_data = request[protocol]

                # Si se envía un booleano directamente, usarlo
                if isinstance(protocol_data, bool):
                    setattr(provider, protocol, protocol_data)
                # Si se envía un dict con enabled, usarlo
                elif isinstance(protocol_data, dict) and "enabled" in protocol_data:
                    setattr(provider, protocol, protocol_data["enabled"])
                    # Guardar configuración adicional si existe
                    if "config" in protocol_data:
                        if not provider.configs:
                            provider.configs = {}
                        provider.configs[protocol] = protocol_data["config"]

                logger.info(f"Updated {protocol} configuration for {provider_key}")

        # Update anonymous_tunnels if provided (Cloudflare specific)
        if "anonymous_tunnels" in request:
            if not provider.configs:
                provider.configs = {}
            provider.configs["anonymous_tunnels"] = request["anonymous_tunnels"]
            logger.info(f"Updated anonymous_tunnels for {provider_key}: {request['anonymous_tunnels']}")

        provider.updated_at = datetime.utcnow()
        db.add(provider)
        db.commit()

        logger.info(f"Provider {provider_key} configuration updated")

        return {"key": provider.key, "message": "Configuration updated successfully"}

    async def delete_provider_config(
        self, provider_key: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
    ) -> Dict[str, str]:
        """Delete provider configuration"""
        logger.info(f"Deleting config for provider: {provider_key}")

        statement = select(Provider).where(Provider.key == provider_key)
        provider = db.exec(statement).first()

        if provider:
            db.delete(provider)
            db.commit()
            logger.info(f"Provider {provider_key} deleted")

        return {"message": f"{provider_key.title()} configuration deleted successfully"}

    # ========== Protocol-specific methods ==========
    async def enable_protocol(
        self,
        provider_key: str,
        protocol: str,
        config: Dict[str, Any] = None,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Dict[str, str]:
        """Enable a protocol for a provider"""
        logger.info(f"Enabling {protocol} for provider: {provider_key}")

        if provider_key not in PROVIDER_DEFINITIONS:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")

        provider = self._get_or_create_provider(provider_key, db)

        # Habilitar protocolo usando campo directo
        setattr(provider, protocol, True)

        # Guardar configuración si se proporciona
        if config:
            if not provider.configs:
                provider.configs = {}
            provider.configs[protocol] = config

        provider.updated_at = datetime.utcnow()

        db.add(provider)
        db.commit()

        return {"message": f"{protocol.upper()} enabled for {provider_key}"}

    async def disable_protocol(
        self,
        provider_key: str,
        protocol: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Dict[str, str]:
        """Disable a protocol for a provider"""
        logger.info(f"Disabling {protocol} for provider: {provider_key}")

        if provider_key not in PROVIDER_DEFINITIONS:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")

        provider = self._get_or_create_provider(provider_key, db)

        # Deshabilitar protocolo usando campo directo
        setattr(provider, protocol, False)

        provider.updated_at = datetime.utcnow()

        db.add(provider)
        db.commit()

        return {"message": f"{protocol.upper()} disabled for {provider_key}"}

    async def test_cloudflare_token(
        self,
        token: str,
        current_user: User = Depends(get_current_user),
    ) -> Dict[str, Any]:
        """Test Cloudflare API token"""
        logger.info("Testing Cloudflare token")
        import httpx

        url = "https://api.cloudflare.com/client/v4/user/tokens/verify"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers)
                data = response.json()

                if response.status_code == 200 and data.get("success"):
                    return {"success": True, "message": "Token verified successfully", "result": data.get("result")}
                else:
                    error_msg = data.get("errors", [{"message": "Unknown error"}])[0].get("message")
                    return {"success": False, "message": f"Token verification failed: {error_msg}"}
            except Exception as e:
                logger.error(f"Error testing Cloudflare token: {str(e)}")
                return {"success": False, "message": f"Error connecting to Cloudflare: {str(e)}"}
