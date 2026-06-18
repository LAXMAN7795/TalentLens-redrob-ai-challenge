import re
import datetime
import logging
from typing import Optional
from backend.core.schemas import CandidateProfile, JobDescription

logger = logging.getLogger(__name__)

class Disqualifier:
    """
    Evaluates baseline criteria to filter out candidates who do not meet mandatory job requirements.
    Filters by minimum experience years and educational background thresholds.
    """
    DEGREE_RANKINGS = {
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

    def _get_degree_value(self, degree_str: Optional[str]) -> int:
        """Assigns an integer rank to a degree string to allow comparison math."""
        if not degree_str:
            return 0
        degree_clean = degree_str.strip().lower()
        for key, value in self.DEGREE_RANKINGS.items():
            if re.search(rf"\b{re.escape(key)}\b", degree_clean):
                return value
        return 0

    def _parse_year(self, date_str: Optional[str]) -> Optional[int]:
        if not date_str:
            return None
        date_str_clean = date_str.strip().lower()
        if "present" in date_str_clean or "current" in date_str_clean or "now" in date_str_clean:
            return datetime.datetime.now().year
        match = re.search(r"\b(19\d{2}|20\d{2})\b", date_str_clean)
        return int(match.group(1)) if match else None

    def _calculate_candidate_experience(self, profile: CandidateProfile) -> float:
        """Calculates a candidate's total years of experience across all roles."""
        total_years = 0.0
        current_year = datetime.datetime.now().year
        
        for exp in profile.experience:
            start_year = self._parse_year(exp.start_date)
            end_year = self._parse_year(exp.end_date) or current_year
            
            if start_year and end_year:
                duration = max(0.0, float(end_year - start_year))
                total_years += duration
                
        return total_years

    def is_disqualified(self, profile: CandidateProfile, jd: JobDescription) -> bool:
        """
        Checks if candidate fails experience or education requirements.
        Returns True if disqualified, False if they meet baseline standards.
        """
        # 1. Check Experience threshold
        if jd.experience_required_years is not None:
            cand_exp_years = self._calculate_candidate_experience(profile)
            if cand_exp_years < jd.experience_required_years:
                logger.info(
                    f"Candidate (ID: {profile.candidate_id}) disqualified: "
                    f"Experience ({cand_exp_years:.1f} years) is less than required ({jd.experience_required_years:.1f} years)."
                )
                return True

        # 2. Check Education threshold
        if jd.education_required:
            required_degree_val = self._get_degree_value(jd.education_required)
            if required_degree_val > 0:
                highest_cand_degree_val = 0
                for edu in profile.education:
                    degree_val = self._get_degree_value(edu.degree)
                    if degree_val > highest_cand_degree_val:
                        highest_cand_degree_val = degree_val
                        
                if highest_cand_degree_val < required_degree_val:
                    logger.info(
                        f"Candidate (ID: {profile.candidate_id}) disqualified: "
                        f"Highest degree (rank: {highest_cand_degree_val}) is less than required (rank: {required_degree_val})."
                    )
                    return True

        return False
