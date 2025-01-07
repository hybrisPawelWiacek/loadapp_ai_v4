"""OpenAI service implementation."""
import time
from typing import Optional, Dict, Any, List
import httpx
from datetime import datetime
from decimal import Decimal

from openai import OpenAI, OpenAIError, RateLimitError, APIError, APITimeoutError

from ...infrastructure.logging import get_logger
from ...infrastructure.external_services.exceptions import ExternalServiceError


# Default configuration values
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 1000


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

    def generate_offer_content(
        self,
        business_name: str,
        route_data: Dict,
        cost_breakdown: Dict,
        final_price: Decimal,
        locations: Dict[str, Dict]
    ) -> str:
        """Generate enhanced offer content with comprehensive route and cost data.
        
        Args:
            business_name: Name of the business entity
            route_data: Dictionary containing route information including:
                - origin and destination details
                - timeline events
                - country segments
                - total distance and duration
                - feasibility status
            cost_breakdown: Detailed cost breakdown including:
                - fuel costs by country
                - toll costs by country
                - driver costs breakdown
                - overhead costs
                - timeline event costs
            final_price: Total price for the transport
            locations: Dictionary of location details keyed by location_id
        """
        # Create a structured prompt with all available information
        prompt = f"""Generate a professional transport offer description for {business_name}. 
        
Route Information:
- From: {locations[str(route_data['origin_id'])]['address']}
- To: {locations[str(route_data['destination_id'])]['address']}
- Total Distance: {route_data['total_distance_km']:.1f} km
- Total Duration: {route_data['total_duration_hours']:.1f} hours
- Pickup Time: {route_data['pickup_time'].strftime('%Y-%m-%d %H:%M')}
- Delivery Time: {route_data['delivery_time'].strftime('%Y-%m-%d %H:%M')}

Timeline:
{self._format_timeline(route_data['timeline_events'], locations)}

Route Segments:
{self._format_segments(route_data['country_segments'])}

Cost Breakdown:
{self._format_cost_breakdown(cost_breakdown)}

Total Price: {final_price:.2f} EUR

Please generate a comprehensive and professional transport offer that highlights:
1. The reliability and experience of {business_name}
2. The efficiency of the proposed route
3. The transparency of our cost structure
4. The value proposition for the client
5. Any relevant certifications or special capabilities

Keep the tone professional but engaging, and emphasize our commitment to reliable service."""

        return self.generate_text(prompt, max_tokens=1000, temperature=0.7)

    def generate_fun_fact(self, origin_location: Dict, destination_location: Dict, route_data: Dict) -> str:
        """Generate a transport-related fun fact relevant to the route.
        
        Args:
            origin_location: Dictionary with origin location details
            destination_location: Dictionary with destination location details
            route_data: Dictionary with route information
        """
        prompt = f"""Share an interesting and brief fun fact about transportation or logistics that relates to:
1. The route from {origin_location['address']} to {destination_location['address']}
2. The countries being traversed: {', '.join(segment['country_code'] for segment in route_data['country_segments'])}
3. The type of transport being used
4. Historical trade routes or modern logistics in these regions

Keep it to one or two sentences and make it engaging and relevant to this specific route."""

        return self.generate_text(prompt, max_tokens=100, temperature=0.8)

    def _format_timeline(self, events: List[Dict], locations: Dict[str, Dict]) -> str:
        """Format timeline events for the prompt."""
        timeline_str = ""
        for event in sorted(events, key=lambda x: x['event_order']):
            location = locations[str(event['location_id'])]
            timeline_str += (
                f"- {event['type'].title()}: {location['address']} "
                f"at {event['planned_time'].strftime('%Y-%m-%d %H:%M')}\n"
            )
        return timeline_str

    def _format_segments(self, segments: List[Dict]) -> str:
        """Format route segments for the prompt."""
        segments_str = ""
        for segment in sorted(segments, key=lambda x: x['segment_order']):
            segments_str += (
                f"- {segment['country_code']}: {segment['distance_km']:.1f} km, "
                f"{segment['duration_hours']:.1f} hours\n"
            )
        return segments_str

    def _format_cost_breakdown(self, breakdown: Dict) -> str:
        """Format cost breakdown for the prompt."""
        cost_str = "Detailed Cost Structure:\n"
        
        # Fuel costs by country
        if breakdown['fuel_costs']:
            cost_str += "Fuel Costs:\n"
            for country, cost in breakdown['fuel_costs'].items():
                cost_str += f"- {country}: {float(cost):.2f} EUR\n"
        
        # Toll costs by country
        if breakdown['toll_costs']:
            cost_str += "Toll Costs:\n"
            for country, cost in breakdown['toll_costs'].items():
                cost_str += f"- {country}: {float(cost):.2f} EUR\n"
        
        # Driver costs
        if breakdown['driver_costs']:
            cost_str += "Driver Costs:\n"
            for cost_type, cost in breakdown['driver_costs'].items():
                cost_str += f"- {cost_type.replace('_', ' ').title()}: {float(cost):.2f} EUR\n"
        
        # Other costs
        cost_str += f"Overhead Costs: {float(breakdown['overhead_costs']):.2f} EUR\n"
        
        if breakdown['timeline_event_costs']:
            cost_str += "Event Costs:\n"
            for event_type, cost in breakdown['timeline_event_costs'].items():
                cost_str += f"- {event_type.title()}: {float(cost):.2f} EUR\n"
        
        return cost_str 