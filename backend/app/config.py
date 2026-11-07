from pathlib import Path
from functools import lru_cache
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")
    llm_provider: Literal["gemini", "openai"] = "gemini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    tavily_api_key: str = ""
    youtube_api_key: str = ""
    google_books_api_key: str = ""
    database_url: str = f"sqlite:///{(BACKEND_DIR / 'lessonforge.db').as_posix()}"
    request_timeout: float = Field(default=30, gt=0, le=180)
    llm_timeout: float = Field(default=120, gt=0, le=600)
    max_sources_per_provider: int = Field(default=5, ge=1, le=10)
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"


@lru_cache
def get_settings():
    return Settings()
