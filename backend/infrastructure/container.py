"""Dependency injection container for the application."""
from typing import Dict, Any
from sqlalchemy.orm import Session
from flask import current_app, g

from .external_services.google_maps_service import GoogleMapsService
from .external_services.toll_rate_service import TollRateService
from .external_services.openai_service import OpenAIService

from .adapters.google_maps_adapter import GoogleMapsAdapter
from .adapters.toll_rate_adapter import TollRateAdapter
from .adapters.openai_adapter import OpenAIAdapter

from ..domain.services.transport_service import TransportService
from ..domain.services.route_service import RouteService
from ..domain.services.cost_service import CostService
from ..domain.services.offer_service import OfferService
from ..domain.services.business_service import BusinessService
from ..domain.services.cargo_service import CargoService
from ..domain.services.location_service import LocationService

from .repositories.transport_repository import SQLTransportRepository, SQLTransportTypeRepository
from .repositories.route_repository import SQLRouteRepository, SQLEmptyDrivingRepository
from .repositories.cargo_repository import (
    SQLCostSettingsRepository,
    SQLCostBreakdownRepository,
    SQLOfferRepository,
    SQLCargoRepository
)
from .repositories.business_repository import SQLBusinessRepository
from .repositories.location_repository import SQLLocationRepository
from .repositories.toll_rate_override_repository import TollRateOverrideRepository
from .repositories.rate_validation_repository import RateValidationRepository
from .repositories.empty_driving_repository import SQLEmptyDrivingRepository


class Container:
    """Service container for dependency injection."""

    def __init__(self, config: Dict[str, Any], db: Session):
        self._config = config
        self._db = db
        self._instances = {}

    def _get_or_create(self, key: str, creator):
        """Get an existing instance or create a new one."""
        if key not in self._instances:
            self._instances[key] = creator()
        return self._instances[key]

    # External Services
    def google_maps_service(self) -> GoogleMapsService:
        """Get Google Maps service instance."""
        return self._get_or_create(
            'google_maps_service',
            lambda: GoogleMapsService(
                api_key=self._config['GOOGLE_MAPS']['API_KEY'],
                location_repo=self.location_repository(),
                timeout=self._config['GOOGLE_MAPS']['TIMEOUT'],
                max_retries=self._config['GOOGLE_MAPS']['MAX_RETRIES'],
                retry_delay=self._config['GOOGLE_MAPS']['RETRY_DELAY']
            )
        )

    def toll_rate_service(self) -> TollRateService:
        """Get Toll Rate service instance."""
        return self._get_or_create(
            'toll_rate_service',
            lambda: TollRateService(
                api_key=self._config['TOLL_RATE']['API_KEY'],
                timeout=self._config['TOLL_RATE']['TIMEOUT'],
                max_retries=self._config['TOLL_RATE']['MAX_RETRIES'],
                retry_delay=self._config['TOLL_RATE']['RETRY_DELAY']
            )
        )

    def openai_service(self) -> OpenAIService:
        """Get OpenAI service instance."""
        return self._get_or_create(
            'openai_service',
            lambda: OpenAIService(api_key=self._config['OPENAI_API_KEY'])
        )

    # Adapters
    def google_maps_adapter(self) -> GoogleMapsAdapter:
        """Get Google Maps adapter instance."""
        return GoogleMapsAdapter(
            maps_service=self.google_maps_service()
        )

    def toll_rate_adapter(self) -> TollRateAdapter:
        """Get Toll Rate adapter instance."""
        return self._get_or_create(
            'toll_rate_adapter',
            lambda: TollRateAdapter(
                toll_service=self.toll_rate_service(),
                override_repository=TollRateOverrideRepository(self._db)
            )
        )

    def openai_adapter(self) -> OpenAIAdapter:
        """Get OpenAI adapter instance."""
        return self._get_or_create(
            'openai_adapter',
            lambda: OpenAIAdapter(self.openai_service())
        )

    def offer_enhancer(self) -> OpenAIAdapter:
        """Get offer enhancer instance."""
        return self._get_or_create(
            'offer_enhancer',
            lambda: OpenAIAdapter(self.openai_service())
        )

    # Repositories
    def transport_repository(self) -> SQLTransportRepository:
        """Get transport repository instance."""
        return self._get_or_create(
            'transport_repository',
            lambda: SQLTransportRepository(self._db)
        )

    def transport_type_repository(self) -> SQLTransportTypeRepository:
        """Get transport type repository instance."""
        return self._get_or_create(
            'transport_type_repository',
            lambda: SQLTransportTypeRepository(self._db)
        )

    def route_repository(self) -> SQLRouteRepository:
        """Get route repository instance."""
        return self._get_or_create(
            'route_repository',
            lambda: SQLRouteRepository(self._db)
        )

    def cost_settings_repository(self) -> SQLCostSettingsRepository:
        """Get cost settings repository instance."""
        return self._get_or_create(
            'cost_settings_repository',
            lambda: SQLCostSettingsRepository(self._db)
        )

    def cost_breakdown_repository(self) -> SQLCostBreakdownRepository:
        """Get cost breakdown repository instance."""
        return self._get_or_create(
            'cost_breakdown_repository',
            lambda: SQLCostBreakdownRepository(self._db)
        )

    def offer_repository(self) -> SQLOfferRepository:
        """Get offer repository instance."""
        return self._get_or_create(
            'offer_repository',
            lambda: SQLOfferRepository(self._db)
        )

    def cargo_repository(self) -> SQLCargoRepository:
        """Get cargo repository instance."""
        return self._get_or_create(
            'cargo_repository',
            lambda: SQLCargoRepository(self._db)
        )

    def business_repository(self) -> SQLBusinessRepository:
        """Get business repository instance."""
        return self._get_or_create(
            'business_repository',
            lambda: SQLBusinessRepository(self._db)
        )

    def location_repository(self) -> SQLLocationRepository:
        """Get location repository instance."""
        return self._get_or_create(
            'location_repository',
            lambda: SQLLocationRepository(self._db)
        )

    def empty_driving_repository(self) -> SQLEmptyDrivingRepository:
        """Get empty driving repository instance."""
        return self._get_or_create(
            'empty_driving_repository',
            lambda: SQLEmptyDrivingRepository(self._db)
        )

    # Domain Services
    def business_service(self) -> BusinessService:
        """Get business service instance."""
        return self._get_or_create(
            'business_service',
            lambda: BusinessService(business_repo=self.business_repository())
        )

    def transport_service(self) -> TransportService:
        """Get transport service instance."""
        return self._get_or_create(
            'transport_service',
            lambda: TransportService(
                transport_repo=self.transport_repository(),
                transport_type_repo=self.transport_type_repository(),
                business_service=self.business_service()
            )
        )

    def route_service(self) -> RouteService:
        """Get route service instance."""
        return self._get_or_create(
            'route_service',
            lambda: RouteService(
                route_repo=self.route_repository(),
                route_calculator=self.google_maps_adapter(),
                location_repo=self.location_repository()
            )
        )

    def cost_service(self) -> CostService:
        """Get cost service instance."""
        return self._get_or_create(
            'cost_service',
            lambda: CostService(
                settings_repo=self.cost_settings_repository(),
                breakdown_repo=self.cost_breakdown_repository(),
                empty_driving_repo=self.empty_driving_repository(),
                toll_calculator=self.toll_rate_adapter(),
                rate_validation_repo=RateValidationRepository(self._db),
                route_repo=self.route_repository(),
                transport_repo=self.transport_repository(),
                business_repo=self.business_repository()
            )
        )

    def offer_service(self) -> OfferService:
        """Get offer service instance."""
        return self._get_or_create(
            'offer_service',
            lambda: OfferService(
                offer_repository=self.offer_repository(),
                offer_enhancer=self.offer_enhancer(),
                cargo_repository=self.cargo_repository(),
                route_repository=self.route_repository(),
                cost_breakdown_repository=self.cost_breakdown_repository(),
                db=self._db
            )
        )

    def cargo_service(self) -> CargoService:
        """Get cargo service instance."""
        return self._get_or_create(
            'cargo_service',
            lambda: CargoService(
                cargo_repository=self.cargo_repository(),
                business_repository=self.business_repository(),
                route_service=self.route_service()
            )
        )

    def location_service(self) -> LocationService:
        """Get location service instance."""
        return self._get_or_create(
            'location_service',
            lambda: LocationService(
                location_repo=self.location_repository(),
                maps_service=self.google_maps_service()
            )
        )

def get_container() -> Container:
    """Get or create the container instance for the current request."""
    if not hasattr(g, 'container'):
        g.container = Container(current_app.config, g.db)
    return g.container 

def create_cost_service(session):
    """Create cost service with dependencies."""
    toll_service = TollRateService()
    toll_override_repo = TollRateOverrideRepository(session)
    toll_calculator = TollRateAdapter(toll_service, toll_override_repo)
    
    return CostService(
        settings_repo=SQLCostSettingsRepository(session),
        breakdown_repo=SQLCostBreakdownRepository(session),
        empty_driving_repo=SQLEmptyDrivingRepository(session),
        toll_calculator=toll_calculator,
        rate_validation_repo=RateValidationRepository(session),
        route_repo=SQLRouteRepository(session),
        transport_repo=SQLTransportRepository(session),
        business_repo=SQLBusinessRepository(session)
    ) 