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
    TOLL_RATE_MULTIPLIER = "toll_rate_multiplier"
    DRIVER_BASE_RATE = "driver_base_rate"
    DRIVER_TIME_RATE = "driver_time_rate"
    DRIVER_OVERTIME_RATE = "driver_overtime_rate"
    EVENT_RATE = "event_rate"
    PICKUP_RATE = "pickup_rate"
    DELIVERY_RATE = "delivery_rate"
    REST_RATE = "rest_rate"
    REFRIGERATION_RATE = "refrigeration_rate"
    OVERHEAD_ADMIN_RATE = "overhead_admin_rate"
    OVERHEAD_INSURANCE_RATE = "overhead_insurance_rate"
    OVERHEAD_FACILITIES_RATE = "overhead_facilities_rate"
    OVERHEAD_OTHER_RATE = "overhead_other_rate"

    @property
    def is_country_specific(self) -> bool:
        """Check if rate type is country-specific."""
        return self in {
            RateType.FUEL_RATE,
            RateType.FUEL_SURCHARGE_RATE,
            RateType.TOLL_RATE,
            RateType.DRIVER_TIME_RATE,
            RateType.DRIVER_OVERTIME_RATE,
            RateType.REFRIGERATION_RATE
        }

    @property
    def requires_certification(self) -> bool:
        """Check if rate type requires certification."""
        return self in {
            RateType.REFRIGERATION_RATE
        }

    @property
    def min_value(self) -> Decimal:
        """Get minimum allowed value for rate type."""
        ranges = {
            RateType.FUEL_RATE: Decimal("0.50"),
            RateType.FUEL_SURCHARGE_RATE: Decimal("0.01"),
            RateType.TOLL_RATE: Decimal("0.10"),
            RateType.TOLL_RATE_MULTIPLIER: Decimal("0.50"),
            RateType.DRIVER_BASE_RATE: Decimal("100.00"),
            RateType.DRIVER_TIME_RATE: Decimal("10.00"),
            RateType.DRIVER_OVERTIME_RATE: Decimal("15.00"),
            RateType.EVENT_RATE: Decimal("20.00"),
            RateType.PICKUP_RATE: Decimal("20.00"),
            RateType.DELIVERY_RATE: Decimal("20.00"),
            RateType.REST_RATE: Decimal("20.00"),
            RateType.REFRIGERATION_RATE: Decimal("0.20"),
            RateType.OVERHEAD_ADMIN_RATE: Decimal("0.01"),
            RateType.OVERHEAD_INSURANCE_RATE: Decimal("0.01"),
            RateType.OVERHEAD_FACILITIES_RATE: Decimal("0.01"),
            RateType.OVERHEAD_OTHER_RATE: Decimal("0.00")
        }
        return ranges[self]

    @property
    def max_value(self) -> Decimal:
        """Get maximum allowed value for rate type."""
        ranges = {
            RateType.FUEL_RATE: Decimal("5.00"),
            RateType.FUEL_SURCHARGE_RATE: Decimal("0.50"),
            RateType.TOLL_RATE: Decimal("2.00"),
            RateType.TOLL_RATE_MULTIPLIER: Decimal("2.00"),
            RateType.DRIVER_BASE_RATE: Decimal("500.00"),
            RateType.DRIVER_TIME_RATE: Decimal("100.00"),
            RateType.DRIVER_OVERTIME_RATE: Decimal("150.00"),
            RateType.EVENT_RATE: Decimal("200.00"),
            RateType.PICKUP_RATE: Decimal("200.00"),
            RateType.DELIVERY_RATE: Decimal("200.00"),
            RateType.REST_RATE: Decimal("150.00"),
            RateType.REFRIGERATION_RATE: Decimal("1.00"),
            RateType.OVERHEAD_ADMIN_RATE: Decimal("1000.00"),
            RateType.OVERHEAD_INSURANCE_RATE: Decimal("1000.00"),
            RateType.OVERHEAD_FACILITIES_RATE: Decimal("1000.00"),
            RateType.OVERHEAD_OTHER_RATE: Decimal("1000.00")
        }
        return ranges[self]


class RateValidationSchema(BaseModel):
    """Schema for rate validation rules."""
    rate_type: RateType = Field(..., description="Type of rate being validated")
    min_value: Decimal = Field(..., ge=0, description="Minimum allowed value")
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

    @classmethod
    def from_rate_type(cls, rate_type: RateType) -> 'RateValidationSchema':
        """Create validation schema from rate type."""
        return cls(
            rate_type=rate_type,
            min_value=rate_type.min_value,
            max_value=rate_type.max_value,
            country_specific=rate_type.is_country_specific,
            requires_certification=rate_type.requires_certification,
            description=None  # Description can be added later if needed
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
        RateType.TOLL_RATE_MULTIPLIER: RateValidationSchema(
            rate_type=RateType.TOLL_RATE_MULTIPLIER,
            min_value=Decimal("0.5"),
            max_value=Decimal("2.0"),
            country_specific=False,
            description="Multiplier applied to base toll rates"
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
        RateType.DRIVER_OVERTIME_RATE: RateValidationSchema(
            rate_type=RateType.DRIVER_OVERTIME_RATE,
            min_value=Decimal("15.0"),
            max_value=Decimal("150.0"),
            country_specific=True,
            description="Overtime hourly rate for driver"
        ),
        RateType.EVENT_RATE: RateValidationSchema(
            rate_type=RateType.EVENT_RATE,
            min_value=Decimal("20.0"),
            max_value=Decimal("200.0"),
            description="Standard event rate"
        ),
        RateType.REFRIGERATION_RATE: RateValidationSchema(
            rate_type=RateType.REFRIGERATION_RATE,
            min_value=Decimal("0.2"),
            max_value=Decimal("1.0"),
            country_specific=True,
            requires_certification=True,
            description="Additional rate per km for refrigeration"
        ),
        RateType.OVERHEAD_ADMIN_RATE: RateValidationSchema(
            rate_type=RateType.OVERHEAD_ADMIN_RATE,
            min_value=Decimal("0.01"),
            max_value=Decimal("1000.0"),
            country_specific=False,
            description="Administrative overhead costs per route"
        ),
        RateType.OVERHEAD_INSURANCE_RATE: RateValidationSchema(
            rate_type=RateType.OVERHEAD_INSURANCE_RATE,
            min_value=Decimal("0.01"),
            max_value=Decimal("1000.0"),
            country_specific=False,
            description="Insurance overhead costs per route"
        ),
        RateType.OVERHEAD_FACILITIES_RATE: RateValidationSchema(
            rate_type=RateType.OVERHEAD_FACILITIES_RATE,
            min_value=Decimal("0.01"),
            max_value=Decimal("1000.0"),
            country_specific=False,
            description="Facilities overhead costs per route"
        ),
        RateType.OVERHEAD_OTHER_RATE: RateValidationSchema(
            rate_type=RateType.OVERHEAD_OTHER_RATE,
            min_value=Decimal("0.0"),
            max_value=Decimal("1000.0"),
            country_specific=False,
            description="Other overhead costs per route"
        ),
        RateType.PICKUP_RATE: RateValidationSchema(
            rate_type=RateType.PICKUP_RATE,
            min_value=Decimal("20.0"),
            max_value=Decimal("200.0"),
            description="Rate for pickup events"
        ),
        RateType.DELIVERY_RATE: RateValidationSchema(
            rate_type=RateType.DELIVERY_RATE,
            min_value=Decimal("20.0"),
            max_value=Decimal("200.0"),
            description="Rate for delivery events"
        ),
        RateType.REST_RATE: RateValidationSchema(
            rate_type=RateType.REST_RATE,
            min_value=Decimal("20.0"),
            max_value=Decimal("150.0"),
            description="Rate for rest events"
        )
    } 