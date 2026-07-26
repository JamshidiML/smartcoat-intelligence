from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings for SmartCoat."""

    model_config = SettingsConfigDict(env_prefix="SMARTCOAT_", env_file=".env", extra="ignore")

    env: str = "development"
    app_name: str = "SmartCoat Intelligence"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = "postgresql+psycopg://smartcoat:smartcoat@localhost:5432/smartcoat"
    secret_key: str = "change-me"
    knowledge_cursor_signing_key: SecretStr | None = None
    enable_debug: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
