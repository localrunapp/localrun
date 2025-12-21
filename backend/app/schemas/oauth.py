from typing import Optional
from pydantic import BaseModel


class OAuthLinkRequest(BaseModel):
    provider: str
    provider_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    username: Optional[str] = None


class OAuthLoginRequest(BaseModel):
    provider: str
    provider_id: str
    email: Optional[str] = None
