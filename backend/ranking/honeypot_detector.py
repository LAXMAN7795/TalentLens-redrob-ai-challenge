import re
import datetime
import logging
from collections import Counter
from typing import Optional
from backend.core.schemas import CandidateProfile

logger = logging.getLogger(__name__)

class HoneypotDetector:
    """
    Analyzes candidate profiles to detect cheating techniques (e.g. keyword stuffing,
    invisible keyword blocks, unrealistic date overlaps) and returns a penalty deduction.
    """
    def __init__(self, repeat_threshold: int = 12, word_penalty_multiplier: float = 3.0):
        self.repeat_threshold = repeat_threshold
        self.word_penalty_multiplier = word_penalty_multiplier
        # Exclude common grammatical terms
        self.ignored_words = {
            "and", "the", "for", "with", "from", "that", "this", "using", "used", 
            "development", "project", "experience", "role", "team", "work", "system"
        }

    def detect_keyword_stuffing(self, profile: CandidateProfile) -> float:
        """
        Analyzes frequency distribution of words in summary, skills, and experience blocks.
        If a target word (like 'python' or 'api') is repeated excessively, applies a penalty.
        """
        text_blocks = []
        if profile.summary:
            text_blocks.append(profile.summary.lower())
        for exp in profile.experience:
            if exp.description:
                text_blocks.append(exp.description.lower())
                
        full_text = " ".join(text_blocks)
        
        # Tokenize words containing alphanumeric characters, length between 3 and 20
        words = re.findall(r"\b[a-z0-9\-]{3,20}\b", full_text)
        if not words:
            return 0.0
            
        word_counts = Counter(words)
        
        # Strip common ignored words
        for term in self.ignored_words:
            if term in word_counts:
                del word_counts[term]
                
        if not word_counts:
            return 0.0
            
        most_common_word, frequency = word_counts.most_common(1)[0]
        
        # If the word exceeds the threshold, calculate penalty
        if frequency > self.repeat_threshold:
            excess = frequency - self.repeat_threshold
            penalty = excess * self.word_penalty_multiplier
            logger.warning(
                f"Candidate (ID: {profile.candidate_id}) flagged for keyword stuffing! "
                f"Word '{most_common_word}' repeated {frequency} times. Penalty: {penalty:.2f}"
            )
            return penalty
            
        return 0.0

    def detect_timeline_anomalies(self, profile: CandidateProfile) -> float:
        """
        Identifies date anomalies (e.g., claiming total experience > 55 years, or overlapping
        active durations that exceed physically realistic career timelines).
        """
        total_years = 0.0
        current_year = datetime.datetime.now().year
        
        for exp in profile.experience:
            start_year = self._parse_year(exp.start_date)
            end_year = self._parse_year(exp.end_date) or current_year
            
            if start_year and end_year:
                duration = end_year - start_year
                if duration > 0:
                    total_years += duration
                    
        # Apply a high penalty if total sum of experience years is unrealistic (e.g. > 55 years)
        if total_years > 55.0:
            logger.warning(
                f"Candidate (ID: {profile.candidate_id}) flagged for timeline anomaly! "
                f"Sum of experience duration is {total_years:.1f} years. Penalty: 25.0"
            )
            return 25.0
            
        return 0.0

    def _parse_year(self, date_str: Optional[str]) -> Optional[int]:
        if not date_str:
            return None
            
        date_str_clean = date_str.strip().lower()
        if "present" in date_str_clean or "current" in date_str_clean or "now" in date_str_clean:
            return datetime.datetime.now().year
            
        # Try to find a 4-digit number representing year
        match = re.search(r"\b(19\d{2}|20\d{2})\b", date_str_clean)
        if match:
            return int(match.group(1))
            
        return None

    def calculate_penalty(self, profile: CandidateProfile) -> float:
        """
        Aggregates all penalties, capped at a maximum deduction of 50.0 points.
        """
        stuffing_penalty = self.detect_keyword_stuffing(profile)
        timeline_penalty = self.detect_timeline_anomalies(profile)
        
        total_penalty = stuffing_penalty + timeline_penalty
        return min(total_penalty, 50.0)
