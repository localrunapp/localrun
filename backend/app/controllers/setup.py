"""
Setup controller for initial system configuration.
Handles first-time setup wizard flow.
"""

import platform
import socket
from datetime import datetime
from typing import Dict, Any

from fastapi import HTTPException, status
from sqlmodel import Session, select
from pydantic import BaseModel, Field

from app.models.config import Config
from app.models.user import User
from core.database import get_db
from core.hash import Hash
from core.logger import setup_logger

logger = setup_logger(__name__)


# Request/Response models
class SetupStatusResponse(BaseModel):
    """Setup status response."""

    setup_completed: bool
    installation_name: str | None = None
    requires_setup: bool




class CompleteSetupRequest(BaseModel):
    """Complete setup request."""

    installation_name: str = Field(..., min_length=1, max_length=255)
    new_password: str = Field(..., min_length=8)
    new_password_confirmation: str = Field(..., min_length=8)


class CompleteSetupResponse(BaseModel):
    """Complete setup response."""

    success: bool
    message: str
    installation_name: str
    reset_token: str


class AgentStatusResponse(BaseModel):
    """Agent status response."""

    os_type: str  # "macos", "linux", "windows"
    requires_agent: bool
    agent_installed: bool
    install_command: str | None = None


class SetupController:
    """Controller for initial system setup."""

    def __init__(self):
        """Initialize setup controller."""
        pass

    def get_system_info(self) -> Dict[str, Any]:
        """
        Get basic system information for setup (no auth required).
        Returns minimal OS info to help with setup UI.
        """
        try:
            import os
            import docker

            uname = platform.uname()
            is_docker = os.path.exists("/.dockerenv")

            # Detect host OS when in Docker
            platform_type = "unknown"
            is_mac = False
            is_arm = False
            cpu_cores = None
            cpu_model = None

            if is_docker:
                try:
                    # Try to connect to Docker API to detect host
                    docker_client = docker.from_env()
                    info = docker_client.info()

                    # Check if running on macOS Docker Desktop
                    architecture = info.get("Architecture", "")
                    is_arm = architecture in ["aarch64", "arm64"]
                    is_mac = is_arm or "Docker Desktop" in info.get(
                        "OperatingSystem", ""
                    )

                    if is_mac:
                        platform_type = "macos"
                    else:
                        platform_type = info.get("OSType", "linux").lower()

                    # Get CPU info
                    cpu_cores = info.get("NCPU")
                    if is_arm and is_mac:
                        cpu_model = (
                            f"Apple Silicon (ARM64) - {cpu_cores} cores"
                            if cpu_cores
                            else "Apple Silicon (ARM64)"
                        )
                    elif cpu_cores:
                        cpu_model = f"{architecture} - {cpu_cores} cores"
                    else:
                        cpu_model = architecture

                except Exception:
                    # Fallback: if can't detect, assume Linux
                    platform_type = "linux"
            else:
                # Not in Docker, use platform detection
                os_type = uname.system.lower()
                platform_type = "macos" if os_type == "darwin" else os_type
                is_mac = os_type == "darwin"

            result = {
                "platform": platform_type,
                "is_mac": is_mac,
                "in_docker": is_docker,
            }

            # Add condensed info
            if is_docker and is_mac:
                result["os_name"] = "macOS (Docker Desktop)"
                result["architecture"] = "arm64" if is_arm else "x86_64"
                result["is_arm"] = is_arm
                if cpu_cores:
                    result["cpu_cores"] = cpu_cores
                if cpu_model:
                    result["cpu_model"] = cpu_model
            else:
                result["os_name"] = uname.system
                result["architecture"] = uname.machine

            return result

        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {
                "platform": "unknown",
                "is_mac": False,
                "in_docker": False,
                "os_name": "unknown",
            }

    def get_setup_status(self) -> SetupStatusResponse:
        """
        Get current setup status.
        Returns whether setup is completed and if it requires completion.
        """
        db = next(get_db())

        try:
            config = db.exec(select(Config)).first()

            if not config:
                # No config exists, needs setup
                return SetupStatusResponse(
                    setup_completed=False, installation_name=None, requires_setup=True
                )

            return SetupStatusResponse(
                setup_completed=config.setup_completed,
                installation_name=config.installation_name,
                requires_setup=not config.setup_completed,
            )
        finally:
            db.close()


    def complete_setup(self, request: CompleteSetupRequest) -> CompleteSetupResponse:
        """
        Complete initial setup:
        1. Validate new password matches confirmation
        2. Update admin password
        3. Generate reset token
        4. Save installation name
        5. Mark setup as completed
        """
        import json
        from pathlib import Path
        import uuid
        
        db = next(get_db())

        try:
            # Get admin user
            admin = db.exec(select(User).where(User.username == "admin")).first()

            if not admin:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Admin user not found",
                )

            # Validate new password confirmation
            if request.new_password != request.new_password_confirmation:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Password confirmation does not match",
                )

            # Update admin password
            admin.password = Hash.make(request.new_password)
            db.add(admin)

            # Generate reset token
            reset_token = str(uuid.uuid4())
            token_file = Path("/app/storage/reset_token.json")
            token_file.parent.mkdir(parents=True, exist_ok=True)
            
            token_data = {
                "token": reset_token,
                "created_at": datetime.now().isoformat(),
                "last_used": None
            }
            
            try:
                with open(token_file, "w") as f:
                    json.dump(token_data, f, indent=2)
            except Exception as e:
                logger.error(f"Could not save reset token: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Could not save reset token",
                )

            # Update or create config
            config = db.exec(select(Config)).first()

            if not config:
                config = Config(
                    setup_completed=True,
                    installation_name=request.installation_name,
                    initial_password_used=False,
                )
            else:
                config.setup_completed = True
                config.installation_name = request.installation_name
                config.initial_password_used = False

            db.add(config)
            db.commit()
            db.refresh(config)

            logger.info(
                f"✅ Setup completed for installation: {request.installation_name}"
            )

            # Update local server name
            from app.models.server import Server

            # Find the local server (flagged as is_local)
            local_server = db.exec(
                select(Server).where(Server.is_local == True)
            ).first()

            if local_server:
                local_server.name = request.installation_name
                db.add(local_server)
                db.commit()

            return CompleteSetupResponse(
                success=True,
                message="Setup completed successfully",
                installation_name=config.installation_name,
                reset_token=reset_token,
            )
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Setup completion failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Setup failed: {str(e)}",
            )
        finally:
            db.close()

    def get_agent_status(self) -> AgentStatusResponse:
        """
        Check if host agent is required and installed.
        Detects OS type and provides installation instructions.
        Uses get_system_info() to detect HOST OS, not container OS.
        """
        # Get host system info (not container's OS)
        system_info = self.get_system_info()
        platform_name = system_info.get("platform", "unknown").lower()

        # Map to standard OS types
        if platform_name == "macos" or system_info.get("is_mac"):
            os_type = "macos"
        elif platform_name == "windows":
            os_type = "windows"
        elif platform_name == "linux":
            os_type = "linux"
        else:
            os_type = "unknown"

        # Check if agent is required (macOS always needs it, Linux uses nsenter)
        requires_agent = os_type == "macos"

        # Check if agent is installed (try to connect to it)
        agent_installed = self._check_agent_installed()

        # Generate install command based on OS
        install_command = None
        if requires_agent and not agent_installed:
            if os_type == "macos":
                install_command = "curl -fsSL https://raw.githubusercontent.com/localrunapp/cli-agent/main/scripts/install-macos.sh | bash"

        return AgentStatusResponse(
            os_type=os_type,
            requires_agent=requires_agent,
            agent_installed=agent_installed,
            install_command=install_command,
        )

    def _check_agent_installed(self) -> bool:
        """Check if host agent is responding."""
        try:
            # Try to connect to agent on host.docker.internal:47777
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(("host.docker.internal", 47777))
            sock.close()
            return result == 0
        except Exception:
            return False

    def get_agent_host_info(self) -> Dict[str, Any]:
        """Get host information from the agent."""
        try:
            import requests

            response = requests.get(
                "http://host.docker.internal:47777/api/host/info", timeout=2
            )
            if response.status_code == 200:
                return response.json()
            return {"error": "Agent not responding"}
        except Exception as e:
            return {"error": str(e)}

    def get_agent_install_script(self) -> str:
        """
        Return installation command for host agent based on detected OS.
        Commands download scripts from: https://github.com/localrunapp/cli-agent/tree/main/scripts
        """
        try:
            # Get system info to detect host OS
            system_info = self.get_system_info()
            os_name = system_info.get("os_name", "").lower()
            platform_name = system_info.get("platform", "").lower()

            # Determine OS and return appropriate install command
            base_url = (
                "https://raw.githubusercontent.com/localrunapp/cli-agent/main/scripts"
            )

            # Check for macOS
            if (
                "darwin" in platform_name
                or "macos" in os_name
                or system_info.get("is_mac")
            ):
                return f"curl -fsSL {base_url}/install-macos.sh | bash"

            # Check for Windows
            elif "windows" in platform_name or "windows" in os_name:
                return f"irm {base_url}/install-windows.ps1 | iex"

            # Default to Linux
            else:
                return f"curl -fsSL {base_url}/install-linux.sh | bash"

        except Exception as e:
            logger.error(f"Error detecting OS for agent install: {e}")
            # Fallback to Linux command
            return "curl -fsSL https://raw.githubusercontent.com/localrunapp/cli-agent/main/scripts/install-linux.sh | bash"

    def get_install_script(self, os_type: str, host: str) -> str:
        """
        Fetch install script from GitHub and inject backend configuration.
        """
        import httpx

        base_url = (
            "https://raw.githubusercontent.com/localrunapp/cli-agent/main/scripts"
        )

        # Map os_type to script name
        if os_type == "macos":
            script_name = "install-macos.sh"
        elif os_type == "windows":
            script_name = "install-windows.ps1"
        else:
            script_name = "install-linux.sh"

        url = f"{base_url}/{script_name}"

        try:
            # Fetch script from GitHub
            response = httpx.get(url, timeout=10.0)
            response.raise_for_status()
            content = response.text

            # Inject BACKEND variable
            # We inject it right after the shebang or at the top
            if os_type == "windows":
                # PowerShell
                injection = f'$env:BACKEND = "{host}"\n'
                return injection + content
            else:
                # Bash
                # Inject after shebang if present, otherwise at top
                if content.startswith("#!"):
                    lines = content.splitlines()
                    lines.insert(1, f'export BACKEND="{host}"')
                    return "\n".join(lines)
                else:
                    return f'export BACKEND="{host}"\n' + content

        except Exception as e:
            logger.error(f"Error fetching install script: {e}")
            return f"# Error fetching script: {str(e)}"
