from datetime import date
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_anon_key: str = ""  # only used by scripts/get_token.py
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-5"
    frontend_origin: str = "http://localhost:5173"
    # Pins "today" for contact-card availability (YYYY-MM-DD), so a demo on a
    # weekend still shows who's in. Leave empty to use the real date.
    demo_date: date | None = None

    @field_validator("demo_date", mode="before")
    @classmethod
    def empty_demo_date(cls, v):
        return v or None


@lru_cache
def get_settings() -> Settings:
    return Settings()
