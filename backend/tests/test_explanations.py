import pytest
from backend.core.schemas import CandidateProfile, Experience, Education, JobDescription, CandidateScoreBreakdown, CandidateExplanation
from backend.llm.groq_client import GroqClient
from backend.llm.explanation_generator import ExplanationGenerator

@pytest.fixture
def sample_candidate():
    return CandidateProfile(
        candidate_id="cand-expl-01",
        name="Sarah Connor",
        summary="Senior Backend Architect with 6 years experience coding high-performance Python services.",
        skills=["Python", "FastAPI", "Docker"],
        experience=[
            Experience(
                company="SkyNet Tech",
                title="Lead developer",
                start_date="2020",
                end_date="Present",
                description="Designed Python microservices and orchestrated containers with Docker."
            )
        ],
        education=[
            Education(institution="UC Berkeley", degree="Bachelor of Science")
        ]
    )

@pytest.fixture
def sample_jd():
    return JobDescription(
        title="Senior Python Architect",
        description="Looking for an engineer to architect Python systems and build FastAPI backend microservices.",
        skills_required=["Python", "FastAPI", "PostgreSQL", "Docker"]
    )

@pytest.fixture
def sample_breakdown():
    return CandidateScoreBreakdown(
        candidate_id="cand-expl-01",
        name="Sarah Connor",
        final_score=85.0,
        semantic_score=82.0,
        skill_score=75.0,
        career_score=90.0,
        behavioral_score=80.0,
        education_score=80.0,
        honeypot_penalty=0.0
    )

def test_explanation_generator_fallback(sample_candidate, sample_jd, sample_breakdown):
    """Tests explanation generation using the template-driven offline fallback."""
    generator = ExplanationGenerator(use_fallback=True)
    explanation = generator.generate_explanation(sample_candidate, sample_jd, sample_breakdown)
    
    assert isinstance(explanation, CandidateExplanation)
    assert explanation.candidate_id == "cand-expl-01"
    assert "Sarah Connor" in explanation.fit_summary
    assert len(explanation.strengths) > 0
    # Missing skill in JD was 'PostgreSQL' (since candidate has Python, FastAPI, Docker)
    # Check if fallback correctly identifies 'PostgreSQL' as a concern or interview question
    concerns_lower = [c.lower() for c in explanation.concerns]
    assert any("postgresql" in c for c in concerns_lower)
    assert any("postgresql" in q.lower() for q in explanation.interview_questions)

def test_explanation_generator_live(sample_candidate, sample_jd, sample_breakdown):
    """Tests explanation generation against the live Groq API."""
    try:
        client = GroqClient()
    except Exception as exc:
        pytest.skip(f"Skipping live Groq explanation test: client failed initialization: {exc}")
        return

    generator = ExplanationGenerator(groq_client=client)
    explanation = generator.generate_explanation(sample_candidate, sample_jd, sample_breakdown)
    
    assert isinstance(explanation, CandidateExplanation)
    assert explanation.candidate_id == "cand-expl-01"
    assert len(explanation.fit_summary) > 0
    assert len(explanation.strengths) > 0
    assert len(explanation.interview_questions) > 0
    
    print("\n[LIVE GROQ RECRUITER EXPLANATION CARD]:")
    print(explanation.model_dump_json(indent=2))
