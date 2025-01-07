"""Service for managing location-related business logic."""
from typing import Optional, Protocol
from uuid import UUID

from ..entities.location import Location
from ...infrastructure.external_services.google_maps_service import GoogleMapsService


class LocationRepository(Protocol):
    """Repository interface for Location entity."""
    def save(self, location: Location) -> Location:
        """Save a location instance."""
        ...
        
    def find_by_id(self, id: UUID) -> Optional[Location]:
        """Find a location by ID."""
        ...


class LocationService:
    """Service for managing location-related business logic."""
    
    def __init__(
        self,
        location_repo: LocationRepository,
        maps_service: GoogleMapsService
    ):
        self._location_repo = location_repo
        self._maps_service = maps_service
        
    def create_location(self, address: str) -> Location:
        """Create a new location from an address.
        
        Args:
            address: The address to geocode
            
        Returns:
            Location: The created location
            
        Raises:
            ValueError: If the address cannot be geocoded
        """
        # Geocode the address
        location = self._maps_service.geocode(address)
        
        # Save and return the location
        return self._location_repo.save(location)
        
    def get_location(self, location_id: UUID) -> Optional[Location]:
        """Get a location by ID.
        
        Args:
            location_id: The location ID
            
        Returns:
            Optional[Location]: The location if found, None otherwise
        """
        return self._location_repo.find_by_id(location_id)
        
    def validate_location(self, address: str) -> dict:
        """Validate a location address.
        
        Args:
            address: The address to validate
            
        Returns:
            dict: Validation result with coordinates if valid
        """
        try:
            location = self._maps_service.geocode(address)
            return {
                "valid": True,
                "coordinates": {
                    "latitude": location.latitude,
                    "longitude": location.longitude
                },
                "formatted_address": location.address
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            } 