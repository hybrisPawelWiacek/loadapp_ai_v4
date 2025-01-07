"""Manual test script for Google Maps service functionality."""
import os
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

# Add the project root directory to Python path to import backend modules
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from backend.domain.entities.route import Location
from backend.infrastructure.external_services.google_maps_service import GoogleMapsService
from backend.domain.services.route_service import LocationRepository
from backend.infrastructure.logging import get_logger

logger = get_logger()

class MockLocationRepository(LocationRepository):
    """Mock repository for testing."""
    def save(self, location):
        return location
    
    def get(self, location_id):
        return None

def test_google_maps_service():
    """Test main Google Maps service functionality."""
    try:
        # Get credentials from environment
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        max_retries = int(os.getenv('GMAPS_MAX_RETRIES', 3))
        retry_delay = float(os.getenv('GMAPS_RETRY_DELAY', 1.0))
        timeout = float(os.getenv('GMAPS_TIMEOUT', 30.0))

        if not api_key:
            logger.error("GOOGLE_MAPS_API_KEY not found in environment variables")
            return False

        # Initialize service
        logger.info("Initializing Google Maps service...")
        service = GoogleMapsService(
            api_key=api_key,
            location_repo=MockLocationRepository(),
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout
        )

        # Test 1: Geocoding
        logger.info("Testing geocoding...")
        berlin_address = "Alexanderplatz, Berlin, Germany"
        berlin_location = service.geocode(berlin_address)
        logger.info(f"Berlin coordinates: {berlin_location.latitude}, {berlin_location.longitude}")

        # Test 2: Reverse Geocoding
        logger.info("Testing reverse geocoding...")
        paris_coords = (48.8566, 2.3522)
        paris_location = service.reverse_geocode(*paris_coords)
        logger.info(f"Paris address: {paris_location.address}")

        # Test 3: Route Calculation
        logger.info("Testing route calculation...")
        origin = Location(
            id=uuid4(),
            latitude=52.5200,
            longitude=13.4050,
            address="Berlin, Germany"
        )
        destination = Location(
            id=uuid4(),
            latitude=48.8566,
            longitude=2.3522,
            address="Paris, France"
        )

        total_distance, total_duration, segments = service.calculate_route(
            origin=origin,
            destination=destination,
            departure_time=int(datetime.now().timestamp())
        )

        logger.info(f"Route calculation results:")
        logger.info(f"Total distance: {total_distance:.2f} km")
        logger.info(f"Total duration: {total_duration:.2f} hours")
        logger.info(f"Number of segments: {len(segments)}")

        for i, segment in enumerate(segments, 1):
            logger.info(f"Segment {i}:")
            logger.info(f"  Country: {segment.country_code}")
            logger.info(f"  Distance: {segment.distance_km:.2f} km")
            logger.info(f"  Duration: {segment.duration_hours:.2f} hours")

        # Test 4: Distance Matrix
        logger.info("Testing distance matrix...")
        origins = [origin]
        destinations = [destination]
        matrix = service.get_distance_matrix(origins, destinations)
        
        logger.info("Distance matrix results:")
        logger.info(f"Distances: {matrix['distances']}")
        logger.info(f"Durations: {matrix['durations']}")

        logger.info("All tests completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_google_maps_service()
    sys.exit(0 if success else 1) 