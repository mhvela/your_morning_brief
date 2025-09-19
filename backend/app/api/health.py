from __future__ import annotations

import platform
import subprocess
from datetime import datetime
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


class HealthResponse(BaseModel):
    status: Literal["ok"]


class ReadinessResponse(BaseModel):
    status: Literal["ready"]


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


@router.get("/readyz", response_model=ReadinessResponse, tags=["health"])
async def readiness_check() -> ReadinessResponse:
    """Readiness check indicating when app is ready to serve traffic.

    Currently returns ready immediately. In future milestones, this will
    check database and Redis connectivity.
    """
    logger.info("Readiness check requested")
    # TODO: Add database and Redis health checks in future milestones
    return ReadinessResponse(status="ready")


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
