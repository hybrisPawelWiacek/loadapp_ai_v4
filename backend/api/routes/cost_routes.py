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
        
        # Import rate validation functions
        from ...infrastructure.data.event_rates import validate_event_rate
        from ...infrastructure.data.fuel_rates import get_fuel_rate
        from ...infrastructure.data.toll_rates import get_toll_rate
        
        # Validate rates
        rates = {}
        for key, value in data.get("rates", {}).items():
            try:
                rate_value = Decimal(str(value))
                
                # Validate event rates
                if key.endswith('_rate') and key.split('_')[0] in ["pickup", "delivery", "rest"]:
                    event_type = key.split('_')[0]
                    if not validate_event_rate(event_type, rate_value):
                        return jsonify({"error": f"Invalid {event_type} event rate"}), 400
                
                # Validate fuel rates
                elif key.startswith('fuel_rate_'):
                    country = key.split('_')[-1]
                    default_rate = get_fuel_rate(country)
                    if not (Decimal("0.50") <= rate_value <= Decimal("5.00")):
                        return jsonify({"error": f"Invalid fuel rate for {country}"}), 400
                
                # Validate toll rates
                elif key.startswith('toll_rate_'):
                    country = key.split('_')[-1]
                    if not (Decimal("0.10") <= rate_value <= Decimal("2.00")):
                        return jsonify({"error": f"Invalid toll rate for {country}"}), 400
                
                rates[key] = rate_value
                
            except (InvalidOperation, ValueError) as e:
                return jsonify({"error": f"Invalid rate value for {key}: {str(e)}"}), 400
        
        # Create settings
        settings_create = CostSettingsCreate(
            enabled_components=data.get("enabled_components", []),
            rates=rates
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


@cost_bp.route("/rates/fuel/<route_id>", methods=["GET"])
def get_fuel_rates(route_id: str):
    """Get default fuel rates for countries in the route."""
    db = get_db()
    
    try:
        print(f"[DEBUG] Getting fuel rates for route_id: {route_id}")
        
        # Get container
        container = get_container()
        route_service = container.route_service()
        cost_service = container.cost_service()
        
        # Validate route exists
        route = route_service.get_route(UUID(route_id))
        if not route:
            print(f"[DEBUG] Route not found: {route_id}")
            return jsonify({"error": "Route not found"}), 404
            
        print(f"[DEBUG] Found route with {len(route.country_segments)} country segments")
            
        # Get current settings if they exist
        settings_repo = container.cost_settings_repository()
        current_settings = settings_repo.find_by_route_id(UUID(route_id))
        print(f"[DEBUG] Current settings found: {current_settings is not None}")
        
        # Get countries from route segments
        countries = {segment.country_code for segment in route.country_segments}
        print(f"[DEBUG] Countries in route: {countries}")
        
        # Import fuel rates configuration
        from ...infrastructure.data.fuel_rates import (
            DEFAULT_FUEL_RATES,
            CONSUMPTION_RATES,
            get_fuel_rate
        )
        
        # Filter default rates for route countries
        default_rates = {}
        for country in countries:
            try:
                rate = get_fuel_rate(country)
                default_rates[country] = str(rate)
            except Exception as e:
                print(f"[DEBUG] Error getting rate for country {country}: {str(e)}")
                default_rates[country] = str(DEFAULT_FUEL_RATES.get(country, "1.50"))
        
        print(f"[DEBUG] Default rates: {default_rates}")
        
        response = {
            "default_rates": default_rates,
            "consumption_rates": {k: str(v) for k, v in CONSUMPTION_RATES.items()}
        }
        
        # Add current settings if they exist
        if current_settings and current_settings.rates:
            response["current_settings"] = {
                k: str(v) for k, v in current_settings.rates.items()
                if k.startswith("fuel_rate_") and k.split("_")[-1] in countries
            }
            print(f"[DEBUG] Added current settings: {response['current_settings']}")
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"[DEBUG] Error in get_fuel_rates: {str(e)}")
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        if hasattr(db, 'rollback'):
            db.rollback()
        return jsonify({"error": str(e)}), 500


@cost_bp.route("/rates/toll/<route_id>", methods=["GET"])
def get_toll_rates(route_id: str):
    """Get toll rates for countries in the route."""
    db = get_db()
    
    try:
        # Get container
        container = get_container()
        route_service = container.route_service()
        cost_service = container.cost_service()
        transport_service = container.transport_service()
        
        # Validate route exists
        route = route_service.get_route(UUID(route_id))
        if not route:
            return jsonify({"error": "Route not found"}), 404
        
        # Get transport details for vehicle class info
        transport = transport_service.get_transport(route.transport_id)
        if not transport:
            return jsonify({"error": "Transport not found"}), 404
        
        # Get current settings if they exist
        current_settings = cost_service.get_settings(UUID(route_id))
        
        # Get countries from route segments
        countries = {segment.country_code for segment in route.country_segments}
        
        # Import toll rates configuration
        from ...infrastructure.data.toll_rates import (
            DEFAULT_TOLL_RATES,
            get_toll_class_description,
            get_euro_class_description,
            get_toll_rate
        )
        
        # Get toll rates for each country
        response = {
            "default_rates": {},
            "vehicle_info": {
                "toll_class": transport.truck_specs.toll_class,
                "euro_class": transport.truck_specs.euro_class,
                "toll_class_description": get_toll_class_description(transport.truck_specs.toll_class),
                "euro_class_description": get_euro_class_description(transport.truck_specs.euro_class)
            }
        }
        
        for country in countries:
            rates = get_toll_rate(
                country,
                transport.truck_specs.toll_class,
                transport.truck_specs.euro_class
            )
            response["default_rates"][country] = {
                "base_rate": str(rates["base_rate"]),
                "euro_adjustment": str(rates["euro_adjustment"])
            }
        
        # Add current settings if they exist
        if current_settings and current_settings.rates:
            response["current_settings"] = {
                k: str(v) for k, v in current_settings.rates.items()
                if k.startswith("toll_rate_") and k.split("_")[-1] in countries
            }
        
        # Add business entity overrides if they exist
        if route.business_entity_id:
            toll_rate_override_repo = container.toll_rate_override_repo()
            overrides = toll_rate_override_repo.find_for_business_multiple(
                business_entity_id=route.business_entity_id,
                countries=list(countries),
                vehicle_class=transport.truck_specs.toll_class
            )
            if overrides:
                response["business_overrides"] = {
                    override.country_code: {
                        "rate_multiplier": str(override.rate_multiplier),
                        "route_type": override.route_type
                    }
                    for override in overrides
                }
        
        return jsonify(response), 200
        
    except Exception as e:
        if hasattr(db, 'rollback'):
            db.rollback()
        return jsonify({"error": str(e)}), 500


@cost_bp.route("/rates/event", methods=["GET"])
def get_event_rates():
    """Get default event rates and allowed ranges."""
    try:
        # Import event rates configuration
        from ...infrastructure.data.event_rates import (
            EVENT_RATES,
            EVENT_RATE_RANGES
        )
        
        response = {
            "rates": {k: str(v) for k, v in EVENT_RATES.items()},
            "ranges": {
                k: (str(min_val), str(max_val))
                for k, (min_val, max_val) in EVENT_RATE_RANGES.items()
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500 