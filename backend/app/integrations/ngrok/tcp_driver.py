"""
Ngrok TCP Tunnel Driver
"""

import asyncio
import httpx
from typing import Dict, Any, Optional

# from app.drivers.tcp import TCPDriver  # TODO: Move TCPDriver to core
from core.logger import setup_logger

logger = setup_logger(__name__)


class NgrokTCPDriver(TCPDriver):
    """Ngrok TCP tunnel driver using ngrok binary"""

    API_URL = "http://localhost:4040/api/tunnels"

    async def start(
        self, local_port: int, credentials: Dict[str, Any], config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Start Ngrok TCP tunnel

        Args:
            local_port: Local port to tunnel
            credentials: {"authtoken": "ngrok_auth_token"}
            config: Optional configuration

        Returns:
            {"public_url": "tcp://0.tcp.ngrok.io:12345", "process": Process}
        """
        logger.info(f"Starting Ngrok TCP tunnel on port {local_port}")

        authtoken = credentials.get("authtoken")
        if not authtoken:
            raise ValueError("Ngrok authtoken is required")

        # Build ngrok command
        cmd = ["ngrok", "tcp", str(local_port), "--authtoken", authtoken, "--log", "stdout"]

        logger.debug(f"Executing: ngrok tcp {local_port} --authtoken ***")

        # Start process
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        # Wait for ngrok to start
        await asyncio.sleep(2)

        # Get public URL from ngrok API
        public_url = await self._get_public_url()

        logger.info(f"Ngrok TCP tunnel started: {public_url}")

        return {"public_url": public_url, "process": process, "pid": process.pid}

    async def stop(self, process) -> None:
        """Stop ngrok process"""
        logger.info(f"Stopping Ngrok TCP tunnel process {process.pid}")

        try:
            process.terminate()
            await asyncio.wait_for(process.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("Process didn't stop gracefully, killing it")
            process.kill()
            await process.wait()

        logger.info("Ngrok TCP tunnel stopped")

    async def get_status(self, process) -> str:
        """Get tunnel status"""
        if process.returncode is None:
            return "running"
        return "stopped"

    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Validate Ngrok credentials"""
        return "authtoken" in credentials and len(credentials["authtoken"]) > 0

    async def _get_public_url(self) -> str:
        """Get public URL from ngrok API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.API_URL)
                response.raise_for_status()
                data = response.json()

                tunnels = data.get("tunnels", [])
                if not tunnels:
                    raise RuntimeError("No tunnels found in ngrok API")

                # Find TCP tunnel
                for tunnel in tunnels:
                    if tunnel["proto"] == "tcp":
                        return tunnel["public_url"]

                raise RuntimeError("No TCP tunnel found")
        except Exception as e:
            logger.error(f"Error getting public URL from ngrok API: {e}")
            raise
