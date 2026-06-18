import re
import logging
from typing import Optional
from backend.core.schemas import CandidateProfile, JobDescription

logger = logging.getLogger(__name__)

class EducationScorer:
    """
    Evaluates educational background against JD demands.
    Tiers degree credentials (PhD, Master, Bachelor) and handles GPA score boosts.
    """
    DEGREE_TIERS = {
        "phd": 3,
        "doctor": 3,
        "doctorate": 3,
        "master": 2,
        "ms": 2,
        "ma": 2,
        "mba": 2,
        "bachelor": 1,
        "bs": 1,
        "ba": 1,
        "degree": 1
    }

    def _get_degree_tier(self, degree_str: Optional[str]) -> int:
        if not degree_str:
            return 0
        degree_clean = degree_str.strip().lower()
        for keyword, tier in self.DEGREE_TIERS.items():
            if re.search(rf"\b{re.escape(keyword)}\b", degree_clean):
                return tier
        return 0

    def score(self, profile: CandidateProfile, jd: JobDescription) -> float:
        """
        Calculates education alignment score between 0.0 and 100.0.
        Adds a small bonus for high GPAs (GPA >= 3.8 receives a +5.0 point boost).
        """
        required_tier = 0
        if jd.education_required:
            required_tier = self._get_degree_tier(jd.education_required)

        if not profile.education:
            # Return baseline if candidate has no education credentials listed
            return 30.0 if required_tier > 0 else 70.0

        highest_cand_tier = 0
        best_gpa = None

        for edu in profile.education:
            tier = self._get_degree_tier(edu.degree)
            if tier > highest_cand_tier:
                highest_cand_tier = tier
            
            # Record highest gpa
            if edu.gpa is not None:
                if best_gpa is None or edu.gpa > best_gpa:
                    best_gpa = edu.gpa

        # 1. Base Score calculation
        if required_tier == 0:
            # Map directly based on candidate's highest degree
            if highest_cand_tier >= 3:
                base_score = 100.0
            elif highest_cand_tier == 2:
                base_score = 90.0
            elif highest_cand_tier == 1:
                base_score = 80.0
            else:
                base_score = 65.0
        else:
            # Job Description specifies a minimum degree requirement
            if highest_cand_tier >= required_tier:
                base_score = 100.0
            elif highest_cand_tier == required_tier - 1 and highest_cand_tier > 0:
                base_score = 75.0  # One tier below (e.g. Master required, Bachelor candidate)
            else:
                base_score = 50.0  # More than one tier below or no degree matched

        # 2. GPA Boost calculation (normalized to 4.0 scale if it is percentage-based)
        gpa_boost = 0.0
        if best_gpa is not None:
            normalized_gpa = best_gpa
            if best_gpa > 4.0:
                # Assume percentage or 10.0 scale, compress to 4.0
                if best_gpa > 10.0:
                    normalized_gpa = (best_gpa / 100.0) * 4.0
                else:
                    normalized_gpa = (best_gpa / 10.0) * 4.0

            if normalized_gpa >= 3.8:
                gpa_boost = 5.0
            elif normalized_gpa >= 3.5:
                gpa_boost = 3.0
            elif normalized_gpa >= 3.0:
                gpa_boost = 1.0

        final_score = min(100.0, base_score + gpa_boost)
        
        logger.info(
            f"Candidate (ID: {profile.candidate_id}) Education Score: {final_score:.2f}% "
            f"(Highest: Tier {highest_cand_tier}, Base: {base_score}, Boost: {gpa_boost})"
        )
        return final_score
