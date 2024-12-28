"""Unit tests for OpenAI service adapter."""
import pytest
from unittest.mock import Mock, patch

from backend.infrastructure.external_services.openai_service import (
    OpenAIService,
    OpenAIServiceError,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_TOKENS
)


@pytest.fixture
def mock_openai():
    """Create a mock OpenAI client."""
    with patch("backend.infrastructure.external_services.openai_service.OpenAI") as mock:
        yield mock


@pytest.fixture
def service(mock_openai):
    """Create an OpenAI service instance with mocked client."""
    return OpenAIService(api_key="test_key")


def test_initialization():
    """Test service initialization."""
    service = OpenAIService(api_key="test_key")
    assert service.api_key == "test_key"
    assert service.model == DEFAULT_MODEL
    assert service.temperature == DEFAULT_TEMPERATURE
    assert service.max_tokens == DEFAULT_MAX_TOKENS


def test_initialization_with_custom_params():
    """Test service initialization with custom parameters."""
    service = OpenAIService(
        api_key="test_key",
        model="gpt-4",
        temperature=0.8,
        max_tokens=1000
    )
    assert service.api_key == "test_key"
    assert service.model == "gpt-4"
    assert service.temperature == 0.8
    assert service.max_tokens == 1000


def test_initialization_without_api_key():
    """Test service initialization without API key."""
    with pytest.raises(ValueError, match="API key is required"):
        OpenAIService(api_key=None)


def test_generate_text_success(service, mock_openai):
    """Test successful text generation."""
    # Mock response
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Generated text"))]
    mock_openai.return_value.chat.completions.create.return_value = mock_response

    result = service.generate_text("Test prompt")
    assert result == "Generated text"

    # Verify the API was called with correct parameters
    mock_openai.return_value.chat.completions.create.assert_called_once_with(
        model=DEFAULT_MODEL,
        messages=[{"role": "user", "content": "Test prompt"}],
        temperature=DEFAULT_TEMPERATURE,
        max_tokens=DEFAULT_MAX_TOKENS
    )


def test_generate_text_with_custom_params(service, mock_openai):
    """Test text generation with custom parameters."""
    # Mock response
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Generated text"))]
    mock_openai.return_value.chat.completions.create.return_value = mock_response

    result = service.generate_text(
        "Test prompt",
        temperature=0.8,
        max_tokens=1000
    )
    assert result == "Generated text"

    # Verify the API was called with custom parameters
    mock_openai.return_value.chat.completions.create.assert_called_once_with(
        model=DEFAULT_MODEL,
        messages=[{"role": "user", "content": "Test prompt"}],
        temperature=0.8,
        max_tokens=1000
    )


def test_generate_text_api_error(service, mock_openai):
    """Test handling of API errors."""
    # Mock API error
    mock_openai.return_value.chat.completions.create.side_effect = Exception("API Error")

    with pytest.raises(OpenAIServiceError, match="Failed to generate text: API Error"):
        service.generate_text("Test prompt")


def test_generate_text_empty_response(service, mock_openai):
    """Test handling of empty API response."""
    # Mock empty response
    mock_response = Mock()
    mock_response.choices = []
    mock_openai.return_value.chat.completions.create.return_value = mock_response

    with pytest.raises(OpenAIServiceError, match="No response generated"):
        service.generate_text("Test prompt")


def test_generate_text_empty_prompt(service):
    """Test handling of empty prompt."""
    with pytest.raises(ValueError, match="Prompt cannot be empty"):
        service.generate_text("")


def test_generate_text_invalid_temperature(service):
    """Test handling of invalid temperature."""
    with pytest.raises(ValueError, match="Temperature must be between 0 and 1"):
        service.generate_text("Test prompt", temperature=1.5)

    with pytest.raises(ValueError, match="Temperature must be between 0 and 1"):
        service.generate_text("Test prompt", temperature=-0.5)


def test_generate_text_invalid_max_tokens(service):
    """Test handling of invalid max_tokens."""
    with pytest.raises(ValueError, match="Max tokens must be positive"):
        service.generate_text("Test prompt", max_tokens=0)

    with pytest.raises(ValueError, match="Max tokens must be positive"):
        service.generate_text("Test prompt", max_tokens=-100)


def test_generate_text_with_system_message(service, mock_openai):
    """Test text generation with system message."""
    # Mock response
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Generated text"))]
    mock_openai.return_value.chat.completions.create.return_value = mock_response

    system_message = "You are a helpful assistant."
    result = service.generate_text(
        "Test prompt",
        system_message=system_message
    )
    assert result == "Generated text"

    # Verify the API was called with system message
    mock_openai.return_value.chat.completions.create.assert_called_once_with(
        model=DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": "Test prompt"}
        ],
        temperature=DEFAULT_TEMPERATURE,
        max_tokens=DEFAULT_MAX_TOKENS
    )


def test_generate_text_with_conversation_history(service, mock_openai):
    """Test text generation with conversation history."""
    # Mock response
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Generated text"))]
    mock_openai.return_value.chat.completions.create.return_value = mock_response

    conversation_history = [
        {"role": "user", "content": "Previous message"},
        {"role": "assistant", "content": "Previous response"}
    ]
    result = service.generate_text(
        "Test prompt",
        conversation_history=conversation_history
    )
    assert result == "Generated text"

    # Verify the API was called with conversation history
    expected_messages = conversation_history + [{"role": "user", "content": "Test prompt"}]
    mock_openai.return_value.chat.completions.create.assert_called_once_with(
        model=DEFAULT_MODEL,
        messages=expected_messages,
        temperature=DEFAULT_TEMPERATURE,
        max_tokens=DEFAULT_MAX_TOKENS
    ) 