"""
LocalRun Backend - Main Application Entry Point
"""

# Standard library
import os
import sys
from contextlib import asynccontextmanager

# Third-party
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

# Local - Core
from core.logger import setup_logger
from core.settings import settings

# Local - App
from app.bootstrap import bootstrap_application, shutdown_application
from app.handler import Handler
from routes.router import router


# Configure Python cache and root path
os.environ["PYTHONPYCACHEPREFIX"] = "/storage/cache/pycache"
os.environ["ROOT_PATH"] = os.path.dirname(os.path.realpath(__file__))

# Setup logger
logger = setup_logger(__name__)

# Set custom exception handler
sys.excepthook = Handler.handle_exception


def show_banner():
    """Display application banner"""
    logger.info("")
    logger.info("=" * 60)
    logger.info(r"  _                    _ ____              ")
    logger.info(r" | |    ___   ___ __ _| |  _ \ _   _ _ __  ")
    logger.info(r" | |   / _ \ / __/ _` | | |_) | | | | '_ \ ")
    logger.info(r" | |__| (_) | (_| (_| | |  _ <| |_| | | | |")
    logger.info(r" |_____\___/ \___\__,_|_|_| \_\\__,_|_| |_|")
    logger.info("")
    logger.info(f" Version: {settings.app_version}")
    logger.info(f" Environment: {settings.app_env}")
    logger.info("=" * 60)
    logger.info("")


def show_credentials(initial_password: str, reset_token: str):
    """Display initial credentials"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("CREDENTIALS")
    logger.info("=" * 80)
    logger.info(f"Initial Setup Password: {initial_password}")
    logger.info(f"Password Reset Token: {reset_token}")
    logger.info("")
    logger.info("=" * 80)


async def startup_tasks():
    """Execute startup tasks"""
    show_banner()
    
    # Bootstrap application
    results = await bootstrap_application()
    
    # Show credentials on first run
    if results.get("is_first_run"):
        show_credentials(results["initial_password"], results["reset_token"])


async def shutdown_tasks():
    """Execute shutdown tasks"""
    await shutdown_application()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    try:
        await startup_tasks()
        yield
    finally:
        await shutdown_tasks()


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title=settings.app_name,
        description="Self-hosted tunnel management platform",
        version=settings.app_version,
        strict_slashes=False,
        redirect_slashes=False,
        lifespan=lifespan,
    )

    # Include routers
    app.include_router(router)

    from app.controllers.update import router as update_router
    app.include_router(update_router, prefix="/api/v1/update", tags=["System"])

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    app.add_exception_handler(Exception, Handler.handle_exception)
    app.add_exception_handler(StarletteHTTPException, Handler.handle_api_exception)
    app.add_exception_handler(RequestValidationError, Handler.handle_validation_error)

    return app


def main() -> None:
    """Application bootstrapper"""
    import uvicorn

    # Check debug mode
    debug_enabled = os.environ.get("DEBUG", "false").lower() == "true"
    hot_reload_enabled = os.environ.get("HOT_RELOAD", "false").lower() == "true"
    debug_port = os.environ.get("DEBUG_PORT")

    # Enable remote debugging if configured
    if debug_enabled and debug_port:
        try:
            import debugpy
            debugpy.listen(("0.0.0.0", int(debug_port)))
            logger.info(f"Debugger listening on port {debug_port}")
            logger.info("To attach: Run 'Localrun Backend Debug' in VS Code")
        except ImportError:
            logger.warning("debugpy not available, install for debugging support")
        except Exception as e:
            logger.warning(f"Could not start debugger: {e}")

    # Run server
    if settings.is_development() and hot_reload_enabled:
        logger.info("Development mode: Hot reload enabled")
        uvicorn.run(
            "main:app",
            host=settings.app_host,
            port=settings.app_port,
            log_level="info",
            reload=True,
            reload_dirs=[".", "app", "core", "database", "routes"],
            access_log=False,
        )
    else:
        logger.info("Production mode")
        app = create_app()
        uvicorn.run(
            app,
            host=settings.app_host,
            port=settings.app_port,
            log_level="info",
            access_log=True,
        )


# Create app instance for hot reload mode
app = create_app()

if __name__ == "__main__":
    main()
