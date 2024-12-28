"""Adapter for OpenAI service implementing ContentEnhancementPort."""
from typing import Tuple

from ...domain.entities.cargo import Offer
from ...domain.services.offer_service import ContentEnhancementPort
from ..external_services.openai_service import OpenAIService
from ..external_services.exceptions import ExternalServiceError


class OpenAIAdapter(ContentEnhancementPort):
    """Adapter implementing ContentEnhancementPort using OpenAI service."""

    def __init__(self, openai_service: OpenAIService):
        self._service = openai_service

    def enhance_offer(self, offer: Offer) -> Tuple[str, str]:
        """
        Generate enhanced content and fun fact for an offer.
        
        Args:
            offer: The offer to enhance
            
        Returns:
            Tuple containing:
            - Enhanced offer content (str)
            - Transport-related fun fact (str)
            
        Raises:
            ExternalServiceError: If OpenAI service fails
        """
        try:
            # Get enhanced content
            content = self._service.generate_offer_content(
                price=float(offer.final_price),
                margin=float(offer.margin_percentage)
            )

            # Get fun fact
            fun_fact = self._service.generate_fun_fact()

            return content, fun_fact

        except Exception as e:
            raise ExternalServiceError(
                f"Failed to enhance offer content: {str(e)}"
            ) from e 