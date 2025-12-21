import docker
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class UpdateResponse(BaseModel):
    status: str
    message: str


@router.post("/docker", response_model=UpdateResponse)
async def update_docker_containers():
    """
    Trigger a one-time update of the running containers using Watchtower.
    This requires the Docker socket to be mounted at /var/run/docker.sock.
    """
    try:
        client = docker.from_env()

        # Check if we can talk to Docker
        client.ping()

        logger.info("Starting Watchtower container for update...")

        # Run Watchtower as a sibling container
        # It will update all containers including this backend, then remove itself.
        # We use detach=True so we can return a response before the backend potentially restarts.
        container = client.containers.run(
            "containrrr/watchtower",
            command="--run-once --cleanup localrun-backend localrun-frontend",
            volumes={"/var/run/docker.sock": {"bind": "/var/run/docker.sock", "mode": "rw"}},
            detach=True,
            remove=True,
        )

        return UpdateResponse(
            status="success",
            message=f"Update initiated. Watchtower container ID: {container.short_id}. The service may restart shortly.",
        )

    except docker.errors.DockerException as e:
        logger.error(f"Docker error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to communicate with Docker: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


@router.get("/check")
async def check_for_updates():
    """
    Check if a new version is available on GitHub.
    """
    try:
        import requests
        from core.settings import settings

        # GitHub API URL
        repo = "localrun-tech/localrun"
        url = f"https://api.github.com/repos/{repo}/releases/latest"

        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            logger.warning(f"Failed to check for updates: {response.status_code}")
            return {"has_update": False, "error": "GitHub API error"}

        data = response.json()
        latest_version = data.get("tag_name", "").lstrip("v")
        current_version = settings.app_version

        # Simple semantic version comparison
        has_update = latest_version != current_version

        return {
            "has_update": has_update,
            "latest_version": latest_version,
            "current_version": current_version,
            "release_url": data.get("html_url"),
        }

    except Exception as e:
        logger.error(f"Error checking for updates: {str(e)}")
        return {"has_update": False, "error": str(e)}
