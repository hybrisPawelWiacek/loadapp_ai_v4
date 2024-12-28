"""Test fixtures for external services."""
import pytest
from unittest.mock import Mock, patch

from backend.infrastructure.external_services.google_maps_service import GoogleMapsService
from backend.infrastructure.external_services.openai_service import OpenAIService
from backend.infrastructure.external_services.toll_rate_service import TollRateService


@pytest.fixture
def mock_googlemaps():
    """Create a mock Google Maps client."""
    with patch("backend.infrastructure.external_services.google_maps_service.googlemaps.Client") as mock:
        instance = Mock()
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_openai():
    """Create a mock OpenAI client."""
    with patch("backend.infrastructure.external_services.openai_service.openai") as mock:
        yield mock


@pytest.fixture
def mock_toll_service():
    """Create a mock toll rate service."""
    with patch("backend.infrastructure.external_services.toll_rate_service.requests") as mock:
        yield mock


@pytest.fixture
def google_maps_service(test_config, mock_googlemaps):
    """Create a Google Maps service instance with test configuration."""
    return GoogleMapsService(
        api_key=test_config.GOOGLE_MAPS.API_KEY,
        timeout=test_config.GOOGLE_MAPS.TIMEOUT,
        max_retries=test_config.GOOGLE_MAPS.MAX_RETRIES,
        retry_delay=test_config.GOOGLE_MAPS.RETRY_DELAY
    )


@pytest.fixture
def openai_service(test_config, mock_openai):
    """Create an OpenAI service instance with test configuration."""
    return OpenAIService(
        api_key=test_config.OPENAI.API_KEY,
        model=test_config.OPENAI.MODEL,
        timeout=test_config.OPENAI.TIMEOUT,
        max_retries=test_config.OPENAI.MAX_RETRIES,
        retry_delay=test_config.OPENAI.RETRY_DELAY
    )


@pytest.fixture
def toll_rate_service(mock_toll_service):
    """Create a toll rate service instance."""
    return TollRateService() 