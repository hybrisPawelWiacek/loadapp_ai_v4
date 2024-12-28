"""Configuration module."""
from functools import lru_cache
from typing import Optional

from pydantic import BaseModel, SecretStr


class APISettings(BaseModel):
    """API settings."""
    # Google Maps settings
    google_maps_api_key: Optional[SecretStr] = None
    gmaps_max_retries: int = 3
    gmaps_retry_delay: float = 1.0
    gmaps_timeout: float = 10.0
    
    # OpenAI settings
    openai_api_key: Optional[SecretStr] = None
    openai_model: str = "gpt-4"
    openai_max_tokens: int = 2000
    openai_temperature: float = 0.7
    openai_timeout: float = 30.0
    openai_max_retries: int = 3
    openai_retry_delay: float = 1.0


class Settings(BaseModel):
    """Application settings."""
    api: APISettings = APISettings()


@lru_cache()
def get_settings() -> Settings:
    """Get application settings.
    
    Returns:
        Settings: Application settings
    """
    return Settings() 