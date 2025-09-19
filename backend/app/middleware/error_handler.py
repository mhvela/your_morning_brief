from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.logging import get_logger, get_request_id, set_request_id

logger = get_logger(__name__)


class ErrorResponse(BaseModel):
    """Standard error response format."""

    error: dict[str, str]


async def logging_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Middleware for request logging and timing."""
    # Set request ID for correlation
    request_id = set_request_id()

    # Log request start
    start_time = time.time()
    logger.info(
        f"{request.method} {request.url.path}",
        extra={
            "endpoint": f"{request.method} {request.url.path}",
            "request_id": request_id,
        },
    )

    # Process request
    response = await call_next(request)

    # Log response
    duration_ms = round((time.time() - start_time) * 1000, 2)
    logger.info(
        f"{request.method} {request.url.path} completed",
        extra={
            "endpoint": f"{request.method} {request.url.path}",
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "request_id": request_id,
        },
    )

    return response


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled errors."""
    request_id = get_request_id()

    # Log the error with full context
    logger.error(
        f"Unhandled exception in {request.method} {request.url.path}: {str(exc)}",
        extra={
            "endpoint": f"{request.method} {request.url.path}",
            "request_id": request_id,
        },
        exc_info=True,
    )

    # Return standardized error response
    error_response = ErrorResponse(
        error={
            "code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "request_id": request_id,
        }
    )

    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(),
    )


def setup_error_handling(app: FastAPI) -> None:
    """Configure error handling for the FastAPI application."""
    # Add logging middleware
    app.middleware("http")(logging_middleware)

    # Add global exception handler
    app.exception_handler(Exception)(global_exception_handler)
