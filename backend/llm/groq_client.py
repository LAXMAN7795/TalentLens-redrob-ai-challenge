import json
import logging
from typing import Type, TypeVar, Optional
from pydantic import BaseModel
from groq import Groq
from backend.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class GroqClient:
    """
    Reusable Groq API Client wrapper designed for fetching structured JSON responses.
    Leverages Groq's JSON Mode to guarantee output format alignment.
    """
    def __init__(self):
        if not settings.GROQ_API_KEY:
            logger.critical("GROQ_API_KEY environment variable is empty or not set.")
            raise ValueError("GROQ_API_KEY is not configured.")
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.default_model = settings.GROQ_MODEL

    def get_structured_completion(
        self,
        prompt: str,
        system_instruction: str,
        response_model: Type[T],
        model: Optional[str] = None
    ) -> Optional[T]:
        """
        Sends requests to Groq, enforces JSON mode, and parses the output directly into Pydantic models.
        """
        model = model or self.default_model
        
        # Extract model JSON schema to guide the LLM context
        schema_definition = json.dumps(response_model.model_json_schema(), indent=2)
        
        # Enforce JSON formatting instructions in the system instructions
        complete_system_instruction = (
            f"{system_instruction}\n\n"
            f"You MUST return a JSON object conforming exactly to this JSON schema:\n"
            f"{schema_definition}\n\n"
            "CRITICAL: Do NOT wrap your response in markdown code blocks like ```json ... ```. "
            "Output the raw JSON string only. Ensure all required properties are present."
        )

        try:
            logger.info(f"Dispatching structured Groq request using model: {model}")
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": complete_system_instruction},
                    {"role": "user", "content": prompt}
                ],
                model=model,
                response_format={"type": "json_object"},
                temperature=0.0,  # Zero-temp for maximum reproducibility and deterministic extraction
                max_tokens=2048
            )

            raw_content = response.choices[0].message.content
            if not raw_content:
                logger.error("Received empty content response from Groq client.")
                return None

            # Parse and load Pydantic schema
            parsed_json = json.loads(raw_content)
            validated_model = response_model.model_validate(parsed_json)
            logger.info("Successfully fetched and validated model from Groq response.")
            return validated_model

        except json.JSONDecodeError as json_exc:
            logger.error(f"Failed to decode JSON from Groq response. Content: {raw_content}. Error: {json_exc}")
            return None
        except Exception as exc:
            logger.error(f"Unexpected error communicating with Groq API: {exc}")
            return None
