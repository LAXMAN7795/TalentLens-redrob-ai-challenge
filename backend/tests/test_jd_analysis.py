import pytest
from backend.core.schemas import JobDescription
from backend.jd_analysis.jd_parser import JobDescriptionParser
from backend.jd_analysis.jd_extractor import JobDescriptionExtractor
from backend.llm.groq_client import GroqClient

SAMPLE_JD_TEXT = """
We are looking for a Senior Software Engineer (Python) to join our team.

Responsibilities:
- Build high-performance backend microservices.
- Design database schemas and optimize SQL queries.
- Deploy applications to cloud environments.

Requirements:
- 5+ years of software development experience with Python.
- Practical experience with FastAPI or Flask.
- Strong knowledge of PostgreSQL databases.
- Hands-on experience with Docker and AWS.
- Minimum Bachelor's degree in Computer Science or related field.

Other details:
- This is a fully Remote position.
- Department: Engineering
"""

def test_jd_parser():
    """Tests basic JD cleaning and parsing of fields."""
    parser = JobDescriptionParser()
    cleaned = parser.clean_text("Line 1\n\n\nLine 2\n  \nLine 3  ")
    assert cleaned == "Line 1\nLine 2\nLine 3"

    jd = parser.parse_raw(
        title="Python Developer",
        description="Write clean code.",
        department="Engineering",
        location="Remote",
        experience_required_years="3",
        skills_required="Python, FastAPI, Docker"
    )
    assert jd.title == "Python Developer"
    assert jd.experience_required_years == 3.0
    assert jd.skills_required == ["Python", "FastAPI", "Docker"]
    assert jd.location == "Remote"

def test_jd_extractor_fallback():
    """Tests the regex-based fallback extraction of JD details."""
    extractor = JobDescriptionExtractor(use_fallback=True)
    jd = extractor.extract_job_details("Senior Software Engineer", SAMPLE_JD_TEXT)
    
    assert isinstance(jd, JobDescription)
    assert jd.title == "Senior Software Engineer"
    assert jd.experience_required_years == 5.0
    assert jd.education_required == "Bachelor"
    assert jd.location == "Remote"
    # Fallback lists should have some identified matching skills from SAMPLE_JD_TEXT
    skills_lower = [s.lower() for s in jd.skills_required]
    assert "python" in skills_lower
    assert "fastapi" in skills_lower
    assert "postgresql" in skills_lower

def test_jd_extractor_live():
    """Tests the live Groq LLM extraction. Requires valid GROQ_API_KEY in .env."""
    try:
        client = GroqClient()
    except Exception as exc:
        pytest.skip(f"Skipping live Groq test because client initialization failed: {exc}")
        return

    extractor = JobDescriptionExtractor(groq_client=client)
    jd = extractor.extract_job_details("Senior Software Engineer", SAMPLE_JD_TEXT)
    
    assert isinstance(jd, JobDescription)
    assert jd.title == "Senior Software Engineer"
    assert jd.experience_required_years == 5.0
    assert jd.education_required is not None
    assert "bachelor" in jd.education_required.lower()
    assert jd.location == "Remote"
    assert jd.department == "Engineering"
    
    # The LLM should extract Python, FastAPI, and PostgreSQL into the skills list
    skills_lower = [s.lower() for s in jd.skills_required]
    assert "python" in skills_lower
    assert "fastapi" in skills_lower
    assert "postgresql" in skills_lower
    
    print("\n[LIVE GROQ TEST SUCCESSFUL] Extracted Job Details:")
    print(jd.model_dump_json(indent=2))
