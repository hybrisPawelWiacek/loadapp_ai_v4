"""Default toll rates and configurations."""
from decimal import Decimal
from typing import Dict, Any

# Common toll road keywords and patterns
TOLL_KEYWORDS = [
    'toll', 'péage', 'maut', 'pedaggio',  # Various languages
    'toll road', 'toll highway', 'toll motorway',
    'toll bridge', 'toll tunnel'
]

# Default toll rates per country and vehicle class (EUR/km)
DEFAULT_TOLL_RATES = {
    "DE": {  # Germany
        "toll_class": {
            "1": Decimal("0.187"),  # Up to 7.5t
            "2": Decimal("0.208"),  # 7.5t - 12t
            "3": Decimal("0.228"),  # 12t - 18t
            "4": Decimal("0.248")   # Over 18t
        },
        "euro_class": {
            "VI": Decimal("0.000"),  # Euro 6
            "V": Decimal("0.021"),   # Euro 5
            "IV": Decimal("0.042"),  # Euro 4
            "III": Decimal("0.063")  # Euro 3
        }
    },
    "FR": {  # France
        "toll_class": {
            "1": Decimal("0.176"),  # Up to 7.5t
            "2": Decimal("0.196"),  # 7.5t - 12t
            "3": Decimal("0.216"),  # 12t - 18t
            "4": Decimal("0.236")   # Over 18t
        },
        "euro_class": {
            "VI": Decimal("0.000"),  # Euro 6
            "V": Decimal("0.020"),   # Euro 5
            "IV": Decimal("0.040"),  # Euro 4
            "III": Decimal("0.060")  # Euro 3
        }
    }
}

# Default rate for unknown countries (EUR/km)
DEFAULT_UNKNOWN_RATE = Decimal("0.200")

# Vehicle class mappings
TOLL_CLASS_WEIGHT_RANGES = {
    "1": "up to 7.5t",
    "2": "7.5t - 12t",
    "3": "12t - 18t",
    "4": "over 18t"
}

EURO_CLASS_DESCRIPTIONS = {
    "VI": "Euro 6",
    "V": "Euro 5",
    "IV": "Euro 4",
    "III": "Euro 3"
}

def get_toll_rate(country_code: str, toll_class: str, euro_class: str) -> Dict[str, Decimal]:
    """Get toll rates for a specific country and vehicle classes.
    
    Args:
        country_code: ISO country code
        toll_class: Vehicle toll class
        euro_class: Vehicle euro emission class
        
    Returns:
        Dictionary containing base_rate and euro_adjustment
    """
    country_rates = DEFAULT_TOLL_RATES.get(country_code, None)
    if not country_rates:
        return {
            "base_rate": DEFAULT_UNKNOWN_RATE,
            "euro_adjustment": Decimal("0.000")
        }
        
    base_rate = country_rates["toll_class"].get(
        toll_class,
        country_rates["toll_class"]["1"]  # Default to class 1
    )
    
    euro_adjustment = country_rates["euro_class"].get(
        euro_class,
        country_rates["euro_class"]["III"]  # Default to EURO III
    )
    
    return {
        "base_rate": base_rate,
        "euro_adjustment": euro_adjustment
    }

def is_valid_toll_class(toll_class: str) -> bool:
    """Check if toll class is valid."""
    return toll_class in TOLL_CLASS_WEIGHT_RANGES

def is_valid_euro_class(euro_class: str) -> bool:
    """Check if euro class is valid."""
    return euro_class in EURO_CLASS_DESCRIPTIONS

def get_toll_class_description(toll_class: str) -> str:
    """Get human-readable description of toll class."""
    return TOLL_CLASS_WEIGHT_RANGES.get(toll_class, "unknown weight class")

def get_euro_class_description(euro_class: str) -> str:
    """Get human-readable description of euro class."""
    return EURO_CLASS_DESCRIPTIONS.get(euro_class, "unknown emission class") 