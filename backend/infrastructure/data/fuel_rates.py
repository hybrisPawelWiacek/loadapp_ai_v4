"""Default fuel rates and configurations."""
from decimal import Decimal
from typing import Dict, Any

# Default fuel rates per country (EUR/L)
DEFAULT_FUEL_RATES = {
    "DE": Decimal("1.85"),  # Germany
    "FR": Decimal("1.82"),  # France
    "PL": Decimal("1.65"),  # Poland
    "NL": Decimal("1.88"),  # Netherlands
}

# Default rates by region when country-specific rates are not available
DEFAULT_RATES_BY_REGION = {
    "EU": Decimal("1.80"),  # Average EU rate
    "OTHER": Decimal("1.60")  # Non-EU default rate
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

# Consumption rates (L/km)
CONSUMPTION_RATES = {
    "empty": Decimal("0.22"),    # Empty driving
    "loaded": Decimal("0.29"),   # Loaded driving
    "per_ton": Decimal("0.03")   # Additional per ton of cargo
}

def get_fuel_rate(country_code: str) -> Decimal:
    """Get fuel rate for a specific country.
    
    Args:
        country_code: ISO country code
        
    Returns:
        Fuel rate in EUR/L
    """
    # Try to get country-specific rate first
    if country_code in DEFAULT_FUEL_RATES:
        return DEFAULT_FUEL_RATES[country_code]
    
    # Fall back to region-based default rate
    region = COUNTRY_REGION_MAP.get(country_code, "OTHER")
    return DEFAULT_RATES_BY_REGION[region]

def get_consumption_rate(is_loaded: bool = False, cargo_weight: float = 0.0) -> Decimal:
    """Calculate fuel consumption rate based on load status and cargo weight.
    
    Args:
        is_loaded: Whether the vehicle is loaded
        cargo_weight: Weight of cargo in tons (if loaded)
        
    Returns:
        Fuel consumption rate in L/km
    """
    if not is_loaded:
        return CONSUMPTION_RATES["empty"]
    
    base_rate = CONSUMPTION_RATES["loaded"]
    weight_adjustment = CONSUMPTION_RATES["per_ton"] * Decimal(str(cargo_weight))
    
    return base_rate + weight_adjustment 