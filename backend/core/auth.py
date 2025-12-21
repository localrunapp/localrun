"""
JWT authentication - Laravel Sanctum style with SQLModel
"""

from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlmodel import Session, select

from app.models.user import User
from core.database import get_db
from core.logger import setup_logger
from core.settings import settings

logger = setup_logger(__name__)


def create_system_user():
    """Crear usuario del sistema para operaciones internas"""
    from app.models.user import User

    return User(id=1, username="system", email="system@localrun", is_active=True)


security = HTTPBearer()


def create_access_token(data: dict) -> str:
    """
    Create JWT access token.
    Laravel equivalent: Sanctum token creation
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    to_encode.update({"exp": expire})

    logger.debug("Creating JWT access token")

    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    Laravel equivalent: Auth::user() middleware
    """
    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.warning("JWT token missing user ID")
            raise credentials_exception
    except JWTError as e:
        logger.warning(f"JWT validation failed: {str(e)}")
        raise credentials_exception from e

    # Get user from database using SQLModel
    statement = select(User).where(User.id == int(user_id))
    user = db.exec(statement).first()

    if user is None:
        logger.warning(f"User not found: {user_id}")
        raise credentials_exception

    if not user.is_active:
        logger.warning(f"Inactive user attempted access: {user.username}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")

    logger.debug(f"User authenticated: {user.username}")
    return user
