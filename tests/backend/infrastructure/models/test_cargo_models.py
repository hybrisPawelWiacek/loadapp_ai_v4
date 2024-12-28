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


@pytest.fixture
def cargo_data():
    """Fixture for cargo test data."""
    return {
        "id": str(uuid4()),
        "weight": 24500.5,
        "value": "45000.00",
        "special_requirements": json.dumps(["TEMPERATURE_CONTROLLED", "HAZMAT"])
    }


@pytest.fixture
def cost_settings_data():
    """Fixture for cost settings test data."""
    return {
        "id": str(uuid4()),
        "route_id": str(uuid4()),
        "business_entity_id": str(uuid4()),
        "enabled_components": json.dumps(["FUEL", "TOLL", "DRIVER", "OVERHEAD"]),
        "rates": json.dumps({
            "fuel_rate": "1.85",
            "driver_rate": "35.00",
            "overhead_rate": "0.15"
        })
    }


@pytest.fixture
def cost_breakdown_data():
    """Fixture for cost breakdown test data."""
    return {
        "id": str(uuid4()),
        "route_id": str(uuid4()),
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
def offer_data(cost_breakdown_data):
    """Fixture for offer test data."""
    return {
        "id": str(uuid4()),
        "route_id": cost_breakdown_data["route_id"],
        "cost_breakdown_id": cost_breakdown_data["id"],
        "margin_percentage": "15.00",
        "final_price": "1592.75",
        "ai_content": "AI-generated offer description",
        "fun_fact": "Interesting fact about the route",
        "created_at": datetime.now(timezone.utc)
    }


def test_cargo_model_creation(db_session, cargo_data):
    """Test creating a cargo model."""
    cargo = CargoModel(**cargo_data)
    db_session.add(cargo)
    db_session.commit()

    saved_cargo = db_session.query(CargoModel).filter_by(id=cargo_data["id"]).first()
    assert saved_cargo is not None
    assert saved_cargo.weight == cargo_data["weight"]
    assert saved_cargo.value == cargo_data["value"]
    assert saved_cargo.special_requirements == cargo_data["special_requirements"]


def test_cargo_special_requirements_methods(db_session, cargo_data):
    """Test cargo special requirements getter/setter methods."""
    cargo = CargoModel(**cargo_data)
    
    # Test get_special_requirements
    requirements = cargo.get_special_requirements()
    assert isinstance(requirements, list)
    assert "TEMPERATURE_CONTROLLED" in requirements
    assert "HAZMAT" in requirements

    # Test set_special_requirements
    new_requirements = ["TEMPERATURE_CONTROLLED", "HAZMAT", "OVERSIZED"]
    cargo.set_special_requirements(new_requirements)
    assert json.loads(cargo.special_requirements) == new_requirements


def test_cost_settings_model_creation(db_session, cost_settings_data):
    """Test creating a cost settings model."""
    cost_settings = CostSettingsModel(**cost_settings_data)
    db_session.add(cost_settings)
    db_session.commit()

    saved_settings = db_session.query(CostSettingsModel).filter_by(id=cost_settings_data["id"]).first()
    assert saved_settings is not None
    assert saved_settings.route_id == cost_settings_data["route_id"]
    assert saved_settings.business_entity_id == cost_settings_data["business_entity_id"]
    assert saved_settings.enabled_components == cost_settings_data["enabled_components"]
    assert saved_settings.rates == cost_settings_data["rates"]


def test_cost_settings_json_methods(db_session, cost_settings_data):
    """Test cost settings JSON getter/setter methods."""
    settings = CostSettingsModel(**cost_settings_data)
    
    # Test get_enabled_components
    components = settings.get_enabled_components()
    assert isinstance(components, list)
    assert "FUEL" in components
    assert "TOLL" in components

    # Test set_enabled_components
    new_components = ["FUEL", "TOLL", "DRIVER"]
    settings.set_enabled_components(new_components)
    assert json.loads(settings.enabled_components) == new_components

    # Test get_rates
    rates = settings.get_rates()
    assert isinstance(rates, dict)
    assert rates["fuel_rate"] == "1.85"
    assert rates["driver_rate"] == "35.00"

    # Test set_rates
    new_rates = {
        "fuel_rate": "1.95",
        "driver_rate": "37.50",
        "overhead_rate": "0.18"
    }
    settings.set_rates(new_rates)
    assert json.loads(settings.rates) == new_rates


def test_cost_breakdown_model_creation(db_session, cost_breakdown_data):
    """Test creating a cost breakdown model."""
    breakdown = CostBreakdownModel(**cost_breakdown_data)
    db_session.add(breakdown)
    db_session.commit()

    saved_breakdown = db_session.query(CostBreakdownModel).filter_by(id=cost_breakdown_data["id"]).first()
    assert saved_breakdown is not None
    assert saved_breakdown.route_id == cost_breakdown_data["route_id"]
    assert saved_breakdown.fuel_costs == cost_breakdown_data["fuel_costs"]
    assert saved_breakdown.toll_costs == cost_breakdown_data["toll_costs"]
    assert saved_breakdown.driver_costs == cost_breakdown_data["driver_costs"]
    assert saved_breakdown.overhead_costs == cost_breakdown_data["overhead_costs"]
    assert saved_breakdown.timeline_event_costs == cost_breakdown_data["timeline_event_costs"]
    assert saved_breakdown.total_cost == cost_breakdown_data["total_cost"]


def test_cost_breakdown_json_methods(db_session, cost_breakdown_data):
    """Test cost breakdown JSON getter/setter methods."""
    breakdown = CostBreakdownModel(**cost_breakdown_data)
    
    # Test get_fuel_costs
    fuel_costs = breakdown.get_fuel_costs()
    assert isinstance(fuel_costs, dict)
    assert fuel_costs["DE"] == "250.00"
    assert fuel_costs["PL"] == "180.00"

    # Test set_fuel_costs
    new_fuel_costs = {"DE": "275.00", "PL": "195.00"}
    breakdown.set_fuel_costs(new_fuel_costs)
    assert json.loads(breakdown.fuel_costs) == new_fuel_costs

    # Test get_toll_costs
    toll_costs = breakdown.get_toll_costs()
    assert isinstance(toll_costs, dict)
    assert toll_costs["DE"] == "120.00"
    assert toll_costs["PL"] == "85.00"

    # Test set_toll_costs
    new_toll_costs = {"DE": "130.00", "PL": "90.00"}
    breakdown.set_toll_costs(new_toll_costs)
    assert json.loads(breakdown.toll_costs) == new_toll_costs

    # Test get_timeline_event_costs
    event_costs = breakdown.get_timeline_event_costs()
    assert isinstance(event_costs, dict)
    assert event_costs["loading"] == "50.00"
    assert event_costs["unloading"] == "50.00"

    # Test set_timeline_event_costs
    new_event_costs = {
        "loading": "55.00",
        "unloading": "55.00",
        "rest_stop": "30.00"
    }
    breakdown.set_timeline_event_costs(new_event_costs)
    assert json.loads(breakdown.timeline_event_costs) == new_event_costs


def test_offer_model_creation(db_session, offer_data, cost_breakdown_data):
    """Test creating an offer model with relationships."""
    # Create cost breakdown first
    breakdown = CostBreakdownModel(**cost_breakdown_data)
    db_session.add(breakdown)
    db_session.commit()

    # Create offer
    offer = OfferModel(**offer_data)
    db_session.add(offer)
    db_session.commit()

    saved_offer = db_session.query(OfferModel).filter_by(id=offer_data["id"]).first()
    assert saved_offer is not None
    assert saved_offer.route_id == offer_data["route_id"]
    assert saved_offer.cost_breakdown_id == offer_data["cost_breakdown_id"]
    assert saved_offer.margin_percentage == offer_data["margin_percentage"]
    assert saved_offer.final_price == offer_data["final_price"]
    assert saved_offer.ai_content == offer_data["ai_content"]
    assert saved_offer.fun_fact == offer_data["fun_fact"]
    assert saved_offer.created_at is not None


def test_offer_relationships(db_session, offer_data, cost_breakdown_data):
    """Test offer relationships."""
    # Create cost breakdown first
    breakdown = CostBreakdownModel(**cost_breakdown_data)
    db_session.add(breakdown)
    db_session.commit()

    # Create offer
    offer = OfferModel(**offer_data)
    db_session.add(offer)
    db_session.commit()

    # Test relationship
    saved_offer = db_session.query(OfferModel).filter_by(id=offer_data["id"]).first()
    assert saved_offer.cost_breakdown is not None
    assert saved_offer.cost_breakdown.id == cost_breakdown_data["id"]
    assert saved_offer.cost_breakdown.total_cost == cost_breakdown_data["total_cost"]


def test_model_required_fields(db_session):
    """Test that required fields raise IntegrityError when missing."""
    # Enable foreign key constraints
    db_session.execute(text("PRAGMA foreign_keys=ON"))
    
    # Test CargoModel required fields
    with pytest.raises(IntegrityError):
        cargo = CargoModel(id=str(uuid4()))  # Missing required fields
        db_session.add(cargo)
        db_session.commit()

    db_session.rollback()

    # Test CostSettingsModel required fields
    with pytest.raises(IntegrityError):
        settings = CostSettingsModel(id=str(uuid4()))  # Missing required fields
        db_session.add(settings)
        db_session.commit()

    db_session.rollback()

    # Test CostBreakdownModel required fields
    with pytest.raises(IntegrityError):
        breakdown = CostBreakdownModel(id=str(uuid4()))  # Missing required fields
        db_session.add(breakdown)
        db_session.commit()

    db_session.rollback()

    # Test OfferModel required fields
    with pytest.raises(IntegrityError):
        offer = OfferModel(id=str(uuid4()))  # Missing required fields
        db_session.add(offer)
        db_session.commit() 