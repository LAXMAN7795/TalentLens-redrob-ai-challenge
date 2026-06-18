import json
import tempfile
from pathlib import Path
import pytest
from sqlalchemy.orm import Session

from backend.database.postgres import SessionLocal, init_db, Base, engine
from backend.database.models import JobDescriptionModel, CandidateModel, RankingModel
from backend.data_ingestion.pipeline import IngestionPipeline

@pytest.fixture(scope="module")
def setup_database():
    """Initializes the database schema for testing, dropping it after run."""
    # Runs init_db to create all tables
    init_db()
    yield
    # Clean up and drop all tables
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def mock_candidates_jsonl():
    """Generates 15 mock candidate profiles for testing the pipeline in chunks."""
    candidates = [
        # 1. Strong Python Dev (Should Rank First)
        {
            "id": f"p-{i}",
            "name": f"Python Engineer {i}",
            "email": f"py_{i}@example.com",
            "summary": "Experienced Software Engineer. Deep expertise in backend services with Python, FastAPI, and Docker. Stable 4 year tenure.",
            "skills": ["Python", "FastAPI", "Docker", "AWS"],
            "experience": [
                {
                    "company": "TechCorp",
                    "title": "Software Developer",
                    "start_date": "2022-01",
                    "end_date": "Present",
                    "description": "Built backend APIs using Python and FastAPI."
                }
            ],
            "education": [
                {
                    "institution": "State College",
                    "degree": "Bachelor of Science",
                    "gpa": 3.8
                }
            ]
        } for i in range(1, 6)
    ] + [
        # 2. Marketing (Low similarity, shouldn't qualify high)
        {
            "id": f"m-{i}",
            "name": f"Marketing Consultant {i}",
            "email": f"mkt_{i}@example.com",
            "summary": "Digital marketing and social media copywriter. Expertise in SEO optimization and lead generation.",
            "skills": ["SEO", "Copywriting", "Marketing"],
            "experience": [
                {
                    "company": "BrandAgency",
                    "title": "Ad Lead",
                    "start_date": "2023-01",
                    "end_date": "2024-12",
                    "description": "Handled SEO campaigns."
                }
            ],
            "education": [
                {
                    "institution": "State College",
                    "degree": "Bachelor of Arts"
                }
            ]
        } for i in range(1, 6)
    ] + [
        # 3. Junior Developer (Under-experienced, should be disqualified)
        {
            "id": f"j-{i}",
            "name": f"Junior Developer {i}",
            "email": f"jr_{i}@example.com",
            "summary": "Junior programmer studying Python and writing simple scripts.",
            "skills": ["Python"],
            "experience": [
                {
                    "company": "Startup",
                    "title": "Intern",
                    "start_date": "2025-01",
                    "end_date": "2025-06"
                }
            ],
            "education": [
                {
                    "institution": "State College",
                    "degree": "Bachelor of Science"
                }
            ]
        } for i in range(1, 6)
    ]

    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".jsonl", encoding="utf-8") as temp_file:
        for item in candidates:
            temp_file.write(json.dumps(item) + "\n")
        temp_file_path = temp_file.name

    yield Path(temp_file_path)
    
    try:
        Path(temp_file_path).unlink()
    except OSError:
        pass

def test_pipeline_execution_and_persistence(setup_database, mock_candidates_jsonl):
    """Runs end-to-end pipeline ingestion, scoring, committed DB validation, and CSV verification."""
    db: Session = SessionLocal()
    
    # Target Job Description criteria
    jd_title = "Senior Python Developer"
    jd_desc = "Looking for a Software Engineer to develop backend APIs using Python, FastAPI and Docker. Needs 4+ years of experience."
    
    # Load pipeline
    pipeline = IngestionPipeline()
    
    # Run the pipeline (Total: 15 candidates. We set batch_size=5, retrieve_k=10, explain_top_n=3)
    jd_model, rankings = pipeline.run_pipeline(
        jd_title=jd_title,
        jd_raw_desc=jd_desc,
        jsonl_path=mock_candidates_jsonl,
        db=db,
        batch_size=5,
        retrieve_k=10,
        explain_top_n=3,
        output_csv_name="test_ranked_submission.csv"
    )
    
    try:
        # 1. Verify JobDescription saved to database
        assert jd_model.id is not None
        jd_db = db.query(JobDescriptionModel).filter_by(id=jd_model.id).first()
        assert jd_db is not None
        assert jd_db.title == "Senior Python Developer"
        assert "Python" in jd_db.skills_required
        assert jd_db.experience_required_years == 4.0

        # 2. Verify Candidates saved to database
        candidates_db = db.query(CandidateModel).all()
        # Verify we parsed and saved all 15 candidates
        assert len(candidates_db) == 15

        # 3. Verify Rankings saved to database
        rankings_db = db.query(RankingModel).filter_by(job_description_id=jd_db.id).all()
        # FAISS retrieved k=10 candidates, so we should have exactly 10 ranking scores committed
        assert len(rankings_db) == 10
        
        # Verify sorting: Top ranked item should be a Python candidate
        rankings_db.sort(key=lambda x: x.final_score, reverse=True)
        top_rank = rankings_db[0]
        assert top_rank.candidate_id.startswith("p-")
        assert top_rank.final_score > 70.0
        assert top_rank.is_disqualified is False
        assert len(top_rank.strengths) > 0

        # Verify disqualified candidates (junior profiles should have 0 score and is_disqualified = True)
        disq_rankings = [r for r in rankings_db if r.candidate_id.startswith("j-")]
        for dr in disq_rankings:
            assert dr.is_disqualified is True
            assert dr.final_score == 0.0

        # 4. Verify CSV File Export
        csv_path = Path(__file__).resolve().parent.parent / "outputs" / "test_ranked_submission.csv"
        assert csv_path.exists()
        
        # Check CSV content structure
        with open(csv_path, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            rows = list(reader)
            # 1 header row + 10 ranked candidate rows = 11 rows
            assert len(rows) == 11
            assert rows[0][0] == "rank"
            assert rows[0][1] == "candidate_id"
            assert rows[0][3] == "final_score"

    finally:
        db.close()
        
        # Clean CSV file
        try:
            csv_path = Path(__file__).resolve().parent.parent / "outputs" / "test_ranked_submission.csv"
            if csv_path.exists():
                csv_path.unlink()
        except OSError:
            pass

# Import csv here for the test helper
import csv
