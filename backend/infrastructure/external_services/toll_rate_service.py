"""Toll rate service implementation."""
import time
from decimal import Decimal
from typing import Dict, Any

import requests
from requests.exceptions import RequestException, Timeout

from ...infrastructure.logging import get_logger
from ...infrastructure.external_services.exceptions import ExternalServiceError


class TollRateServiceError(ExternalServiceError):
    """Specific exception for toll rate service errors."""
    pass


# Default toll rates per country and vehicle class (EUR/km)
DEFAULT_TOLL_RATES = {
    "DE": {  # Germany
        "toll_class": {
            "1": Decimal("0.187"),  # Up to 7.5t
            "2": Decimal("0.208"),  # 7.5t - 12t
            "3": Decimal("0.228"),  # 12t - 18t
            "4": Decimal("0.248")   # Over 18t
        },
        "euro_class": {
            "VI": Decimal("0.000"),
            "V": Decimal("0.021"),
            "IV": Decimal("0.042"),
            "III": Decimal("0.063")
        }
    },
    "FR": {  # France
        "toll_class": {
            "1": Decimal("0.176"),
            "2": Decimal("0.196"),
            "3": Decimal("0.216"),
            "4": Decimal("0.236")
        },
        "euro_class": {
            "VI": Decimal("0.000"),
            "V": Decimal("0.020"),
            "IV": Decimal("0.040"),
            "III": Decimal("0.060")
        }
    }
}


logger = get_logger()


class TollRateService:
    """Service for calculating toll rates."""

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """Initialize toll rate service.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds
        """
        self._logger = logger.bind(service="toll_rate")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._logger.info("Toll rate service initialized successfully")

    def _make_request(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to toll rate API with retry logic."""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
            except Timeout as e:
                last_error = e
                if attempt == self.max_retries - 1:
                    self._logger.error(
                        "Toll rate API timeout",
                        error=str(e),
                        attempt=attempt + 1,
                        max_retries=self.max_retries
                    )
                    break
                self._logger.warning(
                    "Toll rate API timeout, retrying",
                    error=str(e),
                    attempt=attempt + 1,
                    retry_delay=self.retry_delay * (attempt + 1)
                )
                time.sleep(self.retry_delay * (attempt + 1))
            except RequestException as e:
                self._logger.error("Toll rate API error", error=str(e))
                raise TollRateServiceError(f"Toll rate API error: {str(e)}")
            except Exception as e:
                self._logger.error("Unexpected error in toll rate request", error=str(e))
                raise TollRateServiceError(f"Failed to get toll rate: {str(e)}")

        if last_error:
            raise TollRateServiceError(f"Failed after {self.max_retries} retries: {str(last_error)}")

    def get_toll_rate(
        self,
        country_code: str,
        distance_km: float,
        toll_class: str,
        euro_class: str,
        co2_class: str
    ) -> Decimal:
        """Calculate toll rate for a route segment.
        
        For PoC, uses default rates from lookup table.
        In production, would call external toll rate API.
        """
        try:
            # Validate country code
            if country_code not in DEFAULT_TOLL_RATES:
                self._logger.warning(
                    "Unknown country code, using default rate",
                    country_code=country_code
                )
                return Decimal("0.200") * Decimal(str(distance_km))

            # Get base rate for toll class
            toll_rates = DEFAULT_TOLL_RATES[country_code]
            base_rate = toll_rates["toll_class"].get(
                toll_class,
                toll_rates["toll_class"]["1"]  # Default to class 1
            )

            # Add euro class adjustment
            euro_adjustment = toll_rates["euro_class"].get(
                euro_class,
                toll_rates["euro_class"]["III"]  # Default to EURO III
            )

            # Calculate total rate
            total_rate = base_rate + euro_adjustment

            # Calculate total cost
            total_cost = total_rate * Decimal(str(distance_km))

            self._logger.info(
                "Calculated toll cost",
                country_code=country_code,
                distance_km=distance_km,
                toll_class=toll_class,
                euro_class=euro_class,
                base_rate=str(base_rate),
                euro_adjustment=str(euro_adjustment),
                total_cost=str(total_cost)
            )

            return total_cost

        except Exception as e:
            self._logger.error("Failed to calculate toll rate", error=str(e))
            raise TollRateServiceError(f"Failed to calculate toll rate: {str(e)}") 