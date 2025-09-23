import os
from collections.abc import Generator
from contextlib import suppress

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base

# Resolve database URL with test override during pytest runs
_is_running_tests: bool = "PYTEST_CURRENT_TEST" in os.environ

# Prefer SQLite test database when running tests
if _is_running_tests:
    # Derive unique sqlite file per test to avoid cross-test contamination
    test_id = os.environ.get("PYTEST_CURRENT_TEST", "testdb").split("::")[-1]
    safe = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in test_id)
    database_url: str | URL = f"sqlite:///./.pytest_db_{safe}.db"
else:
    database_url = settings.database_url or URL.create(
        "postgresql",
        username=settings.postgres_user,
        password=settings.postgres_password,
        host=settings.postgres_host,
        port=int(settings.postgres_port) if settings.postgres_port else None,
        database=settings.postgres_db,
    )

_engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    echo=settings.database_echo,
)

_SessionMaker = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

_last_test_slug: str | None = None


def _maybe_switch_test_db() -> None:
    global _engine, _SessionMaker, _last_test_slug
    if not _is_running_tests:
        return
    nodeid_raw = os.environ.get("PYTEST_CURRENT_TEST", "testdb")
    # Normalize to be stable across test phases (setup/call/teardown)
    nodeid = nodeid_raw.split(" (")[0].strip()
    slug = "".join(
        c if c.isalnum() or c in ("-", "_", ":", "/") else "_" for c in nodeid
    )
    if slug == _last_test_slug:
        return
    # Build a unique sqlite file path per test node id
    safe = slug.replace("/", "_").replace(":", "_")
    filename = f".pytest_db_{safe}.db"
    new_url = f"sqlite:///./{filename}"
    # Reset existing DB file to ensure clean state per test
    with suppress(Exception):
        db_file_path = os.path.join(os.getcwd(), filename)
        if os.path.exists(db_file_path):
            os.remove(db_file_path)
    with suppress(Exception):
        _engine.dispose()
    _engine = create_engine(new_url, pool_pre_ping=True, echo=settings.database_echo)
    _SessionMaker.configure(bind=_engine)
    with suppress(Exception):
        Base.metadata.create_all(bind=_engine)
    _last_test_slug = slug


class _SessionFactory:
    def __call__(self) -> Session:
        _maybe_switch_test_db()
        return _SessionMaker()


SessionLocal = _SessionFactory()


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


# Ensure tables exist when running tests against SQLite file DB
if (
    _is_running_tests
    and isinstance(database_url, str)
    and database_url.startswith("sqlite")
):
    with suppress(Exception):
        Base.metadata.create_all(bind=_engine)
