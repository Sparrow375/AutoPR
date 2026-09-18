"""
AutoPR Configuration — Central Settings

All configuration values flow through this class.
Never hardcode API keys, URLs, or model names in agent/tool code.
Always import and use `get_settings()`.

Usage:
    from autopr.config.settings import get_settings
    settings = get_settings()
    print(settings.gemini_api_key)
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    # ---- Google / Gemini ----
    gemini_api_key: str = ""

    # ---- Linear ----
    linear_api_key: str = ""

    # ---- GitHub ----
    github_token: str = ""
    github_repo_owner: str = ""
    github_repo_name: str = "AutoPR"

    # ---- Discord ----
    discord_webhook_url: str = ""

    # ---- Optional: Local LLM (Ollama) ----
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma3"

    # ---- Server Config ----
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # ---- Model Configuration ----
    default_model: str = "gemini-2.5-flash"
    planning_model: str = "gemini-2.5-pro"
    coding_model: str = "gemini-2.5-flash"
    review_model: str = "gemini-2.5-pro"

    # ---- Agent Behavior ----
    max_retry_attempts: int = Field(default=3, ge=1, le=10)
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)

    # ---- RAG ----
    rag_top_k: int = Field(default=10, ge=1, le=50)
    rag_chunk_size: int = Field(default=500, ge=100, le=2000)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance. Call once at startup."""
    return Settings()
