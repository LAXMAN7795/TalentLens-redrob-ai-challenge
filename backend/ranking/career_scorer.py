import re
import datetime
import logging
from typing import Optional
from backend.core.schemas import CandidateProfile, JobDescription

logger = logging.getLogger(__name__)

class CareerScorer:
    """
    Heuristically scores a candidate's career quality and growth.
    Measures job stability (avoidance of job-hopping) and title promotion milestones.
    """
    def __init__(self, target_tenure_years: float = 3.0):
        self.target_tenure_years = target_tenure_years
        self.career_keywords = {
            "junior": 1,
            "intern": 1,
            "associate": 2,
            "senior": 3,
            "sr": 3,
            "lead": 4,
            "principal": 5,
            "architect": 5,
            "manager": 6,
            "director": 7,
            "head": 7,
            "vp": 8,
            "cto": 9,
            "cio": 9,
            "founder": 9
        }

    def _parse_year(self, date_str: Optional[str]) -> Optional[int]:
        if not date_str:
            return None
        date_str_clean = date_str.strip().lower()
        if "present" in date_str_clean or "current" in date_str_clean or "now" in date_str_clean:
            return datetime.datetime.now().year
        match = re.search(r"\b(19\d{2}|20\d{2})\b", date_str_clean)
        return int(match.group(1)) if match else None

    def calculate_tenure_score(self, profile: CandidateProfile) -> float:
        """
        Calculates stability score between 0.0 and 100.0 based on average job tenure.
        Average tenure >= 3 years yields 100 points, while < 1 year indicates job hopping.
        """
        if not profile.experience:
            return 0.0
            
        current_year = datetime.datetime.now().year
        total_experience_years = 0.0
        job_count = 0
        
        for exp in profile.experience:
            start_year = self._parse_year(exp.start_date)
            end_year = self._parse_year(exp.end_date) or current_year
            
            if start_year and end_year:
                total_experience_years += max(0.0, float(end_year - start_year))
                job_count += 1
                
        if job_count == 0:
            return 0.0
            
        avg_tenure = total_experience_years / job_count
        
        if avg_tenure >= self.target_tenure_years:
            return 100.0
        elif avg_tenure >= 1.0:
            # Linear scaling between 50 and 100
            return 50.0 + ((avg_tenure - 1.0) / (self.target_tenure_years - 1.0)) * 50.0
        else:
            # Job hoppers: scaling between 0 and 50
            return avg_tenure * 50.0

    def calculate_progression_score(self, profile: CandidateProfile) -> float:
        """
        Analyzes chronological title progression.
        Checks if title ranks increase over the candidate's career timeline.
        """
        if not profile.experience:
            return 50.0  # Base neutral score
            
        chronological_roles = []
        for exp in profile.experience:
            start_year = self._parse_year(exp.start_date) or 0
            chronological_roles.append((start_year, exp.title.lower()))
            
        # Sort oldest to newest
        chronological_roles.sort(key=lambda x: x[0])
        
        role_ranks = []
        for _, title in chronological_roles:
            role_rank = 2  # default rank value for unlisted keywords (standard developer)
            for keyword, value in self.career_keywords.items():
                # Check for whole-word match or direct substring (e.g. 'sr' or 'senior')
                if re.search(rf"\b{keyword}\b", title):
                    role_rank = value
                    break
            role_ranks.append(role_rank)
            
        if len(role_ranks) < 2:
            return 50.0  # No sequence comparison possible, neutral score
            
        growth_points = 0
        for i in range(1, len(role_ranks)):
            # If the rank increased in the subsequent job (e.g. 2 -> 3)
            if role_ranks[i] > role_ranks[i-1]:
                growth_points += 20
            # If rank decreased, apply a mild penalty (unless they became founder/etc.)
            elif role_ranks[i] < role_ranks[i-1]:
                growth_points -= 10
                
        final_score = 50.0 + growth_points
        return min(100.0, max(0.0, final_score))

    def score(self, profile: CandidateProfile, jd: JobDescription) -> float:
        """
        Computes aggregate career score (50% tenure stability + 50% title progression).
        """
        tenure = self.calculate_tenure_score(profile)
        progression = self.calculate_progression_score(profile)
        
        aggregate_score = (tenure * 0.5) + (progression * 0.5)
        logger.info(
            f"Candidate (ID: {profile.candidate_id}) Career Score: {aggregate_score:.2f}% "
            f"(Tenure: {tenure:.1f}%, Prog: {progression:.1f}%)"
        )
        return aggregate_score
