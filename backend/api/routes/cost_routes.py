"""Cost-related API routes."""
from decimal import Decimal
from uuid import UUID
from flask import Blueprint, jsonify, request, g
from flask_restful import Api, Resource
from typing import Dict, Any

from ...domain.entities.cargo import CostSettings, CostBreakdown
from ...domain.services.cost_service import CostService
from ...infrastructure.database import db_session
from ...infrastructure.models.route_models import RouteModel
from ...infrastructure.models.transport_models import TransportModel
from ...infrastructure.models.business_models import BusinessEntityModel
from ...infrastructure.repositories.route_repository import SQLRouteRepository, SQLEmptyDrivingRepository
from ...infrastructure.repositories.business_repository import SQLBusinessRepository
from ...infrastructure.repositories.transport_repository import SQLTransportRepository
from ...infrastructure.repositories.cargo_repository import (
    SQLCostSettingsRepository,
    SQLCostBreakdownRepository
)
from ...infrastructure.adapters.toll_rate_adapter import TollRateAdapter
from ...infrastructure.external_services.toll_rate_service import TollRateService


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
    data = request.get_json()
    db = get_db()
    
    try:
        # Validate route exists
        route = db.query(RouteModel).filter_by(id=route_id).first()
        if not route:
            return jsonify({"error": "Route not found"}), 404
        
        # Initialize services
        cost_service = CostService(
            settings_repo=SQLCostSettingsRepository(db),
            breakdown_repo=SQLCostBreakdownRepository(db),
            empty_driving_repo=SQLEmptyDrivingRepository(db),
            toll_calculator=TollRateAdapter(TollRateService())
        )
        
        # Create settings
        settings = cost_service.create_cost_settings(
            route_id=UUID(route_id),
            business_entity_id=UUID(route.business_entity_id),
            enabled_components=data.get("enabled_components", []),
            rates={k: Decimal(str(v)) for k, v in data.get("rates", {}).items()}
        )
        
        if not settings:
            return jsonify({"error": "Failed to create cost settings"}), 500
        
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


@cost_bp.route("/settings/<route_id>", methods=["PUT"])
def update_cost_settings(route_id: str):
    """Update cost settings for a route."""
    data = request.get_json()
    db = get_db()
    
    try:
        # Validate route exists
        route = db.query(RouteModel).filter_by(id=route_id).first()
        if not route:
            return jsonify({"error": "Route not found"}), 404
        
        # Initialize repositories
        settings_repo = SQLCostSettingsRepository(db)
        
        # Get existing settings
        settings = settings_repo.find_by_route_id(UUID(route_id))
        if not settings:
            return jsonify({"error": "Cost settings not found. Please create settings first."}), 404
        
        # Update settings
        settings.enabled_components = data.get("enabled_components", settings.enabled_components)
        settings.rates = {
            k: Decimal(str(v)) for k, v in data.get("rates", settings.rates).items()
        }
        
        # Save updated settings
        updated_settings = settings_repo.save(settings)
        
        # Convert to response format
        response = {
            "settings": {
                "id": str(updated_settings.id),
                "route_id": str(updated_settings.route_id),
                "business_entity_id": str(updated_settings.business_entity_id),
                "enabled_components": updated_settings.enabled_components,
                "rates": {k: str(v) for k, v in updated_settings.rates.items()}
            }
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
        # Initialize repositories
        route_repo = SQLRouteRepository(db)
        transport_repo = SQLTransportRepository(db)
        business_repo = SQLBusinessRepository(db)
        
        # Get route and related entities
        route = route_repo.find_by_id(UUID(route_id))
        if not route:
            return jsonify({"error": "Route not found"}), 404
            
        # Get transport
        transport = transport_repo.find_by_id(route.transport_id)
        if not transport:
            return jsonify({"error": "Transport not found"}), 404
            
        # Get business entity
        business = business_repo.find_by_id(route.business_entity_id)
        if not business:
            return jsonify({"error": "Business entity not found"}), 404
            
        # Initialize services
        cost_service = CostService(
            settings_repo=SQLCostSettingsRepository(db),
            breakdown_repo=SQLCostBreakdownRepository(db),
            empty_driving_repo=SQLEmptyDrivingRepository(db),
            toll_calculator=TollRateAdapter(TollRateService())
        )
        
        try:
            # Calculate costs
            breakdown = cost_service.calculate_costs(
                route=route,
                transport=transport,
                business=business
            )
            
            if not breakdown:
                return jsonify({"error": "Failed to calculate costs"}), 500
            
            # Convert to response format
            response = {
                "breakdown": {
                    "id": str(breakdown.id),
                    "route_id": str(breakdown.route_id),
                    "fuel_costs": {k: str(v) for k, v in breakdown.fuel_costs.items()},
                    "toll_costs": {k: str(v) for k, v in breakdown.toll_costs.items()},
                    "driver_costs": str(breakdown.driver_costs),
                    "overhead_costs": str(breakdown.overhead_costs),
                    "timeline_event_costs": {k: str(v) for k, v in breakdown.timeline_event_costs.items()},
                    "total_cost": str(breakdown.total_cost)
                }
            }
            
            return jsonify(response), 200
            
        except ValueError as e:
            print(f"ValueError in cost calculation: {str(e)}")  # Add logging
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            print(f"Unexpected error in cost calculation: {str(e)}")  # Add logging
            if hasattr(db, 'rollback'):
                db.rollback()
            return jsonify({"error": str(e)}), 500
            
    except ValueError as e:
        print(f"ValueError in route loading: {str(e)}")  # Add logging
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"Unexpected error in route loading: {str(e)}")  # Add logging
        if hasattr(db, 'rollback'):
            db.rollback()
        return jsonify({"error": str(e)}), 500


@cost_bp.route("/breakdown/<route_id>", methods=["GET"])
def get_cost_breakdown(route_id: str):
    """Get cost breakdown for a route."""
    db = get_db()
    
    try:
        # Initialize repositories
        route_repo = SQLRouteRepository(db)
        breakdown_repo = SQLCostBreakdownRepository(db)
        
        # Validate route exists
        route = route_repo.find_by_id(UUID(route_id))
        if not route:
            return jsonify({"error": "Route not found"}), 404
        
        # Get breakdown
        breakdown = breakdown_repo.find_by_route_id(UUID(route_id))
        if not breakdown:
            return jsonify({"error": "Cost breakdown not found. Please calculate costs first."}), 404
        
        # Convert to response format
        response = {
            "breakdown": {
                "id": str(breakdown.id),
                "route_id": str(breakdown.route_id),
                "fuel_costs": {k: str(v) for k, v in breakdown.fuel_costs.items()},
                "toll_costs": {k: str(v) for k, v in breakdown.toll_costs.items()},
                "driver_costs": str(breakdown.driver_costs),
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


@cost_bp.route("/settings/<route_id>", methods=["GET"])
def get_cost_settings(route_id: str):
    """Get cost settings for a route."""
    db = get_db()
    
    try:
        # Validate route exists
        route = db.query(RouteModel).filter_by(id=route_id).first()
        if not route:
            return jsonify({"error": "Route not found"}), 404
        
        # Initialize repository
        settings_repo = SQLCostSettingsRepository(db)
        
        # Get settings
        settings = settings_repo.find_by_route_id(UUID(route_id))
        if not settings:
            return jsonify({"error": "Cost settings not found. Please create settings first."}), 404
        
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