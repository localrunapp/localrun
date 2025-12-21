"""
Healthcheck controller for receiving status reports from tunnel agents.
"""

from datetime import datetime
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.models.service import Service
from core.database import get_session
from core.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


class HealthcheckReportSchema(BaseModel):
    """Schema for healthcheck reports from tunnel-agent"""
    
    status: str = Field(..., description="Health status: healthy or unhealthy")
    timestamp: datetime = Field(..., description="Timestamp of the check")
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")
    status_code: Optional[int] = Field(None, description="HTTP status code received")
    error: Optional[str] = Field(None, description="Error message if unhealthy")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-12-15T10:00:00Z",
                "response_time_ms": 45,
                "status_code": 200,
                "error": None
            }
        }


@router.post(
    "/services/{service_id}/healthcheck",
    status_code=status.HTTP_200_OK,
    summary="Report healthcheck status",
    description="Endpoint for tunnel-agent to report healthcheck status"
)
async def report_healthcheck(
    service_id: uuid.UUID,
    payload: HealthcheckReportSchema,
    session: Session = Depends(get_session)
):
    """
    Receive and process healthcheck reports from tunnel-agent.
    
    The tunnel-agent will POST to this endpoint every time it performs a healthcheck.
    This endpoint updates the service's healthcheck status in the database.
    """
    # Find the service
    service = session.get(Service, service_id)
    
    if not service:
        logger.warning(f"Healthcheck report for non-existent service: {service_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service {service_id} not found"
        )
    
    # Update healthcheck status
    previous_status = service.healthcheck_status
    service.healthcheck_status = payload.status
    service.healthcheck_last_check = payload.timestamp
    service.updated_at = datetime.utcnow()
    
    if payload.status == "healthy":
        # Reset failure counter on success
        service.healthcheck_consecutive_failures = 0
        service.healthcheck_last_error = None
        
        logger.debug(
            f"Service {service.name} ({service_id}) is healthy",
            extra={
                "service_id": str(service_id),
                "response_time_ms": payload.response_time_ms,
                "status_code": payload.status_code
            }
        )
    else:
        # Increment failure counter
        service.healthcheck_consecutive_failures += 1
        service.healthcheck_last_error = payload.error
        
        logger.warning(
            f"Service {service.name} ({service_id}) is unhealthy",
            extra={
                "service_id": str(service_id),
                "consecutive_failures": service.healthcheck_consecutive_failures,
                "error": payload.error
            }
        )
    
    # Log status changes
    if previous_status != payload.status:
        logger.info(
            f"Service {service.name} healthcheck status changed: {previous_status} → {payload.status}",
            extra={
                "service_id": str(service_id),
                "service_name": service.name,
                "old_status": previous_status,
                "new_status": payload.status
            }
        )
    
    # Save to database
    session.add(service)
    session.commit()
    session.refresh(service)
    
    return {
        "success": True,
        "service_id": str(service_id),
        "status": service.healthcheck_status,
        "consecutive_failures": service.healthcheck_consecutive_failures
    }
