import json
import tempfile
import time
from pathlib import Path
import pytest

from backend.core.schemas import CandidateProfile
from backend.data_ingestion.loader import CandidateLoader
from backend.data_ingestion.parser import CandidateParser
from backend.data_ingestion.document_builder import DocumentBuilder

@pytest.fixture
def sample_jsonl_file():
    """Creates a temporary JSONL file representing raw candidates."""
    candidates = [
        {
            "id": "cand-001",
            "name": "Jane Doe",
            "email": "jane.doe@example.com",
            "phone": "+1-555-0199",
            "summary": "Experienced Python developer with a passion for building backend microservices.",
            "skills": ["Python", "FastAPI", "PostgreSQL"],
            "experience": [
                {
                    "company": "Tech Corp",
                    "title": "Software Engineer",
                    "start_date": "2022-01",
                    "end_date": "Present",
                    "description": "Building microservices using Python and FastAPI.",
                    "skills": "Python, FastAPI",
                    "location": "Remote"
                }
            ],
            "education": [
                {
                    "institution": "State University",
                    "degree": "Bachelor of Science",
                    "major": "Computer Science",
                    "gpa": "3.8/4.0"
                }
            ],
            "certifications": ["AWS Certified Solutions Architect"],
            "languages": "English, Spanish"
        },
        {
            "id": "cand-002",
            "name": "John Smith",
            "skills": [
                {"name": "Java"},
                {"name": "Spring Boot"}
            ],
            "experience": "invalid experience list format",  # invalid format, parser should handle and ignore
            "education": [
                {
                    "institution": "Community College",
                    "degree": "Associate Degree"
                }
            ]
        },
        {
            # completely empty candidate to test ID generation and fallbacks
        }
    ]
    
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".jsonl", encoding="utf-8") as temp_file:
        for item in candidates:
            temp_file.write(json.dumps(item) + "\n")
        temp_file_path = temp_file.name

    yield Path(temp_file_path)
    
    # Clean up
    try:
        Path(temp_file_path).unlink()
    except OSError:
        pass

def test_candidate_loader(sample_jsonl_file):
    """Verifies that the loader streams JSONL records line by line."""
    loader = CandidateLoader(sample_jsonl_file)
    records = list(loader.stream_raw_records())
    
    assert len(records) == 3
    assert records[0]["id"] == "cand-001"
    assert records[1]["name"] == "John Smith"
    assert "name" not in records[2]

def test_candidate_parser(sample_jsonl_file):
    """Verifies that the parser normalizes names, IDs, nested data and cleans corrupt fields."""
    loader = CandidateLoader(sample_jsonl_file)
    parser = CandidateParser()
    
    profiles = []
    for raw in loader.stream_raw_records():
        profile = parser.parse_candidate(raw)
        assert profile is not None
        assert isinstance(profile, CandidateProfile)
        profiles.append(profile)
        
    # Check Candidate 1 (Fully formatted)
    p1 = profiles[0]
    assert p1.candidate_id == "cand-001"
    assert p1.name == "Jane Doe"
    assert p1.email == "jane.doe@example.com"
    assert "Python" in p1.skills
    assert len(p1.experience) == 1
    assert p1.experience[0].company == "Tech Corp"
    assert p1.experience[0].skills == ["Python", "FastAPI"]
    assert len(p1.education) == 1
    assert p1.education[0].institution == "State University"
    assert p1.education[0].gpa == 3.8
    assert p1.certifications[0].name == "AWS Certified Solutions Architect"
    assert p1.languages == ["English", "Spanish"]

    # Check Candidate 2 (Partially missing/dirty data)
    p2 = profiles[1]
    assert p2.candidate_id == "cand-002"
    assert p2.name == "John Smith"
    assert p2.skills == ["Java", "Spring Boot"]  # Nested skill dictionaries normalized
    assert p2.experience == []  # Invalid string experience cleaned to empty list
    assert len(p2.education) == 1
    assert p2.education[0].institution == "Community College"
    assert p2.education[0].gpa is None

    # Check Candidate 3 (Completely empty fallback)
    p3 = profiles[2]
    assert p3.candidate_id.startswith("gen-")
    assert p3.name == "Unknown Candidate"
    assert p3.skills == []
    assert p3.experience == []
    assert p3.education == []

def test_document_builder(sample_jsonl_file):
    """Verifies that the document builder creates detailed text documents for embeddings."""
    loader = CandidateLoader(sample_jsonl_file)
    parser = CandidateParser()
    
    for raw in loader.stream_raw_records():
        profile = parser.parse_candidate(raw)
        doc = DocumentBuilder.build_candidate_document(profile)
        
        assert isinstance(doc, str)
        assert len(doc) > 0
        
        if profile.candidate_id == "cand-001":
            assert "Candidate Name: Jane Doe" in doc
            assert "Technical & Professional Skills: Python, FastAPI, PostgreSQL" in doc
            assert "Professional Experience:\n1. Software Engineer at Tech Corp" in doc
            assert "Building microservices using Python and FastAPI." in doc
            assert "[Skills used: Python, FastAPI]" in doc
            assert "GPA: 3.80" in doc
            assert "AWS Certified Solutions Architect" in doc
            assert "Languages: English, Spanish" in doc

def test_performance_benchmark():
    """Simulates loading, parsing, and formatting 1,000 records to check speed and stability."""
    candidate_template = {
        "id": "cand-benchmark",
        "name": "Alex Dev",
        "email": "alex.dev@example.com",
        "phone": "+1-555-9999",
        "summary": "Full stack engineer specializing in AI integrations and cloud architectures.",
        "skills": ["Python", "Docker", "AWS", "Kubernetes", "React", "Node.js", "SQL"],
        "experience": [
            {
                "company": "Big Tech Corp",
                "title": "Lead Software Architect",
                "start_date": "2020-03",
                "end_date": "Present",
                "description": "Orchestrating highly scalable deployments on AWS and Kubernetes. Led team of 10 developers.",
                "skills": "Python, Docker, AWS, Kubernetes"
            },
            {
                "company": "Startup Inc",
                "title": "Full Stack Developer",
                "start_date": "2017-06",
                "end_date": "2020-02",
                "description": "Developed dynamic interfaces using React and backend APIs using Node.js.",
                "skills": "React, Node.js, SQL"
            }
        ],
        "education": [
            {
                "institution": "Institute of Technology",
                "degree": "Master of Science",
                "major": "Computer Science",
                "gpa": "3.9"
            }
        ],
        "certifications": ["CKA", "AWS Professional Architect"]
    }
    
    num_records = 1000
    
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".jsonl", encoding="utf-8") as temp_file:
        for i in range(num_records):
            record = candidate_template.copy()
            record["id"] = f"cand-{i}"
            temp_file.write(json.dumps(record) + "\n")
        temp_file_path = temp_file.name

    try:
        loader = CandidateLoader(temp_file_path)
        parser = CandidateParser()
        
        start_time = time.time()
        
        count = 0
        for raw in loader.stream_raw_records():
            profile = parser.parse_candidate(raw)
            if profile:
                doc = DocumentBuilder.build_candidate_document(profile)
                count += 1
                
        elapsed_time = time.time() - start_time
        throughput = count / elapsed_time if elapsed_time > 0 else 0
        
        print(f"\nIngested & Processed {count} profiles in {elapsed_time:.4f} seconds.")
        print(f"Throughput: {throughput:.2f} profiles/second.")
        
        assert count == num_records
        # Target a very modest throughput of at least 500 profiles/sec for simple local parsing
        assert throughput > 500
        
    finally:
        try:
            Path(temp_file_path).unlink()
        except OSError:
            pass
