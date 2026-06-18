import json
import tempfile
import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.database.postgres import Base, engine

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Wipes test database tables before running API integration checks."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_api_health():
    """Verifies that the root health check is online."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_job_description_endpoints():
    """Verifies posting a JD triggers LLM parsing, saves criteria, and retrieves detail list."""
    # 1. Post a new Job Description
    payload = {
        "title": "FastAPI Architect",
        "description": "Requires 3+ years experience building APIs with FastAPI, Python, PostgreSQL, and Docker. Remote position."
    }
    response = client.post("/api/jobs", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["id"] is not None
    assert data["title"] == "FastAPI Architect"
    skills_lower = [s.lower() for s in data["skills_required"]]
    assert "fastapi" in skills_lower
    assert data["experience_required_years"] == 3.0
    assert data["location"] == "Remote"

    # 2. Get JD list
    list_response = client.get("/api/jobs")
    assert list_response.status_code == 200
    assert len(list_response.json()) >= 1
    assert list_response.json()[0]["id"] == data["id"]

    # 3. Get JD detail
    detail_response = client.get(f"/api/jobs/{data['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["title"] == "FastAPI Architect"

def test_candidate_upload_and_ranking_flow():
    """Simulates creating a job, uploading JSONL records, polling status, and loading leaderboards."""
    # 1. Create a job first
    job_response = client.post("/api/jobs", json={
        "title": "Python Developer",
        "description": "Looking for a Python Developer with 2+ years experience. Skills: Python, FastAPI."
    })
    job_id = job_response.json()["id"]

    # 2. Create mock JSONL file
    candidates = [
        {
            "id": "api-cand-1",
            "name": "Sarah Connor",
            "summary": "Experienced python developer building microservices with FastAPI. Stable tenure of 3 years.",
            "skills": ["Python", "FastAPI"],
            "experience": [
                {
                    "company": "SkyNet",
                    "title": "Engineer",
                    "start_date": "2022",
                    "end_date": "Present"
                }
            ],
            "education": [
                {
                    "institution": "Berkeley",
                    "degree": "Bachelor"
                }
            ]
        },
        {
            "id": "api-cand-2",
            "name": "Bob SEO",
            "summary": "SEO marketing copywriter and strategist.",
            "skills": ["SEO", "Marketing"],
            "experience": [
                {
                    "company": "BrandCorp",
                    "title": "Lead",
                    "start_date": "2024",
                    "end_date": "2025"
                }
            ]
        }
    ]

    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".jsonl", encoding="utf-8") as temp_file:
        for item in candidates:
            temp_file.write(json.dumps(item) + "\n")
        temp_file_path = temp_file.name

    try:
        # 3. Upload dataset using multipart form-data
        with open(temp_file_path, "rb") as file_stream:
            upload_response = client.post(
                f"/api/candidates/upload?job_id={job_id}&batch_size=5&retrieve_k=10&explain_top_n=2&limit=5",
                files={"file": (Path(temp_file_path).name, file_stream, "application/octet-stream")}
            )
            
        assert upload_response.status_code == 202
        assert "Ranking pipeline running in background" in upload_response.json()["message"]

        # 4. Poll status until completed (max 15 attempts)
        for _ in range(15):
            status_response = client.get("/api/candidates/status")
            status_data = status_response.json()
            if status_data["status"] in ["completed", "failed"]:
                break
            time.sleep(1)
            
        assert status_data["status"] == "completed", f"Pipeline failed with error: {status_data['error_message']}"

        # 5. Fetch leaderboard
        leaderboard_response = client.get(f"/api/rankings/{job_id}?filter_disqualified=false")
        assert leaderboard_response.status_code == 200
        
        ranked_list = leaderboard_response.json()
        assert len(ranked_list) == 2
        # Sarah Connor (Python) should rank higher than Bob SEO (Marketing)
        assert ranked_list[0]["candidate_id"] == "api-cand-1"
        assert ranked_list[1]["candidate_id"] == "api-cand-2"
        assert ranked_list[0]["final_score"] > ranked_list[1]["final_score"]

        # 6. Fetch candidate detail card
        detail_response = client.get(f"/api/rankings/{job_id}/candidate/api-cand-1")
        assert detail_response.status_code == 200
        
        card = detail_response.json()
        assert card["name"] == "Sarah Connor"
        assert len(card["strengths"]) > 0
        assert len(card["interview_questions"]) > 0

    finally:
        try:
            Path(temp_file_path).unlink()
        except OSError:
            pass
