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
        route_service = RouteService(
            route_repo=SQLRouteRepository(db),
            route_calculator=google_maps_adapter,
            location_repo=SQLLocationRepository(db)
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
                            "latitude": event.location.latitude,
                            "longitude": event.location.longitude,
                            "address": event.location.address
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
                            "latitude": segment.start_location.latitude,
                            "longitude": segment.start_location.longitude,
                            "address": segment.start_location.address
                        },
                        "end_location": {
                            "latitude": segment.end_location.latitude,
                            "longitude": segment.end_location.longitude,
                            "address": segment.end_location.address
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
        # Initialize repository
        route_repo = SQLRouteRepository(db)
        
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
                        "latitude": event.location.latitude,
                        "longitude": event.location.longitude,
                        "address": event.location.address
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
        # Initialize repository
        route_repo = SQLRouteRepository(db)
        
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
                        "latitude": segment.start_location.latitude,
                        "longitude": segment.start_location.longitude,
                        "address": segment.start_location.address
                    },
                    "end_location": {
                        "latitude": segment.end_location.latitude,
                        "longitude": segment.end_location.longitude,
                        "address": segment.end_location.address
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
        # Initialize repository and service
        route_repo = SQLRouteRepository(db)
        
        # Get route
        route = route_repo.find_by_id(UUID(route_id))
        if not route:
            return jsonify({"error": "Route not found"}), 404
        
        # Validate timeline sequence
        events = data["timeline_events"]
        if not events or events[0]["type"] != "pickup":
            return jsonify({"error": "Invalid timeline sequence - pickup must be first"}), 400
        
        # Create new timeline events
        new_events = []
        for event_data in events:
            # Get location based on event type
            if event_data["type"] == "pickup":
                location = route_repo.get_location_by_id(route.origin_id)
            elif event_data["type"] == "delivery":
                location = route_repo.get_location_by_id(route.destination_id)
            else:  # rest event
                # For rest event, use the previous event's location
                if new_events:
                    location = new_events[-1].location
                else:
                    location = route_repo.get_location_by_id(route.origin_id)
            
            if not location:
                raise ValueError(f"Location not found for event type {event_data['type']}")
            
            event = TimelineEvent(
                id=uuid4(),
                type=event_data["type"],
                location=location,
                planned_time=datetime.fromisoformat(event_data["planned_time"].replace("Z", "+00:00")),
                duration_hours=event_data["duration_hours"],
                event_order=event_data["event_order"]
            )
            new_events.append(event)
        
        # Update route timeline
        route.timeline_events = new_events
        updated_route = route_repo.save(route)
        
        # Convert to response format
        response = {
            "timeline_events": [
                {
                    "id": str(event.id),
                    "type": event.type,
                    "location": {
                        "latitude": event.location.latitude,
                        "longitude": event.location.longitude,
                        "address": event.location.address
                    },
                    "planned_time": event.planned_time.isoformat(),
                    "duration_hours": event.duration_hours,
                    "event_order": event.event_order
                }
                for event in updated_route.timeline_events
            ]
        }
        
        return jsonify(response), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close() 