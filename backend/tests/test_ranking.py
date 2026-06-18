import pytest
from backend.core.schemas import CandidateProfile, Experience, Education, JobDescription
from backend.ranking.honeypot_detector import HoneypotDetector
from backend.ranking.disqualifier import Disqualifier
from backend.ranking.skill_scorer import SkillScorer
from backend.ranking.career_scorer import CareerScorer
from backend.ranking.behavioral_scorer import BehavioralScorer
from backend.ranking.education_scorer import EducationScorer
from backend.ranking.composite_ranker import CompositeRanker

@pytest.fixture
def sample_job_description():
    return JobDescription(
        title="Senior Python Engineer",
        description="Build backend services, write APIs and lead software developers. PostgreSQL database design required.",
        skills_required=["Python", "FastAPI", "PostgreSQL", "AWS"],
        experience_required_years=5.0,
        education_required="Bachelor"
    )

def test_honeypot_detector():
    detector = HoneypotDetector(repeat_threshold=5, word_penalty_multiplier=2.0)
    
    # 1. Honest Candidate
    honest = CandidateProfile(
        candidate_id="h-01",
        name="Alice",
        summary="A clean professional developer who works with Python and databases."
    )
    assert detector.calculate_penalty(honest) == 0.0
    
    # 2. Cheater Candidate (keyword stuffing "fastapi" 10 times in summary)
    cheater = CandidateProfile(
        candidate_id="c-02",
        name="Bob Cheater",
        summary="FastAPI FastAPI FastAPI FastAPI FastAPI FastAPI FastAPI FastAPI FastAPI FastAPI"
    )
    # 10 repetitions - 5 threshold = 5 excess. 5 * 2.0 multiplier = 10.0 penalty.
    assert detector.calculate_penalty(cheater) == 10.0
    
    # 3. Calendar Anomaly (experience spanning > 55 years)
    time_traveler = CandidateProfile(
        candidate_id="c-03",
        name="Old Developer",
        experience=[
            Experience(company="OldCorp", title="COBOL Dev", start_date="1960", end_date="2021")  # 61 years
        ]
    )
    assert detector.calculate_penalty(time_traveler) == 25.0

def test_disqualifier(sample_job_description):
    disq = Disqualifier()
    
    # 1. Qualified Candidate
    qualified = CandidateProfile(
        candidate_id="q-01",
        name="Good Dev",
        experience=[
            Experience(company="CorpA", title="Developer", start_date="2018", end_date="Present")  # 8 years (if current is 2026)
        ],
        education=[
            Education(institution="Uni", degree="Bachelor's Degree")
        ]
    )
    assert disq.is_disqualified(qualified, sample_job_description) is False

    # 2. Under-experienced Candidate
    junior = CandidateProfile(
        candidate_id="j-02",
        name="Jr Dev",
        experience=[
            Experience(company="CorpB", title="Intern", start_date="2024", end_date="2025")  # 1 year
        ],
        education=[
            Education(institution="Uni", degree="Bachelor")
        ]
    )
    assert disq.is_disqualified(junior, sample_job_description) is True

    # 3. Under-educated Candidate
    no_degree = CandidateProfile(
        candidate_id="n-03",
        name="No Degree Dev",
        experience=[
            Experience(company="CorpC", title="Developer", start_date="2015", end_date="Present")  # 11 years
        ],
        education=[]  # Missing degree
    )
    assert disq.is_disqualified(no_degree, sample_job_description) is True

def test_skill_scorer(sample_job_description):
    scorer = SkillScorer()
    
    # 1. Full matches
    cand_full = CandidateProfile(
        candidate_id="s-01",
        name="Full Skill",
        skills=["Python", "FastAPI", "PostgreSQL", "AWS"]
    )
    assert scorer.score(cand_full, sample_job_description) == 100.0
    
    # 2. Mixed direct and contextual matches
    cand_mixed = CandidateProfile(
        candidate_id="s-02",
        name="Mixed Skill",
        skills=["Python", "PostgreSQL"],  # 2 direct matches
        summary="Experienced in writing APIs using FastAPI and deploying workloads on AWS."  # 2 contextual matches
    )
    # Direct = 2 * 1.0 = 2.0. Contextual = 2 * 0.5 = 1.0. Total weight = 3.0 out of 4 required.
    # Score = 3.0 / 4.0 = 75.0%
    assert scorer.score(cand_mixed, sample_job_description) == 75.0

def test_career_scorer():
    scorer = CareerScorer(target_tenure_years=3.0)
    
    # 1. Stable, progressing candidate
    stable_prog = CandidateProfile(
        candidate_id="car-01",
        name="Stable Prog",
        experience=[
            Experience(company="C1", title="Junior Engineer", start_date="2016", end_date="2019"),  # 3 yrs
            Experience(company="C2", title="Senior Architect", start_date="2019", end_date="2023")  # 4 yrs
        ]
    )
    # Average tenure = (3+4)/2 = 3.5 years (Tenure score = 100.0)
    # Progression: Junior -> Senior (value increases, progression score > 50)
    assert scorer.calculate_tenure_score(stable_prog) == 100.0
    assert scorer.calculate_progression_score(stable_prog) > 50.0
    assert scorer.score(stable_prog, None) > 75.0

    # 2. Job hopper
    hopper = CandidateProfile(
        candidate_id="car-02",
        name="Hopper",
        experience=[
            Experience(company="C1", title="Engineer", start_date="2020", end_date="2020"),  # 0 yrs
            Experience(company="C2", title="Engineer", start_date="2021", end_date="2021")   # 0 yrs
        ]
    )
    # Tenure score close to 0
    assert scorer.calculate_tenure_score(hopper) == 0.0

def test_behavioral_scorer():
    scorer = BehavioralScorer()
    
    cand_good = CandidateProfile(
        candidate_id="b-01",
        name="Leader",
        summary="A lead architect who collaborated with cross-functional teams to deliver cloud software. Communicated with stakeholders.",
        experience=[
            Experience(company="X", title="Manager", description="Managed developers and presented design reports.")
        ]
    )
    # Has leadership matches: 'lead', 'managed'
    # Has collaboration matches: 'collaborated', 'team'
    # Has execution matches: 'deliver', 'managed' (Wait: 'deliver' matches delivered, 'optimized', 'implemented')
    # Has communication matches: 'communicated', 'stakeholders', 'presented'
    score = scorer.score(cand_good, None)
    assert score >= 75.0  # Scores well across all behavioral parameters

def test_education_scorer(sample_job_description):
    scorer = EducationScorer()
    
    # 1. Exact match with high GPA boost
    edu_match = CandidateProfile(
        candidate_id="e-01",
        name="Smart BS",
        education=[
            Education(institution="A", degree="Bachelor of Science", gpa=3.9)
        ]
    )
    # Base: 100.0, Boost: 5.0 (capped at 100)
    assert scorer.score(edu_match, sample_job_description) == 100.0
    
    # 2. Under qualification
    edu_under = CandidateProfile(
        candidate_id="e-02",
        name="High School",
        education=[
            Education(institution="H", degree="High School Diploma")
        ]
    )
    # Tier 0, required Tier 1 -> Base: 50.0
    assert scorer.score(edu_under, sample_job_description) == 50.0

def test_composite_ranker(sample_job_description):
    ranker = CompositeRanker()
    
    # Define candidates
    c1 = CandidateProfile(
        candidate_id="cand-good",
        name="Perfect Candidate",
        skills=["Python", "FastAPI", "PostgreSQL", "AWS"],
        experience=[
            Experience(company="A", title="Senior Engineer", start_date="2018", end_date="2023", description="Led API delivery.")
        ],
        education=[
            Education(institution="U", degree="Bachelor of Science", gpa=3.9)
        ]
    )
    
    c2 = CandidateProfile(
        candidate_id="cand-cheater",
        name="Keyword Stuffer",
        skills=["Python", "FastAPI"],
        summary="Python Python Python Python Python Python Python Python Python Python Python Python Python Python Python", # stuffed
        experience=[
            Experience(company="B", title="Developer", start_date="2015", end_date="2022")
        ],
        education=[
            Education(institution="U", degree="Bachelor")
        ]
    )
    
    c3 = CandidateProfile(
        candidate_id="cand-disq",
        name="Under Experience",
        skills=["Python"],
        experience=[
            Experience(company="C", title="Developer", start_date="2024", end_date="2025") # 1 year
        ],
        education=[
            Education(institution="U", degree="Bachelor")
        ]
    )
    
    candidates = [
        (c1, 0.85),  # Candidate 1 semantic similarity
        (c2, 0.70),  # Candidate 2 semantic similarity
        (c3, 0.60)   # Candidate 3 semantic similarity
    ]
    
    # Rank candidates (keeping disqualified for visibility test)
    results_all = ranker.rank_candidates(candidates, sample_job_description, filter_disqualified=False)
    
    assert len(results_all) == 3
    # Check sorting: c1 should be top, c3 should be bottom (disqualified)
    assert results_all[0].candidate_id == "cand-good"
    assert results_all[2].candidate_id == "cand-disq"
    assert results_all[2].final_score == 0.0
    assert results_all[2].is_disqualified is True
    
    # Cheater should be penalized
    cheater_breakdown = [r for r in results_all if r.candidate_id == "cand-cheater"][0]
    assert cheater_breakdown.honeypot_penalty > 0.0
    
    # Rank candidates filtering disqualified
    results_filtered = ranker.rank_candidates(candidates, sample_job_description, filter_disqualified=True)
    assert len(results_filtered) == 2
    assert "cand-disq" not in [r.candidate_id for r in results_filtered]
