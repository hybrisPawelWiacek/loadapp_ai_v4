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
def berlin_location(test_locations) -> Location:
    """Create a sample location in Berlin."""
    berlin, _ = test_locations
    return Location(
        id=UUID(berlin.id),
        latitude=berlin.latitude,
        longitude=berlin.longitude,
        address=berlin.address
    )


@pytest.fixture
def warsaw_location(test_locations) -> Location:
    """Create a sample location in Warsaw."""
    _, warsaw = test_locations
    return Location(
        id=UUID(warsaw.id),
        latitude=warsaw.latitude,
        longitude=warsaw.longitude,
        address=warsaw.address
    )


@pytest.fixture
def test_empty_driving(db):
    """Create test empty driving record in the database."""
    empty_driving = EmptyDrivingModel(
        id=str(uuid4()),
        distance_km=200.0,
        duration_hours=4.0
    )
    db.add(empty_driving)
    db.commit()
    return empty_driving


@pytest.fixture
def empty_driving(test_empty_driving) -> EmptyDriving:
    """Create a sample empty driving segment."""
    return EmptyDriving(
        id=UUID(test_empty_driving.id),
        distance_km=test_empty_driving.distance_km,
        duration_hours=test_empty_driving.duration_hours
    )


@pytest.fixture
def timeline_events(berlin_location: Location) -> list[TimelineEvent]:
    """Create sample timeline events."""
    base_time = datetime(2024, 1, 1, 7, 0, tzinfo=timezone.utc)
    return [
        TimelineEvent(
            id=uuid4(),
            type="pickup",
            location=berlin_location,
            planned_time=base_time,
            duration_hours=1.0,
            event_order=1
        ),
        TimelineEvent(
            id=uuid4(),
            type="rest",
            location=berlin_location,
            planned_time=base_time.replace(hour=11),
            duration_hours=1.0,
            event_order=2
        ),
        TimelineEvent(
            id=uuid4(),
            type="delivery",
            location=berlin_location,
            planned_time=base_time.replace(hour=15),
            duration_hours=1.0,
            event_order=3
        )
    ]


@pytest.fixture
def country_segments(berlin_location: Location, warsaw_location: Location) -> list[CountrySegment]:
    """Create sample country segments."""
    return [
        CountrySegment(
            country_code="DE",
            distance_km=300.0,
            duration_hours=4.0,
            start_location=berlin_location,
            end_location=warsaw_location
        ),
        CountrySegment(
            country_code="PL",
            distance_km=200.0,
            duration_hours=3.0,
            start_location=warsaw_location,
            end_location=warsaw_location
        )
    ]


@pytest.fixture
def test_business_entity(db):
    """Create a test business entity."""
    business = BusinessEntityModel(
        id=str(uuid4()),
        name="Test Transport Company",
        address="Test Address, Berlin",
        contact_info={
            "email": "test@example.com",
            "phone": "+49123456789"
        },
        business_type="TRANSPORT_COMPANY",
        certifications=["ISO9001", "ADR"],
        operating_countries=["DE", "PL"],
        cost_overheads={
            "admin": "0.15",
            "insurance": "0.05"
        }
    )
    db.add(business)
    db.commit()
    return business


@pytest.fixture
def test_truck_specs(db):
    """Create test truck specifications."""
    specs = TruckSpecificationModel(
        id=str(uuid4()),
        fuel_consumption_empty=25.0,
        fuel_consumption_loaded=32.0,
        toll_class="EURO_6",
        euro_class="EURO_6",
        co2_class="A",
        maintenance_rate_per_km="0.15"
    )
    db.add(specs)
    db.commit()
    return specs


@pytest.fixture
def test_driver_specs(db):
    """Create test driver specifications."""
    specs = DriverSpecificationModel(
        id=str(uuid4()),
        daily_rate="350.00",
        required_license_type="CE",
        required_certifications=json.dumps(["ADR"])
    )
    db.add(specs)
    db.commit()
    return specs


@pytest.fixture
def test_transport_type(db, test_truck_specs, test_driver_specs):
    """Create test transport type."""
    transport_type = TransportTypeModel(
        id="TRUCK_FLATBED",
        name="Flatbed Truck",
        truck_specifications=test_truck_specs,
        driver_specifications=test_driver_specs
    )
    db.add(transport_type)
    db.commit()
    return transport_type


@pytest.fixture
def test_transport(db, test_business_entity, test_transport_type, test_truck_specs, test_driver_specs):
    """Create a test transport."""
    transport = TransportModel(
        id=str(uuid4()),
        transport_type_id=test_transport_type.id,
        business_entity_id=test_business_entity.id,
        truck_specifications_id=test_truck_specs.id,
        driver_specifications_id=test_driver_specs.id,
        is_active=True
    )
    db.add(transport)
    db.commit()
    return transport


@pytest.fixture
def test_cargo(db):
    """Create a test cargo."""
    cargo = CargoModel(
        id=str(uuid4()),
        weight=5000.0,
        volume=24.0,
        value=str(Decimal("50000.00")),
        special_requirements=["TEMPERATURE_CONTROLLED"]
    )
    db.add(cargo)
    db.commit()
    return cargo


@pytest.fixture
def route(
    berlin_location: Location,
    warsaw_location: Location,
    empty_driving: EmptyDriving,
    timeline_events: list[TimelineEvent],
    country_segments: list[CountrySegment],
    test_transport: TransportModel,
    test_business_entity: BusinessEntityModel,
    test_cargo: CargoModel,
    test_empty_driving: EmptyDrivingModel
) -> Route:
    """Create a sample route."""
    return Route(
        id=uuid4(),
        transport_id=UUID(test_transport.id),
        business_entity_id=UUID(test_business_entity.id),
        cargo_id=UUID(test_cargo.id),
        origin_id=berlin_location.id,
        destination_id=warsaw_location.id,
        pickup_time=timeline_events[0].planned_time,
        delivery_time=timeline_events[-1].planned_time,
        empty_driving_id=UUID(test_empty_driving.id),
        timeline_events=timeline_events,
        country_segments=country_segments,
        total_distance_km=500.0,  # Sum of country segments
        total_duration_hours=7.0,  # Sum of country segments
        is_feasible=True
    )


@pytest.fixture
def route_repository(db):
    """Create a route repository instance."""
    return SQLRouteRepository(db)


@pytest.fixture
def route_model(db, test_transport, test_business_entity, test_cargo, test_locations, test_empty_driving):
    """Create a test route model."""
    berlin, warsaw = test_locations
    base_time = datetime(2024, 1, 1, 7, 0, tzinfo=timezone.utc)
    route = RouteModel(
        id=str(uuid4()),
        transport_id=test_transport.id,
        business_entity_id=test_business_entity.id,
        cargo_id=test_cargo.id,
        origin_id=berlin.id,
        destination_id=warsaw.id,
        pickup_time=base_time,
        delivery_time=base_time.replace(hour=15),
        empty_driving_id=test_empty_driving.id,
        total_distance_km=500.0,
        total_duration_hours=7.0,
        is_feasible=True,
        status="PLANNED"
    )
    db.add(route)
    db.commit()

    # Add timeline events
    timeline_events = [
        {
            "id": str(uuid4()),
            "route_id": route.id,
            "type": "pickup",
            "location_id": berlin.id,
            "planned_time": base_time,
            "duration_hours": 1.0,
            "event_order": 1
        },
        {
            "id": str(uuid4()),
            "route_id": route.id,
            "type": "rest",
            "location_id": berlin.id,
            "planned_time": base_time.replace(hour=11),
            "duration_hours": 1.0,
            "event_order": 2
        },
        {
            "id": str(uuid4()),
            "route_id": route.id,
            "type": "delivery",
            "location_id": warsaw.id,
            "planned_time": base_time.replace(hour=15),
            "duration_hours": 1.0,
            "event_order": 3
        }
    ]
    for event in timeline_events:
        db.execute(
            text("""
            INSERT INTO timeline_events (id, route_id, type, location_id, planned_time, duration_hours, event_order)
            VALUES (:id, :route_id, :type, :location_id, :planned_time, :duration_hours, :event_order)
            """),
            event
        )

    # Add country segments
    country_segments = [
        {
            "id": str(uuid4()),
            "route_id": route.id,
            "country_code": "DE",
            "distance_km": 300.0,
            "duration_hours": 4.0,
            "start_location_id": berlin.id,
            "end_location_id": warsaw.id
        },
        {
            "id": str(uuid4()),
            "route_id": route.id,
            "country_code": "PL",
            "distance_km": 200.0,
            "duration_hours": 3.0,
            "start_location_id": warsaw.id,
            "end_location_id": warsaw.id
        }
    ]
    for segment in country_segments:
        db.execute(
            text("""
            INSERT INTO country_segments (id, route_id, country_code, distance_km, duration_hours, start_location_id, end_location_id)
            VALUES (:id, :route_id, :country_code, :distance_km, :duration_hours, :start_location_id, :end_location_id)
            """),
            segment
        )

    db.commit()
    return route


class TestSQLRouteRepository:
    """Test cases for SQLRouteRepository."""

    def test_save_route(self, db: Session, route: Route):
        """Test saving a route instance."""
        # Arrange
        repo = SQLRouteRepository(db)

        # Act
        saved_route = repo.save(route)

        # Assert
        assert isinstance(saved_route, Route)
        assert saved_route.id == route.id
        assert saved_route.transport_id == route.transport_id
        assert saved_route.business_entity_id == route.business_entity_id
        assert saved_route.cargo_id == route.cargo_id
        assert saved_route.is_feasible == route.is_feasible
        assert saved_route.origin_id == route.origin_id
        assert saved_route.destination_id == route.destination_id
        assert saved_route.empty_driving_id == route.empty_driving_id
        assert saved_route.total_distance_km == route.total_distance_km
        assert saved_route.total_duration_hours == route.total_duration_hours

        # Check timeline events
        assert len(saved_route.timeline_events) == len(route.timeline_events)
        for saved_event, original_event in zip(saved_route.timeline_events, route.timeline_events):
            assert saved_event.type == original_event.type
            assert saved_event.location.id == original_event.location.id
            assert saved_event.location.latitude == original_event.location.latitude
            assert saved_event.location.longitude == original_event.location.longitude
            assert saved_event.location.address == original_event.location.address
            # Convert both datetimes to UTC for comparison
            saved_time = saved_event.planned_time.replace(tzinfo=timezone.utc)
            original_time = original_event.planned_time.replace(tzinfo=timezone.utc)
            assert saved_time == original_time
            assert saved_event.duration_hours == original_event.duration_hours
            assert saved_event.event_order == original_event.event_order

        # Check country segments
        assert len(saved_route.country_segments) == len(route.country_segments)
        for saved_segment, original_segment in zip(saved_route.country_segments, route.country_segments):
            assert saved_segment.country_code == original_segment.country_code
            assert saved_segment.distance_km == original_segment.distance_km
            assert saved_segment.duration_hours == original_segment.duration_hours
            assert saved_segment.start_location.id == original_segment.start_location.id
            assert saved_segment.start_location.latitude == original_segment.start_location.latitude
            assert saved_segment.start_location.longitude == original_segment.start_location.longitude
            assert saved_segment.start_location.address == original_segment.start_location.address
            assert saved_segment.end_location.id == original_segment.end_location.id
            assert saved_segment.end_location.latitude == original_segment.end_location.latitude
            assert saved_segment.end_location.longitude == original_segment.end_location.longitude
            assert saved_segment.end_location.address == original_segment.end_location.address

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

    def test_find_nonexistent_route(self, db: Session):
        """Test finding a route that doesn't exist."""
        # Arrange
        repo = SQLRouteRepository(db)

        # Act
        found_route = repo.find_by_id(uuid4())

        # Assert
        assert found_route is None 
        assert found_route is None 

    def test_get_route_by_id(self, route_repository, route_model):
        """Test getting a route by ID."""
        route = route_repository.get(route_model.id)
        assert route is not None
        assert route.id == route_model.id
        assert route.transport_id == route_model.transport_id
        assert route.business_entity_id == route_model.business_entity_id
        assert route.cargo_id == route_model.cargo_id
        assert route.origin_id == route_model.origin_id
        assert route.destination_id == route_model.destination_id
        assert route.pickup_time.replace(tzinfo=timezone.utc) == route_model.pickup_time.replace(tzinfo=timezone.utc)
        assert route.delivery_time.replace(tzinfo=timezone.utc) == route_model.delivery_time.replace(tzinfo=timezone.utc)
        assert route.empty_driving_id == route_model.empty_driving_id
        assert Decimal(str(route.total_distance_km)) == Decimal(str(route_model.total_distance_km))
        assert Decimal(str(route.total_duration_hours)) == Decimal(str(route_model.total_duration_hours))
        assert route.is_feasible == route_model.is_feasible
        assert route.status == route_model.status 