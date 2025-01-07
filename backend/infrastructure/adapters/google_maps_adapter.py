"""Google Maps adapter implementation."""
from typing import List, Optional, Tuple
from uuid import UUID, uuid4

from ..external_services.google_maps_service import GoogleMapsService
from ...domain.entities.route import Location, CountrySegment, SegmentType

class GoogleMapsAdapter:
    """Adapter for Google Maps service."""

    def __init__(self, maps_service: GoogleMapsService):
        """Initialize adapter with Google Maps service."""
        self._maps_service = maps_service

    def calculate_route(
        self,
        origin: Location,
        destination: Location
    ) -> tuple[float, float, List[CountrySegment], List[List[float]]]:
        """Calculate route details using Google Maps."""
        try:
            # Get route details from Google Maps
            total_distance_km, total_duration_hours, segments, route_points = self._maps_service.calculate_route(
                origin=origin,
                destination=destination
            )

            # Process segments to include route points
            for segment in segments:
                # Get route points for this segment
                segment_points = self._maps_service.get_segment_route_points(
                    origin=self._maps_service._location_repo.find_by_id(segment.start_location_id),
                    destination=self._maps_service._location_repo.find_by_id(segment.end_location_id)
                )
                segment.route_points = segment_points

            return total_distance_km, total_duration_hours, segments, route_points

        except Exception as e:
            raise ValueError(f"Failed to calculate route: {str(e)}")

    def calculate_empty_driving(
        self,
        truck_location: Location,
        origin: Location
    ) -> tuple[float, float]:
        """Calculate empty driving details."""
        try:
            return self._maps_service.calculate_empty_driving(truck_location, origin)
        except Exception as e:
            raise ValueError(f"Failed to calculate empty driving: {str(e)}")

    def get_segment_route_points(self, segment_id: UUID) -> List[List[float]]:
        """Get route points for a segment."""
        try:
            return self._maps_service.get_segment_route_points(segment_id)
        except Exception as e:
            raise ValueError(f"Failed to get segment route points: {str(e)}") 