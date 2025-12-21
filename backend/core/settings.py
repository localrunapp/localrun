import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Localrun"
    app_version: str = "0.1.0"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False

    storage_path: str = os.getenv("STORAGE_PATH", "./storage")

    # Database (use data path in production)
    @property
    def database_url(self) -> str:
        """Database URL with proper path resolution."""
        if self.is_production():
            db_path = Path(self.data_path) / "localrun.db"
            return f"sqlite:///{db_path}"
        return "sqlite:///./database/localrun.db"

    # JWT Configuration
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 10080  # 7 days

    # Quick Tunnel (set at runtime)
    quick_tunnel_url: str | None = None
    quick_tunnel_enabled: bool = True

    # Cloudflare settings (DockFlare style)
    cloudflared_image: str = "cloudflare/cloudflared:latest"
    cloudflared_network_name: str = "host"  # Use host networking

    # Tunneling Agent Configuration
    default_tunnel_provider: str = "cloudflare"  # cloudflare or ngrok

    # Cloudflare Tunnel Configuration
    cloudflare_cert_path: str | None = None  # Path to cert.pem
    cloudflare_account_id: str | None = None
    cloudflare_api_token: str | None = None
    cloudflare_tunnel_name: str = "localrun-tunnel"
    cloudflare_zone_id: str | None = None

    # ngrok Configuration
    ngrok_auth_token: str | None = None  # Optional for basic usage
    ngrok_region: str = "us"  # us, eu, ap, au, sa, jp, in
    ngrok_image: str = "ngrok/ngrok:latest"

    # Tunnel Network Configuration
    tunnel_network_name: str = "localrun_default"  # Docker network for tunnels
    tunnel_use_host_network: bool = True  # Use host.docker.internal mapping

    def is_development(self) -> bool:
        """Check if app is in development environment."""
        return self.app_env.lower() in ("development", "dev", "local")

    def is_production(self) -> bool:
        """Check if app is in production environment."""
        return self.app_env.lower() in ("production", "prod")

    def get_storage_path(self, *paths) -> Path:
        """Get storage path with proper resolution."""
        return Path(self.storage_path) / Path(*paths)


# Global settings instance
settings = Settings()
