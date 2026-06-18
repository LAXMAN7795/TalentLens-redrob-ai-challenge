import logging
import re
from typing import Optional
from backend.core.schemas import JobDescription
from backend.llm.groq_client import GroqClient
from backend.jd_analysis.jd_parser import JobDescriptionParser

logger = logging.getLogger(__name__)

class JobDescriptionExtractor:
    """
    Enriches and extracts semantic fields from unstructured Job Description text.
    Queries the Groq Llama 3.3 model to parse structured fields, with a regex fallback.
    """
    def __init__(self, groq_client: Optional[GroqClient] = None, use_fallback: bool = False):
        if use_fallback:
            self.groq_client = None
        else:
            if groq_client is not None:
                self.groq_client = groq_client
            else:
                try:
                    self.groq_client = GroqClient()
                except Exception as exc:
                    logger.warning(f"Could not initialize GroqClient, falling back to regex: {exc}")
                    self.groq_client = None

    def extract_job_details(self, raw_title: str, raw_description: str) -> JobDescription:
        """
        Extracts structured parameters from the job description text using Groq LLM JSON Mode.
        Falls back to a regex-based extractor if the Groq API is unavailable.
        """
        if not self.groq_client:
            logger.warning("GroqClient is unavailable. Performing fallback regex extraction.")
            return self._fallback_regex_extraction(raw_title, raw_description)
            
        system_instruction = (
            "You are a Principal Technical Recruiter. Your task is to analyze the provided job title "
            "and job description text, then extract a clean, validated JSON object that outlines the "
            "structured parameters of the role."
        )

        prompt = (
            f"Raw Title: {raw_title}\n\n"
            f"Raw Job Description Text:\n{raw_description}\n\n"
            "Please extract the following fields precisely:\n"
            "1. title: Cleaned job title.\n"
            "2. department: The department or team (e.g. Engineering, Sales, or null if not specified).\n"
            "3. description: A concise summary of the responsibilities (2-3 sentences).\n"
            "4. skills_required: A list of key technical skills, programming languages, libraries, and frameworks.\n"
            "5. experience_required_years: The minimum years of experience required as a float (e.g. '5+ years' -> 5.0, '3-5 years' -> 3.0. Set to null if not specified).\n"
            "6. education_required: Minimum educational degree level (e.g., 'Bachelor', 'Master', 'PhD', or null if unspecified).\n"
            "7. location: Work environment. Must be one of 'Remote', 'Hybrid', 'On-site', or null if unspecified."
        )

        try:
            extracted_jd = self.groq_client.get_structured_completion(
                prompt=prompt,
                system_instruction=system_instruction,
                response_model=JobDescription
            )
            if extracted_jd:
                return extracted_jd
        except Exception as exc:
            logger.error(f"Failed to extract details via Groq, falling back to regex: {exc}")

        return self._fallback_regex_extraction(raw_title, raw_description)

    def _fallback_regex_extraction(self, raw_title: str, raw_description: str) -> JobDescription:
        """
        Regex-based parsing fallback for extracting key metrics from the job description.
        Useful for local testing without internet access or Groq credit limits.
        """
        parser = JobDescriptionParser()
        cleaned_desc = parser.clean_text(raw_description)

        # 1. Experience Years extraction
        exp_match = re.search(r"(\d+)\+?\s*(?:-\s*\d+\s*)?years?", raw_description, re.IGNORECASE)
        experience_years = float(exp_match.group(1)) if exp_match else None

        # 2. Education level extraction
        education = None
        if re.search(r"\bph\.?d\b|doctorate", raw_description, re.IGNORECASE):
            education = "PhD"
        elif re.search(r"\bmaster'?s?\b|\bm\.?s\b|\bm\.?b\.?a\b", raw_description, re.IGNORECASE):
            education = "Master"
        elif re.search(r"\bbachelor'?s?\b|\bb\.?s\b|\bb\.?a\b|degree", raw_description, re.IGNORECASE):
            education = "Bachelor"

        # 3. Location extraction
        location = None
        if re.search(r"\bremote\b", raw_description, re.IGNORECASE):
            location = "Remote"
        elif re.search(r"\bhybrid\b", raw_description, re.IGNORECASE):
            location = "Hybrid"
        elif re.search(r"\bon-site\b|\bon site\b|\boffice\b", raw_description, re.IGNORECASE):
            location = "On-site"

        # 4. Simple skill regex search (common buzzwords in tech)
        common_tech = ["python", "java", "javascript", "react", "fastapi", "postgresql", "sql", "aws", "docker", "faiss", "kubernetes", "ml", "machine learning"]
        skills_found = []
        for tech in common_tech:
            if re.search(rf"\b{tech}\b", raw_description, re.IGNORECASE):
                skills_found.append(tech.title() if tech not in ["aws", "sql", "ml", "faiss"] else tech.upper())

        return JobDescription(
            title=raw_title.strip(),
            department=None,
            description=cleaned_desc[:500] + "..." if len(cleaned_desc) > 500 else cleaned_desc,
            skills_required=skills_found,
            experience_required_years=experience_years,
            education_required=education,
            location=location
        )
