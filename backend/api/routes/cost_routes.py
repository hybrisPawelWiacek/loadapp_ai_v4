"""Cost-related API routes."""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from uuid import UUID
from flask import Blueprint, jsonify, request, g
from flask_restful import Api, Resource
from typing import Dict, Any, Optional
from werkzeug.exceptions import HTTPException
import traceback

from ...domain.entities.cargo import (
    CostSettings,
    CostBreakdown,
    CostSettingsCreate,
    CostSettingsPartialUpdate
)
from ...domain.services.cost_service import CostService
from ...infrastructure.database import db_session
from ...infrastructure.container import get_container
import structlog

# Configure logger
logger = structlog.get_logger()

# Create blueprint
cost_bp = Blueprint("cost", __name__, url_prefix="/api/cost")
api = Api(cost_bp)


def get_db():
    """Get the database session."""
    if 'db' in g:
        return g.db
    return db_session


@cost_bp.route("/settings/<route_id>", methods=["POST"])
def create_cost_settings(route_id: str):
    """Create cost settings for a route."""
    print(f"[DEBUG] Received request to create cost settings for route_id: {route_id}")
    data = request.get_json()
    print(f"[DEBUG] Request data: {data}")
    db = get_db()
    
    try:
        # Get container
        container = get_container()
        cost_service = container.cost_service()
        route_service = container.route_service()
        
        # Validate route exists
        route = route_service.get_route(UUID(route_id))
        print(f"[DEBUG] Found route: {route}")
        if not route:
            print(f"[DEBUG] Route not found: {route_id}")
            return jsonify({"error": "Route not found"}), 404
        
        print(f"[DEBUG] Route business entity: {route.business_entity_id}")
        
        # Create settings
        settings_create = CostSettingsCreate(
            enabled_components=data.get("enabled_components", []),
            rates={k: Decimal(str(v)) for k, v in data.get("rates", {}).items()}
        )
        print(f"[DEBUG] Created settings object: {settings_create}")
        
        settings = cost_service.create_cost_settings(
            route_id=UUID(route_id),
            settings=settings_create,
            business_entity_id=UUID(str(route.business_entity_id))
        )
        print(f"[DEBUG] Settings created successfully: {settings}")
        
        # Convert to response format
        response = {
            "id": str(settings.id),
            "route_id": str(settings.route_id),
            "business_entity_id": str(settings.business_entity_id),
            "enabled_components": settings.enabled_components,
            "rates": {k: str(v) for k, v in settings.rates.items()}
        }
        print(f"[DEBUG] Prepared response: {response}")
        
        return jsonify(response), 200
        
    except ValueError as e:
        print(f"[DEBUG] ValueError occurred: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"[DEBUG] Unexpected error occurred: {str(e)}")
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        if hasattr(db, 'rollback'):
            db.rollback()
        return jsonify({"error": str(e)}), 500


@cost_bp.route("/settings/<route_id>", methods=["PUT"])
def update_cost_settings(route_id: str):
    """Update cost settings for a route."""
    data = request.get_json()
    db = get_db()
    
    try:
        # Get container
        container = get_container()
        cost_service = container.cost_service()
        route_service = container.route_service()
        
        # Validate route exists
        route = route_service.get_route(UUID(route_id))
        if not route:
            return jsonify({"error": "Route not found"}), 404
        
        # Update settings
        updated_settings = cost_service.update_cost_settings(
            route_id=UUID(route_id),
            updates=data
        )
        
        # Convert to response format
        response = {
            "id": str(updated_settings.id),
            "route_id": str(updated_settings.route_id),
            "enabled_components": updated_settings.enabled_components,
            "rates": {k: str(v) for k, v in updated_settings.rates.items()}
        }
        
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        if hasattr(db, 'rollback'):
            db.rollback()
        return jsonify({"error": str(e)}), 500


@cost_bp.route("/settings/<route_id>", methods=["GET"])
def get_cost_settings(route_id: str):
    """Get cost settings for a route."""
    db = get_db()
    
    try:
        # Get container
        container = get_container()
        cost_service = container.cost_service()
        route_service = container.route_service()
        
        # Validate route exists
        route = route_service.get_route(UUID(route_id))
        if not route:
            return jsonify({"error": "Route not found"}), 404
        
        # Get settings
        settings = cost_service._settings_repo.find_by_route_id(UUID(route_id))
        if not settings:
            return jsonify({"error": "Cost settings not found. Please create settings first."}), 404
        
        # Convert to response format
        response = {
            "id": str(settings.id),
            "route_id": str(settings.route_id),
            "enabled_components": settings.enabled_components,
            "rates": {k: str(v) for k, v in settings.rates.items()}
        }
        
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        if hasattr(db, 'rollback'):
            db.rollback()
        return jsonify({"error": str(e)}), 500


@cost_bp.route("/calculate/<route_id>", methods=["POST"])
def calculate_costs(route_id: str):
    """Calculate costs for a route."""
    db = get_db()
    
    try:
        # Get container
        container = get_container()
        cost_service = container.cost_service()
        route_service = container.route_service()
        
        # Validate route exists
        route = route_service.get_route(UUID(route_id))
        if not route:
            return jsonify({"error": "Route not found"}), 404
        
        # Calculate and save costs
        breakdown = cost_service.calculate_and_save_costs(
            route_id=UUID(route_id),
            transport_id=route.transport_id,
            business_entity_id=route.business_entity_id
        )
        
        # Convert to response format
        response = {
            "breakdown": {
                "id": str(breakdown.id),
                "route_id": str(breakdown.route_id),
                "fuel_costs": {k: str(v) for k, v in breakdown.fuel_costs.items()},
                "toll_costs": {k: str(v) for k, v in breakdown.toll_costs.items()},
                "driver_costs": {k: str(v) for k, v in breakdown.driver_costs.items()},
                "overhead_costs": str(breakdown.overhead_costs),
                "timeline_event_costs": {k: str(v) for k, v in breakdown.timeline_event_costs.items()},
                "total_cost": str(breakdown.total_cost)
            }
        }
        
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        if hasattr(db, 'rollback'):
            db.rollback()
        return jsonify({"error": str(e)}), 500


@cost_bp.route("/breakdown/<route_id>", methods=["GET"])
def get_cost_breakdown(route_id: str):
    """Get cost breakdown for a route."""
    db = get_db()
    
    try:
        # Get container
        container = get_container()
        cost_service = container.cost_service()
        route_service = container.route_service()
        
        # Validate route exists
        route = route_service.get_route(UUID(route_id))
        if not route:
            return jsonify({"error": "Route not found"}), 404
        
        # Get breakdown
        breakdown = cost_service.get_cost_breakdown(UUID(route_id))
        if not breakdown:
            return jsonify({"error": "Cost breakdown not found. Please calculate costs first."}), 404
        
        # Convert to response format
        response = {
            "breakdown": {
                "id": str(breakdown.id),
                "route_id": str(breakdown.route_id),
                "fuel_costs": {k: str(v) for k, v in breakdown.fuel_costs.items()},
                "toll_costs": {k: str(v) for k, v in breakdown.toll_costs.items()},
                "driver_costs": {k: str(v) for k, v in breakdown.driver_costs.items()},
                "overhead_costs": str(breakdown.overhead_costs),
                "timeline_event_costs": {k: str(v) for k, v in breakdown.timeline_event_costs.items()},
                "total_cost": str(breakdown.total_cost)
            }
        }
        
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        if hasattr(db, 'rollback'):
            db.rollback()
        return jsonify({"error": str(e)}), 500


@cost_bp.route("/settings/<target_route_id>/clone", methods=["POST"])
def clone_settings(target_route_id: str):
    """Clone cost settings from one route to another."""
    data = request.get_json()
    db = get_db()
    
    try:
        # Validate required fields
        if "source_route_id" not in data:
            return jsonify({"error": "source_route_id is required"}), 400
            
        # Get container
        container = get_container()
        cost_service = container.cost_service()
        route_service = container.route_service()
        
        # Validate routes exist
        target_route = route_service.get_route(UUID(target_route_id))
        source_route = route_service.get_route(UUID(data["source_route_id"]))
        
        if not target_route or not source_route:
            return jsonify({"error": "Source or target route not found"}), 404
            
        # Process rate modifications if provided
        rate_modifications = None
        if "rate_modifications" in data:
            try:
                rate_modifications = {
                    k: Decimal(str(v)) for k, v in data["rate_modifications"].items()
                }
            except (ValueError, InvalidOperation) as e:
                return jsonify({"error": f"Invalid rate value: {str(e)}"}), 400
        
        # Clone settings
        settings = cost_service.clone_cost_settings(
            source_route_id=UUID(data["source_route_id"]),
            target_route_id=UUID(target_route_id),
            rate_modifications=rate_modifications
        )
        
        # Convert to response format
        response = {
            "settings": {
                "id": str(settings.id),
                "route_id": str(settings.route_id),
                "business_entity_id": str(settings.business_entity_id),
                "enabled_components": settings.enabled_components,
                "rates": {k: str(v) for k, v in settings.rates.items()}
            }
        }
        
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        if hasattr(db, 'rollback'):
            db.rollback()
        return jsonify({"error": str(e)}), 500


@cost_bp.route("/settings/<route_id>", methods=["PATCH"])
def update_cost_settings_partial(route_id: str):
    """Partially update cost settings for a route."""
    data = request.get_json()
    db = get_db()
    
    try:
        # Get container
        container = get_container()
        cost_service = container.cost_service()
        route_service = container.route_service()
        
        # Validate route exists
        route = route_service.get_route(UUID(route_id))
        if not route:
            return jsonify({"error": "Route not found"}), 404
            
        # Process rates if present
        if "rates" in data:
            try:
                data["rates"] = {
                    k: Decimal(str(v)) for k, v in data["rates"].items()
                }
            except (ValueError, InvalidOperation) as e:
                return jsonify({"error": f"Invalid rate value: {str(e)}"}), 400
        
        # Update settings
        updated_settings = cost_service.update_cost_settings_partial(
            route_id=UUID(route_id),
            updates=data
        )
        
        # Convert to response format
        response = {
            "id": str(updated_settings.id),
            "route_id": str(updated_settings.route_id),
            "business_entity_id": str(updated_settings.business_entity_id),
            "enabled_components": updated_settings.enabled_components,
            "rates": {k: str(v) for k, v in updated_settings.rates.items()}
        }
        
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        if hasattr(db, 'rollback'):
            db.rollback()
        return jsonify({"error": str(e)}), 500 