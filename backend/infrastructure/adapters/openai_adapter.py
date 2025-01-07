"""Adapter for OpenAI service implementing ContentEnhancementPort."""
from typing import Dict, Optional, Tuple, Protocol
from uuid import UUID

from ...domain.entities.cargo import Offer, CostBreakdown
from ...domain.entities.route import Route
from ...domain.entities.business import BusinessEntity
from ...domain.entities.location import Location
from ...domain.services.offer_service import ContentEnhancementPort
from ..external_services.openai_service import OpenAIService
from ..external_services.exceptions import ExternalServiceError


class BusinessRepository(Protocol):
    """Repository interface for BusinessEntity."""
    def find_by_id(self, id: UUID) -> Optional[BusinessEntity]:
        """Find a business entity by ID."""
        ...


class RouteRepository(Protocol):
    """Repository interface for Route."""
    def find_by_id(self, id: UUID) -> Optional[Route]:
        """Find a route by ID."""
        ...


class CostBreakdownRepository(Protocol):
    """Repository interface for CostBreakdown."""
    def find_by_id(self, id: UUID) -> Optional[CostBreakdown]:
        """Find a cost breakdown by ID."""
        ...


class LocationRepository(Protocol):
    """Repository interface for Location."""
    def find_by_id(self, id: UUID) -> Optional[Location]:
        """Find a location by ID."""
        ...


class OpenAIAdapter(ContentEnhancementPort):
    """Adapter implementing ContentEnhancementPort using OpenAI service."""

    def __init__(
        self,
        openai_service: OpenAIService,
        business_repository: BusinessRepository,
        route_repository: RouteRepository,
        cost_breakdown_repository: CostBreakdownRepository,
        location_repository: LocationRepository
    ):
        self._service = openai_service
        self._business_repository = business_repository
        self._route_repository = route_repository
        self._cost_breakdown_repository = cost_breakdown_repository
        self._location_repository = location_repository

    def _get_location_details(self, location_ids: list[UUID]) -> Dict[str, Dict]:
        """Get location details for a list of location IDs."""
        locations = {}
        for loc_id in location_ids:
            location = self._location_repository.find_by_id(loc_id)
            if location:
                locations[str(loc_id)] = location.model_dump()  # Convert Location to dict
        return locations

    def enhance_offer(self, offer: Offer) -> Tuple[str, str]:
        """
        Generate enhanced content and fun fact for an offer.
        
        Args:
            offer: The offer to enhance
            
        Returns:
            Tuple containing:
            - Enhanced offer content (str)
            - Transport-related fun fact (str)
            
        Raises:
            ExternalServiceError: If OpenAI service fails
        """
        try:
            # Get required data
            route = self._route_repository.find_by_id(offer.route_id)
            if not route:
                raise ValueError("Route not found")

            cost_breakdown = self._cost_breakdown_repository.find_by_id(offer.cost_breakdown_id)
            if not cost_breakdown:
                raise ValueError("Cost breakdown not found")

            business = self._business_repository.find_by_id(route.business_entity_id)
            if not business:
                raise ValueError("Business entity not found")

            # Get all required locations
            location_ids = {
                route.origin_id,
                route.destination_id,
                *[event.location_id for event in route.timeline_events]
            }
            locations = self._get_location_details(list(location_ids))

            # Get enhanced content with all data
            content = self._service.generate_offer_content(
                business_name=business.name,
                route_data=route.model_dump(),
                cost_breakdown=cost_breakdown.model_dump(),
                final_price=offer.final_price,
                locations=locations
            )

            # Get origin and destination locations for fun fact
            origin_location = locations.get(str(route.origin_id))
            destination_location = locations.get(str(route.destination_id))
            if not origin_location or not destination_location:
                raise ValueError("Origin or destination location not found")

            # Get fun fact with route context
            fun_fact = self._service.generate_fun_fact(
                origin_location=origin_location,
                destination_location=destination_location,
                route_data=route.model_dump()
            )

            return content, fun_fact

        except Exception as e:
            raise ExternalServiceError(
                f"Failed to enhance offer content: {str(e)}"
            ) from e 