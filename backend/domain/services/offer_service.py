"""Offer service for managing offer-related business logic."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Protocol, Tuple
from uuid import UUID

from ..entities.cargo import CostBreakdown, Offer


class OfferRepository(Protocol):
    """Repository interface for Offer entity."""
    def save(self, offer: Offer) -> Offer:
        """Save an offer."""
        ...

    def find_by_id(self, id: UUID) -> Optional[Offer]:
        """Find an offer by ID."""
        ...


class ContentEnhancementPort(Protocol):
    """External service port for AI content enhancement."""
    def enhance_offer(self, offer: Offer) -> Tuple[str, str]:
        """Generate enhanced content and fun fact."""
        ...


class OfferService:
    """Service for managing offer-related business logic."""

    def __init__(
        self,
        offer_repo: OfferRepository,
        content_enhancer: ContentEnhancementPort
    ):
        self._offer_repo = offer_repo
        self._content_enhancer = content_enhancer

    def create_offer(
        self,
        route_id: UUID,
        cost_breakdown: CostBreakdown,
        margin_percentage: Decimal,
        enhance_with_ai: bool = False
    ) -> Offer:
        """Create a new offer with optional AI enhancement."""
        # Calculate final price with margin
        final_price = cost_breakdown.total_cost * (
            Decimal("1") + margin_percentage / Decimal("100")
        )

        # Create basic offer
        offer = Offer(
            id=UUID(),
            route_id=route_id,
            cost_breakdown_id=cost_breakdown.route_id,
            margin_percentage=margin_percentage,
            final_price=final_price,
            created_at=datetime.utcnow()
        )

        # Add AI enhancement if requested
        if enhance_with_ai:
            content, fun_fact = self._content_enhancer.enhance_offer(offer)
            offer.ai_content = content
            offer.fun_fact = fun_fact

        return self._offer_repo.save(offer)

    def get_offer(self, offer_id: UUID) -> Optional[Offer]:
        """Retrieve an offer by ID."""
        return self._offer_repo.find_by_id(offer_id) 