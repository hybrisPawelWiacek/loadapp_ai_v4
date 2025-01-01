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
            # Calculate the main route first
            route_segment = self._service.calculate_route(origin, destination)
            
            # For now, we'll create a single country segment since the current
            # implementation doesn't provide country-specific data
            segments = [
                CountrySegment(
                    country_code="PL",  # Default to Poland for now
                    distance_km=route_segment.distance_km,
                    duration_hours=route_segment.duration_hours,
                    start_location=origin,
                    end_location=destination
                )
            ]

            return route_segment.distance_km, route_segment.duration_hours, segments

        except Exception as e:
            raise ExternalServiceError(
                f"Failed to calculate route using Google Maps: {str(e)}"
            ) from e 