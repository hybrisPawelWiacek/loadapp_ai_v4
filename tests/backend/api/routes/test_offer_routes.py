"""Tests for offer routes."""
import json
from decimal import Decimal
from uuid import uuid4, UUID
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, Mock
from flask import g
from contextlib import contextmanager
import logging
import time

from backend.domain.entities.cargo import CostBreakdown, Offer
from backend.infrastructure.models.route_models import RouteModel, LocationModel, EmptyDrivingModel
from backend.infrastructure.models.transport_models import (
    TransportModel, TransportTypeModel,
    TruckSpecificationModel, DriverSpecificationModel
)
from backend.infrastructure.models.cargo_models import CargoModel, CostBreakdownModel, OfferModel
from backend.infrastructure.models.business_models import BusinessEntityModel
from backend.infrastructure.container import Container


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


@pytest.fixture
def mock_openai_service():
    """Create a mock OpenAI service."""
    with patch("backend.infrastructure.external_services.openai_service.OpenAIService") as mock:
        mock_instance = Mock()
        mock_instance.generate_offer_content.return_value = "Enhanced offer description"
        mock_instance.generate_fun_fact.return_value = "Fun fact about transport"
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def test_container(test_config, mock_openai_service, db):
    """Create test container with mocked services."""
    container = Container(test_config.to_dict(), db)
    container._instances['openai_service'] = mock_openai_service
    
    # Initialize repositories
    container._instances['offer_repository'] = container.offer_repository()
    container._instances['cargo_repository'] = container.cargo_repository()
    container._instances['route_repository'] = container.route_repository()
    
    # Initialize adapters
    container._instances['openai_adapter'] = container.openai_adapter()
    
    # Initialize offer service with all dependencies and db session
    offer_service = container.offer_service()
    offer_service.db = db  # Add the database session
    container._instances['offer_service'] = offer_service
    
    return container


@pytest.fixture
def app(test_config, test_container, db):
    """Create Flask test app with container."""
    from backend.app import create_app
    app = create_app(test_config)
    
    # Override the database session and container for testing
    @app.before_request
    def before_request():
        g.db = db
        g.container = test_container
        # Ensure all objects are attached to the session
        db.expire_all()
    
    @app.teardown_appcontext
    def teardown_db(exception=None):
        db = g.pop('db', None)
        if db is not None:
            try:
                if exception:
                    db.rollback()
                else:
                    db.commit()
            except:
                db.rollback()
                raise
            finally:
                db.expire_all()
        # Clear container reference
        if hasattr(g, 'container'):
            delattr(g, 'container')
    
    return app


@pytest.fixture
def truck_specs(db):
    """Create sample truck specifications."""
    specs = TruckSpecificationModel(
        id=str(uuid4()),
        fuel_consumption_empty=0.22,
        fuel_consumption_loaded=0.29,
        toll_class="euro6",
        euro_class="EURO6",
        co2_class="A",
        maintenance_rate_per_km="0.15"
    )
    db.add(specs)
    db.commit()
    db.refresh(specs)
    return specs


@pytest.fixture
def driver_specs(db):
    """Create sample driver specifications."""
    specs = DriverSpecificationModel(
        id=str(uuid4()),
        daily_rate="138.0",
        driving_time_rate="25.00",
        required_license_type="CE",
        required_certifications=json.dumps(["ADR"])
    )
    db.add(specs)
    db.commit()
    db.refresh(specs)
    return specs


@pytest.fixture
def transport_type(db, truck_specs, driver_specs):
    """Create sample transport type."""
    transport_type = TransportTypeModel(
        id="flatbed",
        name="Flatbed",
        truck_specifications_id=truck_specs.id,
        driver_specifications_id=driver_specs.id
    )
    db.add(transport_type)
    db.commit()
    db.refresh(transport_type)
    return transport_type


@pytest.fixture
def sample_business(db):
    """Create a sample business entity."""
    business = BusinessEntityModel(
        id=str(uuid4()),
        name="Test Transport Co",
        address="Test Address",
        contact_info={"email": "test@example.com"},
        business_type="TRANSPORT",
        certifications=["ISO9001"],
        operating_countries=["DE", "PL"],
        cost_overheads={"admin": "100.00"}
    )
    db.add(business)
    db.commit()
    db.refresh(business)
    return business


@pytest.fixture
def sample_transport(db, sample_business, transport_type):
    """Create a sample transport."""
    transport = TransportModel(
        id=str(uuid4()),
        transport_type_id=transport_type.id,
        business_entity_id=sample_business.id,
        truck_specifications_id=transport_type.truck_specifications_id,
        driver_specifications_id=transport_type.driver_specifications_id,
        is_active=True
    )
    db.add(transport)
    db.commit()
    db.refresh(transport)
    return transport


@pytest.fixture
def sample_cargo(db, test_data):
    """Create a sample cargo."""
    cargo = CargoModel(
        id=str(uuid4()),
        business_entity_id=test_data["business_entity"].id,
        weight=1500.0,
        volume=10.0,
        cargo_type="general",
        value=str(Decimal("25000.00")),
        special_requirements=["temperature_controlled"],
        status="pending"
    )
    db.add(cargo)
    db.commit()
    db.refresh(cargo)
    logging.debug(f"Creating CargoModel with ID: {cargo.id}")
    logging.debug(f"Inserting CargoModel with ID: {cargo.id} into the database.")
    return cargo


@pytest.fixture
def sample_offer(db, route, sample_cargo):
    """Create a sample offer for testing."""
    # Create cost breakdown first
    cost_breakdown = CostBreakdownModel(
        id=str(uuid4()),
        route_id=route.id,
        fuel_costs={"DE": "100.00", "PL": "150.00"},
        toll_costs={"DE": "50.00", "PL": "75.00"},
        driver_costs={
            "base_cost": "100.00",
            "regular_hours_cost": "50.00",
            "overtime_cost": "50.00",
            "total_cost": "200.00"
        },
        overhead_costs="100.00",
        timeline_event_costs={"loading": "50.00", "unloading": "50.00"},
        total_cost="725.00"
    )
    db.add(cost_breakdown)
    db.commit()
    
    # Create offer
    offer = OfferModel(
        id=str(uuid4()),
        route_id=route.id,
        cost_breakdown_id=cost_breakdown.id,
        margin_percentage=str(Decimal("15.0")),
        final_price=str(Decimal("1500.00")),
        ai_content="Test offer description with AI-generated content",
        fun_fact="Fun fact about transport"
    )
    db.add(offer)
    db.commit()
    db.refresh(offer)
    logging.debug(f"Creating CostBreakdownModel with ID: {cost_breakdown.id}")
    logging.debug(f"Inserting CostBreakdownModel with ID: {cost_breakdown.id} into the database.")
    logging.debug(f"Creating OfferModel with ID: {offer.id}")
    logging.debug(f"Inserting OfferModel with ID: {offer.id} into the database.")
    return offer


@pytest.fixture
def route(test_data):
    """Get the test route."""
    return test_data["route"]


@pytest.fixture
def offer_data(route):
    """Create test offer data."""
    return {
        "route_id": route.id,
        "margin_percentage": 15.0,
        "price": "1500.00",
        "currency": "EUR",
        "validity_hours": 24,
        "status": "draft",
        "content": {
            "title": "Test Offer",
            "description": "Test offer description",
            "highlights": ["Fast delivery", "Professional service"],
            "terms": ["Payment within 30 days", "Insurance included"]
        }
    }


def test_generate_offer_success(client, route, offer_data):
    """Test successful offer generation."""
    response = client.post(f"/api/offer/generate/{route.id}", json=offer_data)
    assert response.status_code == 200
    data = response.get_json()
    assert "offer" in data
    offer = data["offer"]
    assert "id" in offer
    assert offer["route_id"] == str(route.id)
    assert float(offer["margin_percentage"]) == float(offer_data["margin_percentage"])


def test_generate_offer_with_ai(client, route, offer_data):
    """Test offer generation with AI content enhancement."""
    offer_data["enhance_with_ai"] = True
    response = client.post(f"/api/offer/generate/{route.id}", json=offer_data)
    assert response.status_code == 200
    data = response.get_json()
    assert "offer" in data
    offer = data["offer"]
    assert "ai_content" in offer
    assert offer["ai_content"] is not None


def test_enhance_offer_success(client, route, offer_data):
    """Test successful offer enhancement."""
    # First create an offer
    response = client.post(f"/api/offer/generate/{route.id}", json=offer_data)
    assert response.status_code == 200
    offer_id = response.get_json()["offer"]["id"]
    
    # Then enhance it
    response = client.post(f"/api/offer/{offer_id}/enhance")
    assert response.status_code == 200
    data = response.get_json()
    assert "offer" in data
    offer = data["offer"]
    assert "ai_content" in offer
    assert offer["ai_content"] is not None


def test_generate_offer_invalid_margin(client, route, offer_data):
    """Test offer generation with invalid margin."""
    offer_data["margin_percentage"] = -5.0
    response = client.post(f"/api/offer/generate/{route.id}", json=offer_data)
    assert response.status_code == 400


def test_generate_offer_route_not_found(client, offer_data):
    """Test offer generation with non-existent route."""
    offer_data["route_id"] = str(uuid4())
    response = client.post(f"/api/offer/generate/{offer_data['route_id']}", json=offer_data)
    assert response.status_code == 404


@contextmanager
def mock_container_in_request(client, mock_repo):
    """Context manager to mock container in request context."""
    with client.application.test_request_context():
        # Create a fresh container
        container = Container(client.application.config, client.application.container._db)
        
        # Store original container
        original_container = getattr(client.application, 'container', None)
        
        try:
            # Set up mock repository
            container._instances['cost_breakdown_repository'] = mock_repo
            
            # Set container in both app and request context
            client.application.container = container
            g.container = container
            
            yield container
        finally:
            # Restore original container
            if original_container:
                client.application.container = original_container


def test_generate_offer_no_cost_breakdown(client, test_data, db):
    """Test offer generation without cost breakdown."""
    # Create a route without cost breakdown
    route = RouteModel(
        id=str(uuid4()),
        transport_id=test_data["transport"].id,
        business_entity_id=test_data["business_entity"].id,
        cargo_id=test_data["cargo"].id,
        origin_id=test_data["origin"].id,
        destination_id=test_data["destination"].id,
        pickup_time=datetime.utcnow(),
        delivery_time=datetime.utcnow().replace(hour=(datetime.utcnow().hour + 8) % 24),
        empty_driving_id=test_data["empty_driving"].id,
        total_distance_km=550.5,
        total_duration_hours=8.5,
        is_feasible=True,
        status="draft"
    )
    db.add(route)
    db.commit()
    db.refresh(route)

    # Try to generate offer
    response = client.post(f"/api/offer/generate/{route.id}", json={
        "margin_percentage": 15.0,
        "price": "1500.00",
        "currency": "EUR",
        "validity_hours": 24,
        "status": "draft"
    })
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Cost breakdown not found for route"


def test_get_offer_success(client, route, offer_data):
    """Test successful offer retrieval."""
    # First create an offer
    response = client.post(f"/api/offer/generate/{route.id}", json=offer_data)
    assert response.status_code == 200
    offer_id = response.get_json()["offer"]["id"]
    
    # Then retrieve it
    response = client.get(f"/api/offer/{offer_id}")
    assert response.status_code == 200
    data = response.get_json()
    assert "offer" in data
    offer = data["offer"]
    assert offer["id"] == offer_id
    assert offer["route_id"] == str(route.id)


def test_get_offer_not_found(client):
    """Test offer retrieval with non-existent ID."""
    response = client.get(f"/api/offer/{uuid4()}")
    assert response.status_code == 404


def test_enhance_offer_not_found(client):
    """Test offer enhancement with non-existent ID."""
    response = client.post(f"/api/offer/{uuid4()}/enhance")
    assert response.status_code == 404 


def test_finalize_offer_success(client, sample_offer, route, db, test_data):
    """Test successful offer finalization."""
    print("\n=== Starting test_finalize_offer_success ===")
    
    # Log initial state
    print("\n1. Initial State:")
    print(f"Route ID: {route.id}")
    print(f"Sample Offer ID: {sample_offer.id}")
    
    # Get and log cargo and business entity
    cargo = test_data["cargo"]
    business_entity = test_data["business_entity"]
    print("\n2. Test Data Objects:")
    print(f"Cargo ID: {cargo.id}")
    print(f"Cargo Status: {cargo.status}")
    print(f"Cargo Business Entity ID: {cargo.business_entity_id}")
    print(f"Business Entity ID: {business_entity.id}")
    
    # Verify cargo exists in database
    db_cargo = db.query(CargoModel).filter_by(id=cargo.id).first()
    print("\n3. Cargo in Database:")
    print(f"DB Cargo exists: {db_cargo is not None}")
    if db_cargo:
        print(f"DB Cargo ID: {db_cargo.id}")
        print(f"DB Cargo Business Entity ID: {db_cargo.business_entity_id}")
        print(f"DB Cargo Status: {db_cargo.status}")
    
    # Update route
    print("\n4. Updating Route:")
    print(f"Previous Route Cargo ID: {route.cargo_id}")
    print(f"Previous Route Business Entity ID: {route.business_entity_id}")
    route.cargo_id = cargo.id
    route.business_entity_id = business_entity.id
    db.add(route)
    
    # Update offer
    print("\n5. Updating Offer:")
    print(f"Previous Offer Route ID: {sample_offer.route_id}")
    sample_offer.route_id = route.id
    db.add(sample_offer)
    
    try:
        print("\n6. Committing Changes:")
        db.commit()
        print("Commit successful")
        
        # Refresh objects
        print("\n7. Refreshing Objects:")
        db.refresh(route)
        print(f"Route refreshed - Cargo ID: {route.cargo_id}")
        db.refresh(sample_offer)
        print(f"Offer refreshed - Route ID: {sample_offer.route_id}")
        db.refresh(cargo)
        print(f"Cargo refreshed - Status: {cargo.status}")
        
        # Verify relationships after refresh
        print("\n8. Verifying Relationships After Refresh:")
        print(f"Route -> Cargo ID: {route.cargo_id}")
        print(f"Route -> Business Entity ID: {route.business_entity_id}")
        print(f"Offer -> Route ID: {sample_offer.route_id}")
        
        # Make the finalize request
        print("\n9. Making Finalize Request:")
        response = client.post(f"/api/offer/{sample_offer.id}/finalize")
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Data: {response.get_json()}")
        
        # Assertions
        print("\n10. Running Assertions:")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.get_json()
        assert data["status"] == "success", f"Expected success status, got {data.get('status')}"
        assert data["offer"]["status"] == "finalized", f"Expected finalized status, got {data['offer'].get('status')}"
        
        # Verify status changes
        assert data["status"] == "success"
        assert data["offer"]["status"] == "finalized"
        
        # Verify status history was created
        history_response = client.get(f"/api/cargo/{cargo.id}/status-history")
        assert history_response.status_code == 200
        
        history_data = history_response.get_json()
        assert history_data["current_status"] == "in_transit"
        assert len(history_data["history"]) == 1
        
        history_entry = history_data["history"][0]
        assert history_entry["old_status"] == "pending"
        assert history_entry["new_status"] == "in_transit"
        assert history_entry["trigger"] == "offer_finalization"
        assert history_entry["trigger_id"] == str(sample_offer.id)
        assert "offer_id" in history_entry["details"]
        assert "route_id" in history_entry["details"]
        assert "final_price" in history_entry["details"]
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        print(f"Error type: {type(e)}")
        db.rollback()
        raise
    finally:
        print("\n=== Test Completed ===\n")


def test_finalize_offer_not_found(client):
    """Test finalization of non-existent offer."""
    response = client.post(f"/api/offer/{uuid4()}/finalize")
    assert response.status_code == 404
    assert "Offer not found" in response.json["error"]


def test_finalize_offer_invalid_cargo_state(client, sample_offer, route, db):
    """Test finalizing an offer with invalid cargo state."""
    print("\nStarting test_finalize_offer_invalid_cargo_state")
    print(f"Initial Route ID: {route.id}")
    print(f"Initial Offer ID: {sample_offer.id}")
    
    # Get the route's cargo
    route_cargo = db.query(CargoModel).filter_by(id=route.cargo_id).first()
    print(f"Route's cargo ID: {route_cargo.id}")
    print(f"Initial Cargo Status: {route_cargo.status}")
    
    try:
        # Set cargo to an invalid state
        print("Attempting to update cargo status to 'in_transit'")
        route_cargo.status = "in_transit"
        db.commit()
        db.refresh(route_cargo)
        print(f"Updated Cargo status to: {route_cargo.status}")

        # Verify cargo status in database
        cargo_from_db = db.query(CargoModel).filter_by(id=route_cargo.id).first()
        print(f"Cargo status in database: {cargo_from_db.status}")

        # Try to finalize the offer
        print(f"Attempting to finalize offer with ID: {sample_offer.id}")
        response = client.post(f"/api/offer/{sample_offer.id}/finalize")
        print(f"Finalize offer response status code: {response.status_code}")
        print(f"Finalize offer response data: {response.get_json()}")
        
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "cargo is not in pending state" in data["error"]
        
    except Exception as e:
        print(f"Error during test execution: {e}")
        db.rollback()
        raise
    finally:
        print("Cleaning up test resources")
        db.rollback()


def test_finalize_offer_missing_cargo(client, sample_offer, db):
    """Test offer finalization with missing cargo."""
    with client.application.app_context():
        # Get route
        route = db.query(RouteModel).filter_by(id=sample_offer.route_id).first()
        
        # Create a new route without cargo
        new_route = RouteModel(
            id=str(uuid4()),
            transport_id=route.transport_id,
            business_entity_id=route.business_entity_id,
            origin_id=route.origin_id,
            destination_id=route.destination_id,
            pickup_time=route.pickup_time,
            delivery_time=route.delivery_time,
            empty_driving_id=route.empty_driving_id,
            total_distance_km=route.total_distance_km,
            total_duration_hours=route.total_duration_hours,
            is_feasible=True,
            status="draft"
        )
        db.add(new_route)
        db.flush()
        
        # Create a new cost breakdown
        cost_breakdown = CostBreakdownModel(
            id=str(uuid4()),
            route_id=new_route.id,
            fuel_costs=json.dumps({"DE": "250.00", "PL": "180.00"}),
            toll_costs=json.dumps({"DE": "120.00", "PL": "85.00"}),
            driver_costs=json.dumps({
                "base_cost": "200.00",
                "regular_hours_cost": "150.00",
                "overtime_cost": "100.00",
                "total_cost": "450.00"
            }),
            overhead_costs="175.00",
            timeline_event_costs=json.dumps({
                "unloading": "50.00",
                "rest_stop": "25.00"
            }),
            total_cost="1385.00"
        )
        db.add(cost_breakdown)
        db.flush()
        
        # Create new offer referencing the new route and cost breakdown
        new_offer = OfferModel(
            id=str(uuid4()),
            route_id=new_route.id,
            cost_breakdown_id=cost_breakdown.id,
            margin_percentage="15.0",
            final_price="1500.00",
            status="draft"
        )
        db.add(new_offer)
        db.commit()
        
        response = client.post(f"/api/offer/{new_offer.id}/finalize")
        assert response.status_code == 400
        assert "Route has no cargo assigned" in response.json["error"] 


def test_get_offer_status_history(client, sample_offer):
    """Test getting offer status history."""
    # First update the status a few times
    status_updates = [
        ("in_progress", "Started processing offer"),
        ("accepted", "Offer accepted by carrier"),
        ("completed", "Offer completed successfully")
    ]

    for status, comment in status_updates:
        response = client.put(
            f"/api/offer/{sample_offer.id}/status",
            json={"status": status, "comment": comment}
        )
        assert response.status_code == 200

    # Get status history
    response = client.get(f"/api/offer/{sample_offer.id}/status-history")
    assert response.status_code == 200
    
    history = response.json
    assert len(history) == 3  # 3 status updates
    
    # Check if history is ordered by timestamp (descending)
    assert history[0]["status"] == "completed"
    assert history[1]["status"] == "accepted"
    assert history[2]["status"] == "in_progress"
    
    # Check comments
    assert history[0]["comment"] == "Offer completed successfully"
    assert history[1]["comment"] == "Offer accepted by carrier"
    assert history[2]["comment"] == "Started processing offer"


def test_get_offer_status_history_not_found(client):
    """Test getting status history for non-existent offer."""
    response = client.get(f"/api/offer/{uuid4()}/status-history")
    assert response.status_code == 404
    assert "error" in response.json


def test_update_offer_status_with_comment(client, sample_offer):
    """Test updating offer status with comment."""
    response = client.put(
        f"/api/offer/{sample_offer.id}/status",
        json={
            "status": "in_progress",
            "comment": "Starting to process the offer"
        }
    )
    assert response.status_code == 200
    assert response.json["old_status"] == "draft"
    assert response.json["new_status"] == "in_progress"

    # Verify status history
    response = client.get(f"/api/offer/{sample_offer.id}/status-history")
    assert response.status_code == 200
    history = response.json
    assert len(history) == 1
    assert history[0]["status"] == "in_progress"
    assert history[0]["comment"] == "Starting to process the offer" 


@pytest.fixture
def sample_cost_breakdown(db, sample_route):
    """Create a sample cost breakdown."""
    breakdown = CostBreakdownModel(
        id=str(uuid4()),
        route_id=sample_route.id,
        fuel_costs=json.dumps({"DE": "250.00", "PL": "200.00"}),
        toll_costs=json.dumps({"DE": "150.00", "PL": "100.00"}),
        driver_costs=json.dumps({
            "base_cost": "200.00",
            "regular_hours_cost": "200.00",
            "overtime_cost": "100.00",
            "total_cost": "500.00"
        }),
        overhead_costs="200.00",
        timeline_event_costs=json.dumps({"REST": "50.00"}),
        total_cost="1450.00"
    )
    db.add(breakdown)
    db.commit()
    return breakdown 