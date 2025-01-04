"""Adapter for toll rate service implementing TollCalculationPort."""
from decimal import Decimal
from typing import Dict, Any, Optional
from uuid import UUID

from ...domain.entities.route import CountrySegment
from ...domain.services.cost_service import TollCalculationPort
from ..external_services.toll_rate_service import TollRateService
from ..external_services.exceptions import ExternalServiceError
from ..repositories.toll_rate_override_repository import TollRateOverrideRepository


class TollRateAdapter(TollCalculationPort):
    """Adapter implementing TollCalculationPort using toll rate service."""

    def __init__(self, toll_service: TollRateService, override_repository: TollRateOverrideRepository):
        self._service = toll_service
        self._override_repo = override_repository

    def calculate_toll(
        self,
        segment: CountrySegment,
        truck_specs: dict,
        business_entity_id: Optional[UUID] = None,
        overrides: Optional[Dict[str, Any]] = None
    ) -> Decimal:
        """
        Calculate toll costs for a country segment with optional overrides.
        
        Args:
            segment: Route segment in a specific country
            truck_specs: Dictionary containing truck specifications
            business_entity_id: Optional business entity ID for rate overrides
            overrides: Optional dictionary with rate override settings
                
        Returns:
            Decimal representing toll costs for the segment
            
        Raises:
            ExternalServiceError: If toll rate service fails
        """
        try:
            # Get base toll cost
            base_toll = self._service.get_toll_rate(
                country_code=segment.country_code,
                distance_km=segment.distance_km,
                toll_class=truck_specs["toll_class"],
                euro_class=truck_specs["euro_class"],
                co2_class=truck_specs["co2_class"]
            )

            # If no overrides needed, return base toll
            if not business_entity_id or not overrides:
                return base_toll

            # Look for applicable override
            override = self._override_repo.find_for_business(
                business_entity_id=business_entity_id,
                country_code=segment.country_code,
                vehicle_class=overrides.get("vehicle_class", truck_specs["toll_class"])
            )

            # If override found, apply multiplier
            if override:
                return base_toll * override.rate_multiplier

            return base_toll

        except Exception as e:
            raise ExternalServiceError(
                f"Failed to calculate toll costs: {str(e)}"
            ) from e 