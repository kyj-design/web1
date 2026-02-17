"""
Configuration management for Canva-Etsy Automation system.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from functools import lru_cache
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Etsy API
    etsy_api_key: str
    etsy_shared_secret: str
    etsy_callback_url: str = "http://localhost:3000/auth/callback"

    # AI/LLM Provider
    llm_provider: Literal["ollama", "openai"] = "ollama"
    ollama_model: str = "llama3:8b"
    ollama_base_url: str = "http://localhost:11434"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4"

    # Database
    database_url: str = "sqlite:///./canva_etsy.db"

    # eRank API (optional)
    erank_api_key: str | None = None

    # Redis (for Celery, optional)
    redis_url: str = "redis://localhost:6379/0"

    # CORS
    frontend_url: str = "http://localhost:3000"

    # File Storage
    upload_dir: str = "./backend/uploads"
    pdf_dir: str = "./backend/static/pdfs"
    image_dir: str = "./backend/static/images"

    # Logging
    log_level: str = "INFO"

    # Model Configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to avoid reloading .env file on every call.
    """
    return Settings()


# For convenience
settings = get_settings()
