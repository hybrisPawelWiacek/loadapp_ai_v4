"""Tests for cargo-related SQLAlchemy models."""
import json
from decimal import Decimal
from uuid import uuid4
from datetime import datetime, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from backend.infrastructure.models.cargo_models import (
    CargoModel,
    CostSettingsModel,
    CostBreakdownModel,
    OfferModel
)
from backend.infrastructure.models.route_models import (
    RouteModel,
    LocationModel,
    EmptyDrivingModel
)
from backend.infrastructure.models.business_models import BusinessEntityModel
from backend.infrastructure.models.transport_models import (
    TransportModel,
    TransportTypeModel,
    TruckSpecificationModel,
    DriverSpecificationModel
)


@pytest.fixture
def complete_test_data(db):
    """Create a complete set of test data with all required entities."""
    # Create business entity
    business = BusinessEntityModel(
        id=str(uuid4()),
        name="Test Business",
        address="123 Test St",
        contact_info={"email": "test@example.com"},
        business_type="CARRIER",
        certifications=[],
        operating_countries=[],
        cost_overheads={}
    )
    db.add(business)
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
        latitude="52.229676",
        longitude="21.012229",
        address="Warsaw, Poland"
    )
    db.add_all([origin, destination])
    db.flush()

    # Create truck and driver specifications
    truck_spec = TruckSpecificationModel(
        id=str(uuid4()),
        fuel_consumption_empty=22.5,
        fuel_consumption_loaded=29.0,
        toll_class="4_axle",
        euro_class="EURO_6",
        co2_class="A",
        maintenance_rate_per_km="0.15"
    )
    driver_spec = DriverSpecificationModel(
        id=str(uuid4()),
        daily_rate="138.0",
        driving_time_rate="25.00",
        required_license_type="CE",
        required_certifications=json.dumps(["ADR"])
    )
    db.add_all([truck_spec, driver_spec])
    db.flush()

    # Create transport type
    transport_type = TransportTypeModel(
        id="flatbed",
        name="Flatbed Truck",
        truck_specifications_id=truck_spec.id,
        driver_specifications_id=driver_spec.id
    )
    db.add(transport_type)
    db.flush()

    # Create transport
    transport = TransportModel(
        id=str(uuid4()),
        transport_type_id=transport_type.id,
        business_entity_id=business.id,
        truck_specifications_id=truck_spec.id,
        driver_specifications_id=driver_spec.id,
        is_active=True
    )
    db.add(transport)
    db.flush()

    # Create cargo
    cargo = CargoModel(
        id=str(uuid4()),
        business_entity_id=business.id,
        weight=1000.0,
        volume=2.5,
        cargo_type="GENERAL",
        value="5000.00",
        special_requirements=json.dumps(["TAIL_LIFT"]),
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

    # Create route
    route = RouteModel(
        id=str(uuid4()),
        transport_id=transport.id,
        business_entity_id=business.id,
        cargo_id=cargo.id,
        origin_id=origin.id,
        destination_id=destination.id,
        pickup_time=datetime.now(timezone.utc),
        delivery_time=datetime.now(timezone.utc).replace(hour=(datetime.now().hour + 8) % 24),
        empty_driving_id=empty_driving.id,
        total_distance_km=550.5,
        total_duration_hours=8.5,
        is_feasible=True,
        status="draft"
    )
    db.add(route)
    db.flush()

    # Create cost settings
    cost_settings = CostSettingsModel(
        id=str(uuid4()),
        route_id=route.id,
        business_entity_id=business.id,
        enabled_components=json.dumps(["FUEL", "TOLL", "DRIVER", "OVERHEAD"]),
        rates=json.dumps({
            "fuel_rate": "1.85",
            "driver_rate": "35.00",
            "overhead_rate": "0.15"
        })
    )
    db.add(cost_settings)
    db.flush()

    # Create cost breakdown
    cost_breakdown = CostBreakdownModel(
        id=str(uuid4()),
        route_id=route.id,
        fuel_costs=json.dumps({"DE": "250.00", "PL": "180.00"}),
        toll_costs=json.dumps({"DE": "120.00", "PL": "85.00"}),
        driver_costs="450.00",
        overhead_costs="175.00",
        timeline_event_costs=json.dumps({
            "loading": "50.00",
            "unloading": "50.00",
            "rest_stop": "25.00"
        }),
        total_cost="1385.00"
    )
    db.add(cost_breakdown)
    db.flush()

    # Create offer
    offer = OfferModel(
        id=str(uuid4()),
        route_id=route.id,
        cost_breakdown_id=cost_breakdown.id,
        margin_percentage="15.00",
        final_price="1592.75",
        ai_content="AI-generated offer description",
        fun_fact="Interesting fact about the route",
        created_at=datetime.now(timezone.utc)
    )
    db.add(offer)
    db.flush()

    db.commit()

    return {
        "business": business,
        "origin": origin,
        "destination": destination,
        "truck_spec": truck_spec,
        "driver_spec": driver_spec,
        "transport_type": transport_type,
        "transport": transport,
        "cargo": cargo,
        "empty_driving": empty_driving,
        "route": route,
        "cost_settings": cost_settings,
        "cost_breakdown": cost_breakdown,
        "offer": offer
    }


@pytest.fixture
def cargo_data(complete_test_data):
    """Fixture for cargo test data."""
    return {
        "id": str(uuid4()),
        "business_entity_id": complete_test_data["business"].id,
        "weight": 24500.5,
        "volume": 10.0,
        "cargo_type": "GENERAL",
        "value": "45000.00",
        "special_requirements": json.dumps(["TEMPERATURE_CONTROLLED", "HAZMAT"]),
        "status": "pending"
    }


@pytest.fixture
def cost_settings_data(complete_test_data):
    """Fixture for cost settings test data."""
    return {
        "id": str(uuid4()),
        "route_id": complete_test_data["route"].id,
        "business_entity_id": complete_test_data["business"].id,
        "enabled_components": json.dumps(["FUEL", "TOLL", "DRIVER", "OVERHEAD"]),
        "rates": json.dumps({
            "fuel_rate": "1.85",
            "driver_rate": "35.00",
            "overhead_rate": "0.15"
        })
    }


@pytest.fixture
def cost_breakdown_data(complete_test_data):
    """Fixture for cost breakdown test data."""
    return {
        "id": str(uuid4()),
        "route_id": complete_test_data["route"].id,
        "fuel_costs": json.dumps({"DE": "250.00", "PL": "180.00"}),
        "toll_costs": json.dumps({"DE": "120.00", "PL": "85.00"}),
        "driver_costs": "450.00",
        "overhead_costs": "175.00",
        "timeline_event_costs": json.dumps({
            "loading": "50.00",
            "unloading": "50.00",
            "rest_stop": "25.00"
        }),
        "total_cost": "1385.00"
    }


@pytest.fixture
def offer_data(complete_test_data):
    """Fixture for offer test data."""
    return {
        "id": str(uuid4()),
        "route_id": complete_test_data["route"].id,
        "cost_breakdown_id": complete_test_data["cost_breakdown"].id,
        "margin_percentage": "15.00",
        "final_price": "1592.75",
        "ai_content": "AI-generated offer description",
        "fun_fact": "Interesting fact about the route",
        "created_at": datetime.now(timezone.utc)
    }


def test_cargo_model_creation(db, cargo_data):
    """Test creating a cargo model."""
    cargo = CargoModel(**cargo_data)
    db.add(cargo)
    db.commit()

    saved_cargo = db.query(CargoModel).filter_by(id=cargo_data["id"]).first()
    assert saved_cargo is not None
    assert saved_cargo.weight == cargo_data["weight"]
    assert saved_cargo.value == cargo_data["value"]
    assert saved_cargo.special_requirements == cargo_data["special_requirements"]


def test_cargo_special_requirements_methods(db, cargo_data):
    """Test JSON getter/setter methods for special requirements."""
    cargo = CargoModel(**cargo_data)
    db.add(cargo)
    db.commit()

    # Test get method
    requirements = cargo.get_special_requirements()
    assert isinstance(requirements, list)
    assert "TEMPERATURE_CONTROLLED" in requirements
    assert "HAZMAT" in requirements

    # Test set method
    new_requirements = ["FRAGILE", "OVERSIZED"]
    cargo.set_special_requirements(new_requirements)
    db.commit()

    assert cargo.get_special_requirements() == new_requirements


def test_cost_settings_model_creation(db, cost_settings_data):
    """Test creating a cost settings model."""
    settings = CostSettingsModel(**cost_settings_data)
    db.add(settings)
    db.commit()

    saved_settings = db.query(CostSettingsModel).filter_by(id=cost_settings_data["id"]).first()
    assert saved_settings is not None
    assert saved_settings.route_id == cost_settings_data["route_id"]
    assert saved_settings.business_entity_id == cost_settings_data["business_entity_id"]
    assert saved_settings.enabled_components == cost_settings_data["enabled_components"]
    assert saved_settings.rates == cost_settings_data["rates"]


def test_cost_settings_json_methods(db, cost_settings_data):
    """Test JSON getter/setter methods for cost settings."""
    settings = CostSettingsModel(**cost_settings_data)
    db.add(settings)
    db.commit()

    # Test get methods
    assert settings.get_enabled_components() == ["FUEL", "TOLL", "DRIVER", "OVERHEAD"]
    assert settings.get_rates() == {
        "fuel_rate": "1.85",
        "driver_rate": "35.00",
        "overhead_rate": "0.15"
    }

    # Test set methods
    new_components = ["FUEL", "TOLL", "DRIVER"]
    new_rates = {
        "fuel_rate": "1.95",
        "driver_rate": "40.00"
    }

    settings.set_enabled_components(new_components)
    settings.set_rates(new_rates)
    db.commit()

    assert settings.get_enabled_components() == new_components
    assert settings.get_rates() == new_rates


def test_cost_breakdown_model_creation(db, cost_breakdown_data):
    """Test creating a cost breakdown model."""
    breakdown = CostBreakdownModel(**cost_breakdown_data)
    db.add(breakdown)
    db.commit()

    saved_breakdown = db.query(CostBreakdownModel).filter_by(id=cost_breakdown_data["id"]).first()
    assert saved_breakdown is not None
    assert saved_breakdown.route_id == cost_breakdown_data["route_id"]
    assert saved_breakdown.fuel_costs == cost_breakdown_data["fuel_costs"]
    assert saved_breakdown.toll_costs == cost_breakdown_data["toll_costs"]
    assert saved_breakdown.get_driver_costs() == {
        "base_cost": "0",
        "regular_hours_cost": "450.00",
        "overtime_cost": "0",
        "total_cost": "450.00"
    }
    assert saved_breakdown.overhead_costs == cost_breakdown_data["overhead_costs"]
    assert saved_breakdown.timeline_event_costs == cost_breakdown_data["timeline_event_costs"]
    assert saved_breakdown.total_cost == cost_breakdown_data["total_cost"]


def test_cost_breakdown_json_methods(db, cost_breakdown_data):
    """Test JSON getter/setter methods for cost breakdown."""
    breakdown = CostBreakdownModel(**cost_breakdown_data)
    db.add(breakdown)
    db.commit()

    # Test get methods
    assert breakdown.get_fuel_costs() == {"DE": "250.00", "PL": "180.00"}
    assert breakdown.get_toll_costs() == {"DE": "120.00", "PL": "85.00"}
    assert breakdown.get_timeline_event_costs() == {
        "loading": "50.00",
        "unloading": "50.00",
        "rest_stop": "25.00"
    }

    # Test set methods
    new_fuel = {"DE": "300.00", "PL": "200.00"}
    new_toll = {"DE": "150.00", "PL": "100.00"}
    new_events = {
        "loading": "60.00",
        "unloading": "60.00",
        "rest_stop": "30.00"
    }

    breakdown.set_fuel_costs(new_fuel)
    breakdown.set_toll_costs(new_toll)
    breakdown.set_timeline_event_costs(new_events)
    db.commit()

    assert breakdown.get_fuel_costs() == new_fuel
    assert breakdown.get_toll_costs() == new_toll
    assert breakdown.get_timeline_event_costs() == new_events


def test_offer_model_creation(db, offer_data, cost_breakdown_data):
    """Test creating an offer model."""
    # First create the cost breakdown
    breakdown = CostBreakdownModel(**cost_breakdown_data)
    db.add(breakdown)
    db.commit()

    # Then create the offer
    offer = OfferModel(**offer_data)
    db.add(offer)
    db.commit()

    saved_offer = db.query(OfferModel).filter_by(id=offer_data["id"]).first()
    assert saved_offer is not None
    assert saved_offer.route_id == offer_data["route_id"]
    assert saved_offer.cost_breakdown_id == offer_data["cost_breakdown_id"]


def test_offer_relationships(db, offer_data, complete_test_data):
    """Test offer relationships."""
    # Create the offer using the existing cost breakdown from complete test data
    offer = OfferModel(**offer_data)
    db.add(offer)
    db.commit()

    # Test relationship with cost breakdown
    saved_offer = db.query(OfferModel).filter_by(id=offer_data["id"]).first()
    assert saved_offer.cost_breakdown is not None
    assert saved_offer.cost_breakdown.id == complete_test_data["cost_breakdown"].id


def test_model_required_fields(db):
    """Test that required fields raise ValueError when missing."""
    # Test missing weight
    try:
        cargo = CargoModel(
            id=str(uuid4()),
            value="1000.00",  # Include value since it's required
            special_requirements=json.dumps([])  # Include special_requirements since it's required
        )
        db.add(cargo)
        db.commit()
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "weight is required" in str(e)
        db.rollback()

    # Test missing value
    try:
        cargo = CargoModel(
            id=str(uuid4()),
            weight=1000.0,  # Include weight since it's required
            special_requirements=json.dumps([])  # Include special_requirements since it's required
        )
        db.add(cargo)
        db.commit()
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "value is required" in str(e)
        db.rollback()

    # Test missing special_requirements
    try:
        cargo = CargoModel(
            id=str(uuid4()),
            weight=1000.0,  # Include weight since it's required
            value="1000.00"  # Include value since it's required
        )
        db.add(cargo)
        db.commit()
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "special_requirements is required" in str(e)
        db.rollback() 