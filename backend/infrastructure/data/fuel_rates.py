"""Default fuel rates and configurations."""
from decimal import Decimal
from typing import Dict, Any
import decimal

# Default fuel rates per country (EUR/L)
DEFAULT_FUEL_RATES = {
    "DE": Decimal("1.85"),  # Germany
    "FR": Decimal("1.82"),  # France
    "PL": Decimal("1.65"),  # Poland
    "NL": Decimal("1.88"),  # Netherlands
    "CZ": Decimal("1.70"),  # Czech Republic
    "AT": Decimal("1.83"),  # Austria
    "SK": Decimal("1.68"),  # Slovakia
    "HU": Decimal("1.63"),  # Hungary
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
        
    Raises:
        ValueError: If country code is invalid
    """
    if not country_code or not isinstance(country_code, str):
        raise ValueError(f"Invalid country code: {country_code}")
        
    country_code = country_code.upper()
    
    # Try to get country-specific rate first
    if country_code in DEFAULT_FUEL_RATES:
        return DEFAULT_FUEL_RATES[country_code]
    
    # Fall back to region-based default rate
    region = COUNTRY_REGION_MAP.get(country_code, "OTHER")
    return DEFAULT_RATES_BY_REGION[region]

def validate_fuel_rate(rate: Decimal) -> bool:
    """Validate if a fuel rate is within allowed range.
    
    Args:
        rate: Fuel rate to validate
        
    Returns:
        bool: True if rate is valid
    """
    try:
        rate_decimal = Decimal(str(rate))
        return Decimal("0.50") <= rate_decimal <= Decimal("5.00")
    except (TypeError, ValueError, decimal.InvalidOperation):
        return False

__all__ = [
    'DEFAULT_FUEL_RATES',
    'CONSUMPTION_RATES',
    'get_fuel_rate',
    'validate_fuel_rate'
] 