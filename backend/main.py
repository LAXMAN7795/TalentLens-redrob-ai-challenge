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
