"""Google Maps service implementation."""
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID, uuid4
import polyline

from ...domain.entities.location import Location
from ...domain.entities.route import CountrySegment, SegmentType
from .exceptions import ExternalServiceError
from ...domain.services.route_service import LocationRepository
from ...infrastructure.logging import get_logger

import time
from functools import lru_cache

import googlemaps
from googlemaps.exceptions import ApiError, TransportError, Timeout
from retry import retry

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
        location_repo: LocationRepository,
        mode: str = DEFAULT_MODE,
        units: str = DEFAULT_UNITS,
        language: str = DEFAULT_LANGUAGE,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """Initialize Google Maps service."""
        if not api_key:
            raise ValueError("API key is required")

        self._logger = logger.bind(service="google_maps")
        self._logger.info("Google Maps client initialized successfully")
        self._client = googlemaps.Client(
            key=api_key,
            timeout=timeout,
            retry_over_query_limit=True,
            queries_per_second=50
        )
        self._location_repo = location_repo
        self._mode = mode
        self._units = units
        self._language = language
        self._max_retries = max_retries
        self._retry_delay = retry_delay

    def _log_route_details(self, route_data: Dict) -> None:
        """Log detailed route information for debugging."""
        self._logger.debug("Route calculation details", 
            total_distance=route_data.get('legs', [{}])[0].get('distance', {}).get('value'),
            total_duration=route_data.get('legs', [{}])[0].get('duration', {}).get('value'),
            waypoints=len(route_data.get('legs', [])),
            route_status=route_data.get('status'),
            route_warnings=route_data.get('warnings', [])
        )

    def _log_segment_details(self, segment: Dict, country_code: str) -> None:
        """Log segment processing details."""
        self._logger.debug("Processing country segment",
            country_code=country_code,
            segment_distance=segment.get('distance_km'),
            segment_duration=segment.get('duration_hours'),
            start_location=segment.get('start_location'),
            end_location=segment.get('end_location')
        )

    def _make_request(self, request_func: callable, *args: Any, **kwargs: Any) -> Any:
        """Make a request to Google Maps API with retry logic."""
        last_error = None
        for attempt in range(self._max_retries):
            try:
                return request_func(*args, **kwargs)
            except (ApiError, TransportError, Timeout) as e:
                last_error = e
                if attempt == self._max_retries - 1:
                    self._logger.error(
                        "Google Maps API error",
                        error=str(e),
                        attempt=attempt + 1,
                        max_retries=self._max_retries
                    )
                    break
                self._logger.warning(
                    "Google Maps API error, retrying",
                    error=str(e),
                    attempt=attempt + 1,
                    retry_delay=self._retry_delay * (attempt + 1)
                )
                time.sleep(self._retry_delay * (attempt + 1))
            except Exception as e:
                self._logger.error("Unexpected error in Google Maps request", error=str(e))
                raise GoogleMapsServiceError(f"Failed to calculate route: {str(e)}")
        
        if last_error:
            raise GoogleMapsServiceError(f"Failed to calculate route: {str(last_error)}")

    def _extract_country_code(self, geocoded_result: Dict) -> str:
        """Extract country code from geocoded result."""
        for component in geocoded_result.get("address_components", []):
            if "country" in component.get("types", []):
                return component.get("short_name", "")
        return ""

    def _create_and_save_location(self, lat: float, lng: float, address: str) -> Location:
        """Create and save a location."""
        location = Location(
            id=uuid4(),
            latitude=lat,
            longitude=lng,
            address=address
        )
        return self._location_repo.save(location)

    @retry(GoogleMapsServiceError, tries=3, delay=1)
    def calculate_route(
        self,
        origin: Location,
        destination: Location,
        departure_time: Optional[int] = None,
        avoid: Optional[List[str]] = None,
        waypoints: Optional[List[Location]] = None
    ) -> tuple[float, float, List[CountrySegment], List[List[float]]]:
        """
        Calculate route details using Google Maps API.
        Returns tuple of (total_distance_km, total_duration_hours, country_segments, route_polylines).
        """
        try:
            # Prepare waypoints if provided
            waypoints_param = None
            if waypoints:
                waypoints_param = [{"lat": wp.latitude, "lng": wp.longitude} for wp in waypoints]

            # Get route from Google Maps
            route_data = self._make_request(
                self._client.directions,
                origin={"lat": origin.latitude, "lng": origin.longitude},
                destination={"lat": destination.latitude, "lng": destination.longitude},
                mode=self._mode,
                units=self._units,
                language=self._language,
                waypoints=waypoints_param,
                departure_time=departure_time,
                avoid=avoid,
                alternatives=False
            )

            if not route_data:
                raise GoogleMapsServiceError("No route found")

            self._log_route_details(route_data[0])

            # Extract total distance and duration
            leg = route_data[0]["legs"][0]
            total_distance_km = leg["distance"]["value"] / 1000.0  # Convert to km
            total_duration_hours = leg["duration"]["value"] / 3600.0  # Convert to hours

            self._logger.info("Route totals",
                            total_distance_km=total_distance_km,
                            total_duration_hours=total_duration_hours)

            # Extract polyline points for the entire route
            route_polyline = route_data[0]["overview_polyline"]["points"]
            route_points = self._decode_polyline(route_polyline)

            # Process steps to create country segments
            steps = leg["steps"]
            segments = []
            current_country = None
            current_distance = 0.0
            current_duration = 0.0
            current_start_location = None
            current_route_points = []

            self._logger.debug("Processing route steps",
                             step_count=len(steps))

            # Get initial country from origin
            origin_geocoded = self._make_request(
                self._client.reverse_geocode,
                (origin.latitude, origin.longitude)
            )
            current_country = self._extract_country_code(origin_geocoded[0])
            current_start_location = origin

            for i, step in enumerate(steps):
                step_lat = step["end_location"]["lat"]
                step_lng = step["end_location"]["lng"]
                step_geocoded = self._make_request(
                    self._client.reverse_geocode,
                    (step_lat, step_lng)
                )
                step_country = self._extract_country_code(step_geocoded[0])
                
                # Add distance and duration for current step
                current_distance += step["distance"]["value"] / 1000.0  # Convert to km
                current_duration += step["duration"]["value"] / 3600.0  # Convert to hours

                # Add route points for this step
                step_points = self._decode_polyline(step["polyline"]["points"])
                current_route_points.extend(step_points)

                # If country changes or this is the last step, create a segment
                if step_country != current_country or i == len(steps) - 1:
                    # Create location for segment end
                    end_location = self._create_and_save_location(
                        step_lat,
                        step_lng,
                        step_geocoded[0].get("formatted_address", "")
                    )

                    # Create segment
                    segment = CountrySegment(
                        id=uuid4(),
                        route_id=None,
                        country_code=current_country,
                        segment_type=SegmentType.ROUTE,
                        distance_km=current_distance,
                        duration_hours=current_duration,
                        start_location_id=current_start_location.id,
                        end_location_id=end_location.id,
                        segment_order=len(segments)
                    )
                    # Add route points to segment
                    segment.route_points = current_route_points
                    segments.append(segment)

                    # Reset counters and update current country
                    current_country = step_country
                    current_distance = 0.0
                    current_duration = 0.0
                    current_start_location = end_location
                    current_route_points = []

            self._logger.info("Segment totals",
                            segment_count=len(segments),
                            total_distance_km=sum(seg.distance_km for seg in segments),
                            total_duration_hours=sum(seg.duration_hours for seg in segments))

            return total_distance_km, total_duration_hours, segments, route_points

        except Exception as e:
            self._logger.error("Failed to calculate route", error=str(e))
            raise GoogleMapsServiceError(f"Failed to calculate route: {str(e)}")

    def _decode_polyline(self, polyline_str: str) -> List[List[float]]:
        """
        Decodes a polyline string into a list of lat/lng points.
        Returns points in the format [lat, lng] for backend compatibility.
        """
        try:
            # Decode the polyline into a list of [lat, lng] coordinates
            coords = polyline.decode(polyline_str)
            # Return the coordinates directly as [lat, lng] lists
            return coords
        except Exception as e:
            self._logger.error("Failed to decode polyline", error=str(e))
            return []

    def get_distance_matrix(
        self,
        origins: List[Location],
        destinations: List[Location]
    ) -> Dict[str, List[List[float]]]:
        """Get distance matrix between multiple origins and destinations."""
        try:
            origin_coords = [(loc.latitude, loc.longitude) for loc in origins]
            destination_coords = [(loc.latitude, loc.longitude) for loc in destinations]
            
            matrix = self._make_request(
                self._client.distance_matrix,
                origins=origin_coords,
                destinations=destination_coords,
                mode=self._mode,
                units=self._units,
                language=self._language
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
            
        except Exception as e:
            self._logger.error("Error getting distance matrix",
                             error=str(e),
                             error_type=type(e).__name__)
            raise GoogleMapsServiceError(f"Failed to get distance matrix: {str(e)}")

    def geocode(self, address: str) -> Location:
        """Geocode an address to get its coordinates.
        
        Args:
            address: Address to geocode
            
        Returns:
            Location: Location object with coordinates
            
        Raises:
            GoogleMapsServiceError: If geocoding fails
        """
        try:
            results = self._make_request(
                self._client.geocode,
                address=address,
                language=self._language
            )
            
            if not results:
                raise GoogleMapsServiceError(f"No results found for address: {address}")
            
            location = results[0]["geometry"]["location"]
            return Location(
                id=uuid4(),
                latitude=location["lat"],
                longitude=location["lng"],
                address=results[0]["formatted_address"]
            )
            
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
            GoogleMapsServiceError: If reverse geocoding fails
        """
        try:
            results = self._make_request(
                self._client.reverse_geocode,
                latlng=(latitude, longitude),
                language=self._language
            )
            
            if not results:
                raise GoogleMapsServiceError(f"No results found for coordinates: {latitude}, {longitude}")
            
            return Location(
                id=uuid4(),
                latitude=latitude,
                longitude=longitude,
                address=results[0]["formatted_address"]
            )
            
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
                self._client.directions,
                origin=(origin.latitude, origin.longitude),
                destination=(destination.latitude, destination.longitude),
                mode=self._mode,
                units=self._units,
                language=self._language
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
                        id=uuid4(),
                        latitude=step['end_location']['lat'],
                        longitude=step['end_location']['lng'],
                        address=""  # We'll get this from reverse geocoding
                    )
                    
                    # Extract country from geocoded location
                    geocoded_result = self._make_request(
                        self._client.reverse_geocode,
                        (step_location.latitude, step_location.longitude)
                    )
                    
                    if not geocoded_result:
                        continue
                        
                    country_code = self._extract_country_code(geocoded_result[0])
                    
                    if current_country is None:
                        current_country = country_code
                        current_start_location = Location(
                            id=uuid4(),
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
                            self._client.reverse_geocode,
                            (next_step['end_location']['lat'], next_step['end_location']['lng'])
                        )
                        if next_geocoded:
                            next_step_country = self._extract_country_code(next_geocoded[0])
                    
                    if is_last_step or (next_step_country and next_step_country != current_country):
                        # Create segment for current country
                        segments.append(CountrySegment(
                            id=uuid4(),
                            country_code=current_country,
                            distance_km=current_distance / 1000,  # Convert to km
                            duration_hours=current_duration / 3600,  # Convert to hours
                            start_location_id=current_start_location.id,
                            end_location_id=current_end_location.id
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

    def calculate_empty_driving(
        self,
        truck_location: Location,
        origin: Location
    ) -> tuple[float, float]:
        """Calculate empty driving distance and duration from truck to origin."""
        try:
            # Get route from Google Maps
            route_data = self._make_request(
                self._client.directions,
                origin={"lat": truck_location.latitude, "lng": truck_location.longitude},
                destination={"lat": origin.latitude, "lng": origin.longitude},
                mode=self._mode,
                units=self._units,
                language=self._language,
                alternatives=False
            )

            if not route_data:
                raise GoogleMapsServiceError("No route found for empty driving")

            # Extract distance and duration
            leg = route_data[0]["legs"][0]
            distance_km = leg["distance"]["value"] / 1000.0  # Convert to km
            duration_hours = leg["duration"]["value"] / 3600.0  # Convert to hours

            self._logger.info("Empty driving calculated",
                            distance_km=distance_km,
                            duration_hours=duration_hours)

            return distance_km, duration_hours

        except Exception as e:
            self._logger.error("Failed to calculate empty driving", error=str(e))
            raise GoogleMapsServiceError(f"Failed to calculate empty driving: {str(e)}")

    def get_segment_route_points(
        self,
        origin: Location,
        destination: Location
    ) -> List[List[float]]:
        """Get route points for a segment between two locations."""
        try:
            # Get route from Google Maps
            route_data = self._make_request(
                self._client.directions,
                origin={"lat": origin.latitude, "lng": origin.longitude},
                destination={"lat": destination.latitude, "lng": destination.longitude},
                mode=self._mode,
                units=self._units,
                language=self._language,
                alternatives=False
            )

            if not route_data:
                raise GoogleMapsServiceError("No route found for segment")

            # Extract polyline points for the route
            route_polyline = route_data[0]["overview_polyline"]["points"]
            return self._decode_polyline(route_polyline)

        except Exception as e:
            self._logger.error("Failed to get segment route points", error=str(e))
            raise GoogleMapsServiceError(f"Failed to get segment route points: {str(e)}")

    @property
    def api_key(self) -> str:
        """Get the API key."""
        return self._client.key

    @property
    def mode(self) -> str:
        """Get the transport mode."""
        return self._mode

    @property
    def units(self) -> str:
        """Get the units setting."""
        return self._units

    @property
    def language(self) -> str:
        """Get the language setting."""
        return self._language 