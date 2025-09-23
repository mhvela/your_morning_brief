from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.middleware.error_handler import setup_error_handling

# Setup logging as early as possible
setup_logging()
logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.version,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Setup error handling and logging middleware
    setup_error_handling(app)

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health_router)

    # Log application startup
    logger.info("Application startup complete", extra={"component": "main"})

    return app


app = create_app()


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    logger.info(f"Starting server on {settings.api_host}:{settings.api_port}")
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_config=None,  # Use our custom logging
    )
