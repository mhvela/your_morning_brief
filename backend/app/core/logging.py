from __future__ import annotations

import json
import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any

from app.core.config import settings

# Context variable for request ID tracking
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "component": record.name,
        }

        # Add request ID if available
        request_id = request_id_ctx.get("")
        if request_id:
            log_data["request_id"] = request_id

        # Add extra fields
        if hasattr(record, "endpoint"):
            log_data["endpoint"] = record.endpoint
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging() -> None:
    """Configure structured logging for the application."""
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler with structured formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredFormatter(datefmt="%Y-%m-%dT%H:%M:%S"))

    # Add handler to root logger
    root_logger.addHandler(console_handler)

    # Configure uvicorn loggers to use our formatting
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.access").propagate = True


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


def set_request_id(request_id: str | None = None) -> str:
    """Set request ID in context and return it."""
    if request_id is None:
        request_id = f"req_{uuid.uuid4().hex[:8]}"

    request_id_ctx.set(request_id)
    return request_id


def get_request_id() -> str:
    """Get current request ID from context."""
    return request_id_ctx.get("")
