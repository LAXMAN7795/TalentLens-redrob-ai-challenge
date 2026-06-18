import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.core.config import settings

logger = logging.getLogger(__name__)

# Configure engine arguments based on DB driver
engine_kwargs = {}
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite requires check_same_thread=False for multi-threaded async frameworks like FastAPI
    engine_kwargs["connect_args"] = {"check_same_thread": False}

try:
    logger.info(f"Connecting to database using URL: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    engine = create_engine(settings.DATABASE_URL, **engine_kwargs)
    
    # Session factory config
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as exc:
    logger.critical(f"Failed to initialize database engine: {exc}")
    raise

# Base class for declarative SQLAlchemy models
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a scoped database session and closes it after completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    """
    Creates all defined database tables. Runs once during application startup.
    """
    try:
        logger.info("Initializing database schemas...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database schemas initialized successfully.")
    except Exception as exc:
        logger.error(f"Error initializing database schemas: {exc}")
        raise
