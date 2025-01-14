"""Offer service for managing offer-related business logic."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Protocol, Tuple
from uuid import UUID, uuid4
import logging
from sqlalchemy.orm import Session

from ..entities.cargo import CostBreakdown, Offer, Cargo
from ..entities.route import Route, RouteStatus
from ...infrastructure.models.cargo_models import CargoStatusHistoryModel
from ...infrastructure.models.route_models import RouteStatusHistoryModel
from ...infrastructure.models.cargo_models import OfferStatusHistoryModel


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


class CostBreakdownRepository(Protocol):
    """Repository interface for CostBreakdown entity."""
    def find_by_id(self, id: UUID) -> Optional[CostBreakdown]:
        """Find a cost breakdown by ID."""
        ...

    def find_by_route_id(self, route_id: UUID) -> Optional[CostBreakdown]:
        """Find a cost breakdown by route ID."""
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
        route_repository: RouteRepository,
        cost_breakdown_repository: CostBreakdownRepository,
        db: Session
    ):
        self.repository = offer_repository
        self.enhancer = offer_enhancer
        self.cargo_repository = cargo_repository
        self.route_repository = route_repository
        self.cost_breakdown_repository = cost_breakdown_repository
        self.db = db

    def validate_margin_percentage(self, margin: Decimal) -> None:
        """Validate margin percentage."""
        if margin < 0:
            raise ValueError("Margin percentage cannot be negative")

    def create_offer(
        self,
        route_id: UUID,
        cost_breakdown_id: UUID,
        margin_percentage: Decimal,
        enhance_with_ai: bool = False
    ) -> Offer:
        """Create a new offer with optional AI enhancement."""
        # Validate margin percentage
        self.validate_margin_percentage(margin_percentage)

        # Validate route exists
        route = self.route_repository.find_by_id(route_id)
        if not route:
            raise ValueError("Route not found")

        # Get cost breakdown
        cost_breakdown = self.cost_breakdown_repository.find_by_id(cost_breakdown_id)
        if not cost_breakdown:
            raise ValueError("Cost breakdown not found")

        # Calculate final price based on cost breakdown and margin
        final_price = self._calculate_final_price(cost_breakdown.total_cost, margin_percentage)

        # Create basic offer
        offer = Offer(
            id=uuid4(),
            route_id=route_id,
            cost_breakdown_id=cost_breakdown_id,
            margin_percentage=margin_percentage,
            final_price=final_price,
            created_at=datetime.utcnow(),
            status="draft"
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
        logging.info(f"Starting offer finalization process for ID: {offer_id}")
        
        # Get the offer first
        offer = self.repository.find_by_id(offer_id)
        if not offer:
            logging.error(f"Offer not found with ID: {offer_id}")
            return None

        logging.info(f"Found offer: ID={offer.id}, Status={offer.status}, Route ID={offer.route_id}")

        # Validate offer state
        if offer.status != "draft":
            logging.error(f"Invalid offer status for finalization: {offer.status}")
            raise ValueError(f"Cannot finalize offer in {offer.status} state")

        # Get the route through the offer's route_id
        route = self.route_repository.find_by_id(offer.route_id)
        if not route:
            logging.error(f"Route not found for offer: {offer.route_id}")
            raise ValueError("Route not found for offer")

        logging.info(f"Found route: ID={route.id}, Status={route.status}, Cargo ID={route.cargo_id}")

        # Get the cargo through the route
        if not route.cargo_id:
            logging.error("Route has no cargo assigned")
            raise ValueError("Route has no cargo assigned")

        cargo = self.cargo_repository.find_by_id(route.cargo_id)
        if not cargo:
            logging.error(f"Cargo not found for route: {route.cargo_id}")
            raise ValueError("Cargo not found for route")

        logging.info(f"Found cargo: ID={cargo.id}, Status={cargo.status}, Business Entity ID={cargo.business_entity_id}")

        # Validate cargo status
        if cargo.status != "pending":
            logging.error(f"Invalid cargo status for finalization: {cargo.status}")
            raise ValueError(f"Cannot finalize offer: cargo is not in pending state")

        # Update all entities
        try:
            logging.info("Starting entity updates for finalization")
            
            # Update cargo status first
            logging.info(f"Updating cargo status: {cargo.id} -> in_transit")
            cargo.status = "in_transit"
            updated_cargo = self.cargo_repository.save(cargo)
            logging.info(f"Cargo updated successfully: {updated_cargo.id}, Status={updated_cargo.status}")

            # Track status change
            status_history = CargoStatusHistoryModel(
                id=str(uuid4()),
                cargo_id=str(cargo.id),
                old_status="pending",
                new_status="in_transit",
                trigger="offer_finalization",
                trigger_id=str(offer.id),
                details={
                    "offer_id": str(offer.id),
                    "route_id": str(route.id),
                    "final_price": str(offer.final_price)
                }
            )
            self.db.add(status_history)
            
            # Update route status
            logging.info(f"Updating route status: {route.id} -> planned")
            route.status = RouteStatus.PLANNED
            updated_route = self.route_repository.save(route)
            logging.info(f"Route updated successfully: {updated_route.id}, Status={updated_route.status}")

            # Update offer status last
            logging.info(f"Updating offer status: {offer.id} -> finalized")
            offer.status = "finalized"
            offer.finalized_at = datetime.utcnow()
            updated_offer = self.repository.save(offer)
            logging.info(f"Offer updated successfully: {updated_offer.id}, Status={updated_offer.status}")

            return updated_offer

        except Exception as e:
            logging.error(f"Error during finalization: {str(e)}")
            logging.info("Starting rollback process")
            
            # Rollback any changes if something fails
            if cargo.status == "in_transit":
                logging.info(f"Rolling back cargo status: {cargo.id} -> pending")
                cargo.status = "pending"
                self.cargo_repository.save(cargo)
                
            if route.status == RouteStatus.PLANNED:
                logging.info(f"Rolling back route status: {route.id} -> draft")
                route.status = RouteStatus.DRAFT
                self.route_repository.save(route)
                
            raise ValueError(f"Failed to finalize offer: {str(e)}")

    def _calculate_final_price(self, total_cost: Decimal, margin_percentage: Decimal) -> Decimal:
        """Calculate final price with margin."""
        if isinstance(total_cost, str):
            total_cost = Decimal(total_cost)
        margin_multiplier = Decimal("1.0") + (margin_percentage / Decimal("100.0"))
        return total_cost * margin_multiplier 

    def update_status(self, offer_id: UUID, new_status: str, comment: Optional[str] = None) -> Optional[Offer]:
        """Update an offer's status and record the change in history."""
        # Get offer
        offer = self.get_offer(offer_id)
        if not offer:
            raise ValueError("Offer not found")

        # Validate status transition
        self._validate_status_transition(offer.status, new_status)

        old_status = offer.status
        offer.status = new_status

        # Create status history entry
        history_entry = OfferStatusHistoryModel(
            id=str(uuid4()),
            offer_id=str(offer_id),
            old_status=old_status,
            new_status=new_status,
            trigger="manual_update",
            details={"comment": comment} if comment else None
        )
        self.db.add(history_entry)

        try:
            # Save changes
            updated_offer = self.repository.save(offer)
            self.db.commit()
            return updated_offer
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to update offer status: {str(e)}")

    def get_status_history(self, offer_id: UUID) -> list:
        """Get the status history of an offer."""
        # Check if offer exists
        offer = self.get_offer(offer_id)
        if not offer:
            raise ValueError("Offer not found")

        # Get history entries ordered by timestamp
        history = (self.db.query(OfferStatusHistoryModel)
                  .filter(OfferStatusHistoryModel.offer_id == str(offer_id))
                  .order_by(OfferStatusHistoryModel.timestamp.desc())
                  .all())

        return [{
            "id": str(entry.id),
            "status": entry.new_status,
            "timestamp": entry.timestamp.isoformat(),
            "comment": entry.get_details().get("comment") if entry.details else None
        } for entry in history]

    def _validate_status_transition(self, current_status: str, new_status: str) -> None:
        """Validate if a status transition is allowed."""
        # Define allowed transitions
        allowed_transitions = {
            "draft": ["finalized", "cancelled"],
            "finalized": ["completed", "cancelled"],
            "cancelled": [],  # No transitions allowed from cancelled
            "completed": []   # No transitions allowed from completed
        }

        if current_status not in allowed_transitions:
            raise ValueError(f"Invalid current status: {current_status}")

        if new_status not in allowed_transitions[current_status]:
            raise ValueError(
                f"Invalid status transition from {current_status} to {new_status}. "
                f"Allowed transitions: {allowed_transitions[current_status]}"
            ) 