"""Toll rate service implementation."""
from decimal import Decimal
from typing import Dict, Optional
from uuid import UUID

from ...domain.entities.route import CountrySegment
from ...domain.services.cost_service import TollCalculationPort
from ...infrastructure.logging import get_logger
from ...config import get_settings

logger = get_logger()

# Default toll rates per km by country and vehicle class
DEFAULT_TOLL_RATES = {
    "DE": {  # Germany
        "toll_class": {
            "7.5": Decimal("0.15"),  # 7.5t
            "12": Decimal("0.20"),   # 12t
            "40": Decimal("0.25")    # 40t
        },
        "euro_class": {
            "EURO6": Decimal("-0.03"),  # Discount for EURO6
            "EURO5": Decimal("0"),      # No adjustment
            "EURO4": Decimal("0.02")    # Penalty for EURO4
        },
        "co2_class": {
            "A": Decimal("-0.02"),  # Low emissions
            "B": Decimal("0"),      # Standard
            "C": Decimal("0.02")    # High emissions
        }
    },
    "PL": {  # Poland
        "toll_class": {
            "7.5": Decimal("0.10"),
            "12": Decimal("0.15"),
            "40": Decimal("0.20")
        },
        "euro_class": {
            "EURO6": Decimal("-0.02"),
            "EURO5": Decimal("0"),
            "EURO4": Decimal("0.01")
        },
        "co2_class": {
            "A": Decimal("-0.01"),
            "B": Decimal("0"),
            "C": Decimal("0.01")
        }
    },
    # Add more countries as needed
}

class DefaultTollRateService(TollCalculationPort):
    """Default implementation of TollCalculationPort using predefined rates."""

    def __init__(self):
        """Initialize toll rate service."""
        self._logger = logger.bind(service="toll_rate")
        self.rates = DEFAULT_TOLL_RATES

    def calculate_toll(
        self,
        segment: CountrySegment,
        truck_specs: dict
    ) -> Decimal:
        """Calculate toll costs for a country segment.
        
        Args:
            segment: Country segment to calculate toll for
            truck_specs: Dictionary containing:
                - toll_class: Vehicle weight class (7.5, 12, 40)
                - euro_class: Emission standard (EURO4, EURO5, EURO6)
                - co2_class: CO2 emission class (A, B, C)
                
        Returns:
            Calculated toll amount
            
        Raises:
            ValueError: If country not supported or invalid specs
        """
        country_code = segment.country_code
        if country_code not in self.rates:
            self._logger.warning(f"No toll rates for country: {country_code}")
            return Decimal("0")

        try:
            country_rates = self.rates[country_code]
            
            # Get base rate for toll class
            base_rate = country_rates["toll_class"][str(truck_specs["toll_class"])]
            
            # Apply adjustments for euro class
            euro_adjustment = country_rates["euro_class"][truck_specs["euro_class"]]
            
            # Apply adjustments for CO2 class
            co2_adjustment = country_rates["co2_class"][truck_specs["co2_class"]]
            
            # Calculate final rate
            final_rate = base_rate + euro_adjustment + co2_adjustment
            
            # Calculate total toll
            toll = final_rate * Decimal(str(segment.distance_km))
            
            self._logger.info(
                "Toll calculated",
                country=country_code,
                distance_km=segment.distance_km,
                base_rate=base_rate,
                euro_adj=euro_adjustment,
                co2_adj=co2_adjustment,
                final_rate=final_rate,
                total_toll=toll
            )
            
            return toll
            
        except KeyError as e:
            self._logger.error(
                "Invalid truck specifications",
                error=str(e),
                country=country_code,
                specs=truck_specs
            )
            raise ValueError(f"Invalid truck specifications: {str(e)}")
        except Exception as e:
            self._logger.error(
                "Error calculating toll",
                error=str(e),
                country=country_code,
                specs=truck_specs
            )
            raise ValueError(f"Error calculating toll: {str(e)}")

    def get_toll_rates(self, country_code: str) -> Dict[str, Dict[str, Decimal]]:
        """Get toll rates for a country.
        
        Args:
            country_code: ISO country code
            
        Returns:
            Dictionary of toll rates
        """
        return self.rates.get(country_code, {}) 