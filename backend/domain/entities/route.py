"""Route domain entities."""
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .location import Location


class RouteStatus(str, Enum):
    """Route status enumeration."""
    DRAFT = "draft"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EmptyDriving(BaseModel):
    """Empty driving segment before main route."""
    
    id: UUID = Field(
        ...,
        description="Empty driving segment identifier"
    )
    distance_km: float = Field(
        default=200.0,
        gt=0,
        description="Empty driving distance in kilometers"
    )
    duration_hours: float = Field(
        default=4.0,
        gt=0,
        description="Empty driving duration in hours"
    )

class RouteSegment(BaseModel):
    """Segment of a route with distance and duration."""
    
    distance_km: float = Field(
        ...,
        gt=0,
        description="Segment distance in kilometers"
    )
    duration_hours: float = Field(
        ...,
        gt=0,
        description="Segment duration in hours"
    )
    start_location: Location = Field(
        ...,
        description="Start location"
    )
    end_location: Location = Field(
        ...,
        description="End location"
    )

class CountrySegment(BaseModel):
    """Route segment within a single country."""
    
    country_code: str = Field(
        ...,
        min_length=2,
        max_length=2,
        description="ISO 3166-1 alpha-2 country code"
    )
    distance_km: float = Field(
        ...,
        gt=0,
        description="Distance within country in kilometers"
    )
    duration_hours: float = Field(
        ...,
        gt=0,
        description="Duration within country in hours"
    )
    start_location: Location = Field(
        ...,
        description="Start location"
    )
    end_location: Location = Field(
        ...,
        description="End location"
    )

class TimelineEvent(BaseModel):
    """Event in route timeline (pickup/rest/delivery)."""
    
    id: UUID = Field(
        ...,
        description="Event identifier"
    )
    type: str = Field(
        ...,
        min_length=1,
        description="Event type (pickup/rest/delivery)"
    )
    location: Location = Field(
        ...,
        description="Event location"
    )
    planned_time: datetime = Field(
        ...,
        description="Planned event time"
    )
    duration_hours: float = Field(
        default=1.0,
        gt=0,
        description="Event duration in hours"
    )
    event_order: int = Field(
        ...,
        ge=0,
        description="Order of event in timeline"
    )

class Route(BaseModel):
    """Complete transport route with timeline."""
    
    id: UUID = Field(
        ...,
        description="Route identifier"
    )
    transport_id: UUID = Field(
        ...,
        description="Reference to transport"
    )
    business_entity_id: UUID = Field(
        ...,
        description="Reference to business entity"
    )
    cargo_id: UUID = Field(
        ...,
        description="Reference to cargo"
    )
    origin_id: UUID = Field(
        ...,
        description="Reference to origin location"
    )
    destination_id: UUID = Field(
        ...,
        description="Reference to destination location"
    )
    pickup_time: datetime = Field(
        ...,
        description="Pickup time"
    )
    delivery_time: datetime = Field(
        ...,
        description="Delivery time"
    )
    empty_driving_id: UUID = Field(
        ...,
        description="Reference to empty driving segment"
    )
    timeline_events: List[TimelineEvent] = Field(
        default_factory=list,
        description="Timeline events"
    )
    country_segments: List[CountrySegment] = Field(
        default_factory=list,
        description="Country segments"
    )
    total_distance_km: float = Field(
        ...,
        ge=0,
        description="Total distance in kilometers"
    )
    total_duration_hours: float = Field(
        ...,
        ge=0,
        description="Total duration in hours"
    )
    is_feasible: bool = Field(
        default=True,
        description="Route feasibility flag"
    )
    status: RouteStatus = Field(
        default=RouteStatus.DRAFT,
        description="Route status"
    ) 