"""
Setup routes - Initial setup and configuration endpoints.
"""

from fastapi import APIRouter, Request
from app.controllers.setup import SetupController

router = APIRouter(prefix="/setup", tags=["setup"])
setup_controller = SetupController()


# System info
router.add_api_route(
    "/system-info", setup_controller.get_system_info, methods=["GET"]
)

# Setup status
router.add_api_route("/status", setup_controller.get_setup_status, methods=["GET"])

# Verify password
router.add_api_route(
    "/verify-password", setup_controller.verify_initial_password, methods=["POST"]
)

# Complete setup
router.add_api_route("/complete", setup_controller.complete_setup, methods=["POST"])

# Agent status
router.add_api_route("/agent-status", setup_controller.get_agent_status, methods=["GET"])

# Agent host info
router.add_api_route(
    "/agent-host-info", setup_controller.get_agent_host_info, methods=["GET"]
)


# Agent install script
@router.get("/agent-install-script")
async def get_agent_install_script():
    """Get installation script for host agent."""
    script = setup_controller.get_agent_install_script()
    from fastapi.responses import PlainTextResponse

    return PlainTextResponse(script, media_type="text/plain")


# Install script by OS
@router.get("/install/{os_type}")
async def get_install_script_endpoint(os_type: str, request: Request):
    """
    Get installation script for specific OS with backend config injected.
    os_type: linux, macos, windows
    """
    from fastapi.responses import PlainTextResponse

    # Determine host from request
    host = request.headers.get("host", "localhost:8000")

    script = setup_controller.get_install_script(os_type, host)
    return PlainTextResponse(script, media_type="text/plain")


# Agent version endpoint
@router.get("/agent-version")
async def get_agent_version():
    """Get the current agent version available for download."""
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse("0.1.43", media_type="text/plain")


# Download agent tarball
@router.get("/download/{filename}")
async def download_agent_tarball(filename: str):
    """
    Download agent tarball.
    filename: e.g., v0.1.43-linux-x64.tar.gz
    """
    from fastapi.responses import FileResponse
    from pathlib import Path
    import os
    
    # Security: only allow specific filename patterns
    if not filename.startswith("v") or not filename.endswith(".tar.gz"):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    # Look for tarball in storage/agent-tarballs directory
    # Use absolute path from this file's location
    base_dir = Path(__file__).resolve().parent.parent / "storage" / "agent-tarballs"
    tarball_path = base_dir / filename
    
    if not tarball_path.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Tarball not found: {filename}. Looking in: {base_dir}")
    
    return FileResponse(
        path=str(tarball_path),
        media_type="application/gzip",
        filename=filename
    )

