"""
Cloudflare TCP Tunnel Driver
"""

import asyncio
import re
from typing import Dict, Any, Optional

# from app.drivers.tcp import TCPDriver  # TODO: Move TCPDriver to core
from core.logger import setup_logger

logger = setup_logger(__name__)


class CloudflaredTCPDriver(TCPDriver):
    """Cloudflare TCP tunnel driver using cloudflared"""

    async def start(
        self, local_port: int, credentials: Dict[str, Any], config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Start Cloudflare TCP tunnel

        Args:
            local_port: Local port to tunnel
            credentials: {"token": "cloudflare_tunnel_token"}
            config: Optional configuration

        Returns:
            {"public_url": "tcp://xxx.cfargotunnel.com:PORT", "process": Process}
        """
        logger.info(f"Starting Cloudflare TCP tunnel on port {local_port}")

        token = credentials.get("token")
        if not token:
            raise ValueError("Cloudflare tunnel token is required")

        # Build cloudflared command for TCP
        cmd = ["cloudflared", "tunnel", "--url", f"tcp://localhost:{local_port}", "run", "--token", token]

        logger.debug(f"Executing: cloudflared tunnel --url tcp://localhost:{local_port} run --token ***")

        # Start process
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        # Extract public URL
        public_url = await self._extract_public_url(process)

        logger.info(f"Cloudflare TCP tunnel started: {public_url}")

        return {"public_url": public_url, "process": process, "pid": process.pid}

    async def stop(self, process) -> None:
        """Stop cloudflared process"""
        logger.info(f"Stopping Cloudflare TCP tunnel process {process.pid}")

        try:
            process.terminate()
            await asyncio.wait_for(process.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("Process didn't stop gracefully, killing it")
            process.kill()
            await process.wait()

        logger.info("Cloudflare TCP tunnel stopped")

    async def get_status(self, process) -> str:
        """Get tunnel status"""
        if process.returncode is None:
            return "running"
        return "stopped"

    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Validate Cloudflare credentials"""
        return "token" in credentials and len(credentials["token"]) > 0

    async def _extract_public_url(self, process) -> str:
        """Extract public URL from cloudflared output"""
        try:
            async for line in process.stderr:
                decoded = line.decode().strip()
                logger.debug(f"cloudflared: {decoded}")

                # Look for TCP URL in output
                match = re.search(r"tcp://[a-zA-Z0-9.-]+:\d+", decoded)
                if match:
                    return match.group(0)

            raise RuntimeError("Could not extract public URL from cloudflared output")
        except Exception as e:
            logger.error(f"Error extracting public URL: {e}")
            raise
