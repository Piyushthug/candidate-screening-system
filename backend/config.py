"""Configuration for candidate screening system."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # API Keys
    google_api_key: str

    # Database
    database_url: str = "sqlite:///./candidate_screening.db"

    # Server
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True

    # LLM Configuration
    llm_model: str = "gpt-4-turbo-preview"
    llm_temperature: float = 0.3

    # Screening Configuration
    max_retries: int = 2
    approval_required: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
