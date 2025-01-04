"""Rate types and validation schemas for LoadApp.AI."""
from enum import Enum
from decimal import Decimal
from typing import Optional, Dict
from pydantic import BaseModel, Field


class RateType(str, Enum):
    """Enumeration of supported rate types."""
    FUEL_RATE = "fuel_rate"
    FUEL_SURCHARGE_RATE = "fuel_surcharge_rate"
    TOLL_RATE = "toll_rate"
    DRIVER_BASE_RATE = "driver_base_rate"
    DRIVER_TIME_RATE = "driver_time_rate"
    EVENT_RATE = "event_rate"


class RateValidationSchema(BaseModel):
    """Schema for rate validation rules."""
    rate_type: RateType = Field(..., description="Type of rate being validated")
    min_value: Decimal = Field(..., gt=0, description="Minimum allowed value")
    max_value: Decimal = Field(..., gt=0, description="Maximum allowed value")
    country_specific: bool = Field(
        default=False,
        description="Whether rate varies by country"
    )
    requires_certification: bool = Field(
        default=False,
        description="Whether special certification is needed"
    )
    description: Optional[str] = Field(
        default=None,
        description="Optional description of the rate type"
    )


def validate_rate(rate_type: RateType, value: Decimal, schema: RateValidationSchema) -> bool:
    """
    Validate a rate value against its schema.
    
    Args:
        rate_type: Type of rate being validated
        value: Rate value to validate
        schema: Validation schema to check against
        
    Returns:
        bool: True if rate is valid, False otherwise
    """
    if schema.rate_type != rate_type:
        return False
    return schema.min_value <= value <= schema.max_value


def get_default_validation_schemas() -> Dict[RateType, RateValidationSchema]:
    """
    Get default validation schemas for all rate types.
    
    Returns:
        Dictionary mapping rate types to their default validation schemas
    """
    return {
        RateType.FUEL_RATE: RateValidationSchema(
            rate_type=RateType.FUEL_RATE,
            min_value=Decimal("0.5"),
            max_value=Decimal("5.0"),
            country_specific=True,
            description="Fuel rate per liter"
        ),
        RateType.FUEL_SURCHARGE_RATE: RateValidationSchema(
            rate_type=RateType.FUEL_SURCHARGE_RATE,
            min_value=Decimal("0.01"),
            max_value=Decimal("0.5"),
            country_specific=True,
            description="Additional fuel surcharge percentage"
        ),
        RateType.TOLL_RATE: RateValidationSchema(
            rate_type=RateType.TOLL_RATE,
            min_value=Decimal("0.1"),
            max_value=Decimal("2.0"),
            country_specific=True,
            description="Toll rate per kilometer"
        ),
        RateType.DRIVER_BASE_RATE: RateValidationSchema(
            rate_type=RateType.DRIVER_BASE_RATE,
            min_value=Decimal("100.0"),
            max_value=Decimal("500.0"),
            country_specific=False,
            description="Base daily rate for driver"
        ),
        RateType.DRIVER_TIME_RATE: RateValidationSchema(
            rate_type=RateType.DRIVER_TIME_RATE,
            min_value=Decimal("10.0"),
            max_value=Decimal("100.0"),
            country_specific=True,
            description="Hourly rate for driver time"
        ),
        RateType.EVENT_RATE: RateValidationSchema(
            rate_type=RateType.EVENT_RATE,
            min_value=Decimal("20.0"),
            max_value=Decimal("200.0"),
            country_specific=False,
            description="Rate per timeline event"
        )
    } 