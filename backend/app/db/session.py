from collections.abc import Generator

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Resolve database URL with a fallback to a valid DSN string
database_url: str | URL = settings.database_url or URL.create(
    "postgresql",
    username=settings.postgres_user,
    password=settings.postgres_password,
    host=settings.postgres_host,
    port=int(settings.postgres_port) if settings.postgres_port else None,
    database=settings.postgres_db,
)

# Create engine with connection pooling
engine = create_engine(
    database_url,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    echo=settings.database_echo,  # Log SQL statements in debug mode
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    Ensures proper cleanup after request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
