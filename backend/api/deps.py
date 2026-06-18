from sqlalchemy.orm import Session
from fastapi import Depends
from backend.database.postgres import get_db

# Common dependency injection hooks
def get_database_session(db: Session = Depends(get_db)) -> Session:
    """
    FastAPI dependency that provides a scoped database session.
    """
    return db
