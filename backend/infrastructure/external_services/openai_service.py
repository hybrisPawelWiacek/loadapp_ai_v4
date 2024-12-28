"""OpenAI service implementation."""
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from openai import OpenAI, OpenAIError
from openai.types.chat import ChatCompletion, ChatCompletionMessage
import httpx

from ...domain.entities.route import Route, Location
from ...infrastructure.logging import get_logger
from ...config import get_settings


# Default settings
DEFAULT_MODEL = "gpt-4-turbo-preview"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 500


class OpenAIServiceError(Exception):
    """Custom exception for OpenAI service errors."""
    pass


logger = get_logger()


class OpenAIService:
    """OpenAI service for route descriptions and insights."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS
    ):
        """Initialize OpenAI service.
        
        Args:
            api_key: Optional API key (defaults to settings.openai_api_key)
            model: Model to use for completions
            temperature: Temperature for completions
            max_tokens: Maximum tokens for completions
            
        Raises:
            ValueError: If API key is not found
            ValueError: If temperature is not between 0 and 1
            ValueError: If max_tokens is not positive
        """
        self._logger = logger.bind(service="openai")
        settings = get_settings()
        
        # Validate parameters
        if temperature < 0 or temperature > 1:
            raise ValueError("Temperature must be between 0 and 1")
        if max_tokens <= 0:
            raise ValueError("Max tokens must be positive")
        
        # Get API key from settings if not provided
        if api_key is None:
            if settings.api.openai_api_key:
                self.api_key = settings.api.openai_api_key.get_secret_value()
            else:
                raise ValueError("API key is required")
        else:
            self.api_key = api_key
            
        # Store parameters
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        try:
            # Create a basic httpx client with timeout settings
            http_client = httpx.Client(
                timeout=settings.api.openai_timeout
            )
            
            # Initialize OpenAI with custom http client
            self.client = OpenAI(
                api_key=self.api_key,
                http_client=http_client
            )
            self._logger.info("OpenAI client initialized successfully")
        except Exception as e:
            self._logger.error("Failed to initialize OpenAI client", error=str(e))
            raise OpenAIServiceError(f"Failed to initialize OpenAI client: {str(e)}")

    def generate_text(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate text using the OpenAI API.
        
        Args:
            prompt: The prompt to generate text from
            system_message: Optional system message to set context
            conversation_history: Optional conversation history
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            
        Returns:
            str: Generated text
            
        Raises:
            ValueError: If prompt is empty
            ValueError: If temperature is invalid
            ValueError: If max_tokens is invalid
            OpenAIServiceError: If API request fails
        """
        if not prompt:
            raise ValueError("Prompt cannot be empty")
            
        if temperature is not None and (temperature < 0 or temperature > 1):
            raise ValueError("Temperature must be between 0 and 1")
            
        if max_tokens is not None and max_tokens <= 0:
            raise ValueError("Max tokens must be positive")
        
        # Build messages list
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens
            )
            
            if not response.choices:
                raise OpenAIServiceError("No response generated")
                
            return response.choices[0].message.content or ""
            
        except OpenAIError as e:
            self._logger.error("OpenAI API error", error=str(e))
            raise OpenAIServiceError(f"Failed to generate text: {str(e)}")
        except OpenAIServiceError:
            raise
        except Exception as e:
            self._logger.error("Unexpected error", error=str(e))
            raise OpenAIServiceError(f"Failed to generate text: {str(e)}")

    def _format_location(self, location: Location) -> str:
        """Format location for prompt.
        
        Args:
            location: Location object
            
        Returns:
            str: Formatted location string
        """
        return location.address 