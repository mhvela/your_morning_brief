from __future__ import annotations

import os
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: Literal["ok"]


class VersionResponse(BaseModel):
    version: str


@router.get("/healthz", response_model=HealthResponse, tags=["health"])
def healthcheck() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/readyz", response_model=HealthResponse, tags=["health"])
def readycheck() -> HealthResponse:
    # For now, simply return ok. Later can check DB/Redis connections.
    return HealthResponse(status="ok")


@router.get("/version", response_model=VersionResponse, tags=["health"])
def version() -> VersionResponse:
    return VersionResponse(version=os.getenv("APP_VERSION", "0.1.0"))
