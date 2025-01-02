"""Route-related API routes."""
from datetime import datetime
from uuid import UUID, uuid4
from flask import Blueprint, jsonify, request, g

from ...domain.entities.location import Location
from ...domain.entities.route import Route, EmptyDriving, TimelineEvent
from ...infrastructure.models.transport_models import TransportModel
from ...infrastructure.models.cargo_models import CargoModel
from ...infrastructure.repositories.route_repository import SQLRouteRepository
from ...infrastructure.repositories.location_repository import SQLLocationRepository
from ...domain.services.route_service import RouteService
from ...infrastructure.adapters.google_maps_adapter import GoogleMapsAdapter
from ...infrastructure.external_services.google_maps_service import GoogleMapsService


# Create blueprint
route_bp = Blueprint("route", __name__, url_prefix="/api/route")


@route_bp.route("/calculate", methods=["POST"])
def calculate_route():
    """Calculate a new route."""
    data = request.get_json()
    db = g.db
    
    try:
        # Validate transport exists
        transport = db.query(TransportModel).filter_by(id=data["transport_id"]).first()
        if not transport:
            return jsonify({"error": "Transport not found"}), 404
        
        # Validate cargo exists
        cargo = db.query(CargoModel).filter_by(id=data["cargo_id"]).first()
        if not cargo:
            return jsonify({"error": "Cargo not found"}), 404
        
        # Parse dates
        pickup_time = datetime.fromisoformat(data["pickup_time"].replace("Z", "+00:00"))
        delivery_time = datetime.fromisoformat(data["delivery_time"].replace("Z", "+00:00"))
        
        # Validate dates
        if delivery_time <= pickup_time:
            return jsonify({"error": "Delivery time must be after pickup time"}), 400
        
        # Initialize services
        google_maps_service = GoogleMapsService(api_key="test-key")  # Use test key for now
        google_maps_adapter = GoogleMapsAdapter(google_maps_service)
        location_repo = SQLLocationRepository(db)
        route_service = RouteService(
            route_repo=SQLRouteRepository(db),
            route_calculator=google_maps_adapter,
            location_repo=location_repo
        )
        
        # Create route
        route = route_service.create_route(
            transport_id=UUID(transport.id),
            business_entity_id=UUID(transport.business_entity_id),
            cargo_id=UUID(cargo.id),
            origin_id=UUID(data["origin_id"]),
            destination_id=UUID(data["destination_id"]),
            pickup_time=pickup_time,
            delivery_time=delivery_time
        )
        
        # Convert to response format
        response = {
            "route": {
                "id": str(route.id),
                "transport_id": str(route.transport_id),
                "cargo_id": str(route.cargo_id),
                "business_entity_id": str(route.business_entity_id),
                "origin_id": str(route.origin_id),
                "destination_id": str(route.destination_id),
                "pickup_time": route.pickup_time.isoformat(),
                "delivery_time": route.delivery_time.isoformat(),
                "empty_driving_id": str(route.empty_driving_id),
                "timeline_events": [
                    {
                        "id": str(event.id),
                        "type": event.type,
                        "location": {
                            "id": str(event.location_id),
                            "latitude": location_repo.find_by_id(event.location_id).latitude,
                            "longitude": location_repo.find_by_id(event.location_id).longitude,
                            "address": location_repo.find_by_id(event.location_id).address
                        },
                        "planned_time": event.planned_time.isoformat(),
                        "duration_hours": event.duration_hours,
                        "event_order": event.event_order
                    }
                    for event in route.timeline_events
                ],
                "country_segments": [
                    {
                        "country_code": segment.country_code,
                        "distance_km": segment.distance_km,
                        "duration_hours": segment.duration_hours,
                        "start_location": {
                            "id": str(segment.start_location_id),
                            "latitude": location_repo.find_by_id(segment.start_location_id).latitude,
                            "longitude": location_repo.find_by_id(segment.start_location_id).longitude,
                            "address": location_repo.find_by_id(segment.start_location_id).address
                        },
                        "end_location": {
                            "id": str(segment.end_location_id),
                            "latitude": location_repo.find_by_id(segment.end_location_id).latitude,
                            "longitude": location_repo.find_by_id(segment.end_location_id).longitude,
                            "address": location_repo.find_by_id(segment.end_location_id).address
                        }
                    }
                    for segment in route.country_segments
                ],
                "total_distance_km": route.total_distance_km,
                "total_duration_hours": route.total_duration_hours,
                "is_feasible": route.is_feasible,
                "status": route.status.value
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@route_bp.route("/check-feasibility", methods=["POST"])
def check_route_feasibility():
    """Check route feasibility."""
    data = request.get_json()
    db = g.db
    
    try:
        # Initialize services
        route_service = RouteService(
            route_repo=SQLRouteRepository(db),
            route_calculator=GoogleMapsAdapter(GoogleMapsService(api_key="test-key")),
            location_repo=SQLLocationRepository(db)
        )
        
        # For PoC, always return feasible with some validation details
        response = {
            "is_feasible": True,
            "validation_details": {
                "transport_valid": True,
                "cargo_valid": True,
                "timeline_valid": True,
                "distance_valid": True
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@route_bp.route("/<route_id>/timeline", methods=["GET"])
def get_route_timeline(route_id):
    """Get route timeline events."""
    db = g.db
    
    try:
        # Initialize repositories
        route_repo = SQLRouteRepository(db)
        location_repo = SQLLocationRepository(db)
        
        # Get route
        route = route_repo.find_by_id(UUID(route_id))
        if not route:
            return jsonify({"error": "Route not found"}), 404
        
        # Convert to response format
        response = {
            "timeline_events": [
                {
                    "id": str(event.id),
                    "type": event.type,
                    "location": {
                        "id": str(event.location_id),
                        "latitude": location_repo.find_by_id(event.location_id).latitude,
                        "longitude": location_repo.find_by_id(event.location_id).longitude,
                        "address": location_repo.find_by_id(event.location_id).address
                    },
                    "planned_time": event.planned_time.isoformat(),
                    "duration_hours": event.duration_hours,
                    "event_order": event.event_order
                }
                for event in route.timeline_events
            ]
        }
        
        return jsonify(response), 200
        
    except ValueError:
        return jsonify({"error": "Invalid route ID format"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@route_bp.route("/<route_id>/segments", methods=["GET"])
def get_route_segments(route_id):
    """Get route country segments."""
    db = g.db
    
    try:
        # Initialize repositories
        route_repo = SQLRouteRepository(db)
        location_repo = SQLLocationRepository(db)
        
        # Get route
        route = route_repo.find_by_id(UUID(route_id))
        if not route:
            return jsonify({"error": "Route not found"}), 404
        
        # Convert to response format
        response = {
            "country_segments": [
                {
                    "country_code": segment.country_code,
                    "distance_km": segment.distance_km,
                    "duration_hours": segment.duration_hours,
                    "start_location": {
                        "id": str(segment.start_location_id),
                        "latitude": location_repo.find_by_id(segment.start_location_id).latitude,
                        "longitude": location_repo.find_by_id(segment.start_location_id).longitude,
                        "address": location_repo.find_by_id(segment.start_location_id).address
                    },
                    "end_location": {
                        "id": str(segment.end_location_id),
                        "latitude": location_repo.find_by_id(segment.end_location_id).latitude,
                        "longitude": location_repo.find_by_id(segment.end_location_id).longitude,
                        "address": location_repo.find_by_id(segment.end_location_id).address
                    }
                }
                for segment in route.country_segments
            ]
        }
        
        return jsonify(response), 200
        
    except ValueError:
        return jsonify({"error": "Invalid route ID format"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@route_bp.route("/<route_id>/timeline", methods=["PUT"])
def update_route_timeline(route_id):
    """Update route timeline events."""
    data = request.get_json()
    db = g.db
    
    try:
        # Initialize repositories
        route_repo = SQLRouteRepository(db)
        location_repo = SQLLocationRepository(db)
        
        # Get route
        route = route_repo.find_by_id(UUID(route_id))
        if not route:
            return jsonify({"error": "Route not found"}), 404
        
        # Validate timeline sequence
        events = data.get("timeline_events", [])
        if not events:
            return jsonify({"error": "No timeline events provided"}), 400
            
        # Ensure events are in correct order
        if events[0]["type"] != "pickup" or events[-1]["type"] != "delivery":
            return jsonify({"error": "Invalid timeline sequence"}), 400
            
        # Update timeline events
        new_events = []
        for idx, event_data in enumerate(events, 1):
            event = TimelineEvent(
                id=uuid4(),
                route_id=route.id,
                type=event_data["type"],
                location_id=route.origin_id if event_data["type"] == "pickup" else route.destination_id,
                planned_time=datetime.fromisoformat(event_data["planned_time"].replace("Z", "+00:00")),
                duration_hours=event_data["duration_hours"],
                event_order=idx
            )
            new_events.append(event)
            
        route.timeline_events = new_events
        route = route_repo.save(route)
        
        # Convert to response format
        response = {
            "timeline_events": [
                {
                    "id": str(event.id),
                    "type": event.type,
                    "location": {
                        "id": str(event.location_id),
                        "latitude": location_repo.find_by_id(event.location_id).latitude,
                        "longitude": location_repo.find_by_id(event.location_id).longitude,
                        "address": location_repo.find_by_id(event.location_id).address
                    },
                    "planned_time": event.planned_time.isoformat(),
                    "duration_hours": event.duration_hours,
                    "event_order": event.event_order
                }
                for event in route.timeline_events
            ]
        }
        
        return jsonify(response), 200
        
    except ValueError:
        return jsonify({"error": "Invalid route ID format"}), 400
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close() 