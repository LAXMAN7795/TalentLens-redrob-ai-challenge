import logging
from typing import List, Tuple, Optional
from backend.core.schemas import CandidateProfile, JobDescription
from backend.data_ingestion.document_builder import DocumentBuilder
from backend.embeddings.embedder import CandidateEmbedder
from backend.embeddings.faiss_index import FAISSIndexManager

logger = logging.getLogger(__name__)

class CandidateRetriever:
    """
    Coordinates CandidateEmbedder and FAISSIndexManager.
    Handles indexing candidate profile structures and executing semantic search queries against JDs.
    """
    def __init__(self, embedder: Optional[CandidateEmbedder] = None, index_manager: Optional[FAISSIndexManager] = None):
        self.embedder = embedder or CandidateEmbedder()
        self.index_manager = index_manager or FAISSIndexManager(dimension=self.embedder.dimension)

    def _build_job_query_text(self, job_desc: JobDescription) -> str:
        """
        Builds a structured search-optimized query text from a JobDescription model.
        Aligns formatting directly with DocumentBuilder candidate passages.
        """
        query_parts = []
        query_parts.append(f"Job Title: {job_desc.title}")
        
        if job_desc.skills_required:
            query_parts.append(f"Required Skills & Technologies: {', '.join(job_desc.skills_required)}")
            
        if job_desc.experience_required_years is not None:
            query_parts.append(f"Experience Level Needed: {job_desc.experience_required_years} years")
            
        if job_desc.education_required:
            query_parts.append(f"Education Level Needed: {job_desc.education_required}")

        if job_desc.description:
            query_parts.append(f"Job Responsibilities & Role Details: {job_desc.description}")
            
        return "\n\n".join(query_parts)

    def index_candidates(self, candidates: List[CandidateProfile], batch_size: int = 64) -> None:
        """
        Converts CandidateProfile objects to text, generates BGE embeddings, and inserts them into the FAISS index.
        """
        if not candidates:
            return
            
        logger.info(f"Preparing to index {len(candidates)} candidates...")
        
        # Build text passages
        passages = [DocumentBuilder.build_candidate_document(cand) for cand in candidates]
        candidate_ids = [cand.candidate_id for cand in candidates]
        
        # Generate dense embeddings
        vectors = self.embedder.embed_passages(passages, batch_size=batch_size)
        
        # Ingest vectors to FAISS index
        self.index_manager.add_vectors(vectors, candidate_ids)
        logger.info(f"Successfully indexed {len(candidates)} candidates into vector index.")

    def retrieve(self, job_desc: JobDescription, k: int = 10) -> List[Tuple[str, float]]:
        """
        Queries the FAISS index with a semantic representation of the Job Description.
        Returns a list of (candidate_id, similarity_score) tuples representing the top matching candidates.
        """
        logger.info(f"Executing semantic retrieval for Job Title: '{job_desc.title}' (K={k})")
        
        # Build matching query text
        query_text = self._build_job_query_text(job_desc)
        
        # Generate query vector
        query_vector = self.embedder.embed_query(query_text)
        
        # Perform FAISS similarity search
        search_results = self.index_manager.search(query_vector, k=k)
        
        logger.info(f"Retrieval complete. Found {len(search_results)} semantic candidate matches.")
        return search_results
