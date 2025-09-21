import os
import sqlite3
import sys
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import Engine

# Ensure the local backend package is imported before any similarly named site-packages
TESTS_DIR = os.path.dirname(__file__)
BACKEND_ROOT = os.path.abspath(os.path.join(TESTS_DIR, ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)


# Ensure SQLite enforces foreign key constraints for tests
@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(
    dbapi_connection: Any, connection_record: Any
) -> None:  # noqa: D401
    """Enable foreign key checks in SQLite connections used by tests."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
