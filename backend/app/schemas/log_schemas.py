"""
Log Schemas for LocalRun
Pydantic models for log query parameters and responses.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime


class LogQueryParams(BaseModel):
    """Parameters for querying logs with pagination, filtering, and sorting."""
    
    search: Optional[str] = Field(
        None,
        description="Search term to find in message, server_name, category, level, or metadata"
    )
    categories: Optional[List[str]] = Field(
        None,
        description="Filter by one or more categories (metrics, websocket, services, backend, agents)"
    )
    levels: Optional[List[str]] = Field(
        None,
        description="Filter by one or more levels (info, warning, error)"
    )
    server_id: Optional[str] = Field(
        None,
        description="Filter by specific server ID"
    )
    sort_by: str = Field(
        "timestamp",
        description="Field to sort by (timestamp, category, level, server_name, message)"
    )
    sort_order: Literal["asc", "desc"] = Field(
        "desc",
        description="Sort order: ascending or descending"
    )
    page: int = Field(
        1,
        ge=1,
        description="Page number (1-indexed)"
    )
    page_size: int = Field(
        50,
        ge=1,
        le=500,
        description="Number of items per page (max 500)"
    )
    
    @field_validator('sort_by')
    @classmethod
    def validate_sort_by(cls, v: str) -> str:
        """Validate sort_by field."""
        allowed_fields = ['timestamp', 'category', 'level', 'server_name', 'message', 'server_id']
        if v not in allowed_fields:
            raise ValueError(f"sort_by must be one of: {', '.join(allowed_fields)}")
        return v
    
    @field_validator('categories')
    @classmethod
    def validate_categories(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate categories."""
        if v is None:
            return v
        allowed = ['metrics', 'websocket', 'services', 'backend', 'agents']
        for cat in v:
            if cat not in allowed:
                raise ValueError(f"Invalid category: {cat}. Allowed: {', '.join(allowed)}")
        return v
    
    @field_validator('levels')
    @classmethod
    def validate_levels(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate levels."""
        if v is None:
            return v
        allowed = ['info', 'warning', 'error']
        for level in v:
            if level not in allowed:
                raise ValueError(f"Invalid level: {level}. Allowed: {', '.join(allowed)}")
        return v


class LogEntry(BaseModel):
    """Model for a single log entry."""
    
    id: str = Field(..., description="Unique log entry ID")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    category: str = Field(..., description="Log category")
    level: str = Field(..., description="Log level")
    message: str = Field(..., description="Log message")
    server_id: Optional[str] = Field(None, description="Associated server ID")
    server_name: Optional[str] = Field(None, description="Associated server name")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2025-12-11T03:00:00Z",
                "category": "services",
                "level": "info",
                "message": "Tunnel started successfully",
                "server_id": "srv_123",
                "server_name": "my-server",
                "metadata": {"port": 8080}
            }
        }


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class PaginatedLogsResponse(BaseModel):
    """Response model for paginated logs."""
    
    items: List[LogEntry] = Field(..., description="List of log entries")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Applied filters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "timestamp": "2025-12-11T03:00:00Z",
                        "category": "services",
                        "level": "info",
                        "message": "Tunnel started",
                        "server_id": "srv_123",
                        "server_name": "my-server",
                        "metadata": {}
                    }
                ],
                "pagination": {
                    "total": 150,
                    "page": 1,
                    "page_size": 50,
                    "total_pages": 3,
                    "has_next": True,
                    "has_prev": False
                },
                "filters": {
                    "search": "tunnel",
                    "categories": ["services"],
                    "levels": None,
                    "server_id": None
                }
            }
        }


class LogStatsResponse(BaseModel):
    """Response model for log statistics."""
    
    total_logs: int
    by_category: Dict[str, int]
    by_level: Dict[str, int]
    oldest_log: Optional[str]
    newest_log: Optional[str]
