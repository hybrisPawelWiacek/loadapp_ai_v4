"""Tests for cargo domain entities."""
import pytest
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from backend.domain.entities.cargo import (
    Cargo,
    CostSettings,
    CostBreakdown,
    Offer
)


@pytest.fixture
def sample_cargo():
    """Create sample cargo."""
    return Cargo(
        id=uuid4(),
        weight=24000.0,
        value=Decimal("50000.00"),
        special_requirements=["TEMPERATURE_CONTROLLED", "FRAGILE"]
    )


@pytest.fixture
def sample_cost_settings():
    """Create sample cost settings."""
    return CostSettings(
        id=uuid4(),
        route_id=uuid4(),
        enabled_components=["FUEL", "TOLL", "DRIVER", "OVERHEAD"],
        rates={
            "fuel_rate": Decimal("1.85"),
            "overhead_rate": Decimal("0.25")
        },
        business_entity_id=uuid4()
    )


@pytest.fixture
def sample_cost_breakdown():
    """Create sample cost breakdown."""
    return CostBreakdown(
        route_id=uuid4(),
        fuel_costs={"DE": Decimal("250.00"), "PL": Decimal("200.00")},
        toll_costs={"DE": Decimal("150.00"), "PL": Decimal("100.00")},
        driver_costs=Decimal("500.00"),
        overhead_costs=Decimal("200.00"),
        timeline_event_costs={"REST": Decimal("50.00")},
        total_cost=Decimal("1450.00")
    )


@pytest.fixture
def sample_offer(sample_cost_breakdown):
    """Create sample offer."""
    return Offer(
        id=uuid4(),
        route_id=uuid4(),
        cost_breakdown_id=uuid4(),
        margin_percentage=Decimal("15.00"),
        final_price=Decimal("1667.50"),
        ai_content="AI-enhanced offer description",
        fun_fact="Interesting fact about the route",
        created_at=datetime.now()
    )


def test_cargo_creation(sample_cargo):
    """Test cargo creation."""
    assert isinstance(sample_cargo.id, UUID)
    assert sample_cargo.weight == 24000.0
    assert sample_cargo.value == Decimal("50000.00")
    assert len(sample_cargo.special_requirements) == 2
    assert "TEMPERATURE_CONTROLLED" in sample_cargo.special_requirements
    assert "FRAGILE" in sample_cargo.special_requirements


def test_cost_settings_creation(sample_cost_settings):
    """Test cost settings creation."""
    assert isinstance(sample_cost_settings.id, UUID)
    assert isinstance(sample_cost_settings.route_id, UUID)
    assert len(sample_cost_settings.enabled_components) == 4
    assert "FUEL" in sample_cost_settings.enabled_components
    assert sample_cost_settings.rates["fuel_rate"] == Decimal("1.85")
    assert isinstance(sample_cost_settings.business_entity_id, UUID)


def test_cost_breakdown_creation(sample_cost_breakdown):
    """Test cost breakdown creation."""
    assert isinstance(sample_cost_breakdown.route_id, UUID)
    assert len(sample_cost_breakdown.fuel_costs) == 2
    assert sample_cost_breakdown.fuel_costs["DE"] == Decimal("250.00")
    assert sample_cost_breakdown.driver_costs == Decimal("500.00")
    assert sample_cost_breakdown.total_cost == Decimal("1450.00")


def test_offer_creation(sample_offer):
    """Test offer creation."""
    assert isinstance(sample_offer.id, UUID)
    assert isinstance(sample_offer.route_id, UUID)
    assert isinstance(sample_offer.cost_breakdown_id, UUID)
    assert sample_offer.margin_percentage == Decimal("15.00")
    assert sample_offer.final_price == Decimal("1667.50")
    assert sample_offer.ai_content is not None
    assert sample_offer.fun_fact is not None
    assert isinstance(sample_offer.created_at, datetime)


def test_cargo_validation():
    """Test cargo validation."""
    with pytest.raises((TypeError, ValueError)):  # dataclass validation can raise either
        Cargo(
            id="invalid",  # Should be UUID
            weight="invalid",  # Should be float
            value="invalid",  # Should be Decimal
            special_requirements="invalid"  # Should be list
        )


def test_cost_settings_validation():
    """Test cost settings validation."""
    with pytest.raises((TypeError, ValueError)):  # dataclass validation can raise either
        CostSettings(
            id="invalid",  # Should be UUID
            route_id="invalid",  # Should be UUID
            enabled_components="invalid",  # Should be list
            rates="invalid",  # Should be dict
            business_entity_id="invalid"  # Should be UUID
        )


def test_cost_breakdown_validation():
    """Test cost breakdown validation."""
    with pytest.raises((TypeError, ValueError)):  # dataclass validation can raise either
        CostBreakdown(
            route_id="invalid",  # Should be UUID
            fuel_costs="invalid",  # Should be dict
            toll_costs="invalid",  # Should be dict
            driver_costs="invalid",  # Should be Decimal
            overhead_costs="invalid",  # Should be Decimal
            timeline_event_costs="invalid",  # Should be dict
            total_cost="invalid"  # Should be Decimal
        )


def test_offer_validation():
    """Test offer validation."""
    with pytest.raises((TypeError, ValueError)):  # dataclass validation can raise either
        Offer(
            id="invalid",  # Should be UUID
            route_id="invalid",  # Should be UUID
            cost_breakdown_id="invalid",  # Should be UUID
            margin_percentage="invalid",  # Should be Decimal
            final_price="invalid",  # Should be Decimal
            ai_content=123,  # Should be string or None
            fun_fact=123,  # Should be string or None
            created_at="invalid"  # Should be datetime
        ) 