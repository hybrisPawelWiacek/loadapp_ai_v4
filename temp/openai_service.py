"""OpenAI service implementation."""
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID
import time
from datetime import timezone as tz

from openai import OpenAI, OpenAIError
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
import httpx

from src.domain.entities.route import Route
from src.domain.interfaces.services.ai_service import AIService, AIServiceError
from src.infrastructure.logging import get_logger
from src.settings import get_settings
from src.domain.value_objects import Location

logger = get_logger()

def utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(tz.utc)

class OpenAIService(AIService):
    """OpenAI API implementation of AIService."""

    def __init__(self, api_key: str = None):
        """Initialize OpenAI service."""
        settings = get_settings()
        api_settings = settings.api
        
        # Get API key with proper error handling
        try:
            self.api_key = (api_key if api_key else 
                       api_settings.openai_api_key.get_secret_value() if api_settings.openai_api_key 
                       else None)
        except Exception as e:
            raise AIServiceError(
                message=f"Error accessing API key: {str(e)}",
                code="API_KEY_ERROR",
                details={"error_type": type(e).__name__},
                original_error=e
            )
            
        if not self.api_key:
            raise AIServiceError(
                message="OpenAI API key not found in settings or environment",
                code="API_KEY_MISSING"
            )

        # Store other settings
        self.model = api_settings.openai_model
        self.max_retries = api_settings.openai_max_retries
        self.retry_delay = api_settings.openai_retry_delay
        
        try:
            # Create a basic httpx client with just timeout settings
            http_client = httpx.Client(
                timeout=api_settings.openai_timeout
            )
            
            # Initialize OpenAI with custom http client
            self.client = OpenAI(
                api_key=self.api_key,
                http_client=http_client
            )
        except Exception as e:
            raise AIServiceError(
                message=f"Failed to initialize OpenAI client: {str(e)}",
                code="CLIENT_INIT_ERROR",
                details={
                    "error_type": type(e).__name__,
                    "error_details": str(e)
                },
                original_error=e
            )

    def _make_request(self, messages: List[Dict[str, str]], **kwargs: Dict[str, Any]) -> ChatCompletion:
        """Make a request to OpenAI API with retry logic.
        
        Args:
            messages: List of message dictionaries
            **kwargs: Additional arguments for the API call
            
        Returns:
            ChatCompletion: API response
            
        Raises:
            AIServiceError: If request fails after retries
        """
        for attempt in range(self.max_retries):
            try:
                return self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    **kwargs
                )
            except OpenAIError as e:
                if attempt == self.max_retries - 1:
                    raise AIServiceError(
                        message=f"OpenAI API error after {self.max_retries} retries: {str(e)}",
                        code="API_ERROR",
                        details={
                            "error_type": type(e).__name__,
                            "error_details": str(e)
                        }
                    )
                time.sleep(self.retry_delay * (attempt + 1))
            except Exception as e:
                raise AIServiceError(
                    message=f"Unexpected error in OpenAI request: {str(e)}",
                    code="REQUEST_ERROR",
                    details={
                        "error_type": type(e).__name__,
                        "error_details": str(e)
                    }
                )

    def _format_location(self, location: Location) -> str:
        """Format location for prompt.
        
        Args:
            location: Location object
            
        Returns:
            str: Formatted location string
        """
        if location.address:
            return location.address
        elif location.city:
            return f"{location.city}, {location.country}"
        return "Unknown Location"

    def generate_route_fact(self, origin: Location, destination: Location, context: Optional[Dict] = None) -> str:
        """Generate an interesting fact about a route.
        
        Args:
            origin: Origin location
            destination: Destination location
            context: Optional additional context
            
        Returns:
            str: An interesting fact about the route
            
        Raises:
            AIServiceError: If fact generation fails
        """
        prompt = (
            f"Generate a brief, interesting fact about a route from {self._format_location(origin)} "
            f"to {self._format_location(destination)}"
        )
        if context:
            prompt += f" considering: {context}"
        return self.generate_response(prompt, temperature=0.7, max_tokens=100)

    def enhance_route_description(self, origin: Location, destination: Location, distance_km: float, duration_hours: float, context: Optional[Dict] = None) -> str:
        """Generate an enhanced description of a route with logistics-relevant information.
        
        Args:
            origin: Origin location
            destination: Destination location
            distance_km: Distance of the route in kilometers
            duration_hours: Duration of the route in hours
            context: Optional additional context with keys like:
                    - transport_type: Type of transport being used
                    - cargo_type: Type of cargo being transported
                    - special_requirements: Any special transport requirements
                    
        Returns:
            str: Enhanced route description with logistics insights
            
        Raises:
            AIServiceError: If description generation fails
        """
        system_prompt = (
            "You are a logistics route analyst specializing in freight transport routes. "
            "Provide detailed route descriptions that focus on logistics-relevant information such as:"
            "\n- Major highways and transport corridors"
            "\n- Known traffic patterns or bottlenecks"
            "\n- Rest stops and service areas"
            "\n- Border crossings or administrative boundaries"
            "\n- Weather considerations"
            "\n- Special considerations for freight transport"
        )
        
        user_prompt = (
            f"Analyze the transport route from {self._format_location(origin)} to {self._format_location(destination)}.\n"
            f"Distance: {distance_km:.1f} km\n"
            f"Duration: {duration_hours:.1f} hours\n"
        )
        
        if context:
            user_prompt += "\nAdditional context:\n"
            for key, value in context.items():
                user_prompt += f"- {key}: {value}\n"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = self._make_request(messages, temperature=0.7, max_tokens=500)
            return response.choices[0].message.content or ""
        except AIServiceError as e:
            raise AIServiceError(
                message=f"Failed to generate route description: {str(e)}",
                code="DESCRIPTION_GENERATION_ERROR",
                details={
                    "error_type": type(e).__name__,
                    "error_details": str(e)
                }
            )

    def generate_response(self, prompt: str, **kwargs: Dict[str, Any]) -> str:
        """Generate a response from the AI model.

        Args:
            prompt: The input prompt for the AI model.
            **kwargs: Additional arguments to pass to the AI model.

        Returns:
            The generated response as a string.

        Raises:
            AIServiceError: If there is an error generating the response.
        """
        messages = [
            {"role": "system", "content": "You are a helpful assistant that provides informative and engaging responses about transportation routes."},
            {"role": "user", "content": prompt}
        ]
        try:
            response = self._make_request(messages, **kwargs)
            return response.choices[0].message.content or ""
        except AIServiceError as e:
            raise AIServiceError(
                message=f"Failed to generate response: {str(e)}",
                code="RESPONSE_GENERATION_ERROR",
                details={
                    "error_type": type(e).__name__,
                    "error_details": str(e)
                }
            )
        except Exception as e:
            raise AIServiceError(
                message=f"Unexpected error in response generation: {str(e)}",
                code="RESPONSE_GENERATION_ERROR",
                details={
                    "error_type": type(e).__name__,
                    "error_details": str(e)
                }
            )

    def generate_route_description(self, route: Route) -> str:
        """Generate an enhanced description of the route using AI."""
        ai_logger = logger.bind(service="openai", route_id=str(route.id))
        ai_logger.info("generating_route_description")
        ai_logger.debug("route_data", origin=route.origin, destination=route.destination)
        
        try:
            # Extract location info safely with fallbacks
            origin_addr = self._format_location(route.origin)
            dest_addr = self._format_location(route.destination)
            
            messages = [
                {"role": "system", "content": "You are a helpful assistant that generates concise route descriptions for a logistics company."},
                {"role": "user", "content": f"Generate a brief, professional description for a transport route from {origin_addr} to {dest_addr}. Distance: {route.distance_km:.1f} km, Duration: {route.duration_hours:.1f} hours"}
            ]
            
            response = self._make_request(messages)
            description = response.choices[0].message.content.strip()
            ai_logger.info("description_generated", length=len(description))
            return description
        except Exception as e:
            ai_logger.error("description_generation_failed", error=str(e))
            raise AIServiceError(
                message=f"Failed to generate route description: {str(e)}",
                code="DESCRIPTION_GENERATION_ERROR",
                details={
                    "error_type": type(e).__name__,
                    "error_details": str(e)
                }
            )

    def generate_fun_fact(self, route: Route) -> str:
        """Generate an interesting fact about the route using AI."""
        ai_logger = logger.bind(service="openai", route_id=str(route.id))
        ai_logger.info("generating_fun_fact")
        ai_logger.debug("route_data", origin=route.origin, destination=route.destination)
        
        try:
            # Use address and country for location info
            origin_location = route.origin.address
            origin_country = route.origin.country or 'Unknown Country'
            dest_location = route.destination.address
            dest_country = route.destination.country or 'Unknown Country'
            
            messages = [
                {"role": "system", "content": "You are a helpful assistant that generates interesting facts about transport routes."},
                {"role": "user", "content": f"Generate a brief, interesting fact about a transport route from {origin_location} to {dest_location}. Make it relevant to logistics or transportation."}
            ]
            
            response = self._make_request(messages)
            fun_fact = response.choices[0].message.content.strip()
            ai_logger.info("fun_fact_generated", length=len(fun_fact))
            return fun_fact
        except Exception as e:
            ai_logger.error("fun_fact_generation_failed", error=str(e))
            raise AIServiceError(
                message=f"Failed to generate fun fact: {str(e)}",
                code="FUN_FACT_GENERATION_ERROR",
                details={
                    "error_type": type(e).__name__,
                    "error_details": str(e)
                }
            )
