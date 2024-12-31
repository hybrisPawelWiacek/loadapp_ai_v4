"""Tests for offer service."""
import pytest
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Optional, Tuple
from uuid import UUID, uuid4

from backend.domain.services.offer_service import OfferService
from backend.domain.entities.cargo import CostBreakdown, Offer


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


class MockContentEnhancer:
    """Mock service for AI content enhancement."""
    
    def enhance_offer(self, offer: Offer) -> Tuple[str, str]:
        """Generate enhanced content and fun fact."""
        return (
            f"Enhanced offer description for route {offer.route_id}",
            f"Fun fact about transport with price {offer.final_price}"
        )


@pytest.fixture
def cost_breakdown() -> CostBreakdown:
    """Create sample cost breakdown."""
    return CostBreakdown(
        id=uuid4(),
        route_id=uuid4(),
        fuel_costs={"DE": Decimal("100.00"), "PL": Decimal("80.00")},
        toll_costs={"DE": Decimal("50.00"), "PL": Decimal("30.00")},
        driver_costs=Decimal("250.00"),
        overhead_costs=Decimal("100.00"),
        timeline_event_costs={
            "pickup": Decimal("50.00"),
            "delivery": Decimal("50.00")
        },
        total_cost=Decimal("710.00")  # Sum of all costs
    )


@pytest.fixture
def offer_repo() -> MockOfferRepository:
    """Create mock offer repository."""
    return MockOfferRepository()


@pytest.fixture
def content_enhancer() -> MockContentEnhancer:
    """Create mock content enhancer."""
    return MockContentEnhancer()


@pytest.fixture
def offer_service(
    offer_repo,
    content_enhancer
) -> OfferService:
    """Create offer service with mock dependencies."""
    return OfferService(
        offer_repo=offer_repo,
        content_enhancer=content_enhancer
    )


def test_create_offer_without_ai(
    offer_service,
    cost_breakdown
):
    """Test creating an offer without AI enhancement."""
    # Arrange
    route_id = uuid4()
    margin_percentage = Decimal("15.00")  # 15% margin
    expected_price = Decimal("816.50")  # 710.00 * 1.15
    
    # Act
    offer = offer_service.create_offer(
        route_id=route_id,
        cost_breakdown=cost_breakdown,
        margin_percentage=margin_percentage,
        enhance_with_ai=False
    )
    
    # Assert
    assert offer is not None
    assert isinstance(offer.id, UUID)
    assert offer.route_id == route_id
    assert offer.cost_breakdown_id == cost_breakdown.route_id
    assert offer.margin_percentage == margin_percentage
    assert offer.final_price == expected_price
    assert offer.ai_content is None
    assert offer.fun_fact is None
    assert isinstance(offer.created_at, datetime)


def test_create_offer_with_ai(
    offer_service,
    cost_breakdown
):
    """Test creating an offer with AI enhancement."""
    # Arrange
    route_id = uuid4()
    margin_percentage = Decimal("20.00")  # 20% margin
    expected_price = Decimal("852.00")  # 710.00 * 1.20
    
    # Act
    offer = offer_service.create_offer(
        route_id=route_id,
        cost_breakdown=cost_breakdown,
        margin_percentage=margin_percentage,
        enhance_with_ai=True
    )
    
    # Assert
    assert offer is not None
    assert isinstance(offer.id, UUID)
    assert offer.route_id == route_id
    assert offer.cost_breakdown_id == cost_breakdown.route_id
    assert offer.margin_percentage == margin_percentage
    assert offer.final_price == expected_price
    assert offer.ai_content is not None
    assert offer.fun_fact is not None
    assert isinstance(offer.created_at, datetime)
    assert f"route {route_id}" in offer.ai_content
    assert str(expected_price) in offer.fun_fact


def test_get_existing_offer(
    offer_service,
    cost_breakdown
):
    """Test retrieving an existing offer."""
    # Arrange
    route_id = uuid4()
    margin_percentage = Decimal("10.00")
    offer = offer_service.create_offer(
        route_id=route_id,
        cost_breakdown=cost_breakdown,
        margin_percentage=margin_percentage
    )
    
    # Act
    retrieved_offer = offer_service.get_offer(offer.id)
    
    # Assert
    assert retrieved_offer is not None
    assert retrieved_offer.id == offer.id
    assert retrieved_offer.route_id == route_id
    assert retrieved_offer.margin_percentage == margin_percentage


def test_get_nonexistent_offer(offer_service):
    """Test retrieving a non-existent offer."""
    # Act
    offer = offer_service.get_offer(uuid4())
    
    # Assert
    assert offer is None


def test_create_offer_margin_calculation(
    offer_service,
    cost_breakdown
):
    """Test margin percentage calculations for different values."""
    test_cases = [
        (Decimal("0.00"), Decimal("710.00")),   # No margin
        (Decimal("10.00"), Decimal("781.00")),  # 10% margin
        (Decimal("25.00"), Decimal("887.50")),  # 25% margin
        (Decimal("50.00"), Decimal("1065.00")), # 50% margin
        (Decimal("100.00"), Decimal("1420.00")) # 100% margin
    ]
    
    for margin, expected_price in test_cases:
        # Act
        offer = offer_service.create_offer(
            route_id=uuid4(),
            cost_breakdown=cost_breakdown,
            margin_percentage=margin
        )
        
        # Assert
        assert offer.margin_percentage == margin
        assert offer.final_price == expected_price 