"""Seed data for LoadApp.AI database initialization."""
from decimal import Decimal
import uuid

# Rate Validation Rules
RATE_VALIDATION_RULES = [
    {
        "id": str(uuid.uuid4()),
        "rate_type": "fuel_rate",
        "min_value": Decimal("0.5"),
        "max_value": Decimal("5.0"),
        "country_specific": True,
        "requires_certification": False,
        "description": "Fuel rate per liter"
    },
    {
        "id": str(uuid.uuid4()),
        "rate_type": "fuel_surcharge_rate",
        "min_value": Decimal("0.01"),
        "max_value": Decimal("0.5"),
        "country_specific": True,
        "requires_certification": False,
        "description": "Additional fuel surcharge percentage"
    },
    {
        "id": str(uuid.uuid4()),
        "rate_type": "toll_rate",
        "min_value": Decimal("0.1"),
        "max_value": Decimal("2.0"),
        "country_specific": True,
        "requires_certification": False,
        "description": "Toll rate per kilometer"
    },
    {
        "id": str(uuid.uuid4()),
        "rate_type": "driver_base_rate",
        "min_value": Decimal("100.0"),
        "max_value": Decimal("500.0"),
        "country_specific": False,
        "requires_certification": False,
        "description": "Base daily rate for driver"
    },
    {
        "id": str(uuid.uuid4()),
        "rate_type": "driver_time_rate",
        "min_value": Decimal("10.0"),
        "max_value": Decimal("100.0"),
        "country_specific": True,
        "requires_certification": False,
        "description": "Hourly rate for driver time"
    },
    {
        "id": str(uuid.uuid4()),
        "rate_type": "driver_overtime_rate",
        "min_value": Decimal("15.0"),
        "max_value": Decimal("150.0"),
        "country_specific": True,
        "requires_certification": False,
        "description": "Overtime hourly rate for driver"
    },
    {
        "id": str(uuid.uuid4()),
        "rate_type": "event_rate",
        "min_value": Decimal("20.0"),
        "max_value": Decimal("200.0"),
        "country_specific": False,
        "requires_certification": False,
        "description": "Rate per timeline event"
    },
    {
        "id": str(uuid.uuid4()),
        "rate_type": "refrigeration_rate",
        "min_value": Decimal("0.2"),
        "max_value": Decimal("1.0"),
        "country_specific": True,
        "requires_certification": True,
        "description": "Additional rate per km for refrigeration"
    }
] 

# Transport Types with their specifications
TRANSPORT_TYPES = [
    {
        "id": "flatbed",
        "name": "Flatbed Truck",
        "truck_specs": {
            "fuel_consumption_empty": 0.22,
            "fuel_consumption_loaded": 0.29,
            "toll_class": "4-axle",
            "euro_class": "EURO6",
            "co2_class": "A",
            "maintenance_rate_per_km": "0.15"
        },
        "driver_specs": {
            "daily_rate": "138.00",
            "required_license_type": "CE",
            "required_certifications": ["ADR"],
            "driving_time_rate": "35.00"
        }
    },
    {
        "id": "container",
        "name": "Container Truck",
        "truck_specs": {
            "fuel_consumption_empty": 0.24,
            "fuel_consumption_loaded": 0.32,
            "toll_class": "5-axle",
            "euro_class": "EURO6",
            "co2_class": "B",
            "maintenance_rate_per_km": "0.18"
        },
        "driver_specs": {
            "daily_rate": "142.00",
            "required_license_type": "CE",
            "required_certifications": ["Container", "ADR"],
            "driving_time_rate": "36.00"
        }
    },
    {
        "id": "livestock",
        "name": "Livestock Carrier",
        "truck_specs": {
            "fuel_consumption_empty": 0.25,
            "fuel_consumption_loaded": 0.33,
            "toll_class": "4-axle",
            "euro_class": "EURO6",
            "co2_class": "B",
            "maintenance_rate_per_km": "0.20"
        },
        "driver_specs": {
            "daily_rate": "145.00",
            "required_license_type": "CE",
            "required_certifications": ["Livestock", "Animal welfare"],
            "driving_time_rate": "37.00"
        }
    },
    {
        "id": "plandeka",
        "name": "Tautliner",
        "truck_specs": {
            "fuel_consumption_empty": 0.23,
            "fuel_consumption_loaded": 0.30,
            "toll_class": "4-axle",
            "euro_class": "EURO6",
            "co2_class": "A",
            "maintenance_rate_per_km": "0.16"
        },
        "driver_specs": {
            "daily_rate": "140.00",
            "required_license_type": "CE",
            "required_certifications": ["ADR"],
            "driving_time_rate": "35.50"
        }
    },
    {
        "id": "oversized",
        "name": "Oversized Transport",
        "truck_specs": {
            "fuel_consumption_empty": 0.35,
            "fuel_consumption_loaded": 0.45,
            "toll_class": "special",
            "euro_class": "EURO6",
            "co2_class": "C",
            "maintenance_rate_per_km": "0.25"
        },
        "driver_specs": {
            "daily_rate": "160.00",
            "required_license_type": "CE",
            "required_certifications": ["Oversized", "Special transport"],
            "driving_time_rate": "40.00"
        }
    },
    {
        "id": "refrigerated",
        "name": "Refrigerated Truck",
        "truck_specs": {
            "fuel_consumption_empty": 0.26,
            "fuel_consumption_loaded": 0.35,
            "toll_class": "4-axle",
            "euro_class": "EURO6",
            "co2_class": "B",
            "maintenance_rate_per_km": "0.22"
        },
        "driver_specs": {
            "daily_rate": "150.00",
            "required_license_type": "CE",
            "required_certifications": ["ADR", "ATP"],
            "driving_time_rate": "38.00"
        }
    }
]

# Business Entities with their settings
BUSINESS_ENTITIES = [
    {
        "id": str(uuid.uuid4()),
        "name": "EcoTrans GmbH",
        "address": "Hauptstraße 123, 10115 Berlin, Germany",
        "contact_info": {
            "email": "contact@ecotrans.de",
            "phone": "+49 30 123456",
            "website": "www.ecotrans.de"
        },
        "business_type": "carrier",
        "certifications": [
            "ISO 9001",
            "ISO 14001",  # Environmental management
            "GDP",        # Good Distribution Practice
            "SQAS"       # Safety & Quality Assessment System
        ],
        "operating_countries": ["DE", "PL", "CZ", "AT", "NL"],
        "cost_overheads": {
            "admin": "100.00",
            "insurance": "250.00",
            "eco_compliance": "180.00",
            "quality_management": "150.00"
        },
        "default_cost_settings": {
            "fuel_rate": "1.85",            # Slightly higher due to eco-friendly fuel
            "driver_base_rate": "200.00",   # Premium for qualified eco-drivers
            "toll_rate": "0.18",
            "enabled_components": ["fuel", "toll", "driver", "eco"]
        },
        "is_active": True
    },
    {
        "id": str(uuid.uuid4()),
        "name": "SpeedLog Express",
        "address": "Logistics Park 45, 00-001 Warsaw, Poland",
        "contact_info": {
            "email": "operations@speedlog.pl",
            "phone": "+48 22 987654",
            "website": "www.speedlog.pl"
        },
        "business_type": "logistics_provider",
        "certifications": [
            "ISO 9001",
            "AEO",        # Authorized Economic Operator
            "TAPA FSR"    # Security certification
        ],
        "operating_countries": ["PL", "DE", "CZ", "SK", "HU", "LT"],
        "cost_overheads": {
            "admin": "80.00",
            "insurance": "200.00",
            "security": "120.00",
            "tracking": "90.00"
        },
        "default_cost_settings": {
            "fuel_rate": "1.65",
            "driver_base_rate": "150.00",
            "toll_rate": "0.17",
            "enabled_components": ["fuel", "toll", "driver", "security"]
        },
        "is_active": True
    },
    {
        "id": str(uuid.uuid4()),
        "name": "HeavyHaul Solutions",
        "address": "Industrieweg 78, 3542 AD Utrecht, Netherlands",
        "contact_info": {
            "email": "info@heavyhaul.nl",
            "phone": "+31 30 789012",
            "website": "www.heavyhaul.nl"
        },
        "business_type": "specialized_transport",
        "certifications": [
            "ISO 9001",
            "DEKRA",          # Technical inspection certification
            "IMCA",           # Heavy lift certification
            "LEEA"            # Lifting Equipment Engineers Association
        ],
        "operating_countries": ["NL", "DE", "BE", "FR"],
        "cost_overheads": {
            "admin": "150.00",
            "insurance": "400.00",
            "special_equipment": "300.00",
            "permits": "250.00"
        },
        "default_cost_settings": {
            "fuel_rate": "1.75",
            "driver_base_rate": "180.00",
            "toll_rate": "0.20",
            "enabled_components": ["fuel", "toll", "driver", "permits"]
        },
        "is_active": True
    },
    {
        "id": str(uuid.uuid4()),
        "name": "FreshFood Logistics",
        "address": "Via Logistica 45, 20019 Milan, Italy",
        "contact_info": {
            "email": "info@freshfood-log.it",
            "phone": "+39 02 123456",
            "website": "www.freshfood-logistics.it"
        },
        "business_type": "food_transport",
        "certifications": [
            "ISO 22000",     # Food safety
            "HACCP",         # Food safety
            "IFS Logistics", # Food safety
            "ATP"           # Temperature-controlled transport
        ],
        "operating_countries": ["IT", "FR", "DE", "ES"],
        "cost_overheads": {
            "admin": "120.00",
            "insurance": "300.00",
            "temperature_monitoring": "200.00",
            "quality_control": "180.00"
        },
        "default_cost_settings": {
            "fuel_rate": "1.70",
            "driver_base_rate": "160.00",
            "toll_rate": "0.18",
            "refrigeration_rate": "0.25",
            "enabled_components": ["fuel", "toll", "driver", "refrigeration"]
        },
        "is_active": True
    }
]

# Cargo Types with their validation rules
CARGO_TYPES = [
    {
        "id": "general",
        "name": "General Cargo",
        "requires_temp_control": False,
        "requires_certification": False,
        "min_volume": 0.1,
        "max_volume": 100.0,
        "allowed_transport_types": ["flatbed", "container", "plandeka"]
    },
    {
        "id": "perishable",
        "name": "Perishable Goods",
        "requires_temp_control": True,
        "requires_certification": True,
        "min_volume": 0.1,
        "max_volume": 80.0,
        "allowed_transport_types": ["refrigerated"]
    },
    {
        "id": "oversized",
        "name": "Oversized Cargo",
        "requires_temp_control": False,
        "requires_certification": True,
        "min_volume": 50.0,
        "max_volume": 200.0,
        "allowed_transport_types": ["oversized"]
    },
    {
        "id": "livestock",
        "name": "Live Animals",
        "requires_temp_control": True,
        "requires_certification": True,
        "min_volume": 10.0,
        "max_volume": 90.0,
        "allowed_transport_types": ["livestock"]
    },
    {
        "id": "dangerous",
        "name": "Dangerous Goods",
        "requires_temp_control": False,
        "requires_certification": True,
        "min_volume": 0.1,
        "max_volume": 70.0,
        "allowed_transport_types": ["container", "flatbed"]
    }
] 