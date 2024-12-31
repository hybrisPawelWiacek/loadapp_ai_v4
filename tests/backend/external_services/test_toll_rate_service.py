"""Unit tests for toll rate service adapter."""
import pytest
from decimal import Decimal
from uuid import uuid4

from backend.domain.entities.route import CountrySegment, Location
from backend.infrastructure.external_services.toll_rate_service import (
    TollRateService, DEFAULT_TOLL_RATES
)


@pytest.fixture
def service():
    """Create a toll rate service instance."""
    return TollRateService()


@pytest.fixture
def sample_segment():
    """Create a sample route segment."""
    return CountrySegment(
        country_code="DE",
        distance_km=100.0,
        duration_hours=1.5,
        start_location=Location(
            id=uuid4(),
            latitude=52.5200,
            longitude=13.4050,
            address="Berlin, Germany"
        ),
        end_location=Location(
            id=uuid4(),
            latitude=52.3000,
            longitude=13.2000,
            address="Brandenburg, Germany"
        )
    )


@pytest.fixture
def sample_truck_specs():
    """Create sample truck specifications."""
    return {
        "toll_class": "4",  # Class 4 (over 18t)
        "euro_class": "VI",  # EURO VI
        "co2_class": "A"
    }


def test_initialization():
    """Test service initialization."""
    service = TollRateService()
    assert service.timeout == 30.0
    assert service.max_retries == 3
    assert service.retry_delay == 1.0


def test_get_toll_rate_success(service, sample_segment, sample_truck_specs):
    """Test successful toll calculation."""
    toll = service.get_toll_rate(
        country_code=sample_segment.country_code,
        distance_km=sample_segment.distance_km,
        toll_class=sample_truck_specs["toll_class"],
        euro_class=sample_truck_specs["euro_class"],
        co2_class=sample_truck_specs["co2_class"]
    )

    # Calculate expected toll:
    # Base rate for class 4 in DE: 0.248
    # EURO VI adjustment: 0.000
    # Total rate: 0.248 per km
    # Distance: 100 km
    # Expected toll: 24.80
    expected_toll = Decimal("24.80")

    assert toll == expected_toll


def test_get_toll_rate_unknown_country(service, sample_segment, sample_truck_specs):
    """Test toll calculation for unknown country."""
    toll = service.get_toll_rate(
        country_code="XX",
        distance_km=sample_segment.distance_km,
        toll_class=sample_truck_specs["toll_class"],
        euro_class=sample_truck_specs["euro_class"],
        co2_class=sample_truck_specs["co2_class"]
    )
    # Should use default rate of 0.200 EUR/km
    expected_toll = Decimal("20.00")
    assert toll == expected_toll


def test_toll_rates_for_different_countries(service, sample_segment, sample_truck_specs):
    """Test toll calculation for different countries."""
    # Test Germany
    toll_de = service.get_toll_rate(
        country_code="DE",
        distance_km=sample_segment.distance_km,
        toll_class=sample_truck_specs["toll_class"],
        euro_class=sample_truck_specs["euro_class"],
        co2_class=sample_truck_specs["co2_class"]
    )

    # Test France
    toll_fr = service.get_toll_rate(
        country_code="FR",
        distance_km=sample_segment.distance_km,
        toll_class=sample_truck_specs["toll_class"],
        euro_class=sample_truck_specs["euro_class"],
        co2_class=sample_truck_specs["co2_class"]
    )

    # France should have lower rates than Germany
    assert toll_fr < toll_de


def test_toll_rates_for_different_truck_classes(service, sample_segment):
    """Test toll calculation for different truck classes."""
    # Test class 1 truck (up to 7.5t)
    toll_class_1 = service.get_toll_rate(
        country_code=sample_segment.country_code,
        distance_km=sample_segment.distance_km,
        toll_class="1",
        euro_class="VI",
        co2_class="A"
    )

    # Test class 4 truck (over 18t)
    toll_class_4 = service.get_toll_rate(
        country_code=sample_segment.country_code,
        distance_km=sample_segment.distance_km,
        toll_class="4",
        euro_class="VI",
        co2_class="A"
    )

    # Heavier trucks should pay more
    assert toll_class_4 > toll_class_1


def test_toll_rates_for_different_euro_classes(service, sample_segment):
    """Test toll calculation for different euro classes."""
    # Test EURO VI (most efficient)
    toll_euro_6 = service.get_toll_rate(
        country_code=sample_segment.country_code,
        distance_km=sample_segment.distance_km,
        toll_class="4",
        euro_class="VI",
        co2_class="A"
    )

    # Test EURO III (less efficient)
    toll_euro_3 = service.get_toll_rate(
        country_code=sample_segment.country_code,
        distance_km=sample_segment.distance_km,
        toll_class="4",
        euro_class="III",
        co2_class="A"
    )

    # Less efficient engines should pay more
    assert toll_euro_3 > toll_euro_6 