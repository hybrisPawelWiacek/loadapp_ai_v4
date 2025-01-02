"""Offer service for managing offer-related business logic."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Protocol, Tuple
from uuid import UUID, uuid4

from ..entities.cargo import CostBreakdown, Offer, Cargo
from ..entities.route import Route


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


class CargoRepository(Protocol):
    """Repository interface for Cargo entity."""
    def find_by_id(self, id: UUID) -> Optional[Cargo]:
        """Find a cargo by ID."""
        ...

    def save(self, cargo: Cargo) -> Cargo:
        """Save a cargo."""
        ...


class RouteRepository(Protocol):
    """Repository interface for Route entity."""
    def find_by_id(self, id: UUID) -> Optional[Route]:
        """Find a route by ID."""
        ...

    def find_by_cargo_id(self, cargo_id: UUID) -> Optional[Route]:
        """Find a route by cargo ID."""
        ...

    def save(self, route: Route) -> Route:
        """Save a route."""
        ...


class OfferService:
    """Service for managing offer-related business logic."""

    def __init__(
        self,
        offer_repository: OfferRepository,
        offer_enhancer: ContentEnhancementPort,
        cargo_repository: CargoRepository,
        route_repository: RouteRepository
    ):
        self.repository = offer_repository
        self.enhancer = offer_enhancer
        self.cargo_repository = cargo_repository
        self.route_repository = route_repository

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
            content, fun_fact = self.enhancer.enhance_offer(offer)
            offer.ai_content = content
            offer.fun_fact = fun_fact

        return self.repository.save(offer)

    def get_offer(self, offer_id: UUID) -> Optional[Offer]:
        """Retrieve an offer by ID."""
        return self.repository.find_by_id(offer_id)

    def enhance_offer(self, offer_id: UUID) -> Optional[Offer]:
        """Enhance an offer with AI content."""
        # Get the existing offer
        offer = self.get_offer(offer_id)
        if not offer:
            return None

        try:
            # Generate AI content
            content, fun_fact = self.enhancer.enhance_offer(offer)
            
            # Update the offer
            offer.ai_content = content
            offer.fun_fact = fun_fact
            
            # Save and return the updated offer
            return self.repository.save(offer)
        except Exception as e:
            raise ValueError(f"Failed to enhance offer: {str(e)}")

    def finalize_offer(self, offer_id: UUID) -> Optional[Offer]:
        """Finalize an offer and update related entities."""
        # Get the offer
        offer = self.get_offer(offer_id)
        if not offer:
            return None

        # Get the route
        route = self.route_repository.find_by_id(offer.route_id)
        if not route:
            raise ValueError("Route not found for offer")

        # Check if route has a cargo
        if not route.cargo_id:
            raise ValueError("Route has no cargo assigned")

        # Get the cargo
        cargo = self.cargo_repository.find_by_id(route.cargo_id)
        if not cargo:
            raise ValueError("Cargo not found for route")

        # Validate cargo status
        if cargo.status != "pending":
            raise ValueError("Cannot finalize offer: cargo is not in pending state")

        # Update cargo status
        cargo.status = "in_transit"
        self.cargo_repository.save(cargo)

        # Update route status
        route.status = "planned"
        self.route_repository.save(route)

        # Update offer status
        offer.status = "finalized"
        return self.repository.save(offer)

    def _calculate_final_price(self, margin_percentage: Decimal) -> Decimal:
        """Calculate the final price with margin."""
        base_price = Decimal("1000")  # Example base price
        return base_price * (Decimal("1") + margin_percentage / Decimal("100")) 