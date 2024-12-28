"""Test configuration and shared fixtures."""
import pytest
from pathlib import Path
import sys

# Add backend directory to path
backend_dir = Path(__file__).parent.parent / 'backend'
if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))

from backend.config import (
    Config, ServerConfig, DatabaseConfig,
    OpenAIConfig, GoogleMapsConfig, LoggingConfig,
    FrontendConfig
)


@pytest.fixture
def test_config() -> Config:
    """Create test configuration."""
    return Config(
        ENV='testing',
        SERVER=ServerConfig(
            HOST='localhost',
            PORT=5001,
            DEBUG=True
        ),
        DATABASE=DatabaseConfig(
            URL='sqlite:///:memory:',
            ECHO=False,
            TRACK_MODIFICATIONS=False
        ),
        OPENAI=OpenAIConfig(
            API_KEY='test-openai-key',
            MODEL='gpt-4o-mini',
            MAX_RETRIES=1,
            RETRY_DELAY=0.1,
            TIMEOUT=1.0
        ),
        GOOGLE_MAPS=GoogleMapsConfig(
            API_KEY='test-gmaps-key',
            MAX_RETRIES=1,
            RETRY_DELAY=0.1,
            TIMEOUT=1.0,
            CACHE_TTL=60
        ),
        LOGGING=LoggingConfig(
            LEVEL='DEBUG'
        ),
        FRONTEND=FrontendConfig(
            PORT=8501
        )
    ) 