import logging
from typing import Any, Dict

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from core.logger import setup_logger

logger = setup_logger(__name__)


class Handler:
    """Centralized exception handler."""

    @staticmethod
    async def handle_exception(request: Request, exc: Exception) -> JSONResponse:
        """
        Handle generic exceptions.

        Args:
            request: FastAPI request
            exc: Exception raised

        Returns:
            JSONResponse with error details
        """
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
            },
        )

    @staticmethod
    async def handle_api_exception(request: Request, exc: HTTPException) -> JSONResponse:
        """
        Handle HTTPException from FastAPI.

        Args:
            request: FastAPI request
            exc: HTTPException raised

        Returns:
            JSONResponse with error details
        """
        logger.warning(
            f"HTTP exception: {exc.status_code} - {exc.detail} | "
            f"{request.method} {request.url.path}"
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
            },
        )

    @staticmethod
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        """
        Handle request validation errors.

        Args:
            request: FastAPI request
            exc: RequestValidationError from Pydantic

        Returns:
            JSONResponse with field-level error details
        """
        # Format validation errors
        errors: Dict[str, Any] = {}
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            errors[field] = error["msg"]

        logger.warning(f"Validation error: {errors}")

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Validation error",
                "errors": errors,
            },
        )
