"""Offer service for managing offer-related business logic."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Protocol, Tuple
from uuid import UUID, uuid4

from ..entities.cargo import CostBreakdown, Offer


class OfferRepository(Protocol):
    """Repository interface for Offer entity."""
    def save(self, offer: Offer) -> Offer:
        """Save an offer."""
        ...

    def find_by_id(self, id: UUID) -> Optional[Offer]:
        """Find an offer by ID."""
        ...

    def find_by_route_id(self, route_id: UUID) -> Optional[Offer]:
        """Find an offer by route ID."""
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
        cost_breakdown_id: UUID,
        margin_percentage: Decimal,
        enhance_with_ai: bool = False
    ) -> Offer:
        """Create a new offer with optional AI enhancement."""
        # Create basic offer
        offer = Offer(
            id=uuid4(),
            route_id=route_id,
            cost_breakdown_id=cost_breakdown_id,
            margin_percentage=margin_percentage,
            final_price=self._calculate_final_price(margin_percentage),
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

    def enhance_offer(self, offer_id: UUID) -> Optional[Offer]:
        """Enhance an offer with AI content."""
        # Get the existing offer
        offer = self.get_offer(offer_id)
        if not offer:
            return None

        try:
            # Generate AI content
            content, fun_fact = self._content_enhancer.enhance_offer(offer)
            
            # Update the offer
            offer.ai_content = content
            offer.fun_fact = fun_fact
            
            # Save and return the updated offer
            return self._offer_repo.save(offer)
        except Exception as e:
            raise ValueError(f"Failed to enhance offer: {str(e)}")

    def _calculate_final_price(self, margin_percentage: Decimal) -> Decimal:
        """Calculate the final price with margin."""
        base_price = Decimal("1000")  # Example base price
        return base_price * (Decimal("1") + margin_percentage / Decimal("100")) 