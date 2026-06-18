import tempfile
from pathlib import Path
import numpy as np
import pytest

from backend.core.schemas import CandidateProfile, Experience, Education, JobDescription
from backend.embeddings.embedder import CandidateEmbedder
from backend.embeddings.faiss_index import FAISSIndexManager
from backend.embeddings.retriever import CandidateRetriever

@pytest.fixture(scope="module")
def embedder():
    """Shared CandidateEmbedder instance for module testing."""
    return CandidateEmbedder()

def test_embedder_dimension_and_normalization(embedder):
    """Verifies that the embedder outputs normalized vectors of exactly 1024 dimensions."""
    texts = ["I am a Python engineer.", "React frontend developer specializing in CSS."]
    vectors = embedder.embed_passages(texts)
    
    assert vectors.shape == (2, 1024)
    # Check L2 normalization (norm should be extremely close to 1.0)
    for vec in vectors:
        norm = np.linalg.norm(vec)
        assert pytest.approx(norm, rel=1e-5) == 1.0

def test_embedder_query_prefix(embedder):
    """Verifies query vector embedding generation and normalization."""
    query = "Python developer"
    query_vec = embedder.embed_query(query)
    
    assert query_vec.shape == (1024,)
    assert pytest.approx(np.linalg.norm(query_vec), rel=1e-5) == 1.0

def test_faiss_index_lifecycle():
    """Verifies FAISSIndexManager adds vectors, searches, saves, and loads mapping correctly."""
    manager = FAISSIndexManager(dimension=4)
    
    # Create normalized vectors
    v1 = np.array([1, 0, 0, 0], dtype=np.float32)
    v2 = np.array([0, 1, 0, 0], dtype=np.float32)
    vectors = np.stack([v1, v2])
    ids = ["id-1", "id-2"]
    
    manager.add_vectors(vectors, ids)
    assert manager.index.ntotal == 2
    
    # Query matching v1
    results = manager.search(np.array([1, 0, 0, 0], dtype=np.float32), k=1)
    assert len(results) == 1
    assert results[0][0] == "id-1"
    assert results[0][1] == 1.0  # Cosine similarity matching perfectly
    
    # Persistence test
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as temp_file:
        temp_path = Path(temp_file.name)
        
    try:
        manager.save(temp_path)
        
        # Load in a new manager
        new_manager = FAISSIndexManager(dimension=4)
        new_manager.load(temp_path)
        
        assert new_manager.index.ntotal == 2
        new_results = new_manager.search(np.array([0, 1, 0, 0], dtype=np.float32), k=1)
        assert len(new_results) == 1
        assert new_results[0][0] == "id-2"
        assert new_results[0][1] == 1.0
        
    finally:
        # Clean files
        try:
            temp_path.unlink()
            temp_path.with_suffix(".mapping.json").unlink()
        except OSError:
            pass

def test_candidate_retriever_semantic_match(embedder):
    """Verifies that retriever scores a relevant candidate significantly higher than an irrelevant one."""
    retriever = CandidateRetriever(embedder=embedder)
    
    # Mock candidates
    cand_python = CandidateProfile(
        candidate_id="cand-py-01",
        name="Alice Dev",
        summary="Backend Software Architect with deep experience in Python, FastAPI, and PostgreSQL databases.",
        skills=["Python", "FastAPI", "PostgreSQL", "SQL"],
        experience=[
            Experience(
                company="DataTech",
                title="Python Backend Developer",
                description="Designed high performance API services using FastAPI and optimized raw SQL schemas in PostgreSQL."
            )
        ]
    )
    
    cand_marketing = CandidateProfile(
        candidate_id="cand-mkt-02",
        name="Bob Marketer",
        summary="Digital marketing manager specializing in SEO copywriting, Google Ads, and brand campaigns.",
        skills=["SEO", "Copywriting", "Marketing", "Google Ads"],
        experience=[
            Experience(
                company="BrandCorp",
                title="SEO Lead",
                description="Managed digital copy and improved organic website traffic through SEO techniques."
            )
        ]
    )
    
    # Index candidates
    retriever.index_candidates([cand_python, cand_marketing])
    
    # Define Job Description matching candidate A
    jd = JobDescription(
        title="FastAPI Backend Engineer",
        description="Looking for a Python developer to build backend APIs with FastAPI and manage PostgreSQL database systems.",
        skills_required=["Python", "FastAPI", "PostgreSQL"]
    )
    
    # Retrieve
    results = retriever.retrieve(jd, k=2)
    
    assert len(results) == 2
    # Relevant candidate should be first
    assert results[0][0] == "cand-py-01"
    assert results[1][0] == "cand-mkt-02"
    
    # Semantic match score should be higher than irrelevant score
    score_py = results[0][1]
    score_mkt = results[1][1]
    assert score_py > score_mkt
    print(f"\n[SEMANTIC RETRIEVAL MATCH]: Python score = {score_py:.4f}, Marketing score = {score_mkt:.4f}")
