"""Default event rates and configurations."""
from decimal import Decimal
from typing import Dict, Tuple

# Default rates for different event types (EUR/event)
EVENT_RATES = {
    "pickup": Decimal("50.00"),
    "delivery": Decimal("50.00"),
    "rest": Decimal("30.00")     # Different rate for rest stops
}

# Allowed rate ranges for each event type (min, max in EUR)
EVENT_RATE_RANGES = {
    "pickup": (Decimal("20.00"), Decimal("200.00")),
    "delivery": (Decimal("20.00"), Decimal("200.00")),
    "rest": (Decimal("20.00"), Decimal("150.00"))
}

def get_event_rate(event_type: str) -> Decimal:
    """Get default rate for a specific event type.
    
    Args:
        event_type: Type of event (pickup, delivery, rest)
        
    Returns:
        Default rate in EUR
        
    Raises:
        KeyError: If event type is not recognized
    """
    return EVENT_RATES[event_type]

def get_rate_range(event_type: str) -> Tuple[Decimal, Decimal]:
    """Get allowed rate range for a specific event type.
    
    Args:
        event_type: Type of event (pickup, delivery, rest)
        
    Returns:
        Tuple of (min_rate, max_rate) in EUR
        
    Raises:
        KeyError: If event type is not recognized
    """
    return EVENT_RATE_RANGES[event_type]

def validate_event_rate(event_type: str, rate: Decimal) -> bool:
    """Validate if a rate is within allowed range for event type.
    
    Args:
        event_type: Type of event (pickup, delivery, rest)
        rate: Rate to validate
        
    Returns:
        True if rate is valid, False otherwise
    """
    try:
        min_rate, max_rate = EVENT_RATE_RANGES[event_type]
        return min_rate <= rate <= max_rate
    except KeyError:
        return False

def is_valid_event_type(event_type: str) -> bool:
    """Check if event type is valid.
    
    Args:
        event_type: Type of event to validate
        
    Returns:
        True if event type is valid, False otherwise
    """
    return event_type in EVENT_RATES
