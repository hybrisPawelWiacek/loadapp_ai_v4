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

    def find_by_route_id(self, route_id: UUID) -> Optional[Offer]:
        """Find an offer by route ID."""
        for offer in self.offers.values():
            if offer.route_id == route_id:
                return offer
        return None


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
        total_cost=Decimal("710.00")
    )


def test_create_offer_without_ai(cost_breakdown):
    """Test creating an offer without AI enhancement."""
    # Arrange
    repo = MockOfferRepository()
    enhancer = MockContentEnhancer()
    service = OfferService(repo, enhancer)
    route_id = cost_breakdown.route_id
    margin_percentage = Decimal("15.0")
    
    # Act
    offer = service.create_offer(
        route_id=route_id,
        cost_breakdown_id=cost_breakdown.id,
        margin_percentage=margin_percentage,
        enhance_with_ai=False
    )
    
    # Assert
    assert offer.id is not None
    assert offer.route_id == route_id
    assert offer.cost_breakdown_id == cost_breakdown.id
    assert offer.margin_percentage == margin_percentage
    assert offer.final_price > Decimal("0")
    assert offer.created_at is not None
    assert offer.ai_content is None
    assert offer.fun_fact is None


def test_create_offer_with_ai(cost_breakdown):
    """Test creating an offer with AI enhancement."""
    # Arrange
    repo = MockOfferRepository()
    enhancer = MockContentEnhancer()
    service = OfferService(repo, enhancer)
    route_id = cost_breakdown.route_id
    margin_percentage = Decimal("15.0")
    
    # Act
    offer = service.create_offer(
        route_id=route_id,
        cost_breakdown_id=cost_breakdown.id,
        margin_percentage=margin_percentage,
        enhance_with_ai=True
    )
    
    # Assert
    assert offer.id is not None
    assert offer.route_id == route_id
    assert offer.cost_breakdown_id == cost_breakdown.id
    assert offer.margin_percentage == margin_percentage
    assert offer.final_price > Decimal("0")
    assert offer.created_at is not None
    assert offer.ai_content is not None
    assert offer.fun_fact is not None


def test_get_existing_offer(cost_breakdown):
    """Test retrieving an existing offer."""
    # Arrange
    repo = MockOfferRepository()
    enhancer = MockContentEnhancer()
    service = OfferService(repo, enhancer)
    route_id = cost_breakdown.route_id
    margin_percentage = Decimal("15.0")
    
    # Create an offer first
    created_offer = service.create_offer(
        route_id=route_id,
        cost_breakdown_id=cost_breakdown.id,
        margin_percentage=margin_percentage,
        enhance_with_ai=False
    )
    
    # Act
    retrieved_offer = service.get_offer(created_offer.id)
    
    # Assert
    assert retrieved_offer is not None
    assert retrieved_offer.id == created_offer.id
    assert retrieved_offer.route_id == route_id
    assert retrieved_offer.cost_breakdown_id == cost_breakdown.id
    assert retrieved_offer.margin_percentage == margin_percentage


def test_get_nonexistent_offer():
    """Test retrieving a non-existent offer."""
    # Arrange
    repo = MockOfferRepository()
    enhancer = MockContentEnhancer()
    service = OfferService(repo, enhancer)
    
    # Act
    offer = service.get_offer(uuid4())
    
    # Assert
    assert offer is None


def test_create_offer_margin_calculation(cost_breakdown):
    """Test margin calculation in offer creation."""
    # Arrange
    repo = MockOfferRepository()
    enhancer = MockContentEnhancer()
    service = OfferService(repo, enhancer)
    route_id = cost_breakdown.route_id
    margin_percentage = Decimal("20.0")
    
    # Act
    offer = service.create_offer(
        route_id=route_id,
        cost_breakdown_id=cost_breakdown.id,
        margin_percentage=margin_percentage,
        enhance_with_ai=False
    )
    
    # Assert
    assert offer.final_price == Decimal("1200.0")  # Base price 1000 * (1 + 20%) 