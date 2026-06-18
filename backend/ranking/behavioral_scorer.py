import re
import logging
from backend.core.schemas import CandidateProfile, JobDescription

logger = logging.getLogger(__name__)

class BehavioralScorer:
    """
    Evaluates behavioral signals and soft-skill attributes from candidate experience text.
    Categories scored: Leadership/Initiative, Collaboration, Execution/Delivery, and Communication.
    """
    def __init__(self):
        self.categories = {
            "leadership": [
                r"\blead\b", r"\bmanaged\b", r"\bmentored\b", r"\bmentoring\b", r"\bspearheaded\b",
                r"\bownership\b", r"\bheaded\b", r"\barchitected\b", r"\bdirected\b", r"\bguided\b"
            ],
            "collaboration": [
                r"\bcollaborated\b", r"\bteam\b", r"\bpartnered\b", r"\bcross-functional\b",
                r"\bsupported\b", r"\bcooperated\b", r"\bshared\b", r"\bjointly\b", r"\bfacilitated\b"
            ],
            "execution": [
                r"\bdelivered\b", r"\blaunched\b", r"\bdeployed\b", r"\boptimized\b", r"\bimplemented\b",
                r"\bachieved\b", r"\breduced\b", r"\bincreased\b", r"\bsaved\b", r"\bresolved\b"
            ],
            "communication": [
                r"\bpresented\b", r"\bcommunicated\b", r"\bstakeholders\b", r"\bclients\b",
                r"\bdocumentation\b", r"\breports\b", r"\bwriting\b", r"\bnegotiated\b", r"\bliaised\b"
            ]
        }

    def score(self, profile: CandidateProfile, jd: JobDescription) -> float:
        """
        Computes behavioral score between 0.0 and 100.0.
        Each of the 4 soft-skills categories can contribute up to 25.0 points.
        """
        text_corpus_parts = []
        if profile.summary:
            text_corpus_parts.append(profile.summary.lower())
            
        for exp in profile.experience:
            if exp.description:
                text_corpus_parts.append(exp.description.lower())
                
        full_text = " ".join(text_corpus_parts)
        
        if not full_text:
            return 0.0
            
        category_points = {}
        for category, patterns in self.categories.items():
            matched_count = 0
            for pattern in patterns:
                if re.search(pattern, full_text, re.IGNORECASE):
                    matched_count += 1
            
            # 2+ distinct terms matched = full category points (25.0)
            # 1 distinct term matched = half category points (12.5)
            if matched_count >= 2:
                category_points[category] = 25.0
            elif matched_count == 1:
                category_points[category] = 12.5
            else:
                category_points[category] = 0.0
                
        total_score = sum(category_points.values())
        
        logger.info(
            f"Candidate (ID: {profile.candidate_id}) Behavioral Score: {total_score:.2f}% "
            f"(Leadership: {category_points['leadership']:.1f}, "
            f"Collab: {category_points['collaboration']:.1f}, "
            f"Execution: {category_points['execution']:.1f}, "
            f"Comm: {category_points['communication']:.1f})"
        )
        
        return total_score
