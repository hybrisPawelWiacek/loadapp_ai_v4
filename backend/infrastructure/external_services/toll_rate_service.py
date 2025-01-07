"""Toll rate service implementation."""
import time
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, List, Tuple
from uuid import UUID

import googlemaps
from googlemaps.exceptions import ApiError, TransportError
import requests
import re

from ...domain.entities.route import CountrySegment
from ...infrastructure.logging import get_logger
from ...infrastructure.external_services.exceptions import ExternalServiceError
from ..data.toll_rates import (
    TOLL_KEYWORDS,
    get_toll_rate,
    get_toll_class_description,
    get_euro_class_description,
    DEFAULT_UNKNOWN_RATE
)


class TollRateServiceError(ExternalServiceError):
    """Specific exception for toll rate service errors."""
    pass


logger = get_logger()


class TollRateService:
    """Service for calculating toll rates using Google Maps API with fallback to default rates."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """Initialize toll rate service.
        
        Args:
            api_key: Google Maps API key (optional)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds
        """
        self._logger = logger.bind(service="toll_rate")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Initialize Google Maps client if API key is provided
        self.client = None
        if api_key:
            try:
                self.client = googlemaps.Client(key=api_key)
                self._logger.info("Google Maps client initialized successfully")
            except Exception as e:
                self._logger.warning(
                    "Failed to initialize Google Maps client, will use default rates",
                    error=str(e)
                )

    def _extract_road_name(self, text: str) -> Optional[str]:
        """Extract road name from text using common patterns."""
        patterns = [
            r'\b[aA][0-9]{1,3}\b',  # A1, A12, A123
            r'\b[eE][0-9]{1,3}\b',  # E40, E55
            r'\b[dD][0-9]{1,3}\b',  # D1, D11
            r'\b[sS][0-9]{1,3}\b'   # S1, S8
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0).upper()
                
        autobahn_match = re.search(r'autobahn[- ]?([0-9]{1,3})', text.lower())
        if autobahn_match:
            return f"A{autobahn_match.group(1)}"
            
        return None

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        text = re.sub(r'<[^>]+>', '', text)
        text = text.replace('&nbsp;', ' ').replace('/<wbr/>', ' ')
        return ' '.join(text.split()).lower()

    def _get_toll_data(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
        vehicle_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get toll data from Google Maps Directions API.
        
        Returns None if the API call fails or no route is found.
        """
        if not self.client:
            return None

        try:
            result = self.client.directions(
                origin=origin,
                destination=destination,
                mode="driving",
                alternatives=False,
                units="metric",
                avoid=None,  # Don't avoid tolls
                departure_time="now",
                language="en"
            )
            
            if not result:
                self._logger.warning("No route found from Google Maps API")
                return None
                
            return result[0]
            
        except Exception as e:
            self._logger.warning(
                "Failed to get toll data from Google Maps API",
                error=str(e)
            )
            return None

    def _calculate_default_toll(
        self,
        country_code: str,
        distance_km: float,
        toll_class: str,
        euro_class: str
    ) -> Tuple[Decimal, bool]:
        """Calculate toll using default rates.
        
        Returns:
            Tuple of (toll_amount, used_default_rates)
        """
        rates = get_toll_rate(country_code, toll_class, euro_class)
        total_rate = rates["base_rate"] + rates["euro_adjustment"]
        total_cost = total_rate * Decimal(str(distance_km))

        self._logger.info(
            "Calculated toll cost using default rates",
            country_code=country_code,
            distance_km=distance_km,
            toll_class=f"{toll_class} ({get_toll_class_description(toll_class)})",
            euro_class=f"{euro_class} ({get_euro_class_description(euro_class)})",
            base_rate=str(rates["base_rate"]),
            euro_adjustment=str(rates["euro_adjustment"]),
            total_cost=str(total_cost)
        )

        return total_cost, True

    def get_toll_rate(
        self,
        country_code: str,
        distance_km: float,
        toll_class: str,
        euro_class: str,
        co2_class: str,
        origin: Optional[tuple[float, float]] = None,
        destination: Optional[tuple[float, float]] = None
    ) -> Tuple[Decimal, bool]:
        """Calculate toll rate for a route segment.
        
        Args:
            country_code: ISO country code
            distance_km: Distance in kilometers
            toll_class: Vehicle toll class
            euro_class: Vehicle euro emission class
            co2_class: Vehicle CO2 emission class
            origin: Optional start coordinates (lat, lon)
            destination: Optional end coordinates (lat, lon)
            
        Returns:
            Tuple of (toll_amount, used_default_rates)
            
        Raises:
            TollRateServiceError: If calculation fails completely
        """
        try:
            # Try to use Google Maps API if coordinates are provided
            if origin and destination:
                route_data = self._get_toll_data(origin, destination, toll_class)
                
                if route_data:
                    # Extract toll information
                    toll_amount = Decimal('0')
                    has_tolls = any('toll' in warning.lower() for warning in route_data.get('warnings', []))
                    
                    # Process each leg of the route
                    if route_data.get('legs'):
                        for leg in route_data['legs']:
                            for step in leg.get('steps', []):
                                html_instructions = self._clean_html(step.get('html_instructions', ''))
                                
                                # Check for toll roads
                                is_toll = False
                                
                                # Check toll keywords
                                if any(keyword in html_instructions for keyword in TOLL_KEYWORDS):
                                    is_toll = True
                                
                                # Check road names
                                road_name = self._extract_road_name(html_instructions)
                                if road_name and has_tolls:
                                    is_toll = True
                                
                                # Calculate toll if toll road found
                                if is_toll:
                                    step_distance_km = step['distance']['value'] / 1000
                                    rates = get_toll_rate(country_code, toll_class, euro_class)
                                    total_rate = rates["base_rate"] + rates["euro_adjustment"]
                                    segment_toll = Decimal(str(step_distance_km)) * total_rate
                                    
                                    self._logger.info(
                                        "Toll segment found via Google Maps",
                                        road=road_name,
                                        distance_km=step_distance_km,
                                        rate=str(total_rate),
                                        toll=str(segment_toll)
                                    )
                                    
                                    toll_amount += segment_toll
                    
                    if toll_amount > Decimal('0'):
                        return toll_amount, False

            # Fall back to default rates if:
            # 1. No coordinates provided
            # 2. Google Maps API call failed
            # 3. No toll roads found in Google Maps data
            return self._calculate_default_toll(country_code, distance_km, toll_class, euro_class)

        except Exception as e:
            self._logger.error("Failed to calculate toll rate", error=str(e))
            # Final fallback - use default rates
            return self._calculate_default_toll(country_code, distance_km, toll_class, euro_class) 