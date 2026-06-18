import logging
from backend.core.schemas import CandidateProfile

logger = logging.getLogger(__name__)

class DocumentBuilder:
    """
    Constructs standardized, search-optimized textual representations
    of CandidateProfiles for embedding generation and vector search retrieval.
    """

    @staticmethod
    def build_candidate_document(profile: CandidateProfile) -> str:
        """
        Converts a CandidateProfile into a single, cohesive, natural language text block.
        Includes semantic markers to highlight experience, skills, and education.
        """
        document_parts = []

        # Name / Profile Header
        document_parts.append(f"Candidate Name: {profile.name}")

        # Summary Section
        if profile.summary:
            document_parts.append(f"Professional Summary: {profile.summary.strip()}")

        # Core Skills Section
        if profile.skills:
            # Clean and capitalize skill list
            clean_skills = [skill.strip() for skill in profile.skills if skill.strip()]
            if clean_skills:
                document_parts.append(f"Technical & Professional Skills: {', '.join(clean_skills)}")

        # Professional Work Experience Section
        if profile.experience:
            experience_lines = ["Professional Experience:"]
            for idx, exp in enumerate(profile.experience, start=1):
                exp_detail = f"{idx}. {exp.title} at {exp.company}"
                
                # Append dates if available
                dates = []
                if exp.start_date:
                    dates.append(str(exp.start_date).strip())
                if exp.end_date:
                    dates.append(str(exp.end_date).strip())
                if dates:
                    exp_detail += f" ({' - '.join(dates)})"

                # Append description
                if exp.description:
                    exp_detail += f": {exp.description.strip()}"
                
                # Append skills associated with this job
                if exp.skills:
                    exp_detail += f" [Skills used: {', '.join(exp.skills)}]"
                
                # Append location
                if exp.location:
                    exp_detail += f" (Location: {exp.location})"
                
                experience_lines.append(exp_detail)
            
            document_parts.append("\n".join(experience_lines))

        # Academic / Education Section
        if profile.education:
            education_lines = ["Education & Academic Background:"]
            for idx, edu in enumerate(profile.education, start=1):
                edu_detail = f"{idx}. "
                degree_details = []
                if edu.degree:
                    degree_details.append(str(edu.degree).strip())
                if edu.field_of_study:
                    degree_details.append(str(edu.field_of_study).strip())
                
                degree_string = " / ".join(degree_details) if degree_details else "Degree"
                edu_detail += f"{degree_string} from {edu.institution}"

                # Append dates
                dates = []
                if edu.start_date:
                    dates.append(str(edu.start_date).strip())
                if edu.end_date:
                    dates.append(str(edu.end_date).strip())
                if dates:
                    edu_detail += f" ({' - '.join(dates)})"

                # Append GPA
                if edu.gpa is not None:
                    edu_detail += f" [GPA: {edu.gpa:.2f}]"
                
                education_lines.append(edu_detail)

            document_parts.append("\n".join(education_lines))

        # Certifications Section
        if profile.certifications:
            cert_lines = []
            for cert in profile.certifications:
                cert_detail = cert.name
                details = []
                if cert.issuing_organization:
                    details.append(f"issued by {cert.issuing_organization}")
                if cert.issue_date:
                    details.append(f"date: {cert.issue_date}")
                if details:
                    cert_detail += f" ({', '.join(details)})"
                cert_lines.append(cert_detail)
            
            document_parts.append(f"Certifications: {'; '.join(cert_lines)}")

        # Languages Section
        if profile.languages:
            document_parts.append(f"Languages: {', '.join(profile.languages)}")

        # Combine all parts with double newlines to form a clean document block
        full_document = "\n\n".join(document_parts)
        return full_document
