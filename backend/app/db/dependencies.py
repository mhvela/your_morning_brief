from fastapi import Depends

from .session import get_db

# FastAPI dependency for database session
DatabaseDep = Depends(get_db)
