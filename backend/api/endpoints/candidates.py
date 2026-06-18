import os
import shutil
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session

from backend.api.deps import get_database_session
from backend.database.models import JobDescriptionModel
from backend.data_ingestion.pipeline import IngestionPipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/candidates", tags=["Candidates"])

# Thread-safe global in-memory state tracker for pipeline progress
pipeline_tracker: Dict[str, Any] = {
    "status": "idle",
    "job_id": None,
    "error_message": None,
    "elapsed_time_sec": 0.0,
    "last_run_timestamp": None
}

def execute_pipeline_task(
    temp_file_path: str,
    job_id: int,
    batch_size: int,
    retrieve_k: int,
    explain_top_n: int,
    limit: Optional[int]
) -> None:
    """
    Background worker function that executes the ingestion and scoring pipeline.
    Instantiates its own session since it runs in a background thread.
    """
    global pipeline_tracker
    pipeline_tracker["status"] = "processing"
    pipeline_tracker["job_id"] = job_id
    pipeline_tracker["error_message"] = None
    
    start_time = time.time()
    logger.info(f"Background worker starting pipeline ingestion for Job ID: {job_id} using file: {temp_file_path}")
    
    try:
        from backend.database.postgres import SessionLocal
        db = SessionLocal()
        
        try:
            job_record = db.query(JobDescriptionModel).filter_by(id=job_id).first()
            if not job_record:
                raise ValueError(f"Job Description with ID {job_id} was not found in the database.")
                
            pipeline = IngestionPipeline()
            pipeline.run_pipeline(
                jd_title=job_record.title,
                jd_raw_desc=job_record.description,
                jsonl_path=temp_file_path,
                db=db,
                job_id=job_id,
                batch_size=batch_size,
                retrieve_k=retrieve_k,
                explain_top_n=explain_top_n,
                limit=limit
            )
            pipeline_tracker["status"] = "completed"
            logger.info("Background pipeline worker completed successfully.")
        finally:
            db.close()
            
    except Exception as exc:
        logger.error(f"Error encountered in background pipeline task: {exc}")
        pipeline_tracker["status"] = "failed"
        pipeline_tracker["error_message"] = str(exc)
    finally:
        pipeline_tracker["elapsed_time_sec"] = round(time.time() - start_time, 2)
        pipeline_tracker["last_run_timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Cleanup uploaded temp file
        try:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                logger.info(f"Cleaned up temp upload file: {temp_file_path}")
        except OSError as cleanup_exc:
            logger.error(f"Failed to delete temp file {temp_file_path}: {cleanup_exc}")

@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
def upload_candidates_dataset(
    background_tasks: BackgroundTasks,
    job_id: int,
    file: UploadFile = File(...),
    batch_size: int = 100,
    retrieve_k: int = 100,
    explain_top_n: int = 10,
    limit: Optional[int] = None,
    db: Session = Depends(get_database_session)
):
    """
    Uploads a candidate profiles dataset file (JSONL format) and launches
    the scoring, embedding, and rankings pipeline as an asynchronous background task.
    """
    global pipeline_tracker
    
    # Do not allow parallel executions to prevent SQLite locking or FAISS index corruption
    if pipeline_tracker["status"] == "processing":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A ranking pipeline is currently running. Please wait until it completes."
        )

    # Validate that Job ID exists
    job_exists = db.query(JobDescriptionModel).filter_by(id=job_id).first()
    if not job_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job Description with ID {job_id} does not exist."
        )

    # Save UploadFile stream to a temp file in outputs directory to limit RAM usage
    outputs_dir = Path(__file__).resolve().parent.parent.parent / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    temp_filename = f"upload_{int(time.time())}_{file.filename}"
    temp_filepath = outputs_dir / temp_filename

    try:
        logger.info(f"Streaming uploaded candidate file to disk: {temp_filepath}")
        with open(temp_filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as exc:
        logger.error(f"Failed to write uploaded file to disk: {exc}")
        if temp_filepath.exists():
            temp_filepath.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload dataset: {str(exc)}"
        )
        
    # Queue execution
    background_tasks.add_task(
        execute_pipeline_task,
        temp_file_path=str(temp_filepath),
        job_id=job_id,
        batch_size=batch_size,
        retrieve_k=retrieve_k,
        explain_top_n=explain_top_n,
        limit=limit
    )
    
    # Initialize progress tracker
    pipeline_tracker["status"] = "processing"
    pipeline_tracker["job_id"] = job_id
    pipeline_tracker["error_message"] = None
    
    return {
        "message": "Dataset upload accepted. Ranking pipeline running in background.",
        "job_id": job_id,
        "filename": file.filename,
        "status_url": "/api/candidates/status"
    }

@router.get("/status")
def get_pipeline_status():
    """
    Polls the active pipeline progress.
    """
    return pipeline_tracker
