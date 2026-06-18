import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database.postgres import init_db
from backend.api.endpoints import jobs, candidates, rankings

# Setup logging formatting
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager that handles server startup routines,
    specifically creating database tables.
    """
    import os
    logger.info("================ DEPLOYMENT DIAGNOSTICS ================")
    logger.info(f"Current Working Directory: {os.getcwd()}")
    logger.info(f"Effective UID: {os.getuid() if hasattr(os, 'getuid') else 'N/A'}")
    logger.info(f"Effective GID: {os.getgid() if hasattr(os, 'getgid') else 'N/A'}")
    from backend.core.config import settings
    logger.info(f"DATABASE_URL Env: {settings.DATABASE_URL}")
    
    # Test writing to /tmp
    try:
        with open("/tmp/write_test.txt", "w") as f:
            f.write("test")
        logger.info("Test write to /tmp: SUCCESS")
    except Exception as e:
        logger.info(f"Test write to /tmp: FAILED - {e}")
        
    # Test writing to current directory
    try:
        with open("write_test.txt", "w") as f:
            f.write("test")
        logger.info("Test write to CWD: SUCCESS")
        if os.path.exists("write_test.txt"):
            os.remove("write_test.txt")
    except Exception as e:
        logger.info(f"Test write to CWD: FAILED - {e}")
    logger.info("========================================================")

    logger.info("Starting up TalentLens FastAPI Server...")
    try:
        init_db()
        logger.info("Startup sequence complete. Server is ready.")
    except Exception as exc:
        logger.critical(f"Server startup failed during DB initialization: {exc}")
        raise
    yield
    logger.info("Shutting down TalentLens FastAPI Server...")

app = FastAPI(
    title="TalentLens API",
    description="AI-Powered Candidate Semantic Search, Scoring, and Explanations Engine.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS middleware to connect smoothly with Vite/React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, swap with exact origin domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Mount endpoints under the /api prefix
app.include_router(jobs.router, prefix="/api")
app.include_router(candidates.router, prefix="/api")
app.include_router(rankings.router, prefix="/api")

@app.get("/")
def read_root():
    """
    Root endpoint verifying service health.
    """
    return {
        "status": "online",
        "service": "TalentLens Candidate Ranking Engine",
        "docs_url": "/docs"
    }
