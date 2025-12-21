"""
Auth routes - Authentication and authorization endpoints.
"""

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlmodel import Session
from app.controllers.auth import AuthController
from app.schemas.auth import ResetPasswordRequest
from core.auth import get_current_user
from core.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])
auth_controller = AuthController()


# Login
router.add_api_route("/login", auth_controller.login, methods=["POST"])

# Get current user
router.add_api_route(
    "/me", auth_controller.get_me, methods=["GET"], dependencies=[Depends(get_current_user)]
)

# Logout
router.add_api_route(
    "/logout",
    auth_controller.logout,
    methods=["POST"],
    dependencies=[Depends(get_current_user)],
)

# Link provider
router.add_api_route(
    "/link",
    auth_controller.link_provider,
    methods=["POST"],
    dependencies=[Depends(get_current_user)],
)

# Unlink provider
router.add_api_route(
    "/unlink/{provider}",
    auth_controller.unlink_provider,
    methods=["DELETE"],
    dependencies=[Depends(get_current_user)],
)

# OAuth login
router.add_api_route("/login/oauth", auth_controller.login_with_provider, methods=["POST"])


# Password reset
@router.post("/reset-password")
async def reset_password_endpoint(
    request: ResetPasswordRequest,
    x_reset_token: str = Header(None, alias="X-Reset-Token"),
    db: Session = Depends(get_db),
):
    """
    Reset admin password using reset token.

    The reset token can be found in Docker logs:
    ```
    docker logs $(docker ps -q -f label=localrun-app) | grep "RESET TOKEN"
    ```

    Example curl command:
    ```
    curl -X POST http://localhost:8000/auth/reset-password \\
      -H "Content-Type: application/json" \\
      -H "X-Reset-Token: YOUR_TOKEN_HERE" \\
      -d '{"new_password": "your_new_password"}'
    ```
    """
    if not x_reset_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Reset token required in X-Reset-Token header",
        )

    return await auth_controller.reset_password(
        new_password=request.new_password, reset_token=x_reset_token, db=db
    )
