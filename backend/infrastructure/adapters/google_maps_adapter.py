"""Adapter for Google Maps service implementing RouteCalculationPort."""
from typing import List, Tuple
from decimal import Decimal

from ...domain.entities.route import Location, CountrySegment
from ...domain.services.route_service import RouteCalculationPort
from ..external_services.google_maps_service import GoogleMapsService
from ..external_services.exceptions import ExternalServiceError


class GoogleMapsAdapter(RouteCalculationPort):
    """Adapter implementing RouteCalculationPort using Google Maps service."""

    def __init__(self, google_maps_service: GoogleMapsService):
        self._service = google_maps_service

    def calculate_route(
        self,
        origin: Location,
        destination: Location
    ) -> Tuple[float, float, List[CountrySegment]]:
        """
        Calculate route using Google Maps service.
        
        Args:
            origin: Starting location
            destination: End location
            
        Returns:
            Tuple containing:
            - total distance in km
            - total duration in hours
            - list of country segments
            
        Raises:
            ExternalServiceError: If Google Maps service fails
        """
        try:
            # Get route data from service
            route_data = self._service.get_route(
                origin_lat=origin.latitude,
                origin_lng=origin.longitude,
                dest_lat=destination.latitude,
                dest_lng=destination.longitude
            )

            # Extract total distance and duration
            total_distance_km = route_data["total_distance_km"]
            total_duration_hours = route_data["total_duration_hours"]

            # Convert country segments
            segments = []
            for segment_data in route_data["country_segments"]:
                segment = CountrySegment(
                    country_code=segment_data["country_code"],
                    distance_km=segment_data["distance_km"],
                    duration_hours=segment_data["duration_hours"]
                )
                segments.append(segment)

            return total_distance_km, total_duration_hours, segments

        except Exception as e:
            raise ExternalServiceError(
                f"Failed to calculate route using Google Maps: {str(e)}"
            ) from e 