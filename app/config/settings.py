"""
SurveyAI Backend

Module:
Configuration

Purpose:
Application settings loaded from environment variables.

Author:
Purujeet Kumar

Version:
1.0
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Global application configuration.
    """

    APP_NAME: str
    APP_VERSION: str

    APP_ENV: str
    APP_DEBUG: bool

    HOST: str
    PORT: int

    SECRET_KEY: str

    LOG_LEVEL: str
    
    DATABASE_URL:str

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    """
    return Settings()


settings = get_settings()