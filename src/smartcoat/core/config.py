from functools import lru_cache
from pathlib import Path

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
    enable_debug: bool = True
    voice_transcription_backend: str = "mlx_whisper"
    whisper_model: str = "mlx-community/whisper-small-mlx"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:7b"
    asset_root: Path = Path.home() / ".local" / "share" / "smartcoat" / "pilot-assets"
    max_upload_bytes: int = 25 * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
