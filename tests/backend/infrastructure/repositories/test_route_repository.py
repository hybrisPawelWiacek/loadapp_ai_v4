"""Tests for route repository implementations."""
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4
import json

import pytest
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.domain.entities.route import (
    Route, Location, TimelineEvent,
    CountrySegment, EmptyDriving
)
from backend.infrastructure.repositories.route_repository import SQLRouteRepository
from backend.infrastructure.models.business_models import BusinessEntityModel
from backend.infrastructure.models.transport_models import (
    TransportModel, TransportTypeModel,
    TruckSpecificationModel, DriverSpecificationModel
)
from backend.infrastructure.models.cargo_models import CargoModel
from backend.infrastructure.models.route_models import LocationModel, EmptyDrivingModel, RouteModel


@pytest.fixture
def test_locations(db):
    """Create test locations in the database."""
    berlin = LocationModel(
        id=str(uuid4()),
        latitude=52.520008,
        longitude=13.404954,
        address="Sample Address, Berlin, Germany"
    )
    warsaw = LocationModel(
        id=str(uuid4()),
        latitude=52.237049,
        longitude=21.017532,
        address="Sample Address, Warsaw, Poland"
    )
    db.add(berlin)
    db.add(warsaw)
    db.commit()
    return berlin, warsaw


@pytest.fixture
def test_empty_driving(db):
    """Create test empty driving in the database."""
    empty_driving = EmptyDrivingModel(
        id=str(uuid4()),
        distance_km=200.0,
        duration_hours=4.0
    )
    db.add(empty_driving)
    db.commit()
    return empty_driving


@pytest.fixture
def test_business_entity(db):
    """Create test business entity in the database."""
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
    db.commit()
    return business_entity


@pytest.fixture
def test_transport(db, test_business_entity):
    """Create test transport in the database."""
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
        driving_time_rate="25.00",
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
        business_entity_id=test_business_entity.id,
        truck_specifications_id=truck_spec.id,
        driver_specifications_id=driver_spec.id,
        is_active=True
    )
    db.add(transport)
    db.commit()
    return transport


@pytest.fixture
def test_cargo(db, test_business_entity):
    """Create test cargo in the database."""
    cargo = CargoModel(
        id=str(uuid4()),
        business_entity_id=test_business_entity.id,
        weight=1500.0,
        volume=10.0,
        cargo_type="general",
        value="25000.00",
        special_requirements=json.dumps(["temperature_controlled"]),
        status="pending"
    )
    db.add(cargo)
    db.commit()
    return cargo


@pytest.fixture
def timeline_events(test_locations):
    """Create test timeline events."""
    berlin, warsaw = test_locations
    route_id = uuid4()
    return [
        TimelineEvent(
            id=uuid4(),
            route_id=route_id,
            type="pickup",
            location_id=UUID(berlin.id),
            planned_time=datetime.now(timezone.utc),
            duration_hours=1.0,
            event_order=1
        ),
        TimelineEvent(
            id=uuid4(),
            route_id=route_id,
            type="delivery",
            location_id=UUID(warsaw.id),
            planned_time=datetime.now(timezone.utc),
            duration_hours=1.0,
            event_order=2
        )
    ]


@pytest.fixture
def country_segments(test_locations):
    """Create test country segments."""
    berlin, warsaw = test_locations
    route_id = uuid4()
    return [
        CountrySegment(
            id=uuid4(),
            route_id=route_id,
            country_code="DE",
            distance_km=200.0,  # Empty driving
            duration_hours=4.0,
            start_location_id=UUID(berlin.id),
            end_location_id=UUID(berlin.id),
            segment_order=0
        ),
        CountrySegment(
            id=uuid4(),
            route_id=route_id,
            country_code="DE",
            distance_km=550.0,
            duration_hours=5.5,
            start_location_id=UUID(berlin.id),
            end_location_id=UUID(warsaw.id),
            segment_order=1
        ),
        CountrySegment(
            id=uuid4(),
            route_id=route_id,
            country_code="FR",
            distance_km=500.0,
            duration_hours=4.5,
            start_location_id=UUID(warsaw.id),
            end_location_id=UUID(warsaw.id),
            segment_order=2
        )
    ]


@pytest.fixture
def route(test_transport, test_business_entity, test_cargo, test_locations, test_empty_driving, timeline_events, country_segments):
    """Create test route."""
    berlin, warsaw = test_locations
    return Route(
        id=uuid4(),
        transport_id=UUID(test_transport.id),
        business_entity_id=UUID(test_business_entity.id),
        cargo_id=UUID(test_cargo.id),
        origin_id=UUID(berlin.id),
        destination_id=UUID(warsaw.id),
        pickup_time=datetime.now(timezone.utc),
        delivery_time=datetime.now(timezone.utc),
        empty_driving_id=UUID(test_empty_driving.id),
        total_distance_km=700.0,
        total_duration_hours=9.0,
        is_feasible=True,
        status="draft",
        timeline_events=timeline_events,
        country_segments=country_segments
    )


@pytest.fixture
def route_repository(db):
    """Create a route repository instance."""
    return SQLRouteRepository(db)


class TestSQLRouteRepository:
    """Tests for SQLRouteRepository."""

    def test_save_route(self, db: Session, route: Route):
        """Test saving a route."""
        # Arrange
        repo = SQLRouteRepository(db)

        # Act
        saved_route = repo.save(route)

        # Assert
        assert saved_route is not None
        assert saved_route.id == route.id
        assert saved_route.transport_id == route.transport_id
        assert saved_route.business_entity_id == route.business_entity_id
        assert saved_route.cargo_id == route.cargo_id
        assert saved_route.is_feasible == route.is_feasible
        assert len(saved_route.timeline_events) == len(route.timeline_events)
        assert len(saved_route.country_segments) == len(route.country_segments)

    def test_find_route_by_id(self, db: Session, route: Route):
        """Test finding a route by ID."""
        # Arrange
        repo = SQLRouteRepository(db)
        saved_route = repo.save(route)

        # Act
        found_route = repo.find_by_id(saved_route.id)

        # Assert
        assert found_route is not None
        assert found_route.id == route.id
        assert found_route.transport_id == route.transport_id
        assert found_route.business_entity_id == route.business_entity_id
        assert found_route.cargo_id == route.cargo_id
        assert found_route.is_feasible == route.is_feasible
        assert len(found_route.timeline_events) == len(route.timeline_events)
        assert len(found_route.country_segments) == len(route.country_segments)

    def test_find_nonexistent_route(self, db: Session):
        """Test finding a route that doesn't exist."""
        # Arrange
        repo = SQLRouteRepository(db)

        # Act
        found_route = repo.find_by_id(uuid4())

        # Assert
        assert found_route is None

    def test_get_route_by_id(self, db: Session, route: Route):
        """Test getting a route by ID."""
        # Arrange
        repo = SQLRouteRepository(db)
        saved_route = repo.save(route)

        # Act
        found_route = repo.find_by_id(saved_route.id)

        # Assert
        assert found_route is not None
        assert found_route.id == route.id
        assert found_route.transport_id == route.transport_id
        assert found_route.business_entity_id == route.business_entity_id
        assert found_route.cargo_id == route.cargo_id
        assert found_route.origin_id == route.origin_id
        assert found_route.destination_id == route.destination_id
        assert found_route.pickup_time.replace(tzinfo=timezone.utc) == route.pickup_time.replace(tzinfo=timezone.utc)
        assert found_route.delivery_time.replace(tzinfo=timezone.utc) == route.delivery_time.replace(tzinfo=timezone.utc)
        assert found_route.empty_driving_id == route.empty_driving_id
        assert found_route.total_distance_km == route.total_distance_km
        assert found_route.total_duration_hours == route.total_duration_hours
        assert found_route.is_feasible == route.is_feasible
        assert found_route.status == route.status 