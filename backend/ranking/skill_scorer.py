import re
import logging
from backend.core.schemas import CandidateProfile, JobDescription

logger = logging.getLogger(__name__)

class SkillScorer:
    """
    Evaluates candidate's alignment with JD skills.
    Matches explicit skills inventory and performs keyword search in experience descriptions.
    """
    def score(self, profile: CandidateProfile, jd: JobDescription) -> float:
        """
        Calculates skill match score between 0.0 and 100.0.
        Direct list intersections count for 1.0 weight, while historical mentions count for 0.5 weight.
        """
        if not jd.skills_required:
            logger.info("No required skills defined in job description. Defaulting skill score to 100.0")
            return 100.0

        # Aligns casing to lowercase
        required_skills = {s.strip().lower() for s in jd.skills_required if s.strip()}
        if not required_skills:
            return 100.0

        candidate_skills = {s.strip().lower() for s in profile.skills if s.strip()}

        # 1. Direct match calculation
        direct_matches = required_skills.intersection(candidate_skills)
        
        # 2. Contextual check for missing skills in summary and experience lists
        remaining_skills = required_skills - candidate_skills
        context_matches = set()

        if remaining_skills:
            # Build search content
            text_corpus_parts = []
            if profile.summary:
                text_corpus_parts.append(profile.summary.lower())
                
            for exp in profile.experience:
                if exp.description:
                    text_corpus_parts.append(exp.description.lower())
                for exp_skill in exp.skills:
                    text_corpus_parts.append(exp_skill.lower())

            full_context_text = " ".join(text_corpus_parts)

            # Search text for remaining skills using word boundaries
            for skill in remaining_skills:
                escaped_skill = re.escape(skill)
                # Matches word boundary, allowing optional hyphens or plurals (s)
                pattern = rf"\b{escaped_skill}s?\b"
                if re.search(pattern, full_context_text, re.IGNORECASE):
                    context_matches.add(skill)

        # 3. Calculate weighted score
        # Direct matches = 1.0 point each, Contextual mentions = 0.5 points each
        total_matched_weight = (len(direct_matches) * 1.0) + (len(context_matches) * 0.5)
        total_required_skills = len(required_skills)

        score = (total_matched_weight / total_required_skills) * 100.0
        
        # Log granular scoring breakdown
        logger.info(
            f"Candidate (ID: {profile.candidate_id}) Skill Score: {score:.2f}% "
            f"(Direct: {len(direct_matches)}/{total_required_skills}, "
            f"Context: {len(context_matches)}/{total_required_skills})"
        )
        
        return min(100.0, max(0.0, score))
