"""
Authentication schemas
"""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """
    Login request schema.
    Only password is required, username is always 'admin'.
    """

    password: str = Field(..., min_length=1)

    class Config:
        json_schema_extra = {"example": {"password": "your-secure-password"}}


class TokenResponse(BaseModel):
    """
    Token response schema.
    """

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # Minutes

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 10080,
            }
        }


class UserResponse(BaseModel):
    """
    User response schema.
    """

    id: int
    username: str
    email: str | None
    full_name: str | None
    avatar_url: str | None
    is_active: bool
    is_admin: bool

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "demo",
                "email": "demo@localrun.local",
                "full_name": "Demo User",
                "avatar_url": None,
                "is_active": True,
                "is_admin": True,
            }
        }


class ResetPasswordRequest(BaseModel):
    """
    Password reset request schema.
    """

    new_password: str = Field(..., min_length=8, description="New password (minimum 8 characters)")

    class Config:
        json_schema_extra = {"example": {"new_password": "new-secure-password123"}}
