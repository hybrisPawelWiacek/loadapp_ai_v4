"""Tests for cargo and cost-related repository implementations."""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import UUID, uuid4
import json

import pytest

from backend.domain.entities.cargo import (
    Cargo, CostSettings, CostBreakdown, Offer
)
from backend.infrastructure.repositories.cargo_repository import (
    SQLCargoRepository, SQLCostSettingsRepository,
    SQLCostBreakdownRepository, SQLOfferRepository
)
from backend.infrastructure.models.business_models import BusinessEntityModel
from backend.infrastructure.models.route_models import (
    RouteModel, EmptyDrivingModel, LocationModel,
    TimelineEventModel, CountrySegmentModel
)
from backend.infrastructure.models.transport_models import (
    TruckSpecificationModel, DriverSpecificationModel,
    TransportTypeModel, TransportModel
)
from backend.infrastructure.models.cargo_models import CargoModel


@pytest.fixture
def business_entity_model(db):
    """Create a sample business entity model."""
    model = BusinessEntityModel(
        id="42345678-1234-5678-1234-567812345678",
        name="Test Transport Co",
        address="Test Address, Berlin",
        contact_info=json.dumps({
            "email": "test@example.com",
            "phone": "+49123456789"
        }),
        business_type="TRANSPORT_COMPANY",
        certifications=json.dumps(["ISO9001"]),
        operating_countries=json.dumps(["DE", "PL"]),
        cost_overheads=json.dumps({
            "admin": "100.00",
            "insurance": "150.00"
        })
    )
    db.add(model)
    db.commit()
    return model


@pytest.fixture
def route_model(db):
    """Create a test route for the offer."""
    from datetime import datetime, timezone
    from uuid import uuid4

    # Create business entity first
    business_entity = BusinessEntityModel(
        id=str(uuid4()),
        name="Test Transport Co",
        address="Test Address, Berlin",
        contact_info=json.dumps({
            "email": "test@example.com",
            "phone": "+49123456789"
        }),
        business_type="TRANSPORT_COMPANY",
        certifications=json.dumps(["ISO9001"]),
        operating_countries=json.dumps(["DE", "PL"]),
        cost_overheads=json.dumps({
            "admin": "100.00"
        })
    )
    db.add(business_entity)
    db.flush()

    # Create truck and driver specifications
    truck_spec = TruckSpecificationModel(
        id=str(uuid4()),
        fuel_consumption_empty=0.22,
        fuel_consumption_loaded=0.29,
        toll_class="euro6",
        euro_class="EURO6",
        co2_class="A",
        maintenance_rate_per_km="0.15"
    )
    db.add(truck_spec)

    driver_spec = DriverSpecificationModel(
        id=str(uuid4()),
        daily_rate="138.0",
        required_license_type="CE",
        required_certifications=json.dumps(["ADR"])
    )
    db.add(driver_spec)
    db.flush()

    # Create transport type
    transport_type = TransportTypeModel(
        id=str(uuid4()),
        name="Flatbed",
        truck_specifications_id=truck_spec.id,
        driver_specifications_id=driver_spec.id
    )
    db.add(transport_type)
    db.flush()

    # Create transport
    transport = TransportModel(
        id=str(uuid4()),
        transport_type_id=transport_type.id,
        business_entity_id=business_entity.id,
        truck_specifications_id=truck_spec.id,
        driver_specifications_id=driver_spec.id,
        is_active=True
    )
    db.add(transport)
    db.flush()

    # Create cargo
    cargo = CargoModel(
        id=str(uuid4()),
        business_entity_id=business_entity.id,
        weight=1500.0,
        volume=10.0,
        cargo_type="general",
        value="25000.00",
        special_requirements=json.dumps(["temperature_controlled"]),
        status="pending"
    )
    db.add(cargo)
    db.flush()

    # Create empty driving
    empty_driving = EmptyDrivingModel(
        id=str(uuid4()),
        distance_km=200.0,
        duration_hours=4.0
    )
    db.add(empty_driving)
    db.flush()

    # Create locations
    origin = LocationModel(
        id=str(uuid4()),
        latitude="52.520008",
        longitude="13.404954",
        address="Berlin, Germany"
    )
    destination = LocationModel(
        id=str(uuid4()),
        latitude="52.237049",
        longitude="21.017532",
        address="Warsaw, Poland"
    )
    db.add(origin)
    db.add(destination)
    db.flush()

    # Create route
    route = RouteModel(
        id="32345678-1234-5678-1234-567812345678",  # Match the ID used in offer
        transport_id=transport.id,
        business_entity_id=business_entity.id,
        cargo_id=cargo.id,
        origin_id=origin.id,
        destination_id=destination.id,
        pickup_time=datetime.now(timezone.utc),
        delivery_time=datetime.now(timezone.utc),
        empty_driving_id=empty_driving.id,
        total_distance_km=700.0,
        total_duration_hours=9.0,
        is_feasible=True,
        status="draft"
    )
    db.add(route)
    db.commit()
    return route


@pytest.fixture
def cargo_entity():
    """Create a sample cargo entity for testing."""
    return Cargo(
        id=UUID("12345678-1234-5678-1234-567812345678"),
        weight=1500.5,
        volume=10.0,
        value=Decimal("25000.00"),
        special_requirements=["Temperature Control", "Fragile"]
    )


@pytest.fixture
def cost_settings_entity(route_model, business_entity_model):
    """Create a sample cost settings entity for testing."""
    return CostSettings(
        id=UUID("22345678-1234-5678-1234-567812345678"),
        route_id=UUID(route_model.id),
        business_entity_id=UUID(business_entity_model.id),
        enabled_components=["fuel", "toll", "driver"],
        rates={
            "fuel": Decimal("1.85"),
            "toll": Decimal("0.25"),
            "driver": Decimal("45.00")
        }
    )


@pytest.fixture
def cost_breakdown_entity(route_model):
    """Create a sample cost breakdown entity for testing."""
    return CostBreakdown(
        id=UUID("72345678-1234-5678-1234-567812345678"),
        route_id=UUID(route_model.id),
        fuel_costs={"DE": Decimal("150.00"), "PL": Decimal("120.00")},
        toll_costs={"DE": Decimal("75.00"), "PL": Decimal("50.00")},
        driver_costs=Decimal("450.00"),
        overhead_costs=Decimal("100.00"),
        timeline_event_costs={"pickup": Decimal("50.00"), "delivery": Decimal("50.00")},
        total_cost=Decimal("1045.00")
    )


@pytest.fixture
def cost_breakdown_model(db, route_model):
    """Create a test cost breakdown for the offer."""
    from backend.infrastructure.models.cargo_models import CostBreakdownModel
    breakdown = CostBreakdownModel(
        id="62345678-1234-5678-1234-567812345678",  # Match the ID used in offer
        route_id=route_model.id,
        fuel_costs=json.dumps({"DE": "150.00", "PL": "120.00"}),
        toll_costs=json.dumps({"DE": "75.00", "PL": "50.00"}),
        driver_costs="450.00",
        overhead_costs="100.00",
        timeline_event_costs=json.dumps({"pickup": "50.00", "delivery": "50.00"}),
        total_cost="1045.00"
    )
    db.add(breakdown)
    db.commit()
    return breakdown


@pytest.fixture
def offer_entity(route_model, cost_breakdown_model):
    """Create a test offer entity with valid foreign keys."""
    return Offer(
        id=UUID("52345678-1234-5678-1234-567812345678"),
        route_id=UUID(route_model.id),
        cost_breakdown_id=UUID(cost_breakdown_model.id),
        margin_percentage=Decimal("15.00"),
        final_price=Decimal("1260.69"),
        ai_content="Efficient transport solution with temperature control.",
        fun_fact="This route crosses the historic Via Regia trade route.",
        created_at=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc),
        status="draft"
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
        # Compare timestamps by converting both to UTC and removing timezone info
        assert saved_offer.created_at.replace(tzinfo=None) == \
               offer_entity.created_at.replace(tzinfo=None)

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
        # Compare timestamps by converting both to UTC and removing timezone info
        assert found_offer.created_at.replace(tzinfo=None) == \
               offer_entity.created_at.replace(tzinfo=None)

    def test_find_nonexistent_offer(self, db):
        """Test finding a nonexistent offer."""
        repo = SQLOfferRepository(db)
        found_offer = repo.find_by_id(UUID("00000000-0000-0000-0000-000000000000"))
        assert found_offer is None 