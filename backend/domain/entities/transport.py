"""Transport domain entities for LoadApp.AI."""
from decimal import Decimal
from typing import List
from uuid import UUID

from pydantic import BaseModel, Field


class TruckSpecification(BaseModel):
    """Truck-specific configuration values."""
    fuel_consumption_empty: float = Field(..., gt=0, description="Fuel consumption when truck is empty")
    fuel_consumption_loaded: float = Field(..., gt=0, description="Fuel consumption when truck is loaded")
    toll_class: str = Field(..., min_length=1, description="Toll class of the truck")
    euro_class: str = Field(..., min_length=1, description="Euro emission class")
    co2_class: str = Field(..., min_length=1, description="CO2 emission class")
    maintenance_rate_per_km: Decimal = Field(..., gt=0, description="Maintenance cost per kilometer")


class DriverSpecification(BaseModel):
    """Driver-specific configuration values."""
    daily_rate: Decimal = Field(..., gt=0, description="Daily rate for the driver")
    required_license_type: str = Field(..., min_length=1, description="Required driver's license type")
    required_certifications: List[str] = Field(..., min_items=1, description="Required driver certifications")


class TransportType(BaseModel):
    """Static configuration/catalog of available transport types."""
    id: str = Field(..., min_length=1, description="Transport type identifier")
    name: str = Field(..., min_length=1, description="Transport type name")
    truck_specifications: TruckSpecification = Field(..., description="Truck specifications")
    driver_specifications: DriverSpecification = Field(..., description="Driver specifications")


class Transport(BaseModel):
    """Runtime instance created when user selects transport type."""
    id: UUID = Field(..., description="Transport instance identifier")
    transport_type_id: str = Field(..., min_length=1, description="Reference to transport type")
    business_entity_id: UUID = Field(..., description="Reference to business entity")
    truck_specs: TruckSpecification = Field(..., description="Truck specifications")
    driver_specs: DriverSpecification = Field(..., description="Driver specifications")
    is_active: bool = Field(True, description="Whether the transport is active") 