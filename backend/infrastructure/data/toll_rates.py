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

# Default rates by region when country-specific rates are not available
DEFAULT_RATES_BY_REGION = {
    "EU": {  # European Union default rates
        "toll_class": {
            "1": Decimal("0.177"),  # Average EU rate for class 1
            "2": Decimal("0.198"),  # Average EU rate for class 2
            "3": Decimal("0.218"),  # Average EU rate for class 3
            "4": Decimal("0.238")   # Average EU rate for class 4
        },
        "euro_class": {
            "VI": Decimal("0.000"),  # Euro 6
            "V": Decimal("0.020"),   # Euro 5
            "IV": Decimal("0.041"),  # Euro 4
            "III": Decimal("0.062")  # Euro 3
        }
    },
    "OTHER": {  # Non-EU default rates
        "toll_class": {
            "1": Decimal("0.150"),
            "2": Decimal("0.170"),
            "3": Decimal("0.190"),
            "4": Decimal("0.210")
        },
        "euro_class": {
            "VI": Decimal("0.000"),
            "V": Decimal("0.015"),
            "IV": Decimal("0.030"),
            "III": Decimal("0.045")
        }
    }
}

# Map countries to regions for default rate lookup
COUNTRY_REGION_MAP = {
    # EU countries
    "AT": "EU", "BE": "EU", "BG": "EU", "HR": "EU", "CY": "EU",
    "CZ": "EU", "DK": "EU", "EE": "EU", "FI": "EU", "FR": "EU",
    "DE": "EU", "GR": "EU", "HU": "EU", "IE": "EU", "IT": "EU",
    "LV": "EU", "LT": "EU", "LU": "EU", "MT": "EU", "NL": "EU",
    "PL": "EU", "PT": "EU", "RO": "EU", "SK": "EU", "SI": "EU",
    "ES": "EU", "SE": "EU"
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
    # Try to get country-specific rates first
    country_rates = DEFAULT_TOLL_RATES.get(country_code)
    
    if country_rates:
        base_rate = country_rates["toll_class"].get(
            toll_class,
            country_rates["toll_class"]["1"]  # Default to class 1
        )
        
        euro_adjustment = country_rates["euro_class"].get(
            euro_class,
            country_rates["euro_class"]["III"]  # Default to EURO III
        )
    else:
        # Use region-based default rates
        region = COUNTRY_REGION_MAP.get(country_code, "OTHER")
        region_rates = DEFAULT_RATES_BY_REGION[region]
        
        base_rate = region_rates["toll_class"].get(
            toll_class,
            region_rates["toll_class"]["1"]  # Default to class 1
        )
        
        euro_adjustment = region_rates["euro_class"].get(
            euro_class,
            region_rates["euro_class"]["III"]  # Default to EURO III
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