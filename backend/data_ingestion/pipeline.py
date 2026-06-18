import csv
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

from sqlalchemy.orm import Session

from backend.core.schemas import JobDescription, CandidateProfile, CandidateScoreBreakdown
from backend.database.models import JobDescriptionModel, CandidateModel, RankingModel
from backend.data_ingestion.loader import CandidateLoader
from backend.data_ingestion.parser import CandidateParser
from backend.data_ingestion.document_builder import DocumentBuilder
from backend.jd_analysis.jd_extractor import JobDescriptionExtractor
from backend.embeddings.embedder import CandidateEmbedder
from backend.embeddings.faiss_index import FAISSIndexManager
from backend.embeddings.retriever import CandidateRetriever
from backend.ranking.composite_ranker import CompositeRanker
from backend.llm.explanation_generator import ExplanationGenerator

logger = logging.getLogger(__name__)

class IngestionPipeline:
    """
    Orchestrates the end-to-end ingestion, indexing, ranking, and explanation pipeline.
    Streams large JSONL datasets in batches to ensure O(1) memory overhead.
    """
    def __init__(
        self,
        extractor: Optional[JobDescriptionExtractor] = None,
        retriever: Optional[CandidateRetriever] = None,
        ranker: Optional[CompositeRanker] = None,
        explainer: Optional[ExplanationGenerator] = None
    ):
        self.extractor = extractor or JobDescriptionExtractor()
        self.retriever = retriever or CandidateRetriever()
        self.ranker = ranker or CompositeRanker()
        self.explainer = explainer or ExplanationGenerator()
        self.parser = CandidateParser()

    def run_pipeline(
        self,
        jd_title: str,
        jd_raw_desc: str,
        jsonl_path: Union[str, Path],
        db: Session,
        job_id: Optional[int] = None,
        batch_size: int = 100,
        retrieve_k: int = 100,
        explain_top_n: int = 10,
        limit: Optional[int] = None,
        output_csv_name: str = "ranked_submission.csv"
    ) -> Tuple[JobDescriptionModel, List[RankingModel]]:
        """
        Executes the full data pipeline.
        
        Args:
            jd_title: The raw target job title.
            jd_raw_desc: The raw unstructured job description text.
            jsonl_path: Path to the candidate profiles JSONL file.
            db: Database session.
            job_id: Optional existing Job Description database ID.
            batch_size: Ingestion batch chunk size.
            retrieve_k: Number of candidates to retrieve semantically and score.
            explain_top_n: Number of top candidates to generate live LLM explanations for.
            limit: If set, limits candidates read for fast pipeline testing.
            output_csv_name: Export file name.
            
        Returns:
            A tuple of (created JobDescriptionModel, list of created RankingModel records).
        """
        start_time = time.time()
        jsonl_path = Path(jsonl_path)
        logger.info(f"Starting TalentLens Pipeline for JD: '{jd_title}'...")

        # ----------------------------------------------------
        # Phase 1: Job Description Parsing & Commit / Retrieve
        # ----------------------------------------------------
        if job_id:
            logger.info(f"Using existing Job Description ID: {job_id}")
            jd_db_model = db.query(JobDescriptionModel).filter_by(id=job_id).first()
            if not jd_db_model:
                raise ValueError(f"Job Description with ID {job_id} not found in database.")
                
            jd_schema = JobDescription(
                title=jd_db_model.title,
                department=jd_db_model.department,
                description=jd_db_model.description,
                skills_required=jd_db_model.skills_required or [],
                experience_required_years=jd_db_model.experience_required_years,
                education_required=jd_db_model.education_required,
                location=jd_db_model.location
            )
        else:
            logger.info("Executing Phase 1: Analyzing Job Description...")
            jd_schema = self.extractor.extract_job_details(jd_title, jd_raw_desc)
            
            jd_db_model = JobDescriptionModel(
                title=jd_schema.title,
                department=jd_schema.department,
                description=jd_schema.description,
                skills_required=jd_schema.skills_required,
                experience_required_years=jd_schema.experience_required_years,
                education_required=jd_schema.education_required,
                location=jd_schema.location
            )
            db.add(jd_db_model)
            db.commit()
            db.refresh(jd_db_model)
            logger.info(f"Job Description committed to DB. Assigned ID: {jd_db_model.id}")

        # ----------------------------------------------------
        # Phase 2: Batch Candidate Ingestion & Indexing
        # ----------------------------------------------------
        logger.info("Executing Phase 2: Batch Candidate Ingestion & FAISS Indexing...")
        loader = CandidateLoader(jsonl_path)
        
        batch_profiles: List[CandidateProfile] = []
        candidates_map: Dict[str, CandidateProfile] = {}
        processed_count = 0

        for raw_record in loader.stream_raw_records():
            if limit and processed_count >= limit:
                logger.info(f"Pipeline candidate read limit reached: {limit}")
                break

            profile = self.parser.parse_candidate(raw_record)
            if not profile:
                continue

            batch_profiles.append(profile)
            candidates_map[profile.candidate_id] = profile
            processed_count += 1

            # Ingest when batch chunk size is hit
            if len(batch_profiles) >= batch_size:
                self._process_candidate_batch(batch_profiles, db)
                batch_profiles = []

        # Process any remaining records in final batch
        if batch_profiles:
            self._process_candidate_batch(batch_profiles, db)

        logger.info(f"Ingested and indexed {processed_count} candidate profiles.")

        # ----------------------------------------------------
        # Phase 3: Semantic Candidate Retrieval
        # ----------------------------------------------------
        logger.info(f"Executing Phase 3: Semantic Retrieval (K={retrieve_k})...")
        # Ensure retrieve_k doesn't exceed processed candidates count
        actual_k = min(retrieve_k, processed_count)
        semantic_matches = self.retriever.retrieve(jd_schema, k=actual_k)

        # ----------------------------------------------------
        # Phase 4 & 5: Scoring and Explanations
        # ----------------------------------------------------
        logger.info("Executing Phase 4 & 5: Scoring and Explanation Generation...")
        ranking_models: List[RankingModel] = []

        # Convert matches to profiles with their raw scores
        candidates_to_score = []
        for cand_id, semantic_sim in semantic_matches:
            profile = candidates_map.get(cand_id)
            if profile:
                candidates_to_score.append((profile, semantic_sim))

        # Run composite ranker to score and sort candidates
        scored_breakdowns = self.ranker.rank_candidates(
            candidates_to_score,
            jd_schema,
            filter_disqualified=False  # Keep disqualified flagged for recruiter visibility
        )

        for idx, breakdown in enumerate(scored_breakdowns, start=1):
            profile = candidates_map[breakdown.candidate_id]
            
            # Determine if this candidate qualifies for live LLM explanations
            # Only top-N qualified (non-disqualified) candidates get live LLM explanations
            is_top_n_qualified = (idx <= explain_top_n) and not breakdown.is_disqualified
            
            if is_top_n_qualified:
                logger.info(f"Generating live LLM explanation for Top candidate: {profile.name} (Rank {idx})")
                # Use live explainer
                explanation = self.explainer.generate_explanation(profile, jd_schema, breakdown)
            else:
                # Use fast, template-based fallback explanation
                explanation = self.explainer._generate_fallback_explanation(profile, jd_schema, breakdown)

            rank_db_model = RankingModel(
                job_description_id=jd_db_model.id,
                candidate_id=breakdown.candidate_id,
                final_score=breakdown.final_score,
                semantic_score=breakdown.semantic_score,
                skill_score=breakdown.skill_score,
                career_score=breakdown.career_score,
                behavioral_score=breakdown.behavioral_score,
                education_score=breakdown.education_score,
                honeypot_penalty=breakdown.honeypot_penalty,
                is_disqualified=breakdown.is_disqualified,
                fit_summary=explanation.fit_summary,
                strengths=explanation.strengths,
                concerns=explanation.concerns,
                interview_questions=explanation.interview_questions
            )
            db.add(rank_db_model)
            ranking_models.append(rank_db_model)

        db.commit()
        logger.info(f"Committed {len(ranking_models)} candidate rankings to database.")

        # ----------------------------------------------------
        # Phase 6: Export Ranked Submission CSV
        # ----------------------------------------------------
        logger.info("Executing Phase 6: Exporting Ranked CSV Submission...")
        self._export_to_csv(ranking_models, candidates_map, output_csv_name)

        elapsed_time = time.time() - start_time
        logger.info(f"Pipeline completed successfully in {elapsed_time:.2f} seconds!")
        return jd_db_model, ranking_models

    def _process_candidate_batch(self, profiles: List[CandidateProfile], db: Session) -> None:
        """Helper to write raw profile structures to DB and index in FAISS."""
        # 1. Store in SQL Database
        for profile in profiles:
            # Check if candidate exists to prevent duplicate primary keys
            existing = db.query(CandidateModel).filter_by(candidate_id=profile.candidate_id).first()
            if existing:
                continue
                
            db_model = CandidateModel(
                candidate_id=profile.candidate_id,
                name=profile.name,
                email=profile.email,
                phone=profile.phone,
                summary=profile.summary,
                skills=profile.skills,
                experience=[exp.model_dump() for exp in profile.experience],
                education=[edu.model_dump() for edu in profile.education],
                certifications=[c.model_dump() for c in profile.certifications],
                languages=profile.languages
            )
            db.add(db_model)
        
        db.commit()

        # 2. Ingest into FAISS Vector Search Retriever
        self.retriever.index_candidates(profiles)

    def _export_to_csv(self, rankings: List[RankingModel], candidates_map: Dict[str, CandidateProfile], filename: str) -> None:
        """Exports ranked submission metrics to a CSV file."""
        outputs_dir = Path(__file__).resolve().parent.parent / "outputs"
        outputs_dir.mkdir(exist_ok=True)
        csv_filepath = outputs_dir / filename

        headers = [
            "rank", "candidate_id", "name", "final_score", 
            "semantic_score", "skill_score", "career_score", 
            "behavioral_score", "education_score", "honeypot_penalty", 
            "is_disqualified", "fit_summary"
        ]

        try:
            with open(csv_filepath, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(headers)
                
                for idx, rank in enumerate(rankings, start=1):
                    profile = candidates_map[rank.candidate_id]
                    writer.writerow([
                        idx,
                        rank.candidate_id,
                        profile.name,
                        rank.final_score,
                        rank.semantic_score,
                        rank.skill_score,
                        rank.career_score,
                        rank.behavioral_score,
                        rank.education_score,
                        rank.honeypot_penalty,
                        "YES" if rank.is_disqualified else "NO",
                        rank.fit_summary
                    ])
            logger.info(f"Successfully wrote Ranked CSV Submission to: {csv_filepath}")
        except Exception as exc:
            logger.error(f"Failed to export CSV submission: {exc}")
            raise
