"""Application configuration module following clean architecture principles."""

from functools import lru_cache
from typing import Optional
from pathlib import Path

from pydantic import Field, field_validator, BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseModel):
    """Database-specific settings."""
    url: str = Field(
        default="sqlite:///app.db",
        description="Database connection URL"
    )
    echo: bool = Field(
        default=False,
        description="Enable SQL query logging"
    )
    track_modifications: bool = Field(
        default=False,
        description="Track modifications in SQLAlchemy"
    )


class APISettings(BaseModel):
    """External API settings."""
    openai_api_key: Optional[SecretStr] = Field(
        default=None,
        description="OpenAI API key for AI services"
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model to use"
    )
    openai_max_retries: int = Field(
        default=3,
        description="Maximum number of retries for OpenAI API calls"
    )
    openai_retry_delay: float = Field(
        default=1.0,
        description="Delay between retries for OpenAI API calls"
    )
    openai_timeout: float = Field(
        default=30.0,
        description="Timeout for OpenAI API calls in seconds"
    )


class ServiceSettings(BaseModel):
    """Service-specific settings."""
    backend_host: str = Field(
        default="localhost",
        description="Host for backend service"
    )
    backend_port: int = Field(
        default=5001,
        description="Port for Flask backend service"
    )
    frontend_port: int = Field(
        default=8501,
        description="Port for Streamlit frontend service"
    )
    debug_mode: bool = Field(
        default=True,
        description="Enable debug mode"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )


class Config(BaseSettings):
    """Application configuration following clean architecture principles."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        env_prefix="",
        extra="ignore"
    )

    # Environment
    env: str = Field(
        default="development",
        description="Application environment"
    )

    # Database settings
    database_url: str = Field(
        default="sqlite:///app.db",
        description="Database connection URL"
    )
    sql_echo: bool = Field(
        default=False,
        description="Enable SQL query logging"
    )
    track_modifications: bool = Field(
        default=False,
        description="Track modifications in SQLAlchemy"
    )

    # API settings
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key"
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model to use"
    )
    openai_max_retries: int = Field(
        default=3,
        description="Maximum number of retries for OpenAI API calls"
    )
    openai_retry_delay: float = Field(
        default=1.0,
        description="Delay between retries for OpenAI API calls"
    )
    openai_timeout: float = Field(
        default=30.0,
        description="Timeout for OpenAI API calls in seconds"
    )

    # Service settings
    backend_port: int = Field(
        default=5001,
        description="Backend service port"
    )
    frontend_port: int = Field(
        default=8501,
        description="Frontend service port"
    )
    debug_mode: bool = Field(
        default=True,
        description="Enable debug mode"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )

    @property
    def database(self) -> DatabaseSettings:
        """Get database settings."""
        return DatabaseSettings(
            url=self.database_url,
            echo=self.sql_echo,
            track_modifications=self.track_modifications
        )

    @property
    def api(self) -> APISettings:
        """Get API settings."""
        return APISettings(
            openai_api_key=SecretStr(self.openai_api_key) if self.openai_api_key else None,
            openai_model=self.openai_model,
            openai_max_retries=self.openai_max_retries,
            openai_retry_delay=self.openai_retry_delay,
            openai_timeout=self.openai_timeout
        )

    @property
    def service(self) -> ServiceSettings:
        """Get service settings."""
        return ServiceSettings(
            backend_host="localhost",
            backend_port=self.backend_port,
            frontend_port=self.frontend_port,
            debug_mode=self.debug_mode,
            log_level=self.log_level
        )

    @field_validator("env")
    def validate_env(cls, v: str) -> str:
        """Validate environment setting."""
        allowed = {"development", "testing", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return v

    @field_validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate logging level."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v = v.upper()
        if v not in allowed:
            raise ValueError(f"Log level must be one of: {allowed}")
        return v

    @field_validator("openai_api_key")
    def validate_api_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate API key."""
        if v is None or not v.strip():
            return None
        return v


@lru_cache
def get_config() -> Config:
    """Get cached configuration instance."""
    return Config()


# Export configuration instance
config = get_config() 