"""
Cronjob model for scheduled tasks.
"""

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class Cronjob(SQLModel, table=True):
    """
    Cronjob model for scheduled tasks.
    """

    __tablename__ = "cronjobs"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, index=True)
    schedule: str = Field(max_length=100, description="Cron expression (e.g., '*/5 * * * *')")
    command: str = Field(max_length=500, description="Command or task to execute")
    is_active: bool = Field(default=True)

    last_run: Optional[datetime] = Field(default=None)
    next_run: Optional[datetime] = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def __repr__(self):
        return f"<Cronjob(id={self.id}, name='{self.name}', schedule='{self.schedule}')>"
