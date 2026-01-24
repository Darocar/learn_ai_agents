"""Inbound port for vectorization use cases.

This module defines the port (interface) that controllers use to access
vectorization functionality.
"""

from abc import ABC, abstractmethod

from learn_ai_agents.application.dtos.content_indexer.vectorization import (
    VectorizationRequestDTO,
    VectorizationResponseDTO,
)


class VectorizationInboundPort(ABC):
    """Port for vectorization use cases.

    This abstract interface defines the contract for vectorization
    operations exposed to the API layer.
    """

    @abstractmethod
    async def vectorize_chunks(self, request: VectorizationRequestDTO) -> VectorizationResponseDTO:
        """Vectorize document chunks and store them in the vector database.

        Args:
            request: The vectorization request containing document_id and parameters.

        Returns:
            VectorizationResponseDTO with vectorization results.

        Raises:
            DomainException: If vectorization or storage fails.
        """
        ...
