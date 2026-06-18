from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and the local .env file.
    """
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    GROQ_API_KEY: str = Field(..., description="Groq API Key")
    GROQ_MODEL: str = Field("llama-3.3-70b-versatile", description="Default model for structured extraction")
    DATABASE_URL: str = Field("sqlite:///./talentlens.db", description="Database connection URL")

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def clean_database_url(cls, v: str) -> str:
        """Sanitizes connection prefixes, modifying deprecated postgres:// to postgresql://."""
        if isinstance(v, str) and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

# Global configurations instance
settings = Settings()
