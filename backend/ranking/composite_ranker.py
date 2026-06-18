import logging
from typing import Dict, List, Tuple, Optional

from backend.core.schemas import CandidateProfile, JobDescription, CandidateScoreBreakdown
from backend.ranking.honeypot_detector import HoneypotDetector
from backend.ranking.disqualifier import Disqualifier
from backend.ranking.skill_scorer import SkillScorer
from backend.ranking.career_scorer import CareerScorer
from backend.ranking.behavioral_scorer import BehavioralScorer
from backend.ranking.education_scorer import EducationScorer

logger = logging.getLogger(__name__)

class CompositeRanker:
    """
    The orchestrator that aggregates all sub-scorers and applies honeypot penalties
    to compute a final weighted ranking score out of 100.0.
    """
    def __init__(
        self,
        honeypot_detector: Optional[HoneypotDetector] = None,
        disqualifier: Optional[Disqualifier] = None,
        skill_scorer: Optional[SkillScorer] = None,
        career_scorer: Optional[CareerScorer] = None,
        behavioral_scorer: Optional[BehavioralScorer] = None,
        education_scorer: Optional[EducationScorer] = None
    ):
        self.honeypot_detector = honeypot_detector or HoneypotDetector()
        self.disqualifier = disqualifier or Disqualifier()
        self.skill_scorer = skill_scorer or SkillScorer()
        self.career_scorer = career_scorer or CareerScorer()
        self.behavioral_scorer = behavioral_scorer or BehavioralScorer()
        self.education_scorer = education_scorer or EducationScorer()
        
        # Default weighting distribution
        self.default_weights = {
            "semantic": 0.30,
            "skill": 0.30,
            "career": 0.20,
            "behavioral": 0.10,
            "education": 0.10
        }

    def compute_candidate_score(
        self,
        profile: CandidateProfile,
        jd: JobDescription,
        raw_semantic_score: float,
        weights: Optional[Dict[str, float]] = None
    ) -> CandidateScoreBreakdown:
        """
        Calculates all sub-scores and aggregates them.
        Applies disqualification filters (setting final score to 0.0) and honeypot deductions.
        """
        # Load weights
        active_weights = weights or self.default_weights
        
        # Normalize weights if they do not sum to 1.0
        weight_sum = sum(active_weights.values())
        normalized_weights = {k: v / weight_sum for k, v in active_weights.items()}

        # 1. Disqualification check
        is_disq = self.disqualifier.is_disqualified(profile, jd)
        
        # Calculate sub-scores (0 to 100)
        # Scale semantic search inner-product (typically 0.0 to 1.0 for matches) to 100 scale
        semantic_score = min(100.0, max(0.0, raw_semantic_score * 100.0))
        skill_score = self.skill_scorer.score(profile, jd)
        career_score = self.career_scorer.score(profile, jd)
        behavioral_score = self.behavioral_scorer.score(profile, jd)
        education_score = self.education_scorer.score(profile, jd)
        
        # Calculate honeypot penalties
        honeypot_penalty = self.honeypot_detector.calculate_penalty(profile)

        if is_disq:
            # Disqualified candidates receive a 0.0 final score
            final_score = 0.0
        else:
            # Weighted calculation
            weighted_aggregate = (
                normalized_weights.get("semantic", 0.30) * semantic_score +
                normalized_weights.get("skill", 0.30) * skill_score +
                normalized_weights.get("career", 0.20) * career_score +
                normalized_weights.get("behavioral", 0.10) * behavioral_score +
                normalized_weights.get("education", 0.10) * education_score
            )
            # Subtract penalty and clamp to [0.0, 100.0]
            final_score = min(100.0, max(0.0, weighted_aggregate - honeypot_penalty))

        return CandidateScoreBreakdown(
            candidate_id=profile.candidate_id,
            name=profile.name,
            final_score=round(final_score, 2),
            semantic_score=round(semantic_score, 2),
            skill_score=round(skill_score, 2),
            career_score=round(career_score, 2),
            behavioral_score=round(behavioral_score, 2),
            education_score=round(education_score, 2),
            honeypot_penalty=round(honeypot_penalty, 2),
            is_disqualified=is_disq
        )

    def rank_candidates(
        self,
        candidates_with_semantic_scores: List[Tuple[CandidateProfile, float]],
        jd: JobDescription,
        weights: Optional[Dict[str, float]] = None,
        filter_disqualified: bool = True
    ) -> List[CandidateScoreBreakdown]:
        """
        Processes and ranks a list of candidate profiles.
        Sorts the final list by highest composite score first.
        """
        ranked_list = []
        for profile, raw_semantic_score in candidates_with_semantic_scores:
            breakdown = self.compute_candidate_score(profile, jd, raw_semantic_score, weights)
            
            # Skip if filter_disqualified is enabled and candidate is disqualified
            if filter_disqualified and breakdown.is_disqualified:
                continue
                
            ranked_list.append(breakdown)
            
        # Sort by final score in descending order
        ranked_list.sort(key=lambda x: x.final_score, reverse=True)
        return ranked_list
