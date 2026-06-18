import logging
import uuid
from typing import Dict, Any, List, Optional
from pydantic import ValidationError

from backend.core.schemas import CandidateProfile, Experience, Education, Certification

logger = logging.getLogger(__name__)

class CandidateParser:
    """
    Parser and normalizer to transform raw candidate data dictionaries
    into validated, structured CandidateProfile Pydantic objects.
    """

    @staticmethod
    def _normalize_id(raw: Dict[str, Any]) -> str:
        """Extracts or generates a unique candidate identifier."""
        for field in ["candidate_id", "id", "candidateId", "email"]:
            if raw.get(field):
                return str(raw[field]).strip()
        # Fallback to generating a unique UUID
        generated_id = f"gen-{uuid.uuid4().hex}"
        logger.debug(f"No candidate ID found; generated UUID: {generated_id}")
        return generated_id

    @staticmethod
    def _normalize_name(raw: Dict[str, Any]) -> str:
        """Extracts candidate name or provides a default."""
        for field in ["name", "full_name", "fullName", "first_name"]:
            if raw.get(field):
                # If first name is used, attempt to join with last name
                if field == "first_name" and raw.get("last_name"):
                    return f"{raw['first_name']} {raw['last_name']}".strip()
                return str(raw[field]).strip()
        return "Unknown Candidate"

    @staticmethod
    def _normalize_skills(raw: Dict[str, Any]) -> List[str]:
        """Normalizes skill lists from strings, comma-separated lists, or list of dicts."""
        raw_skills = raw.get("skills")
        if not raw_skills:
            return []
        
        # If it's already a list
        if isinstance(raw_skills, list):
            skills = []
            for skill in raw_skills:
                if isinstance(skill, dict):
                    # Extract name key
                    name = skill.get("name") or skill.get("skill_name") or skill.get("title")
                    if name:
                        skills.append(str(name).strip())
                elif skill:
                    skills.append(str(skill).strip())
            return skills
        
        # If it's a single string
        if isinstance(raw_skills, str):
            return [s.strip() for s in raw_skills.split(",") if s.strip()]
            
        return []

    @staticmethod
    def _parse_experience(raw_exp_list: Any) -> List[Experience]:
        """Parses experience list safely, applying defaults for missing fields."""
        if not isinstance(raw_exp_list, list):
            return []
        
        experiences = []
        for exp in raw_exp_list:
            if not isinstance(exp, dict):
                continue
            
            # Require at least company or title to keep
            company = exp.get("company") or exp.get("organization") or exp.get("company_name")
            title = exp.get("title") or exp.get("role") or exp.get("designation")
            
            if not company and not title:
                continue
                
            # Fallbacks
            company = str(company or "Unknown Company").strip()
            title = str(title or "Unknown Role").strip()
            
            # Normalize skills in experience
            skills = CandidateParser._normalize_skills(exp)
            
            experiences.append(
                Experience(
                    company=company,
                    title=title,
                    start_date=exp.get("start_date") or exp.get("startDate") or exp.get("from"),
                    end_date=exp.get("end_date") or exp.get("endDate") or exp.get("to") or "Present",
                    description=exp.get("description") or exp.get("summary") or exp.get("responsibilities"),
                    skills=skills,
                    location=exp.get("location")
                )
            )
        return experiences

    @staticmethod
    def _parse_education(raw_edu_list: Any) -> List[Education]:
        """Parses education list safely, applying defaults for missing fields."""
        if not isinstance(raw_edu_list, list):
            return []
            
        education_records = []
        for edu in raw_edu_list:
            if not isinstance(edu, dict):
                continue
                
            institution = edu.get("institution") or edu.get("school") or edu.get("university") or edu.get("college")
            if not institution:
                continue
                
            # GPA parsing with fallback
            gpa_raw = edu.get("gpa") or edu.get("grade") or edu.get("score")
            gpa = None
            if gpa_raw is not None:
                try:
                    gpa = float(gpa_raw)
                except ValueError:
                    # If it's a string like '3.8/4.0', try to extract the float part
                    try:
                        gpa = float(str(gpa_raw).split("/")[0])
                    except (ValueError, IndexError):
                        pass

            education_records.append(
                Education(
                    institution=str(institution).strip(),
                    degree=edu.get("degree") or edu.get("qualification"),
                    field_of_study=edu.get("field_of_study") or edu.get("major") or edu.get("fieldOfStudy"),
                    start_date=edu.get("start_date") or edu.get("startDate") or edu.get("from"),
                    end_date=edu.get("end_date") or edu.get("endDate") or edu.get("to"),
                    gpa=gpa
                )
            )
        return education_records

    @staticmethod
    def _parse_certifications(raw_certs: Any) -> List[Certification]:
        """Parses certifications list safely, wrapping simple strings or parsing maps."""
        if not raw_certs:
            return []
            
        certifications = []
        if isinstance(raw_certs, list):
            for cert in raw_certs:
                if isinstance(cert, str):
                    certifications.append(Certification(name=cert.strip()))
                elif isinstance(cert, dict):
                    name = cert.get("name") or cert.get("title") or cert.get("certification_name")
                    if name:
                        certifications.append(
                            Certification(
                                name=str(name).strip(),
                                issuing_organization=cert.get("issuing_organization") or cert.get("issuer"),
                                issue_date=cert.get("issue_date") or cert.get("date")
                            )
                        )
        return certifications

    def parse_candidate(self, raw_dict: Dict[str, Any]) -> Optional[CandidateProfile]:
        """
        Parses a raw input dictionary into a CandidateProfile Pydantic object.
        Returns None if parsing fails validation check, after logging details.
        """
        try:
            candidate_id = self._normalize_id(raw_dict)
            name = self._normalize_name(raw_dict)
            skills = self._normalize_skills(raw_dict)
            
            experience = self._parse_experience(raw_dict.get("experience") or raw_dict.get("work_history") or [])
            education = self._parse_education(raw_dict.get("education") or raw_dict.get("academic_history") or [])
            certifications = self._parse_certifications(raw_dict.get("certifications") or raw_dict.get("certs") or [])
            
            # Languages normalizer
            languages = raw_dict.get("languages") or []
            if isinstance(languages, str):
                languages = [l.strip() for l in languages.split(",") if l.strip()]
            elif not isinstance(languages, list):
                languages = []
            languages = [str(l).strip() for l in languages if l]

            # Construct Pydantic model
            profile = CandidateProfile(
                candidate_id=candidate_id,
                name=name,
                email=raw_dict.get("email"),
                phone=raw_dict.get("phone"),
                summary=raw_dict.get("summary") or raw_dict.get("about") or raw_dict.get("headline"),
                skills=skills,
                experience=experience,
                education=education,
                certifications=certifications,
                languages=languages
            )
            return profile

        except ValidationError as val_err:
            logger.error(f"Validation failed for candidate (ID: {raw_dict.get('id', 'Unknown')}): {val_err}")
            return None
        except Exception as exc:
            logger.error(f"Unexpected error parsing candidate (ID: {raw_dict.get('id', 'Unknown')}): {exc}")
            return None
