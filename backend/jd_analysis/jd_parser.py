import logging
from typing import Any, Dict, Optional
from backend.core.schemas import JobDescription

logger = logging.getLogger(__name__)

class JobDescriptionParser:
    """
    A utility class to clean raw text and build a basic validated
    JobDescription schema before enrichment via LLM.
    """

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Removes formatting noise, normalizes spacing, and eliminates empty lines.
        """
        if not text:
            return ""
        
        lines = [line.strip() for line in text.splitlines()]
        # Remove consecutive empty lines
        cleaned_lines = [line for line in lines if line]
        return "\n".join(cleaned_lines)

    def parse_raw(
        self,
        title: str,
        description: str,
        department: Optional[str] = None,
        location: Optional[str] = None,
        **kwargs
    ) -> JobDescription:
        """
        Constructs a base JobDescription schema from raw metadata and cleaned text.
        """
        cleaned_description = self.clean_text(description)
        
        # Pull details if they exist in kwargs
        skills_required = kwargs.get("skills_required") or []
        if isinstance(skills_required, str):
            skills_required = [s.strip() for s in skills_required.split(",") if s.strip()]
        
        experience_required_years = kwargs.get("experience_required_years")
        if experience_required_years is not None:
            try:
                experience_required_years = float(experience_required_years)
            except ValueError:
                experience_required_years = None

        return JobDescription(
            title=title.strip(),
            department=department.strip() if department else None,
            description=cleaned_description,
            skills_required=skills_required,
            experience_required_years=experience_required_years,
            education_required=kwargs.get("education_required"),
            location=location.strip() if location else None
        )
