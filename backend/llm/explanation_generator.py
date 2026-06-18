import logging
from typing import Optional
from backend.core.schemas import CandidateProfile, JobDescription, CandidateScoreBreakdown, CandidateExplanation
from backend.llm.groq_client import GroqClient

logger = logging.getLogger(__name__)

class ExplanationGenerator:
    """
    Generates personalized recruiter explanations, list of strengths,
    career concerns, and tailored interview questions for candidate profiles.
    Leverages Groq LLM with a rule-based offline template backup.
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
                    logger.warning(f"Could not initialize GroqClient, using fallback: {exc}")
                    self.groq_client = None

    def generate_explanation(
        self,
        profile: CandidateProfile,
        jd: JobDescription,
        breakdown: CandidateScoreBreakdown
    ) -> CandidateExplanation:
        """
        Generates recruiter analysis cards.
        Uses Groq if available; falls back to rule-based templating if offline or disabled.
        """
        if not self.groq_client:
            logger.debug(f"GroqClient not provided. Generating template fallback for ID: {profile.candidate_id}")
            return self._generate_fallback_explanation(profile, jd, breakdown)

        system_instruction = (
            "You are a Senior Executive Talent Acquisition Consultant. Your job is to draft a concise, "
            "highly professional recruiting summary about a candidate, based on their scoring metrics "
            "and resume text compared to the Job Description."
        )

        prompt = (
            f"Candidate: {profile.name} (ID: {profile.candidate_id})\n"
            f"Job Description: {jd.title}\n\n"
            f"Candidate Scoring Metrics:\n"
            f"- Composite Score: {breakdown.final_score}/100\n"
            f"- Semantic Fit: {breakdown.semantic_score}/100\n"
            f"- Skills Match: {breakdown.skill_score}/100\n"
            f"- Career Trajectory: {breakdown.career_score}/100\n"
            f"- Soft Skills: {breakdown.behavioral_score}/100\n"
            f"- Education Level: {breakdown.education_score}/100\n"
            f"- Flagged Cheating/Honeypot Penalty: {breakdown.honeypot_penalty} points\n\n"
            f"Candidate Summary:\n{profile.summary or 'No summary provided.'}\n\n"
            f"Candidate Skills Inventory: {', '.join(profile.skills)}\n\n"
            f"Candidate Experience History:\n"
        )

        for exp in profile.experience:
            prompt += f"- {exp.title} at {exp.company}: {exp.description or ''}\n"

        prompt += (
            "\nBased on this details, please output a JSON object containing:\n"
            "1. fit_summary: A 2-3 sentence recruiter synthesis of the candidate's alignment.\n"
            "2. strengths: 2-3 bullet points of technical or career highlights.\n"
            "3. concerns: 1-2 bullet points flagging experience gaps, missing technologies, or high job change rate (or null if none).\n"
            "4. interview_questions: 2 tailored screening questions focusing on their background/concerns.\n"
        )

        try:
            explanation = self.groq_client.get_structured_completion(
                prompt=prompt,
                system_instruction=system_instruction,
                response_model=CandidateExplanation
            )
            if explanation:
                return explanation
        except Exception as exc:
            logger.error(f"Failed to generate LLM explanation: {exc}. Invoking fallback.")

        return self._generate_fallback_explanation(profile, jd, breakdown)

    def _generate_fallback_explanation(
        self,
        profile: CandidateProfile,
        jd: JobDescription,
        breakdown: CandidateScoreBreakdown
    ) -> CandidateExplanation:
        """
        Rule-based template generator when LLM API is unavailable.
        Uses exact scoring numbers and skill intersections to draft feedback.
        """
        # Determine fit tier
        if breakdown.final_score >= 80.0:
            tier_desc = "excellent fit"
        elif breakdown.final_score >= 60.0:
            tier_desc = "solid, qualified candidate"
        else:
            tier_desc = "moderate match with some experience gaps"

        fit_summary = (
            f"{profile.name} is assessed as a {tier_desc} for the {jd.title} position, "
            f"achieving a composite ranking score of {breakdown.final_score:.1f}/100.0. "
            f"Their semantic profile shows a {breakdown.semantic_score:.1f}% similarity to the role's details."
        )

        # Identify strengths
        strengths = []
        required_skills_lower = [s.lower() for s in jd.skills_required]
        candidate_skills_lower = [s.lower() for s in profile.skills]
        
        matched_skills = [s for s in profile.skills if s.lower() in required_skills_lower]
        if matched_skills:
            strengths.append(f"Demonstrated core competence in key technical areas: {', '.join(matched_skills[:3])}.")
        else:
            strengths.append("Possesses general technical developer skill sets.")

        if breakdown.career_score >= 80.0:
            strengths.append("Displays strong career progression and stable tenure history.")
        elif breakdown.behavioral_score >= 75.0:
            strengths.append("Expresses positive communication and execution signals in experience summaries.")

        # Identify concerns
        concerns = []
        missing_skills = [s for s in jd.skills_required if s.lower() not in candidate_skills_lower]
        if missing_skills:
            concerns.append(f"Lacks explicit profile matching for required technologies: {', '.join(missing_skills[:2])}.")
            
        if breakdown.career_score < 50.0:
            concerns.append("Flags potential tenure stability or job-hopping pattern.")
            
        if breakdown.honeypot_penalty > 0.0:
            concerns.append("Scoring penalizations applied due to keyword stuffing pattern detection.")

        if not concerns:
            concerns.append("No critical career gaps or missing technologies flagged.")

        # Generate interview questions
        questions = []
        if missing_skills:
            questions.append(f"Can you discuss your familiarity with {missing_skills[0]} and how you would apply it to this role?")
        else:
            questions.append("Can you tell us about a challenging technical project you delivered recently?")
            
        if breakdown.career_score < 60.0:
            questions.append("What details can you share about your recent job transitions and what you look for in long-term roles?")
        else:
            questions.append("How do you typically coordinate with stakeholders to gather technical requirements?")

        return CandidateExplanation(
            candidate_id=profile.candidate_id,
            fit_summary=fit_summary,
            strengths=strengths,
            concerns=concerns,
            interview_questions=questions
        )
