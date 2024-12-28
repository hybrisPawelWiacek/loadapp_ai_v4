"""OpenAI service implementation."""
import time
from typing import Optional, Dict, Any, List
import httpx

from openai import OpenAI, OpenAIError, RateLimitError, APIError, APITimeoutError

from ...infrastructure.logging import get_logger
from ...infrastructure.external_services.exceptions import ExternalServiceError


# Default configuration values
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 200


class OpenAIServiceError(ExternalServiceError):
    """Specific exception for OpenAI service errors."""
    pass


logger = get_logger()


class OpenAIService:
    """OpenAI service for content enhancement."""

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """Initialize OpenAI service.
        
        Args:
            api_key: OpenAI API key
            model: Model to use for completions
            temperature: Sampling temperature
            max_tokens: Maximum number of tokens to generate
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds
            
        Raises:
            ValueError: If API key is not provided or parameters are invalid
        """
        if not api_key:
            raise ValueError("API key is required")
        if not 0 <= temperature <= 1:
            raise ValueError("Temperature must be between 0 and 1")
        if max_tokens <= 0:
            raise ValueError("Max tokens must be positive")

        self._logger = logger.bind(service="openai")
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout

        try:
            # Create a basic httpx client with timeout settings
            http_client = httpx.Client(
                timeout=timeout
            )
            
            # Initialize OpenAI with custom http client
            self.client = OpenAI(
                api_key=api_key,
                http_client=http_client
            )
            self._logger.info("OpenAI client initialized successfully")
        except Exception as e:
            self._logger.error("Failed to initialize OpenAI client", error=str(e))
            raise OpenAIServiceError(f"Failed to initialize OpenAI client: {str(e)}")

    def _make_request(self, request_func: callable, *args, **kwargs) -> str:
        """Make a request to OpenAI API with retry logic."""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                return request_func(*args, **kwargs)
            except RateLimitError as e:
                last_error = e
                if attempt == self.max_retries - 1:
                    self._logger.error(
                        "OpenAI rate limit error",
                        error=str(e),
                        attempt=attempt + 1,
                        max_retries=self.max_retries
                    )
                    break
                self._logger.warning(
                    "OpenAI rate limit error, retrying",
                    error=str(e),
                    attempt=attempt + 1,
                    retry_delay=self.retry_delay * (attempt + 1)
                )
                time.sleep(self.retry_delay * (attempt + 1))
            except (APIError, APITimeoutError) as e:
                self._logger.error("OpenAI API error", error=str(e))
                raise OpenAIServiceError(f"Failed to generate text: {str(e)}")
            except Exception as e:
                self._logger.error("Unexpected error in OpenAI request", error=str(e))
                raise OpenAIServiceError(f"Failed to generate text: {str(e)}")

        if last_error:
            raise OpenAIServiceError(f"Failed after {self.max_retries} retries: {str(last_error)}")

    def generate_text(
        self, 
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_message: Optional[str] = None,
        conversation_history: Optional[list] = None
    ) -> str:
        """Generate text using the OpenAI API.
        
        Args:
            prompt: The prompt to generate text from
            temperature: Optional override for sampling temperature
            max_tokens: Optional override for maximum tokens
            system_message: Optional system message to prepend
            conversation_history: Optional conversation history
            
        Returns:
            Generated text response
            
        Raises:
            ValueError: If prompt is empty or parameters are invalid
            OpenAIServiceError: If API request fails
        """
        if not prompt:
            raise ValueError("Prompt cannot be empty")
        if temperature is not None and not 0 <= temperature <= 1:
            raise ValueError("Temperature must be between 0 and 1")
        if max_tokens is not None and max_tokens <= 0:
            raise ValueError("Max tokens must be positive")

        try:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            if conversation_history:
                messages.extend(conversation_history)
            messages.append({"role": "user", "content": prompt})

            response = self._make_request(
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature or self.temperature,
                    max_tokens=max_tokens or self.max_tokens
                )
            )

            if not response.choices:
                raise OpenAIServiceError("No response generated")

            return response.choices[0].message.content.strip()

        except OpenAIServiceError:
            raise
        except Exception as e:
            self._logger.error("Failed to generate text", error=str(e))
            raise OpenAIServiceError(f"Failed to generate text: {str(e)}")

    def generate_offer_content(self, price: float, margin: float) -> str:
        """Generate enhanced offer content."""
        prompt = (
            f"Generate a professional transport offer description for a route "
            f"with a total price of {price:.2f} EUR and a margin of {margin:.1f}%. "
            f"Focus on value proposition and reliability. Keep it concise."
        )
        return self.generate_text(prompt, max_tokens=200, temperature=0.7)

    def generate_fun_fact(self) -> str:
        """Generate a transport-related fun fact."""
        prompt = (
            "Share an interesting and brief fun fact about transportation, "
            "logistics, or the history of cargo movement. Keep it to one sentence."
        )
        return self.generate_text(prompt, max_tokens=100, temperature=0.8) 