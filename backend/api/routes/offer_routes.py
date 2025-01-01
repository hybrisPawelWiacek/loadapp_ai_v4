"""Offer-related API routes."""
from decimal import Decimal
from uuid import UUID
from flask import Blueprint, jsonify, request, g, current_app
from flask_restful import Api

from ...domain.entities.cargo import CostBreakdown
from ...domain.services.offer_service import OfferService
from ...infrastructure.models.route_models import RouteModel
from ...infrastructure.repositories.route_repository import SQLRouteRepository
from ...infrastructure.repositories.cargo_repository import SQLCostBreakdownRepository, SQLOfferRepository
from ...infrastructure.adapters.openai_adapter import OpenAIAdapter


# Create blueprint
offer_bp = Blueprint("offer", __name__, url_prefix="/api/offer")
api = Api(offer_bp)


def get_container():
    """Get the container from the request context."""
    if not hasattr(g, 'container'):
        raise RuntimeError("Application container not initialized")
    return g.container


@offer_bp.route("/generate/<route_id>", methods=["POST"])
def generate_offer(route_id: str):
    """Generate an offer for a route."""
    data = request.get_json()
    db = g.db
    
    try:
        # Get container
        container = get_container()
        
        # Get route
        route = container.route_repository().find_by_id(UUID(route_id))
        if not route:
            return jsonify({"error": "Route not found"}), 404
        
        # Get cost breakdown
        cost_breakdown = container.cost_breakdown_repository().find_by_route_id(UUID(route_id))
        if not cost_breakdown:
            return jsonify({"error": "Cost breakdown not found for route"}), 404

        # Get margin percentage
        try:
            margin_percentage = Decimal(data.get("margin_percentage", "15.0"))
            if margin_percentage < 0:
                return jsonify({"error": "Invalid margin percentage"}), 400
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid margin percentage format"}), 400

        # Generate offer
        enhance_with_ai = data.get("enhance_with_ai", False)
        offer = container.offer_service().create_offer(
            route_id=UUID(route_id),
            cost_breakdown_id=cost_breakdown.id,
            margin_percentage=margin_percentage,
            enhance_with_ai=enhance_with_ai
        )
        
        return jsonify({"offer": offer.to_dict()}), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500


@offer_bp.route("/<offer_id>/enhance", methods=["POST"])
def enhance_offer(offer_id: str):
    """Enhance an existing offer with AI-generated content."""
    db = g.db
    
    try:
        # Get container
        container = get_container()
        
        # Enhance offer
        enhanced_offer = container.offer_service().enhance_offer(UUID(offer_id))
        if not enhanced_offer:
            return jsonify({"error": "Offer not found"}), 404
            
        return jsonify({"offer": enhanced_offer.to_dict()}), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Failed to enhance offer: {str(e)}"}), 500


@offer_bp.route("/<offer_id>", methods=["GET"])
def get_offer(offer_id: str):
    """Get an offer by ID."""
    try:
        # Get container
        container = get_container()
        
        # Get offer
        offer = container.offer_service().get_offer(UUID(offer_id))
        if not offer:
            return jsonify({"error": "Offer not found"}), 404
            
        return jsonify({"offer": offer.to_dict()}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500 