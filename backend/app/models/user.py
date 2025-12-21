"""
User model for authentication and authorization.
"""

from datetime import datetime
from typing import Optional
from sqlmodel import Field
from core.database_model import DatabaseModel


class User(DatabaseModel, table=True):
    """
    User model - Laravel equivalent: App/Models/User
    """

    __tablename__ = "users"

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # Credentials
    username: str = Field(unique=True, index=True, max_length=100)
    email: Optional[str] = Field(default=None, unique=True, index=True, max_length=255)
    password: str = Field(max_length=255)  # Hashed password

    # Profile
    full_name: Optional[str] = Field(default=None, max_length=255)
    avatar_url: Optional[str] = Field(default=None, max_length=500)

    # OAuth Providers
    github_id: Optional[str] = Field(default=None, index=True, max_length=100)
    google_id: Optional[str] = Field(default=None, index=True, max_length=100)
    microsoft_id: Optional[str] = Field(default=None, index=True, max_length=100)

    # Status
    is_active: bool = Field(default=True)
    is_admin: bool = Field(default=False)

    # Timestamps (Laravel style)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = Field(default=None)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"
