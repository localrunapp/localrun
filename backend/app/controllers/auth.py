"""
Authentication controller - Username/Password + JWT with SQLModel
"""

from datetime import datetime

from fastapi import Depends, HTTPException, status
from sqlmodel import Session, select

from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.schemas.oauth import OAuthLinkRequest, OAuthLoginRequest
from core.auth import create_access_token
from core.database import get_db
from core.hash import Hash
from core.logger import setup_logger
from core.settings import settings

logger = setup_logger(__name__)


class AuthController:
    """
    Controller for authentication operations.
    Laravel equivalent: App/Http/Controllers/Auth/AuthController
    """

    async def login(self, request: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
        """
        Authenticate user with password only.
        Username is always 'admin' (single user system).
        Laravel equivalent: AuthController@login

        Args:
            request: Login credentials (password only)
            db: Database session

        Returns:
            JWT token response
        """
        logger.info("Login attempt for admin user")

        # Always use 'admin' username (single user system)
        statement = select(User).where(User.username == "admin")
        user = db.exec(statement).first()

        if not user:
            logger.error("Admin user not found in database")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")

        # Verify password (Laravel: Hash::check($password, $hash))
        if not Hash.check(request.password, user.password):
            logger.warning("Invalid password for admin user")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")

        # Check if user is active
        if not user.is_active:
            logger.warning("Inactive admin user login attempt")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")

        # Update last login
        user.last_login = datetime.utcnow()
        db.add(user)
        db.commit()

        logger.info(f"User authenticated successfully: {user.username}")

        # Create JWT token
        token = create_access_token({"sub": str(user.id)})

        return TokenResponse(
            access_token=token, token_type="bearer", expires_in=settings.jwt_access_token_expire_minutes
        )

    async def get_me(self, current_user: User) -> UserResponse:
        """
        Get current authenticated user.
        Laravel equivalent: AuthController@me

        Args:
            current_user: User from authentication dependency

        Returns:
            User information
        """
        logger.info(f"Fetching user info: {current_user.username}")

        return UserResponse(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            full_name=current_user.full_name,
            avatar_url=current_user.avatar_url,
            is_active=current_user.is_active,
            is_admin=current_user.is_admin,
        )

    async def logout(self, current_user: User) -> dict:
        """
        Logout user (client-side token invalidation).
        Laravel equivalent: AuthController@logout

        Args:
            current_user: User from authentication dependency

        Returns:
            Success message
        """
        logger.info(f"User logout: {current_user.username}")
        return {"message": "Logged out successfully"}

    async def link_provider(
        self, request: OAuthLinkRequest, current_user: User, db: Session = Depends(get_db)
    ) -> UserResponse:
        """
        Link an external provider to the current user.
        """
        logger.info(f"Linking provider {request.provider} to user {current_user.username}")

        if request.provider == "github":
            current_user.github_id = request.provider_id
        elif request.provider == "google":
            current_user.google_id = request.provider_id
        elif request.provider == "microsoft":
            current_user.microsoft_id = request.provider_id
        else:
            raise HTTPException(status_code=400, detail="Invalid provider")

        db.add(current_user)
        db.commit()
        db.refresh(current_user)

        return UserResponse(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            full_name=current_user.full_name,
            avatar_url=current_user.avatar_url,
            is_active=current_user.is_active,
            is_admin=current_user.is_admin,
        )

    async def unlink_provider(self, provider: str, current_user: User, db: Session = Depends(get_db)) -> UserResponse:
        """
        Unlink an external provider from the current user.
        """
        logger.info(f"Unlinking provider {provider} from user {current_user.username}")

        if provider == "github":
            current_user.github_id = None
        elif provider == "google":
            current_user.google_id = None
        elif provider == "microsoft":
            current_user.microsoft_id = None
        else:
            raise HTTPException(status_code=400, detail="Invalid provider")

        db.add(current_user)
        db.commit()
        db.refresh(current_user)

        return UserResponse(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            full_name=current_user.full_name,
            avatar_url=current_user.avatar_url,
            is_active=current_user.is_active,
            is_admin=current_user.is_admin,
        )

    async def login_with_provider(self, request: OAuthLoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
        """
        Login with an external provider.
        """
        logger.info(f"Login attempt with provider {request.provider}")

        statement = select(User)
        if request.provider == "github":
            statement = statement.where(User.github_id == request.provider_id)
        elif request.provider == "google":
            statement = statement.where(User.google_id == request.provider_id)
        elif request.provider == "microsoft":
            statement = statement.where(User.microsoft_id == request.provider_id)
        else:
            raise HTTPException(status_code=400, detail="Invalid provider")

        user = db.exec(statement).first()

        if not user:
            logger.warning(f"No user found linked to {request.provider} ID {request.provider_id}")
            raise HTTPException(status_code=401, detail="Account not linked")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="User account is inactive")

        # Update last login
        user.last_login = datetime.utcnow()
        db.add(user)
        db.commit()

        # Create JWT token
        token = create_access_token({"sub": str(user.id)})

        return TokenResponse(
            access_token=token, token_type="bearer", expires_in=settings.jwt_access_token_expire_minutes
        )

    async def reset_password(self, new_password: str, reset_token: str, db: Session = Depends(get_db)) -> dict:
        """
        Reset admin password using reset token.
        
        Args:
            new_password: New password to set
            reset_token: Reset token from X-Reset-Token header
            db: Database session
            
        Returns:
            Success message
            
        Raises:
            HTTPException: If token is invalid or password reset fails
        """
        import json
        from pathlib import Path
        
        logger.info("Password reset attempt")
        
        # Load token from storage
        token_file = Path('/app/storage/reset_token.json')
        if not token_file.exists():
            logger.error("Reset token file not found")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Reset token not configured"
            )
        
        try:
            with open(token_file, 'r') as f:
                token_data = json.load(f)
        except Exception as e:
            logger.error(f"Could not read reset token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not read reset token"
            )
        
        # Verify token
        if token_data.get('token') != reset_token:
            logger.warning("Invalid reset token provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid reset token"
            )
        
        # Get admin user
        statement = select(User).where(User.username == "admin")
        admin = db.exec(statement).first()
        
        if not admin:
            logger.error("Admin user not found")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Admin user not found"
            )
        
        # Update password
        admin.password = Hash.make(new_password)
        db.add(admin)
        
        # Update last_used timestamp in token file
        token_data['last_used'] = datetime.utcnow().isoformat()
        try:
            with open(token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not update token last_used: {e}")
        
        db.commit()
        
        logger.info("✅ Password reset successfully")
        
        return {
            "success": True,
            "message": "Password reset successfully"
        }
