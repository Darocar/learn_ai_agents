"""Outbound port for content source providers.

This module defines the port (interface) for accessing and retrieving content
from various sources (web, files, databases, etc.).
"""

from typing import Protocol

from learn_ai_agents.domain.models.content_indexer.source_ingestion import ContentRequest, Document


class SourceIngestionPort(Protocol):
    """Protocol defining the interface for content source providers.

    This port defines how the application layer retrieves raw content from
    various sources without depending on specific retrieval implementations.

    Step 1 of the content indexing pipeline: Source Access/Retrieval
    """

    def retrieve_content(self, request: ContentRequest) -> Document:
        """Retrieve content from a source based on the request.

        Args:
            request: ContentRequest specifying the source and parameters.

        Returns:
            Document with the retrieved content and metadata.

        Raises:
            DomainException: If retrieval fails.
        """
        ...
