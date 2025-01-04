"""Tests for offer service."""
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Optional, Tuple
from uuid import UUID, uuid4

from backend.domain.services.offer_service import OfferService
from backend.domain.entities.cargo import CostBreakdown, Offer, Cargo
from backend.domain.entities.route import Route, RouteStatus


class MockOfferRepository:
    """Mock repository for Offer entity."""
    
    def __init__(self):
        self.offers: Dict[UUID, Offer] = {}
        
    def save(self, offer: Offer) -> Offer:
        """Save an offer."""
        self.offers[offer.id] = offer
        return offer
        
    def find_by_id(self, id: UUID) -> Optional[Offer]:
        """Find an offer by ID."""
        return self.offers.get(id)

    def find_by_route_id(self, route_id: UUID) -> Optional[Offer]:
        """Find an offer by route ID."""
        for offer in self.offers.values():
            if offer.route_id == route_id:
                return offer
        return None


class MockCargoRepository:
    """Mock repository for Cargo entity."""
    
    def __init__(self):
        self.cargos: Dict[UUID, Cargo] = {}
        
    def save(self, cargo: Cargo) -> Cargo:
        """Save a cargo."""
        self.cargos[cargo.id] = cargo
        return cargo
        
    def find_by_id(self, id: UUID) -> Optional[Cargo]:
        """Find a cargo by ID."""
        return self.cargos.get(id)


class MockRouteRepository:
    """Mock repository for Route entity."""
    
    def __init__(self):
        self.routes: Dict[UUID, Route] = {}
        
    def save(self, route: Route) -> Route:
        """Save a route."""
        self.routes[route.id] = route
        return route
        
    def find_by_id(self, id: UUID) -> Optional[Route]:
        """Find a route by ID."""
        return self.routes.get(id)

    def find_by_cargo_id(self, cargo_id: UUID) -> Optional[Route]:
        """Find a route by cargo ID."""
        for route in self.routes.values():
            if route.cargo_id == cargo_id:
                return route
        return None


class MockContentEnhancer:
    """Mock service for AI content enhancement."""
    
    def enhance_offer(self, offer: Offer) -> Tuple[str, str]:
        """Generate enhanced content and fun fact."""
        return (
            f"Enhanced offer description for route {offer.route_id}",
            f"Fun fact about transport with price {offer.final_price}"
        )


class MockCostBreakdownRepository:
    """Mock repository for CostBreakdown entity."""
    
    def __init__(self):
        self.cost_breakdowns: Dict[UUID, CostBreakdown] = {}
        
    def save(self, cost_breakdown: CostBreakdown) -> CostBreakdown:
        """Save a cost breakdown."""
        self.cost_breakdowns[cost_breakdown.id] = cost_breakdown
        return cost_breakdown
        
    def find_by_id(self, id: UUID) -> Optional[CostBreakdown]:
        """Find a cost breakdown by ID."""
        return self.cost_breakdowns.get(id)

    def find_by_route_id(self, route_id: UUID) -> Optional[CostBreakdown]:
        """Find a cost breakdown by route ID."""
        for cb in self.cost_breakdowns.values():
            if cb.route_id == route_id:
                return cb
        return None


class MockSession:
    """Mock SQLAlchemy session."""
    
    def __init__(self):
        self.added = []
        self.committed = False
        self.rolled_back = False
        
    def add(self, obj):
        """Add an object to the session."""
        self.added.append(obj)
        
    def commit(self):
        """Commit the session."""
        self.committed = True
        
    def rollback(self):
        """Rollback the session."""
        self.rolled_back = True


@pytest.fixture
def offer_repository_mock():
    """Create mock offer repository."""
    return MockOfferRepository()


@pytest.fixture
def cargo_repository_mock():
    """Create mock cargo repository."""
    return MockCargoRepository()


@pytest.fixture
def route_repository_mock():
    """Create mock route repository."""
    return MockRouteRepository()


@pytest.fixture
def offer_enhancer_mock():
    """Create mock content enhancer."""
    return MockContentEnhancer()


@pytest.fixture
def cost_breakdown_repository_mock():
    """Create mock cost breakdown repository."""
    return MockCostBreakdownRepository()


@pytest.fixture
def db_session_mock():
    """Create mock database session."""
    return MockSession()


@pytest.fixture
def route(route_repository_mock) -> Route:
    """Create and save a sample route."""
    route = Route(
        id=uuid4(),
        transport_id=uuid4(),
        business_entity_id=uuid4(),
        cargo_id=uuid4(),
        origin_id=uuid4(),
        destination_id=uuid4(),
        pickup_time=datetime.now(timezone.utc),
        delivery_time=datetime.now(timezone.utc),
        empty_driving_id=uuid4(),
        total_distance_km=Decimal("500.0"),
        total_duration_hours=Decimal("8.0"),
        is_feasible=True,
        status=RouteStatus.DRAFT
    )
    return route_repository_mock.save(route)


@pytest.fixture
def cost_breakdown(cost_breakdown_repository_mock, route) -> CostBreakdown:
    """Create and save a sample cost breakdown."""
    cost_breakdown = CostBreakdown(
        id=uuid4(),
        route_id=route.id,
        fuel_costs={"DE": Decimal("100.00"), "PL": Decimal("80.00")},
        toll_costs={"DE": Decimal("50.00"), "PL": Decimal("30.00")},
        driver_costs=Decimal("250.00"),
        overhead_costs=Decimal("100.00"),
        timeline_event_costs={
            "pickup": Decimal("50.00"),
            "delivery": Decimal("50.00")
        },
        total_cost=Decimal("710.00")
    )
    return cost_breakdown_repository_mock.save(cost_breakdown)


@pytest.fixture
def cargo(cargo_repository_mock) -> Cargo:
    """Create and save a sample cargo."""
    cargo = Cargo(
        id=uuid4(),
        business_entity_id=uuid4(),
        weight=1500.0,
        volume=10.0,
        cargo_type="general",
        value=Decimal("25000.00"),
        special_requirements=["temperature_controlled"],
        status="pending"
    )
    return cargo_repository_mock.save(cargo)


@pytest.fixture
def service(offer_repository_mock, offer_enhancer_mock, cargo_repository_mock, route_repository_mock, cost_breakdown_repository_mock, db_session_mock):
    """Create offer service with all required dependencies."""
    return OfferService(
        offer_repository_mock,
        offer_enhancer_mock,
        cargo_repository_mock,
        route_repository_mock,
        cost_breakdown_repository_mock,
        db_session_mock
    )


def test_create_offer_without_ai(service, cost_breakdown):
    """Test creating an offer without AI enhancement."""
    # Act
    offer = service.create_offer(
        route_id=cost_breakdown.route_id,
        cost_breakdown_id=cost_breakdown.id,
        margin_percentage=Decimal("15.0"),
        enhance_with_ai=False
    )
    
    # Assert
    assert offer.id is not None
    assert offer.route_id == cost_breakdown.route_id
    assert offer.cost_breakdown_id == cost_breakdown.id
    assert offer.margin_percentage == Decimal("15.0")
    assert offer.final_price > Decimal("0")
    assert offer.created_at is not None
    assert offer.ai_content is None
    assert offer.fun_fact is None


def test_create_offer_with_ai(service, cost_breakdown):
    """Test creating an offer with AI enhancement."""
    # Act
    offer = service.create_offer(
        route_id=cost_breakdown.route_id,
        cost_breakdown_id=cost_breakdown.id,
        margin_percentage=Decimal("15.0"),
        enhance_with_ai=True
    )
    
    # Assert
    assert offer.id is not None
    assert offer.route_id == cost_breakdown.route_id
    assert offer.cost_breakdown_id == cost_breakdown.id
    assert offer.margin_percentage == Decimal("15.0")
    assert offer.final_price > Decimal("0")
    assert offer.created_at is not None
    assert offer.ai_content is not None
    assert offer.fun_fact is not None


def test_get_existing_offer(service, cost_breakdown):
    """Test retrieving an existing offer."""
    # Create an offer first
    created_offer = service.create_offer(
        route_id=cost_breakdown.route_id,
        cost_breakdown_id=cost_breakdown.id,
        margin_percentage=Decimal("15.0"),
        enhance_with_ai=False
    )
    
    # Act
    retrieved_offer = service.get_offer(created_offer.id)
    
    # Assert
    assert retrieved_offer is not None
    assert retrieved_offer.id == created_offer.id
    assert retrieved_offer.route_id == cost_breakdown.route_id
    assert retrieved_offer.cost_breakdown_id == cost_breakdown.id
    assert retrieved_offer.margin_percentage == Decimal("15.0")


def test_get_nonexistent_offer(service):
    """Test retrieving a non-existent offer."""
    # Act
    offer = service.get_offer(uuid4())
    
    # Assert
    assert offer is None


def test_create_offer_margin_calculation(service, cost_breakdown):
    """Test margin calculation in offer creation."""
    # Act
    offer = service.create_offer(
        route_id=cost_breakdown.route_id,
        cost_breakdown_id=cost_breakdown.id,
        margin_percentage=Decimal("20.0"),
        enhance_with_ai=False
    )
    
    # Assert
    assert offer.id is not None
    assert offer.margin_percentage == Decimal("20.0")
    # Total cost is 710.00, with 20% margin should be 852.00
    assert offer.final_price == Decimal("852.00")


def test_finalize_offer_success(service, cost_breakdown, cargo):
    """Test finalizing an offer successfully."""
    # Create a route with the cargo
    route = Route(
        id=cost_breakdown.route_id,
        transport_id=uuid4(),
        business_entity_id=uuid4(),
        cargo_id=cargo.id,
        origin_id=uuid4(),
        destination_id=uuid4(),
        pickup_time=datetime.now(timezone.utc),
        delivery_time=datetime.now(timezone.utc),
        empty_driving_id=uuid4(),
        total_distance_km=Decimal("500.0"),
        total_duration_hours=Decimal("8.0"),
        is_feasible=True,
        status=RouteStatus.DRAFT
    )
    service.route_repository.save(route)

    # Create an offer
    offer = service.create_offer(
        route_id=route.id,
        cost_breakdown_id=cost_breakdown.id,
        margin_percentage=Decimal("15.0"),
        enhance_with_ai=False
    )
    
    # Act
    finalized_offer = service.finalize_offer(offer.id)
    
    # Assert
    assert finalized_offer is not None
    assert finalized_offer.status == "finalized"
    # Check that cargo status was updated
    updated_cargo = service.cargo_repository.find_by_id(cargo.id)
    assert updated_cargo.status == "in_transit"
    # Check that route status was updated
    updated_route = service.route_repository.find_by_id(route.id)
    assert updated_route.status == RouteStatus.PLANNED


def test_finalize_offer_invalid_cargo_state(service, cost_breakdown, cargo):
    """Test finalizing an offer with invalid cargo state."""
    # Set cargo to in_transit state
    cargo.status = "in_transit"
    service.cargo_repository.save(cargo)

    # Create a route with the cargo
    route = Route(
        id=cost_breakdown.route_id,
        transport_id=uuid4(),
        business_entity_id=uuid4(),
        cargo_id=cargo.id,
        origin_id=uuid4(),
        destination_id=uuid4(),
        pickup_time=datetime.now(timezone.utc),
        delivery_time=datetime.now(timezone.utc),
        empty_driving_id=uuid4(),
        total_distance_km=Decimal("500.0"),
        total_duration_hours=Decimal("8.0"),
        is_feasible=True,
        status=RouteStatus.DRAFT
    )
    service.route_repository.save(route)

    # Create an offer
    offer = service.create_offer(
        route_id=route.id,
        cost_breakdown_id=cost_breakdown.id,
        margin_percentage=Decimal("15.0"),
        enhance_with_ai=False
    )
    
    # Act & Assert
    with pytest.raises(ValueError, match="Cannot finalize offer: cargo is not in pending state"):
        service.finalize_offer(offer.id)


def test_finalize_offer_missing_cargo(service, cost_breakdown):
    """Test finalizing an offer with missing cargo."""
    # Create a route without cargo
    route = Route(
        id=cost_breakdown.route_id,
        transport_id=uuid4(),
        business_entity_id=uuid4(),
        cargo_id=None,
        origin_id=uuid4(),
        destination_id=uuid4(),
        pickup_time=datetime.now(timezone.utc),
        delivery_time=datetime.now(timezone.utc),
        empty_driving_id=uuid4(),
        total_distance_km=Decimal("500.0"),
        total_duration_hours=Decimal("8.0"),
        is_feasible=True,
        status=RouteStatus.DRAFT
    )
    service.route_repository.save(route)

    # Create an offer
    offer = service.create_offer(
        route_id=route.id,
        cost_breakdown_id=cost_breakdown.id,
        margin_percentage=Decimal("15.0"),
        enhance_with_ai=False
    )
    
    # Act & Assert
    with pytest.raises(ValueError, match="Route has no cargo assigned"):
        service.finalize_offer(offer.id) 