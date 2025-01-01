"""Dependency injection container for the application."""
from typing import Dict, Any

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

from .repositories.transport_repository import SQLTransportRepository
from .repositories.route_repository import SQLRouteRepository
from .repositories.cargo_repository import SQLCostSettingsRepository, SQLCostBreakdownRepository
from .repositories.business_repository import SQLBusinessRepository


class Container:
    """Service container for dependency injection."""

    def __init__(self, config: Dict[str, Any]):
        self._config = config
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
            lambda: GoogleMapsService(api_key=self._config['GOOGLE_MAPS_API_KEY'])
        )

    def toll_rate_service(self) -> TollRateService:
        """Get toll rate service instance."""
        return self._get_or_create(
            'toll_rate_service',
            lambda: TollRateService()
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
        return self._get_or_create(
            'google_maps_adapter',
            lambda: GoogleMapsAdapter(self.google_maps_service())
        )

    def toll_rate_adapter(self) -> TollRateAdapter:
        """Get toll rate adapter instance."""
        return self._get_or_create(
            'toll_rate_adapter',
            lambda: TollRateAdapter(self.toll_rate_service())
        )

    def openai_adapter(self) -> OpenAIAdapter:
        """Get OpenAI adapter instance."""
        return self._get_or_create(
            'openai_adapter',
            lambda: OpenAIAdapter(self.openai_service())
        )

    # Repositories
    def transport_repository(self) -> SQLTransportRepository:
        """Get transport repository instance."""
        return self._get_or_create(
            'transport_repository',
            SQLTransportRepository
        )

    def route_repository(self) -> SQLRouteRepository:
        """Get route repository instance."""
        return self._get_or_create(
            'route_repository',
            SQLRouteRepository
        )

    def cost_settings_repository(self) -> SQLCostSettingsRepository:
        """Get cost settings repository instance."""
        return self._get_or_create(
            'cost_settings_repository',
            SQLCostSettingsRepository
        )

    def cost_breakdown_repository(self) -> SQLCostBreakdownRepository:
        """Get cost breakdown repository instance."""
        return self._get_or_create(
            'cost_breakdown_repository',
            SQLCostBreakdownRepository
        )

    def business_repository(self) -> SQLBusinessRepository:
        """Get business repository instance."""
        return self._get_or_create(
            'business_repository',
            SQLBusinessRepository
        )

    # Domain Services
    def transport_service(self) -> TransportService:
        """Get transport service instance."""
        return self._get_or_create(
            'transport_service',
            lambda: TransportService(
                transport_repo=self.transport_repository(),
                transport_type_repo=self.transport_repository()
            )
        )

    def route_service(self) -> RouteService:
        """Get route service instance."""
        return self._get_or_create(
            'route_service',
            lambda: RouteService(
                route_repo=self.route_repository(),
                route_calculator=self.google_maps_adapter()
            )
        )

    def cost_service(self) -> CostService:
        """Get cost service instance."""
        return self._get_or_create(
            'cost_service',
            lambda: CostService(
                settings_repo=self.cost_settings_repository(),
                breakdown_repo=self.cost_breakdown_repository(),
                toll_calculator=self.toll_rate_adapter()
            )
        )

    def offer_service(self) -> OfferService:
        """Get offer service instance."""
        return self._get_or_create(
            'offer_service',
            lambda: OfferService(
                offer_repo=self.cost_breakdown_repository(),
                content_enhancer=self.openai_adapter()
            )
        ) 