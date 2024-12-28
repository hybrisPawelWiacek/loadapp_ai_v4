"""Implementation of toll rate service."""
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import UUID
from functools import lru_cache

import googlemaps
from googlemaps.exceptions import ApiError, TransportError
import requests
import json
import re

from src.domain.value_objects import CountrySegment, Location
from src.domain.interfaces.services.toll_rate_service import TollRateService, TollRateServiceError
from src.infrastructure.logging import get_logger
from src.settings import get_settings
from src.infrastructure.data.toll_roads import (
    TOLL_KEYWORDS, TOLL_RATES, is_toll_road, get_toll_rate
)

logger = get_logger()

class GoogleMapsTollRateService(TollRateService):
    """Google Maps implementation of toll rate service."""

    def __init__(self, api_key: Optional[str] = None, route_repository: Optional['RouteRepository'] = None):
        """Initialize Google Maps toll rate service.
        
        Args:
            api_key: Optional API key (defaults to settings.api.google_maps_key)
            route_repository: Optional repository for route lookups
            
        Raises:
            TollRateServiceError: If API key is not found
        """
        self._logger = logger.bind(service="google_maps_toll")
        settings = get_settings()
        
        # Get API key from settings if not provided
        if api_key is None:
            if settings.api.google_maps_key:
                self.api_key = settings.api.google_maps_key.get_secret_value()
            else:
                raise TollRateServiceError("Google Maps API key not found in settings")
        else:
            self.api_key = api_key
            
        self.route_repository = route_repository
        
        # Get API settings
        self.max_retries = settings.api.gmaps_max_retries
        self.retry_delay = settings.api.gmaps_retry_delay
        
        try:
            self.client = googlemaps.Client(key=self.api_key)
            self._logger.info("Google Maps client initialized successfully")
        except Exception as e:
            self._logger.error("Failed to initialize Google Maps client", error=str(e))
            raise TollRateServiceError(f"Failed to initialize Google Maps client: {str(e)}")

    def _extract_road_name(self, text: str) -> Optional[str]:
        """Extract road name from text using common patterns.
        
        Args:
            text: Text to extract road name from
            
        Returns:
            Road name if found, None otherwise
        """
        # Common patterns for road names
        patterns = [
            r'\b[aA][0-9]{1,3}\b',  # A1, A12, A123
            r'\b[eE][0-9]{1,3}\b',  # E40, E55
            r'\b[dD][0-9]{1,3}\b',  # D1, D11 (Czech Republic)
            r'\b[sS][0-9]{1,3}\b'   # S1, S8 (Poland)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0).upper()
                
        # Also check for road numbers after "autobahn"
        autobahn_match = re.search(r'autobahn[- ]?([0-9]{1,3})', text.lower())
        if autobahn_match:
            return f"A{autobahn_match.group(1)}"
            
        return None

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text.
        
        Args:
            text: Text with HTML tags
            
        Returns:
            Text without HTML tags
        """
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove special HTML entities
        text = text.replace('&nbsp;', ' ').replace('/<wbr/>', ' ')
        # Normalize whitespace
        text = ' '.join(text.split())
        return text.lower()

    def _get_toll_data(self, origin: Location, destination: Location, vehicle_type: str) -> Dict[str, Any]:
        """Get toll data from Google Maps Directions API.
        
        Args:
            origin: Start location
            destination: End location
            vehicle_type: Type of vehicle
            
        Returns:
            Dict containing route and toll information
            
        Raises:
            TollRateServiceError: If API call fails
        """
        try:
            # Use the standard directions API
            result = self.client.directions(
                origin=(origin.latitude, origin.longitude),
                destination=(destination.latitude, destination.longitude),
                mode="driving",
                alternatives=False,
                units="metric",
                # Add relevant parameters for toll information
                avoid=None,  # Don't avoid tolls
                departure_time="now",  # Get current traffic
                language="en"  # Ensure English responses
            )
            
            if not result:
                raise TollRateServiceError("No route found")
                
            return result[0]  # Get primary route
            
        except Exception as e:
            self._logger.error("Failed to get toll data", error=str(e))
            raise TollRateServiceError(f"Failed to get toll data: {str(e)}")

    def calculate_toll(
        self,
        route_id: UUID,
        vehicle_type: str,
        time: Optional[datetime] = None
    ) -> Decimal:
        """Calculate toll for a route.
        
        Args:
            route_id: Route ID
            vehicle_type: Type of vehicle
            time: Optional time for rate calculation
            
        Returns:
            Calculated toll amount
            
        Raises:
            TollRateServiceError: If calculation fails
        """
        if not self.route_repository:
            raise TollRateServiceError("Route repository not configured")
            
        try:
            # Get route from repository
            route = self.route_repository.get_by_id(route_id)
            if not route:
                raise TollRateServiceError(f"Route not found: {route_id}")
                
            # Convert location dictionaries to Location objects
            origin = Location(**route.origin)
            destination = Location(**route.destination)
            
            # Get route data from Google Maps
            route_data = self._get_toll_data(origin, destination, vehicle_type)
            
            # Extract toll information from route data
            toll_amount = Decimal('0')
            
            # Check for toll roads in warnings
            warnings = route_data.get('warnings', [])
            has_tolls = any('toll' in warning.lower() for warning in warnings)
            
            self._logger.info(
                "Route warnings",
                warnings=warnings,
                has_tolls=has_tolls
            )
            
            # Process each leg of the route
            if route_data.get('legs'):
                for leg in route_data['legs']:
                    # Check steps for toll roads
                    for step in leg.get('steps', []):
                        html_instructions = self._clean_html(step.get('html_instructions', ''))
                        
                        self._logger.info(
                            "Processing step",
                            instructions=html_instructions
                        )
                        
                        # Multiple ways to detect toll roads:
                        is_toll = False
                        
                        # 1. Check for toll keywords in instructions
                        if any(keyword in html_instructions for keyword in TOLL_KEYWORDS):
                            is_toll = True
                            self._logger.info("Toll detected by keyword")
                            
                        # 2. Extract and check road names against known toll roads
                        road_name = self._extract_road_name(html_instructions)
                        if road_name:
                            # Try to determine country from step
                            # This is a simplification - in reality we'd need better country detection
                            country_code = "DE"  # Default to Germany for now
                            if is_toll_road(road_name, country_code):
                                is_toll = True
                                self._logger.info(
                                    "Toll detected by road name",
                                    road_name=road_name,
                                    country=country_code
                                )
                                
                                # Calculate toll for this segment
                                distance_km = step['distance']['value'] / 1000  # Convert meters to km
                                rate = Decimal(str(get_toll_rate(country_code, vehicle_type)))
                                segment_toll = Decimal(str(distance_km)) * rate
                                
                                self._logger.info(
                                    "Toll segment found",
                                    road=road_name,
                                    distance_km=distance_km,
                                    rate=rate,
                                    toll=segment_toll
                                )
                                
                                toll_amount += segment_toll
                        
                        # 3. Consider the entire step as toll if warnings indicated tolls
                        elif has_tolls and any(keyword in html_instructions for keyword in ['motorway', 'highway', 'autobahn']):
                            is_toll = True
                            self._logger.info("Toll detected by warning + highway")
                            
                            # Calculate toll for this segment
                            distance_km = step['distance']['value'] / 1000  # Convert meters to km
                            rate = Decimal(str(get_toll_rate("DE", vehicle_type)))  # Default to Germany
                            segment_toll = Decimal(str(distance_km)) * rate
                            
                            self._logger.info(
                                "Toll segment found",
                                road="unknown",
                                distance_km=distance_km,
                                rate=rate,
                                toll=segment_toll
                            )
                            
                            toll_amount += segment_toll
            
            return toll_amount
            
        except Exception as e:
            self._logger.error("Failed to calculate toll", error=str(e))
            raise TollRateServiceError(f"Failed to calculate toll: {str(e)}")

    def get_current_rates(self, region: str) -> Dict:
        """Get current toll rates for region.
        
        Args:
            region: Country code
            
        Returns:
            Dict of current rates
        """
        return {
            vehicle_type: rate
            for vehicle_type, rate in TOLL_RATES.get(region, TOLL_RATES["default"]).items()
        }

    def update_rates(self, region: str, new_rates: Dict, effective_date: datetime) -> bool:
        """Update toll rates for region.
        
        Note: Google Maps API is read-only.
        """
        raise NotImplementedError("Rate updates not supported by Google Maps API")

    def validate_rates(self, rates: Dict) -> bool:
        """Validate rate configuration.
        
        Note: Google Maps API is read-only.
        """
        raise NotImplementedError("Rate validation not supported by Google Maps API")

    def get_rate_history(
        self,
        region: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """Get history of rate changes.
        
        Note: Google Maps API doesn't provide rate history.
        """
        raise NotImplementedError("Rate history not supported by Google Maps API")

    def has_toll_roads(self, country_code: str) -> bool:
        """Check if a country has toll roads.
        
        Args:
            country_code: ISO country code
            
        Returns:
            True if country has toll roads
        """
        return country_code.upper() in TOLL_RATES


class DefaultTollRateService(TollRateService):
    """Default implementation of toll rate service using static data."""

    def __init__(self):
        # Default toll rates per km by country and vehicle type
        # In a real implementation, this would come from an API or database
        self._toll_rates = {
            "DE": {  # Germany
                "truck": {
                    "highway": Decimal("0.17"),  # €/km for highways
                    "national": Decimal("0.12"),  # €/km for national roads
                },
                "van": {
                    "highway": Decimal("0.11"),
                    "national": Decimal("0.08"),
                },
            },
            "FR": {  # France
                "truck": {
                    "highway": Decimal("0.20"),
                    "national": Decimal("0.15"),
                },
                "van": {
                    "highway": Decimal("0.12"),
                    "national": Decimal("0.09"),
                },
            },
            # Add more countries as needed
        }
        self._rate_history = {}  # Store rate history by region
        self._rate_updates = {}  # Store pending rate updates

    @lru_cache(maxsize=128)
    def get_toll_rates(self, country_code: str, vehicle_type: str) -> Dict[str, Decimal]:
        """Get toll rates for a specific country and vehicle type."""
        country_rates = self._toll_rates.get(country_code, {})
        return country_rates.get(vehicle_type, {})

    def calculate_segment_toll_rates(
        self, segment: CountrySegment, vehicle_type: str
    ) -> Dict[str, Decimal]:
        """Calculate toll rates for a specific country segment."""
        rates = self.get_toll_rates(segment.country_code, vehicle_type)
        if not rates:
            raise TollRateServiceError(
                f"No toll rates found for country {segment.country_code} "
                f"and vehicle type {vehicle_type}"
            )
        return rates

    def calculate_toll(
        self,
        route_id: UUID,
        vehicle_type: str,
        time: Optional[datetime] = None
    ) -> Decimal:
        """Calculate toll for a route."""
        # In a real implementation, we would:
        # 1. Fetch route details from database
        # 2. Calculate toll based on segments and vehicle type
        # 3. Apply time-based adjustments
        # For now, return a dummy value
        return Decimal("50.00")

    def get_current_rates(self, region: str) -> Dict:
        """Get current toll rates for region."""
        if region not in self._toll_rates:
            raise TollRateServiceError(f"No rates found for region {region}")
        return self._toll_rates[region]

    def update_rates(
        self,
        region: str,
        new_rates: Dict,
        effective_date: datetime
    ) -> bool:
        """Update toll rates for region."""
        try:
            # Validate new rates
            if not self.validate_rates(new_rates):
                return False
            
            # Store current rates in history
            if region not in self._rate_history:
                self._rate_history[region] = []
            self._rate_history[region].append({
                'rates': self._toll_rates.get(region, {}),
                'effective_until': effective_date
            })
            
            # Update rates
            self._toll_rates[region] = new_rates
            self._rate_updates[region] = {
                'rates': new_rates,
                'effective_date': effective_date
            }
            
            # Clear cache to ensure new rates are used
            self.get_toll_rates.cache_clear()
            
            return True
        except Exception as e:
            raise TollRateServiceError(f"Failed to update rates: {str(e)}")

    def validate_rates(self, rates: Dict) -> bool:
        """Validate rate configuration."""
        try:
            # Check structure
            for vehicle_type, vehicle_rates in rates.items():
                if not isinstance(vehicle_type, str):
                    return False
                if not isinstance(vehicle_rates, dict):
                    return False
                
                # Check road types and values
                for road_type, rate in vehicle_rates.items():
                    if road_type not in ('highway', 'national'):
                        return False
                    if not isinstance(rate, (Decimal, float, int)):
                        return False
                    if rate < 0:
                        return False
            
            return True
        except Exception:
            return False

    def get_rate_history(
        self,
        region: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """Get history of rate changes."""
        if region not in self._rate_history:
            raise TollRateServiceError(f"No rate history found for region {region}")
        
        # Filter history by date range
        history = []
        for entry in self._rate_history[region]:
            if start_date <= entry['effective_until'] <= end_date:
                history.append(entry)
        
        return history

    @lru_cache(maxsize=128)
    def has_toll_roads(self, country_code: str) -> bool:
        """Check if a country has toll roads."""
        # For now, just check if we have any toll rates for this country
        return country_code in self._toll_rates
