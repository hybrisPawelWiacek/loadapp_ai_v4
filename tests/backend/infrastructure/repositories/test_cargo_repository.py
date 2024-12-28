"""Tests for cargo and cost-related repository implementations."""
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID
import pytest

from backend.domain.entities.cargo import (
    Cargo, CostSettings, CostBreakdown, Offer
)
from backend.infrastructure.repositories.cargo_repository import (
    SQLCargoRepository, SQLCostSettingsRepository,
    SQLCostBreakdownRepository, SQLOfferRepository
)


@pytest.fixture
def cargo_entity():
    """Create a sample cargo entity for testing."""
    return Cargo(
        id=UUID("12345678-1234-5678-1234-567812345678"),
        weight=1500.5,
        value=Decimal("25000.00"),
        special_requirements=["Temperature Control", "Fragile"]
    )


@pytest.fixture
def cost_settings_entity():
    """Create a sample cost settings entity for testing."""
    return CostSettings(
        id=UUID("22345678-1234-5678-1234-567812345678"),
        route_id=UUID("32345678-1234-5678-1234-567812345678"),
        business_entity_id=UUID("42345678-1234-5678-1234-567812345678"),
        enabled_components=["fuel", "toll", "driver"],
        rates={
            "fuel": Decimal("1.85"),
            "toll": Decimal("0.25"),
            "driver": Decimal("45.00")
        }
    )


@pytest.fixture
def cost_breakdown_entity():
    """Create a sample cost breakdown entity for testing."""
    return CostBreakdown(
        route_id=UUID("32345678-1234-5678-1234-567812345678"),
        fuel_costs={"DE": Decimal("150.50"), "PL": Decimal("120.75")},
        toll_costs={"DE": Decimal("45.00"), "PL": Decimal("30.00")},
        driver_costs=Decimal("450.00"),
        overhead_costs=Decimal("200.00"),
        timeline_event_costs={
            "loading": Decimal("50.00"),
            "unloading": Decimal("50.00")
        },
        total_cost=Decimal("1096.25")
    )


@pytest.fixture
def offer_entity():
    """Create a sample offer entity for testing."""
    return Offer(
        id=UUID("52345678-1234-5678-1234-567812345678"),
        route_id=UUID("32345678-1234-5678-1234-567812345678"),
        cost_breakdown_id=UUID("62345678-1234-5678-1234-567812345678"),
        margin_percentage=Decimal("15.00"),
        final_price=Decimal("1260.69"),
        ai_content="Efficient transport solution with temperature control.",
        fun_fact="This route crosses the historic Via Regia trade route.",
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc)
    )


class TestSQLCargoRepository:
    """Test cases for SQLCargoRepository."""

    def test_save_cargo(self, db, cargo_entity):
        """Test saving a cargo entity."""
        repo = SQLCargoRepository(db)
        saved_cargo = repo.save(cargo_entity)

        assert saved_cargo.id == cargo_entity.id
        assert saved_cargo.weight == cargo_entity.weight
        assert saved_cargo.value == cargo_entity.value
        assert saved_cargo.special_requirements == cargo_entity.special_requirements

    def test_find_cargo_by_id(self, db, cargo_entity):
        """Test finding a cargo entity by ID."""
        repo = SQLCargoRepository(db)
        saved_cargo = repo.save(cargo_entity)
        found_cargo = repo.find_by_id(saved_cargo.id)

        assert found_cargo is not None
        assert found_cargo.id == cargo_entity.id
        assert found_cargo.weight == cargo_entity.weight
        assert found_cargo.value == cargo_entity.value
        assert found_cargo.special_requirements == cargo_entity.special_requirements

    def test_find_nonexistent_cargo(self, db):
        """Test finding a nonexistent cargo entity."""
        repo = SQLCargoRepository(db)
        found_cargo = repo.find_by_id(UUID("00000000-0000-0000-0000-000000000000"))
        assert found_cargo is None


class TestSQLCostSettingsRepository:
    """Test cases for SQLCostSettingsRepository."""

    def test_save_cost_settings(self, db, cost_settings_entity):
        """Test saving cost settings."""
        repo = SQLCostSettingsRepository(db)
        saved_settings = repo.save(cost_settings_entity)

        assert saved_settings.id == cost_settings_entity.id
        assert saved_settings.route_id == cost_settings_entity.route_id
        assert saved_settings.business_entity_id == cost_settings_entity.business_entity_id
        assert saved_settings.enabled_components == cost_settings_entity.enabled_components
        assert saved_settings.rates == cost_settings_entity.rates

    def test_find_cost_settings_by_route_id(self, db, cost_settings_entity):
        """Test finding cost settings by route ID."""
        repo = SQLCostSettingsRepository(db)
        saved_settings = repo.save(cost_settings_entity)
        found_settings = repo.find_by_route_id(saved_settings.route_id)

        assert found_settings is not None
        assert found_settings.id == cost_settings_entity.id
        assert found_settings.route_id == cost_settings_entity.route_id
        assert found_settings.enabled_components == cost_settings_entity.enabled_components
        assert found_settings.rates == cost_settings_entity.rates

    def test_find_nonexistent_cost_settings(self, db):
        """Test finding nonexistent cost settings."""
        repo = SQLCostSettingsRepository(db)
        found_settings = repo.find_by_route_id(UUID("00000000-0000-0000-0000-000000000000"))
        assert found_settings is None


class TestSQLCostBreakdownRepository:
    """Test cases for SQLCostBreakdownRepository."""

    def test_save_cost_breakdown(self, db, cost_breakdown_entity):
        """Test saving a cost breakdown."""
        repo = SQLCostBreakdownRepository(db)
        saved_breakdown = repo.save(cost_breakdown_entity)

        assert saved_breakdown.route_id == cost_breakdown_entity.route_id
        assert saved_breakdown.fuel_costs == cost_breakdown_entity.fuel_costs
        assert saved_breakdown.toll_costs == cost_breakdown_entity.toll_costs
        assert saved_breakdown.driver_costs == cost_breakdown_entity.driver_costs
        assert saved_breakdown.overhead_costs == cost_breakdown_entity.overhead_costs
        assert saved_breakdown.timeline_event_costs == cost_breakdown_entity.timeline_event_costs
        assert saved_breakdown.total_cost == cost_breakdown_entity.total_cost

    def test_find_cost_breakdown_by_route_id(self, db, cost_breakdown_entity):
        """Test finding a cost breakdown by route ID."""
        repo = SQLCostBreakdownRepository(db)
        saved_breakdown = repo.save(cost_breakdown_entity)
        found_breakdown = repo.find_by_route_id(saved_breakdown.route_id)

        assert found_breakdown is not None
        assert found_breakdown.route_id == cost_breakdown_entity.route_id
        assert found_breakdown.fuel_costs == cost_breakdown_entity.fuel_costs
        assert found_breakdown.toll_costs == cost_breakdown_entity.toll_costs
        assert found_breakdown.driver_costs == cost_breakdown_entity.driver_costs
        assert found_breakdown.overhead_costs == cost_breakdown_entity.overhead_costs
        assert found_breakdown.total_cost == cost_breakdown_entity.total_cost

    def test_find_nonexistent_cost_breakdown(self, db):
        """Test finding a nonexistent cost breakdown."""
        repo = SQLCostBreakdownRepository(db)
        found_breakdown = repo.find_by_route_id(UUID("00000000-0000-0000-0000-000000000000"))
        assert found_breakdown is None


class TestSQLOfferRepository:
    """Test cases for SQLOfferRepository."""

    def test_save_offer(self, db, offer_entity):
        """Test saving an offer."""
        repo = SQLOfferRepository(db)
        saved_offer = repo.save(offer_entity)

        assert saved_offer.id == offer_entity.id
        assert saved_offer.route_id == offer_entity.route_id
        assert saved_offer.cost_breakdown_id == offer_entity.cost_breakdown_id
        assert saved_offer.margin_percentage == offer_entity.margin_percentage
        assert saved_offer.final_price == offer_entity.final_price
        assert saved_offer.ai_content == offer_entity.ai_content
        assert saved_offer.fun_fact == offer_entity.fun_fact
        # Compare timestamps in UTC, ignoring timezone info
        assert saved_offer.created_at.astimezone(timezone.utc).replace(tzinfo=None) == \
               offer_entity.created_at.astimezone(timezone.utc).replace(tzinfo=None)

    def test_find_offer_by_id(self, db, offer_entity):
        """Test finding an offer by ID."""
        repo = SQLOfferRepository(db)
        saved_offer = repo.save(offer_entity)
        found_offer = repo.find_by_id(saved_offer.id)

        assert found_offer is not None
        assert found_offer.id == offer_entity.id
        assert found_offer.route_id == offer_entity.route_id
        assert found_offer.cost_breakdown_id == offer_entity.cost_breakdown_id
        assert found_offer.margin_percentage == offer_entity.margin_percentage
        assert found_offer.final_price == offer_entity.final_price
        assert found_offer.ai_content == offer_entity.ai_content
        assert found_offer.fun_fact == offer_entity.fun_fact
        # Compare timestamps in UTC, ignoring timezone info
        assert found_offer.created_at.astimezone(timezone.utc).replace(tzinfo=None) == \
               offer_entity.created_at.astimezone(timezone.utc).replace(tzinfo=None)

    def test_find_nonexistent_offer(self, db):
        """Test finding a nonexistent offer."""
        repo = SQLOfferRepository(db)
        found_offer = repo.find_by_id(UUID("00000000-0000-0000-0000-000000000000"))
        assert found_offer is None 