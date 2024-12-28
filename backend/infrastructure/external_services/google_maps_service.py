"""Google Maps service implementation."""
import time
from typing import Dict, List, Optional, Tuple, Any
from functools import lru_cache

import googlemaps
from googlemaps.exceptions import ApiError, TransportError, Timeout
from retry import retry

from ...domain.entities.route import Location, RouteSegment, Route, CountrySegment
from ...infrastructure.logging import get_logger
from ...infrastructure.external_services.exceptions import ExternalServiceError


# Default settings
DEFAULT_MODE = "driving"
DEFAULT_UNITS = "metric"
DEFAULT_LANGUAGE = "en"


class GoogleMapsServiceError(ExternalServiceError):
    """Specific exception for Google Maps service errors"""
    pass


logger = get_logger()


class GoogleMapsService:
    """Google Maps service for route calculations."""

    def __init__(
        self,
        api_key: str,
        mode: str = DEFAULT_MODE,
        units: str = DEFAULT_UNITS,
        language: str = DEFAULT_LANGUAGE,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """Initialize Google Maps service.
        
        Args:
            api_key: Google Maps API key
            mode: Travel mode (driving, walking, etc.)
            units: Unit system (metric or imperial)
            language: Language for results
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds
            
        Raises:
            ValueError: If API key is not provided
        """
        if not api_key:
            raise ValueError("API key is required")

        self._logger = logger.bind(service="google_maps")
        self.api_key = api_key
        self.mode = mode
        self.units = units
        self.language = language
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        try:
            self.client = googlemaps.Client(
                key=self.api_key,
                timeout=timeout
            )
            self._logger.info("Google Maps client initialized successfully")
        except Exception as e:
            self._logger.error("Failed to initialize Google Maps client", error=str(e))
            raise GoogleMapsServiceError(f"Failed to initialize Google Maps client: {str(e)}")

    def _make_request(self, request_func: callable, *args: Any, **kwargs: Any) -> Any:
        """Make a request to Google Maps API with retry logic."""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                return request_func(*args, **kwargs)
            except (ApiError, TransportError, Timeout) as e:
                last_error = e
                if attempt == self.max_retries - 1:
                    self._logger.error(
                        "Google Maps API error",
                        error=str(e),
                        attempt=attempt + 1,
                        max_retries=self.max_retries
                    )
                    break
                self._logger.warning(
                    "Google Maps API error, retrying",
                    error=str(e),
                    attempt=attempt + 1,
                    retry_delay=self.retry_delay * (attempt + 1)
                )
                time.sleep(self.retry_delay * (attempt + 1))
            except Exception as e:
                self._logger.error("Unexpected error in Google Maps request", error=str(e))
                raise GoogleMapsServiceError(f"Failed to calculate route: {str(e)}")
        
        if last_error:
            raise GoogleMapsServiceError(f"Failed to calculate route: {str(last_error)}")

    @retry(GoogleMapsServiceError, tries=3, delay=1)
    def calculate_route(
        self,
        origin: Location,
        destination: Location,
        departure_time: Optional[int] = None,
        avoid: Optional[List[str]] = None,
        waypoints: Optional[List[Location]] = None
    ) -> RouteSegment:
        """Calculate route between two locations."""
        # Validate locations
        if not origin.latitude or not origin.longitude:
            raise ValueError("Invalid origin location")
        if not destination.latitude or not destination.longitude:
            raise ValueError("Invalid destination location")
            
        # Validate avoid options
        valid_avoid_options = {"tolls", "highways", "ferries"}
        if avoid:
            invalid_options = set(avoid) - valid_avoid_options
            if invalid_options:
                raise ValueError(f"Invalid avoid options: {', '.join(invalid_options)}")
        
        # Format waypoints for logging
        waypoints_dump = [wp.model_dump() for wp in waypoints] if waypoints else None
        
        self._logger.info(
            "Calculating route",
            origin=origin.model_dump(),
            destination=destination.model_dump(),
            departure_time=departure_time,
            avoid=avoid,
            waypoints=waypoints_dump
        )
        
        try:
            # Convert waypoints to coordinates
            waypoint_coords = None
            if waypoints:
                waypoint_coords = [(wp.latitude, wp.longitude) for wp in waypoints]
            
            # Build request parameters
            params = {
                "origin": (origin.latitude, origin.longitude),
                "destination": (destination.latitude, destination.longitude),
                "mode": self.mode,
                "units": self.units,
                "language": self.language
            }
            
            if departure_time:
                params["departure_time"] = departure_time
            
            if avoid:
                params["avoid"] = "|".join(avoid)
                
            if waypoint_coords:
                params["waypoints"] = waypoint_coords
            
            # Make request
            route_data = self._make_request(
                self.client.directions,
                **params
            )
            
            if not route_data or not route_data[0].get("legs"):
                raise GoogleMapsServiceError("No route found")
            
            # Extract route information from first route
            leg = route_data[0]["legs"][0]
            
            # Create route segment
            return RouteSegment(
                distance_km=leg["distance"]["value"] / 1000.0,  # Convert meters to km
                duration_hours=leg["duration"]["value"] / 3600.0,  # Convert seconds to hours
                start_location=origin,
                end_location=destination
            )
            
        except GoogleMapsServiceError:
            raise
        except Exception as e:
            self._logger.error("Failed to calculate route", error=str(e))
            raise GoogleMapsServiceError(f"Failed to calculate route: {str(e)}")

    def get_distance_matrix(
        self,
        origins: List[Location],
        destinations: List[Location]
    ) -> Dict[str, List[List[float]]]:
        """Get distance matrix between multiple origins and destinations.
        
        Args:
            origins: List of origin locations
            destinations: List of destination locations
            
        Returns:
            Dict containing:
            - distances: Matrix of distances in kilometers
            - durations: Matrix of durations in hours
            
        Raises:
            ValueError: If distance matrix cannot be calculated
        """
        try:
            origin_coords = [(loc.latitude, loc.longitude) for loc in origins]
            destination_coords = [(loc.latitude, loc.longitude) for loc in destinations]
            
            matrix = self._make_request(
                self.client.distance_matrix,
                origins=origin_coords,
                destinations=destination_coords,
                mode=self.mode,
                units=self.units,
                language=self.language
            )
            
            if matrix["status"] != "OK":
                raise GoogleMapsServiceError(f"Distance matrix error: {matrix['status']}")
            
            # Extract distances and durations
            distances = []
            durations = []
            
            for row in matrix["rows"]:
                distance_row = []
                duration_row = []
                
                for element in row["elements"]:
                    if element["status"] != "OK":
                        distance_row.append(float("inf"))
                        duration_row.append(float("inf"))
                    else:
                        distance_row.append(element["distance"]["value"] / 1000.0)  # Convert to km
                        duration_row.append(element["duration"]["value"] / 3600.0)  # Convert to hours
                
                distances.append(distance_row)
                durations.append(duration_row)
            
            return {
                "distances": distances,
                "durations": durations
            }
            
        except GoogleMapsServiceError:
            raise
        except Exception as e:
            self._logger.error("Failed to get distance matrix", error=str(e))
            raise GoogleMapsServiceError(f"Failed to get distance matrix: {str(e)}")

    def geocode(self, address: str) -> Location:
        """Geocode an address to get its coordinates.
        
        Args:
            address: Address to geocode
            
        Returns:
            Location: Location object with coordinates
            
        Raises:
            ValueError: If address cannot be geocoded
        """
        try:
            results = self._make_request(
                self.client.geocode,
                address=address,
                language=self.language
            )
            
            if not results:
                raise GoogleMapsServiceError(f"No results found for address: {address}")
            
            location = results[0]["geometry"]["location"]
            return Location(
                latitude=location["lat"],
                longitude=location["lng"],
                address=results[0]["formatted_address"]
            )
            
        except GoogleMapsServiceError:
            raise
        except Exception as e:
            self._logger.error("Failed to geocode address", error=str(e))
            raise GoogleMapsServiceError(f"Failed to geocode address: {str(e)}")

    def reverse_geocode(self, latitude: float, longitude: float) -> Location:
        """Reverse geocode coordinates to get an address.
        
        Args:
            latitude: Latitude
            longitude: Longitude
            
        Returns:
            Location: Location object with address
            
        Raises:
            ValueError: If coordinates cannot be reverse geocoded
        """
        try:
            results = self._make_request(
                self.client.reverse_geocode,
                latlng=(latitude, longitude),
                language=self.language
            )
            
            if not results:
                raise GoogleMapsServiceError(f"No results found for coordinates: {latitude}, {longitude}")
            
            return Location(
                latitude=latitude,
                longitude=longitude,
                address=results[0]["formatted_address"]
            )
            
        except GoogleMapsServiceError:
            raise
        except Exception as e:
            self._logger.error("Failed to reverse geocode coordinates", error=str(e))
            raise GoogleMapsServiceError(f"Failed to reverse geocode coordinates: {str(e)}")

    def get_country_segments(self, origin: Location, destination: Location) -> List[CountrySegment]:
        """Get country segments for a route between two locations.
        
        Args:
            origin: Starting location
            destination: Ending location
            
        Returns:
            List of CountrySegment objects
            
        Raises:
            ValueError: If origin or destination are not Location objects
            GoogleMapsServiceError: If the API call fails
        """
        try:
            # Validate locations before making the API call
            if not isinstance(origin, Location) or not isinstance(destination, Location):
                raise ValueError("Origin and destination must be Location objects")

            # Get directions from Google Maps
            directions_result = self._make_request(
                self.client.directions,
                origin=(origin.latitude, origin.longitude),
                destination=(destination.latitude, destination.longitude),
                mode=self.mode,
                units=self.units,
                language=self.language
            )

            if not directions_result:
                raise GoogleMapsServiceError("No route found between the specified locations")

            # Process the route and extract country segments
            segments = []
            route = directions_result[0]
            
            for leg in route['legs']:
                current_country = None
                current_distance = 0.0
                current_duration = 0.0
                current_start_location = None
                current_end_location = None

                for i, step in enumerate(leg['steps']):
                    # Create location for current step
                    step_location = Location(
                        latitude=step['end_location']['lat'],
                        longitude=step['end_location']['lng'],
                        address=""  # We'll get this from reverse geocoding
                    )
                    
                    # Extract country from geocoded location
                    geocoded_result = self._make_request(
                        self.client.reverse_geocode,
                        (step_location.latitude, step_location.longitude)
                    )
                    
                    if not geocoded_result:
                        continue
                        
                    country_code = self._extract_country_code(geocoded_result[0])
                    
                    if current_country is None:
                        current_country = country_code
                        current_start_location = Location(
                            latitude=step['start_location']['lat'],
                            longitude=step['start_location']['lng'],
                            address=""  # We'll get this from reverse geocoding
                        )
                    
                    current_distance += step['distance']['value']
                    current_duration += step['duration']['value']
                    current_end_location = step_location

                    # Check if country changes in next step or if this is the last step
                    is_last_step = i == len(leg['steps']) - 1
                    next_step_country = None
                    
                    if not is_last_step:
                        next_step = leg['steps'][i + 1]
                        next_geocoded = self._make_request(
                            self.client.reverse_geocode,
                            (next_step['end_location']['lat'], next_step['end_location']['lng'])
                        )
                        if next_geocoded:
                            next_step_country = self._extract_country_code(next_geocoded[0])
                    
                    if is_last_step or (next_step_country and next_step_country != current_country):
                        # Create segment for current country
                        segments.append(CountrySegment(
                            country_code=current_country,
                            distance_km=current_distance / 1000,  # Convert to km
                            duration_hours=current_duration / 3600,  # Convert to hours
                            start_location=current_start_location,
                            end_location=current_end_location
                        ))
                        
                        if not is_last_step:
                            # Start new segment
                            current_country = next_step_country
                            current_distance = 0
                            current_duration = 0
                            current_start_location = current_end_location

            return segments

        except ValueError as e:
            # Re-raise ValueError directly
            raise e
        except Exception as e:
            self._logger.error("Failed to calculate country segments", error=str(e))
            raise GoogleMapsServiceError(f"Failed to calculate country segments: {str(e)}")

    def _extract_country_code(self, geocoded_result: dict) -> str:
        """Extract country code from geocoded result.
        
        Args:
            geocoded_result: Geocoding result from Google Maps API
            
        Returns:
            Two-letter country code
        """
        for component in geocoded_result.get('address_components', []):
            if 'country' in component['types']:
                return component['short_name']
        return 'Unknown' 