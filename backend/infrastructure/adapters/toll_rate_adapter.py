"""Adapter for toll rate service implementing TollCalculationPort."""
from decimal import Decimal

from ...domain.entities.route import CountrySegment
from ...domain.services.cost_service import TollCalculationPort
from ..external_services.toll_rate_service import TollRateService
from ..external_services.exceptions import ExternalServiceError


class TollRateAdapter(TollCalculationPort):
    """Adapter implementing TollCalculationPort using toll rate service."""

    def __init__(self, toll_service: TollRateService):
        self._service = toll_service

    def calculate_toll(
        self,
        segment: CountrySegment,
        truck_specs: dict
    ) -> Decimal:
        """
        Calculate toll costs for a country segment.
        
        Args:
            segment: Route segment in a specific country
            truck_specs: Dictionary containing truck specifications
                - toll_class: Toll class of the truck
                - euro_class: Euro emission class
                - co2_class: CO2 emission class
                
        Returns:
            Decimal representing toll costs for the segment
            
        Raises:
            ExternalServiceError: If toll rate service fails
        """
        try:
            toll_cost = self._service.get_toll_rate(
                country_code=segment.country_code,
                distance_km=segment.distance_km,
                toll_class=truck_specs["toll_class"],
                euro_class=truck_specs["euro_class"],
                co2_class=truck_specs["co2_class"]
            )
            
            return Decimal(str(toll_cost))

        except Exception as e:
            raise ExternalServiceError(
                f"Failed to calculate toll costs: {str(e)}"
            ) from e 