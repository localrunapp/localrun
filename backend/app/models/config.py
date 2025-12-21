"""
System configuration model for setup and installation settings.
"""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Config(SQLModel, table=True):
    """
    System configuration table.
    Stores setup completion status and installation metadata.
    """

    __tablename__ = "configs"

    id: Optional[int] = Field(default=None, primary_key=True)
    setup_completed: bool = Field(default=False, description="Whether initial setup is completed")
    installation_name: Optional[str] = Field(
        default=None, max_length=255, description="Custom name for this installation (e.g., 'Server Home')"
    )
    initial_password_used: bool = Field(
        default=False, description="Whether the initial random password has been used for setup"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "setup_completed": True,
                "installation_name": "Server Home",
                "initial_password_used": True,
            }
        }
