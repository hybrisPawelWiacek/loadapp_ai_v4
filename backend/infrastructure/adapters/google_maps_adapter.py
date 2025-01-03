"""Adapter for Google Maps service implementing RouteCalculationPort."""
from typing import List, Tuple
from decimal import Decimal

from ...domain.entities.route import Location, CountrySegment
from ...domain.services.route_service import RouteCalculationPort, LocationRepository
from ..external_services.google_maps_service import GoogleMapsService
from ..external_services.exceptions import ExternalServiceError


class GoogleMapsAdapter(RouteCalculationPort):
    """Adapter implementing RouteCalculationPort using Google Maps service."""

    def __init__(self, google_maps_service: GoogleMapsService, location_repo: LocationRepository):
        """Initialize adapter with Google Maps service and location repository."""
        self._service = google_maps_service
        self._location_repo = location_repo

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
            distance_km, duration_hours, segments = self._service.calculate_route(origin, destination)
            
            # Return the values directly since they're already in the format we need
            return distance_km, duration_hours, segments

        except Exception as e:
            raise ExternalServiceError(
                f"Failed to calculate route using Google Maps: {str(e)}"
            ) from e 