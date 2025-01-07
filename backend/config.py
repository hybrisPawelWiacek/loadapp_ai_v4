"""Configuration management for the application."""
import os
from typing import Dict, Any, Literal
from dataclasses import dataclass

# Type definitions
EnvironmentType = Literal['development', 'testing', 'staging', 'production']
LogLevel = Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']


@dataclass
class ServerConfig:
    """Server configuration settings."""
    HOST: str
    PORT: int
    DEBUG: bool


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    URL: str
    ECHO: bool
    TRACK_MODIFICATIONS: bool


@dataclass
class OpenAIConfig:
    """OpenAI API configuration settings."""
    API_KEY: str
    MODEL: str
    MAX_RETRIES: int
    RETRY_DELAY: float
    TIMEOUT: float


@dataclass
class GoogleMapsConfig:
    """Google Maps API configuration settings."""
    API_KEY: str
    MAX_RETRIES: int
    RETRY_DELAY: float
    TIMEOUT: float
    CACHE_TTL: int


@dataclass
class TollRateConfig:
    """Toll Rate API configuration settings."""
    API_KEY: str
    MAX_RETRIES: int
    RETRY_DELAY: float
    TIMEOUT: float


@dataclass
class LoggingConfig:
    """Logging configuration settings."""
    LEVEL: LogLevel


@dataclass
class FrontendConfig:
    """Frontend configuration settings."""
    PORT: int


@dataclass
class Config:
    """Application configuration."""
    # Environment
    ENV: EnvironmentType
    
    # Nested configurations
    SERVER: ServerConfig
    DATABASE: DatabaseConfig
    OPENAI: OpenAIConfig
    GOOGLE_MAPS: GoogleMapsConfig
    TOLL_RATE: TollRateConfig
    LOGGING: LoggingConfig
    FRONTEND: FrontendConfig

    @classmethod
    def from_env(cls) -> 'Config':
        """Create configuration from environment variables."""
        return cls(
            ENV=os.getenv('ENV', 'development'),
            
            SERVER=ServerConfig(
                HOST=os.getenv('HOST', 'localhost'),
                PORT=int(os.getenv('PORT', '5001')),
                DEBUG=os.getenv('DEBUG', 'true').lower() == 'true'
            ),
            
            DATABASE=DatabaseConfig(
                URL=os.getenv('DATABASE_URL', 'sqlite:///loadapp.db'),
                ECHO=os.getenv('SQL_ECHO', 'false').lower() == 'true',
                TRACK_MODIFICATIONS=os.getenv('TRACK_MODIFICATIONS', 'false').lower() == 'true'
            ),
            
            OPENAI=OpenAIConfig(
                API_KEY=os.getenv('OPENAI_API_KEY', ''),
                MODEL=os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview'),
                MAX_RETRIES=int(os.getenv('OPENAI_MAX_RETRIES', '3')),
                RETRY_DELAY=float(os.getenv('OPENAI_RETRY_DELAY', '1.0')),
                TIMEOUT=float(os.getenv('OPENAI_TIMEOUT', '30.0'))
            ),
            
            GOOGLE_MAPS=GoogleMapsConfig(
                API_KEY=os.getenv('GOOGLE_MAPS_API_KEY', ''),
                MAX_RETRIES=int(os.getenv('GMAPS_MAX_RETRIES', '3')),
                RETRY_DELAY=float(os.getenv('GMAPS_RETRY_DELAY', '1.0')),
                TIMEOUT=float(os.getenv('GMAPS_TIMEOUT', '30.0')),
                CACHE_TTL=int(os.getenv('GMAPS_CACHE_TTL', '3600'))
            ),
            
            TOLL_RATE=TollRateConfig(
                API_KEY=os.getenv('TOLL_RATE_API_KEY', ''),
                MAX_RETRIES=int(os.getenv('TOLL_RATE_MAX_RETRIES', '3')),
                RETRY_DELAY=float(os.getenv('TOLL_RATE_RETRY_DELAY', '1.0')),
                TIMEOUT=float(os.getenv('TOLL_RATE_TIMEOUT', '30.0'))
            ),
            
            LOGGING=LoggingConfig(
                LEVEL=os.getenv('LOG_LEVEL', 'INFO')
            ),
            
            FRONTEND=FrontendConfig(
                PORT=int(os.getenv('FRONTEND_PORT', '8501'))
            )
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'ENV': self.ENV,
            'SERVER': {
                'HOST': self.SERVER.HOST,
                'PORT': self.SERVER.PORT,
                'DEBUG': self.SERVER.DEBUG
            },
            'DATABASE': {
                'URL': self.DATABASE.URL,
                'ECHO': self.DATABASE.ECHO,
                'TRACK_MODIFICATIONS': self.DATABASE.TRACK_MODIFICATIONS
            },
            'OPENAI': {
                'API_KEY': self.OPENAI.API_KEY,
                'MODEL': self.OPENAI.MODEL,
                'MAX_RETRIES': self.OPENAI.MAX_RETRIES,
                'RETRY_DELAY': self.OPENAI.RETRY_DELAY,
                'TIMEOUT': self.OPENAI.TIMEOUT
            },
            'GOOGLE_MAPS': {
                'API_KEY': self.GOOGLE_MAPS.API_KEY,
                'MAX_RETRIES': self.GOOGLE_MAPS.MAX_RETRIES,
                'RETRY_DELAY': self.GOOGLE_MAPS.RETRY_DELAY,
                'TIMEOUT': self.GOOGLE_MAPS.TIMEOUT,
                'CACHE_TTL': self.GOOGLE_MAPS.CACHE_TTL
            },
            'TOLL_RATE': {
                'API_KEY': self.TOLL_RATE.API_KEY,
                'MAX_RETRIES': self.TOLL_RATE.MAX_RETRIES,
                'RETRY_DELAY': self.TOLL_RATE.RETRY_DELAY,
                'TIMEOUT': self.TOLL_RATE.TIMEOUT
            },
            'LOGGING': {
                'LEVEL': self.LOGGING.LEVEL
            },
            'FRONTEND': {
                'PORT': self.FRONTEND.PORT
            }
        } 