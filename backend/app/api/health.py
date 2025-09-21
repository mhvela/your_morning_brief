from __future__ import annotations

import platform
import subprocess
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import get_db

logger = get_logger(__name__)
router = APIRouter()


class HealthResponse(BaseModel):
    status: Literal["ok"]


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    database: Literal["connected", "disconnected"] = "connected"
    version: str


class VersionResponse(BaseModel):
    version: str
    build_date: str
    commit_hash: str
    python_version: str


def get_commit_hash() -> str:
    """Get current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()[:8]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return "unknown"


@router.get("/healthz", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    """Basic liveness check for load balancers/orchestrators.

    Returns OK if the application is running. No dependencies checked.
    """
    logger.info("Health check requested")
    return HealthResponse(status="ok")


@router.get("/readyz", tags=["health"])
async def readiness_check(db: Session = Depends(get_db)):  # noqa: B008
    """Readiness check indicating when app is ready to serve traffic.

    Includes database connectivity check.
    """
    logger.info("Readiness check requested")

    try:
        # Check database connection
        db.execute(text("SELECT 1"))
        db.commit()

        return ReadinessResponse(
            status="ready", database="connected", version=settings.version
        )
    except Exception as e:
        logger.error(f"Database connection failed: {e}")

        error_message = (
            str(e) if settings.log_level == "DEBUG" else "Database connection failed"
        )

        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "database": "disconnected",
                "version": settings.version,
                "error": error_message,
            },
        )


@router.get("/version", response_model=VersionResponse, tags=["health"])
async def version_info() -> VersionResponse:
    """Version information for deployment tracking and debugging."""
    logger.info("Version info requested")

    # Get build info
    build_date = settings.build_date or datetime.utcnow().isoformat() + "Z"
    commit_hash = settings.commit_hash or get_commit_hash()
    python_version = settings.python_version or platform.python_version()

    return VersionResponse(
        version=settings.version,
        build_date=build_date,
        commit_hash=commit_hash,
        python_version=python_version,
    )
