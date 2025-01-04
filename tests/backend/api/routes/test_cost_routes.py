"""Tests for cost routes."""
import json
import uuid
from decimal import Decimal
from datetime import datetime, timezone
import pytest
from flask import g

from backend.infrastructure.models.cargo_models import CostBreakdownModel
from backend.infrastructure.models.route_models import RouteModel
from backend.infrastructure.models.transport_models import (
    TransportTypeModel, TruckSpecificationModel,
    DriverSpecificationModel, TransportModel
)
from backend.infrastructure.models.business_models import BusinessEntityModel 