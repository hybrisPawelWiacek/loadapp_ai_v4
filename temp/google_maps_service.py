"""Google Maps service implementation."""
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any, Callable
from uuid import UUID
import time
from functools import lru_cache

import googlemaps
from googlemaps.exceptions import ApiError, TransportError

from src.domain.value_objects import Location, CountrySegment
from src.domain.interfaces.services.location_service import LocationService, LocationServiceError
from src.infrastructure.logging import get_logger
from src.settings import get_settings
from src.infrastructure.services.toll_rate_service import DefaultTollRateService

logger = get_logger()

class GoogleMapsService(LocationService):
    """Google Maps API implementation of LocationService."""

    def __init__(self, api_key: Optional[str] = None, toll_rate_service: Optional[DefaultTollRateService] = None):
        """
        Initialize the Google Maps service.

        Args:
            api_key: Optional API key (defaults to settings.google_maps_api_key)
            toll_rate_service: Optional toll rate service (defaults to DefaultTollRateService)

        Raises:
            LocationServiceError: If API key is not found in settings or environment
        """
        self._logger = logger.bind(service="google_maps")
        settings = get_settings()
        self.api_key = api_key or settings.google_maps_api_key
        if not self.api_key:
            raise LocationServiceError("Google Maps API key not found in settings or environment")
        
        # Get API settings
        api_settings = settings.api
        self.max_retries = api_settings.gmaps_max_retries
        self.retry_delay = api_settings.gmaps_retry_delay
        self.cache_ttl = api_settings.gmaps_cache_ttl
        
        try:
            self.client = googlemaps.Client(key=self.api_key)
            self._logger.info("Google Maps client initialized successfully")
        except Exception as e:
            self._logger.error("Failed to initialize Google Maps client", error=str(e))
            raise LocationServiceError(f"Failed to initialize Google Maps client: {str(e)}")
        
        # Initialize toll rate service
        self.toll_rate_service = toll_rate_service or DefaultTollRateService()

    def _make_request(self, request_func: callable, *args, **kwargs) -> Dict[str, Any]:
        """
        Make a request to Google Maps API with retry logic.
        
        Args:
            request_func: Google Maps API function to call
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Dict: API response
            
        Raises:
            LocationServiceError: If request fails after retries
        """
        for attempt in range(self.max_retries):
            try:
                return request_func(*args, **kwargs)
            except (ApiError, Timeout, TransportError) as e:
                if attempt == self.max_retries - 1:
                    self._logger.error("Google Maps API error", 
                                     error=str(e), 
                                     attempt=attempt + 1, 
                                     max_retries=self.max_retries)
                    raise LocationServiceError(f"Google Maps API error after {self.max_retries} retries: {str(e)}")
                self._logger.warning("Google Maps API error, retrying", 
                                   error=str(e), 
                                   attempt=attempt + 1, 
                                   retry_delay=self.retry_delay * (attempt + 1))
                time.sleep(self.retry_delay * (attempt + 1))
            except Exception as e:
                self._logger.error("Unexpected error in Google Maps request", error=str(e))
                raise LocationServiceError(f"Unexpected error in Google Maps request: {str(e)}")

    @lru_cache(maxsize=128)
    def _get_route_data_cached(self, origin_coords: tuple, destination_coords: tuple) -> Dict[str, Any]:
        """Get cached route data from Google Maps using coordinates."""
        return self._make_request(
            self.client.directions,
            origin=origin_coords,
            destination=destination_coords,
            mode="driving",
            alternatives=False,
            units="metric"
        )

    def _get_route_data(self, origin: Location, destination: Location) -> Dict[str, Any]:
        """Get route data from Google Maps."""
        origin_coords = (origin.latitude, origin.longitude)
        destination_coords = (destination.latitude, destination.longitude)
        return self._get_route_data_cached(origin_coords, destination_coords)

    def calculate_distance(self, origin: Location, destination: Location) -> float:
        """Calculate distance between two locations using Google Maps Distance Matrix API."""
        self._logger.info("Calculating distance", 
                         origin=origin.dict(), 
                         destination=destination.dict())
        
        result = self._make_request(
            self.client.distance_matrix,
            origins=[(origin.latitude, origin.longitude)],
            destinations=[(destination.latitude, destination.longitude)],
            mode="driving",
            units="metric"
        )

        if not result.get('rows'):
            self._logger.error("No route found")
            raise LocationServiceError("No route found")

        elements = result['rows'][0]['elements']
        if not elements or elements[0].get('status') != 'OK':
            self._logger.error("Route calculation failed", elements=elements)
            raise LocationServiceError("Route calculation failed")

        # Convert meters to kilometers
        distance = elements[0]['distance']['value'] / 1000.0
        self._logger.info("Distance calculated successfully", distance_km=distance)
        return distance

    def calculate_duration(self, origin: Location, destination: Location) -> float:
        """Calculate duration between two locations using Google Maps Distance Matrix API."""
        self._logger.info("Calculating duration", 
                         origin=origin.dict(), 
                         destination=destination.dict())
        
        result = self._make_request(
            self.client.distance_matrix,
            origins=[(origin.latitude, origin.longitude)],
            destinations=[(destination.latitude, destination.longitude)],
            mode="driving",
            units="metric"
        )

        if not result.get('rows'):
            self._logger.error("No route found")
            raise LocationServiceError("No route found")

        elements = result['rows'][0]['elements']
        if not elements or elements[0].get('status') != 'OK':
            self._logger.error("Route calculation failed", elements=elements)
            raise LocationServiceError("Route calculation failed")

        # Convert seconds to hours
        duration = elements[0]['duration']['value'] / 3600.0
        self._logger.info("Duration calculated successfully", duration_hours=duration)
        return duration

    def get_country_code(self, country: str) -> str:
        """Convert country name to ISO code."""
        country_codes = {
            "Poland": "PL",
            "Germany": "DE",
            "France": "FR",
            "Spain": "ES",
            "Italy": "IT",
            "Netherlands": "NL",
            "Belgium": "BE",
            "Austria": "AT",
            "Switzerland": "CH",
            "Czech Republic": "CZ",
            "Slovakia": "SK",
            "Hungary": "HU",
            "Romania": "RO",
            "Bulgaria": "BG",
            "Croatia": "HR",
            "Slovenia": "SI",
            "Ukraine": "UA",
            "Belarus": "BY",
            "Lithuania": "LT",
            "Latvia": "LV",
            "Estonia": "EE"
        }
        return country_codes.get(country, country)

    def get_route_segments(self, origin: Location, destination: Location, include_tolls: bool = False) -> List[CountrySegment]:
        """
        Get route segments for a route.
        
        Args:
            origin: Starting location
            destination: End location
            include_tolls: Whether to include toll information
            
        Returns:
            List of country segments with distances
            
        Raises:
            LocationServiceError: If segment calculation fails
        """
        logger = get_logger(__name__).bind(
            origin=origin.dict(),
            destination=destination.dict()
        )
        
        try:
            # Get route data from Google Maps
            route_data = self._get_route_data(origin, destination)
            if not route_data:
                raise LocationServiceError("No route found")
            
            # Get total distance and duration
            total_distance = Decimal(str(self.calculate_distance(origin, destination)))
            total_duration = Decimal(str(self.calculate_duration(origin, destination)))
            
            # Process route steps
            segments = []
            current_country = None
            current_distance = Decimal('0')
            current_duration = Decimal('0')
            
            if not route_data[0].get('legs', []):
                raise LocationServiceError("Invalid route data: no legs found")
                
            for leg in route_data[0]['legs']:
                for step in leg.get('steps', []):
                    # Get location details
                    end_location = step['end_location']
                    result = self._make_request(
                        self.client.reverse_geocode,
                        (end_location['lat'], end_location['lng'])
                    )
                    
                    if not result:
                        continue
                        
                    # Extract country from geocoding result
                    country = None
                    for component in result[0]['address_components']:
                        if 'country' in component['types']:
                            country = component['long_name']
                            break
                    
                    if not country:
                        continue
                        
                    # Convert distance to kilometers and duration to hours
                    step_distance = Decimal(str(step['distance']['value'])) / Decimal('1000')
                    step_duration = Decimal(str(step['duration']['value'])) / Decimal('3600')  # Convert seconds to hours
                    
                    if current_country != country:
                        if current_country:
                            # Add completed segment
                            segments.append(CountrySegment(
                                country_code=self.get_country_code(current_country),
                                distance=current_distance,
                                duration_hours=current_duration,
                                has_tolls=self._check_for_tolls(current_country) if include_tolls else False
                            ))
                        # Start new segment
                        current_country = country
                        current_distance = step_distance
                        current_duration = step_duration
                    else:
                        current_distance += step_distance
                        current_duration += step_duration
            
            # Add final segment
            if current_country:
                segments.append(CountrySegment(
                    country_code=self.get_country_code(current_country),
                    distance=current_distance,
                    duration_hours=current_duration,
                    has_tolls=self._check_for_tolls(current_country) if include_tolls else False
                ))
            
            return segments
            
        except Exception as e:
            logger.error("Failed to get route segments", error=str(e))
            raise LocationServiceError(f"Failed to get route segments: {str(e)}")

    def validate_location(self, location: Location) -> bool:
        """
        Validate a location using Google Maps Geocoding API.
        
        Args:
            location: Location to validate
            
        Returns:
            True if location is valid, False otherwise
            
        Raises:
            LocationServiceError: If validation fails
        """
        try:
            # Try to geocode the location
            result = self._make_request(
                self.client.geocode,
                location.address if location.address else f"{location.latitude},{location.longitude}"
            )
            
            # Check if we got any results
            if not result:
                self._logger.warning("Location not found", location=location.dict())
                return False
                
            # Verify the result has the expected components
            if not result[0].get('geometry') or not result[0].get('formatted_address'):
                self._logger.warning("Invalid location data", location=location.dict())
                return False
                
            # Check if the coordinates match (if provided)
            if location.latitude and location.longitude:
                result_lat = result[0]['geometry']['location']['lat']
                result_lng = result[0]['geometry']['location']['lng']
                
                # Allow for small differences in coordinates (approx 100m)
                lat_diff = abs(location.latitude - result_lat)
                lng_diff = abs(location.longitude - result_lng)
                if lat_diff > 0.001 or lng_diff > 0.001:
                    self._logger.warning(
                        "Location coordinates mismatch",
                        original=location.dict(),
                        found={"lat": result_lat, "lng": result_lng}
                    )
                    return False
            
            return True
            
        except Exception as e:
            self._logger.error("Location validation failed", error=str(e), location=location.dict())
            raise LocationServiceError(f"Location validation failed: {str(e)}")

    def _check_for_tolls(self, country: str) -> bool:
        """Check if a country has toll roads."""
        return self.toll_rate_service.has_toll_roads(self.get_country_code(country))
