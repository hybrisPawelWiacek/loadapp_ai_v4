"""Unit tests for toll rate service adapter."""
import pytest
from decimal import Decimal

from backend.domain.entities.route import CountrySegment, Location
from backend.infrastructure.external_services.toll_rate_service import (
    DefaultTollRateService, DEFAULT_TOLL_RATES
)


@pytest.fixture
def service():
    """Create a toll rate service instance."""
    return DefaultTollRateService()


@pytest.fixture
def sample_segment():
    """Create a sample route segment."""
    return CountrySegment(
        country_code="DE",
        distance_km=100.0,
        duration_hours=1.5,
        start_location=Location(
            latitude=52.5200,
            longitude=13.4050,
            address="Berlin, Germany"
        ),
        end_location=Location(
            latitude=52.3000,
            longitude=13.2000,
            address="Brandenburg, Germany"
        )
    )


@pytest.fixture
def sample_truck_specs():
    """Create sample truck specifications."""
    return {
        "toll_class": "40",  # 40t
        "euro_class": "EURO6",
        "co2_class": "A"
    }


def test_initialization():
    """Test service initialization."""
    service = DefaultTollRateService()
    assert service.rates == DEFAULT_TOLL_RATES


def test_calculate_toll_success(service, sample_segment, sample_truck_specs):
    """Test successful toll calculation."""
    toll = service.calculate_toll(sample_segment, sample_truck_specs)

    # Calculate expected toll:
    # Base rate for 40t in DE: 0.25
    # EURO6 adjustment: -0.03
    # CO2 class A adjustment: -0.02
    # Final rate: 0.20 per km
    # Distance: 100 km
    # Expected toll: 20.00
    expected_toll = Decimal("20.00")

    assert toll == expected_toll


def test_calculate_toll_unknown_country(service, sample_segment, sample_truck_specs):
    """Test toll calculation for unknown country."""
    sample_segment.country_code = "XX"
    toll = service.calculate_toll(sample_segment, sample_truck_specs)
    assert toll == Decimal("0")


def test_calculate_toll_invalid_truck_class(service, sample_segment):
    """Test toll calculation with invalid truck class."""
    invalid_specs = {
        "toll_class": "999",  # Invalid class
        "euro_class": "EURO6",
        "co2_class": "A"
    }

    with pytest.raises(ValueError, match="Invalid truck specifications"):
        service.calculate_toll(sample_segment, invalid_specs)


def test_calculate_toll_invalid_euro_class(service, sample_segment):
    """Test toll calculation with invalid euro class."""
    invalid_specs = {
        "toll_class": "40",
        "euro_class": "INVALID",  # Invalid class
        "co2_class": "A"
    }

    with pytest.raises(ValueError, match="Invalid truck specifications"):
        service.calculate_toll(sample_segment, invalid_specs)


def test_calculate_toll_invalid_co2_class(service, sample_segment):
    """Test toll calculation with invalid CO2 class."""
    invalid_specs = {
        "toll_class": "40",
        "euro_class": "EURO6",
        "co2_class": "INVALID"  # Invalid class
    }

    with pytest.raises(ValueError, match="Invalid truck specifications"):
        service.calculate_toll(sample_segment, invalid_specs)


def test_calculate_toll_missing_specs(service, sample_segment):
    """Test toll calculation with missing specifications."""
    incomplete_specs = {
        "toll_class": "40"
        # Missing euro_class and co2_class
    }

    with pytest.raises(ValueError, match="Invalid truck specifications"):
        service.calculate_toll(sample_segment, incomplete_specs)


def test_toll_rates_for_different_countries(service, sample_segment, sample_truck_specs):
    """Test toll calculation for different countries."""
    # Test Germany
    sample_segment.country_code = "DE"
    toll_de = service.calculate_toll(sample_segment, sample_truck_specs)

    # Test Poland
    sample_segment.country_code = "PL"
    toll_pl = service.calculate_toll(sample_segment, sample_truck_specs)

    # Poland should have lower rates than Germany
    assert toll_pl < toll_de


def test_toll_rates_for_different_truck_classes(service, sample_segment, sample_truck_specs):
    """Test toll calculation for different truck classes."""
    # Test 7.5t truck
    specs_7_5 = dict(sample_truck_specs)
    specs_7_5["toll_class"] = "7.5"
    toll_7_5 = service.calculate_toll(sample_segment, specs_7_5)

    # Test 40t truck
    specs_40 = dict(sample_truck_specs)
    specs_40["toll_class"] = "40"
    toll_40 = service.calculate_toll(sample_segment, specs_40)

    # Heavier trucks should pay more
    assert toll_40 > toll_7_5


def test_toll_rates_for_different_euro_classes(service, sample_segment, sample_truck_specs):
    """Test toll calculation for different euro classes."""
    # Test EURO6 (most efficient)
    specs_euro6 = dict(sample_truck_specs)
    specs_euro6["euro_class"] = "EURO6"
    toll_euro6 = service.calculate_toll(sample_segment, specs_euro6)

    # Test EURO4 (less efficient)
    specs_euro4 = dict(sample_truck_specs)
    specs_euro4["euro_class"] = "EURO4"
    toll_euro4 = service.calculate_toll(sample_segment, specs_euro4)

    # Less efficient engines should pay more
    assert toll_euro4 > toll_euro6


def test_toll_rates_for_different_co2_classes(service, sample_segment, sample_truck_specs):
    """Test toll calculation for different CO2 classes."""
    # Test class A (most efficient)
    specs_a = dict(sample_truck_specs)
    specs_a["co2_class"] = "A"
    toll_a = service.calculate_toll(sample_segment, specs_a)

    # Test class C (least efficient)
    specs_c = dict(sample_truck_specs)
    specs_c["co2_class"] = "C"
    toll_c = service.calculate_toll(sample_segment, specs_c)

    # Less efficient CO2 class should pay more
    assert toll_c > toll_a


def test_get_toll_rates(service):
    """Test getting toll rates for a country."""
    # Test existing country
    de_rates = service.get_toll_rates("DE")
    assert de_rates == DEFAULT_TOLL_RATES["DE"]

    # Test non-existing country
    unknown_rates = service.get_toll_rates("XX")
    assert unknown_rates == {} 