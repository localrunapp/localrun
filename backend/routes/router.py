"""
API Router - Main router configuration.
Includes all route modules and defines basic endpoints.
"""

from fastapi import APIRouter, Depends

# Import all route modules
from routes import (
    setup,
    system,
    auth,
    config,
    drivers,
    providers,
    domains,
    dns,
    services,
    servers,
    metrics,
)
from app.controllers import terminal, agent, system_logs, analytics, healthcheck
from core.auth import get_current_user

# Create main router
router = APIRouter()


# ========== Basic Endpoints ==========


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@router.get("/ping")
async def ping():
    """Ping endpoint."""
    return {"status": "pong"}


@router.get("/")
async def root():
    """Root endpoint - redirect to docs."""
    return {"message": "LocalRun Backend API", "docs": "/docs", "health": "/health"}


# ========== Include Route Modules ==========

# Public routes (no auth required)
router.include_router(setup.router)
router.include_router(auth.router)
router.include_router(config.router)

# Protected routes (auth required)
router.include_router(system.router, dependencies=[Depends(get_current_user)])
router.include_router(drivers.router, dependencies=[Depends(get_current_user)])
router.include_router(providers.router)  # Has auth in individual routes
router.include_router(domains.router)  # Has auth in individual routes
router.include_router(dns.router)  # Has auth in individual routes
router.include_router(services.router)  # Has auth in individual routes
router.include_router(servers.router)  # Has auth and db in router itself
router.include_router(metrics.router)  # Metrics endpoints

# Controller-based routers (legacy pattern, to be migrated)
router.include_router(terminal.router, tags=["terminal"])
router.include_router(agent.router, tags=["agent"])
router.include_router(system_logs.router, tags=["logs"])
router.include_router(analytics.router)
router.include_router(healthcheck.router, prefix="/api", tags=["healthcheck"])
