"""
Quick Tunnel - Temporary Cloudflare tunnel without authentication
Starts automatically when backend starts for immediate access
"""

import asyncio
import re
from typing import Optional

from core.logger import setup_logger

logger = setup_logger(__name__)


class QuickTunnel:
    """
    Cloudflare Quick Tunnel - Temporary tunnel without authentication.
    Perfect for development and first system startup.
    """

    def __init__(self):
        self.process: Optional[asyncio.subprocess.Process] = None
        self.public_url: Optional[str] = None
        self.is_running = False

    async def start(self, local_port: int = 8000) -> str:
        """
        Starts a Cloudflare Quick Tunnel.
        No token or authentication required.

        Args:
            local_port: Backend local port (default: 8000)

        Returns:
            Temporary public URL (e.g: https://abc123.trycloudflare.com)
        """
        if self.is_running:
            logger.warning("Quick Tunnel is already running")
            return self.public_url

        logger.info(f"Starting Quick Tunnel for port {local_port}...")

        # Comando para Quick Tunnel (sin --token)
        cmd = ["cloudflared", "tunnel", "--url", f"http://localhost:{local_port}"]

        try:
            # Iniciar proceso
            self.process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            logger.debug(f"Proceso cloudflared iniciado, PID: {self.process.pid}")

            # Extraer URL pública del output
            self.public_url = await asyncio.wait_for(self._extract_url(), timeout=30.0)

            self.is_running = True

            logger.info(f"Quick Tunnel ready: {self.public_url}")
            logger.info("")
            logger.info("╔" + "═" * 70 + "╗")
            logger.info("║ TEMPORARY PUBLIC ACCESS                                              ║")
            logger.info("║                                                                      ║")
            logger.info(f"║ URL: {self.public_url:<59} ║")
            logger.info("║                                                                      ║")
            logger.info("║ WARNING: This URL is temporary and will change on restart           ║")
            logger.info("║ TIP: Configure a permanent tunnel in the admin panel               ║")
            logger.info("╚" + "═" * 70 + "╝")
            logger.info("")

            return self.public_url

        except asyncio.TimeoutError:
            logger.error("Timeout waiting for Quick Tunnel URL")
            await self.stop()
            raise RuntimeError("Could not get Quick Tunnel URL")
        except Exception as e:
            logger.error(f"Error starting Quick Tunnel: {e}")
            await self.stop()
            raise

    async def _extract_url(self) -> str:
        """Extracts public URL from cloudflared output"""
        while True:
            line = await self.process.stderr.readline()
            if not line:
                raise RuntimeError("cloudflared cerró sin proporcionar URL")

            decoded = line.decode().strip()

            # Cloudflared muestra: "https://random-words-1234.trycloudflare.com"
            if "trycloudflare.com" in decoded:
                match = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", decoded)
                if match:
                    return match.group(0)

    async def stop(self):
        """Stops the Quick Tunnel"""
        if not self.process:
            return

        logger.info("Stopping Quick Tunnel...")

        try:
            self.process.terminate()
            await asyncio.wait_for(self.process.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("Quick Tunnel no respondió, forzando cierre")
            self.process.kill()
            await self.process.wait()

        self.is_running = False
        self.public_url = None
        logger.info("Quick Tunnel stopped")

    def get_status(self) -> dict:
        """Gets current Quick Tunnel status"""
        return {
            "is_running": self.is_running,
            "public_url": self.public_url,
            "pid": self.process.pid if self.process else None,
        }


# Instancia global del Quick Tunnel
quick_tunnel = QuickTunnel()
