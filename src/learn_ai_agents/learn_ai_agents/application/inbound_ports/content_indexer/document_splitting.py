"""Inbound port for document splitting use cases.

This module defines the port (interface) that controllers use to access
document splitting functionality.
"""

from abc import ABC, abstractmethod

from learn_ai_agents.application.dtos.content_indexer.document_splitting import (
    DocumentSplittingRequestDTO,
    DocumentSplittingResponseDTO,
)


class DocumentSplittingInboundPort(ABC):
    """Port for document splitting use cases.

    This abstract interface defines the contract for document splitting
    operations exposed to the API layer.
    """

    @abstractmethod
    async def split_documents(self, request: DocumentSplittingRequestDTO) -> DocumentSplittingResponseDTO:
        """Split documents into chunks and store them.

        Args:
            request: The document splitting request containing document_id and parameters.

        Returns:
            DocumentSplittingResponseDTO with splitting results.

        Raises:
            DomainException: If splitting or storage fails.
        """
        ...
