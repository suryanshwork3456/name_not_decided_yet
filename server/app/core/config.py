# ============================================================
# File: app/core/config.py
# ============================================================
"""
Centralized application settings using Pydantic BaseSettings.
Loads environment variables such as DB connection URL, JWT secret key,
external API keys (satellite/weather providers), and Redis config.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    SECRET_KEY: str
    PORT: int = 8000

    model_config = SettingsConfigDict(env_file=".env",env_file_encoding="utf-8")

settings = Settings()