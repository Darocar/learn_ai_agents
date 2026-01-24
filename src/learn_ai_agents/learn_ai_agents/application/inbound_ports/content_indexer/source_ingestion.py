"""Inbound port for content ingestion use cases.

This module defines the port (interface) that controllers use to access
content ingestion functionality.
"""

from typing import Protocol

from learn_ai_agents.application.dtos.content_indexer.source_ingestion import (
    SourceIngestionRequestDTO,
    SourceIngestionResponseDTO,
)


class SourceIngestionInboundPort(Protocol):
    """Port for content ingestion use cases.

    This abstract interface defines the contract for content ingestion
    operations exposed to the API layer.
    """

    async def ingest_content(self, request: SourceIngestionRequestDTO) -> SourceIngestionResponseDTO:
        """Ingest content from a source and store it.

        Args:
            request: The content ingestion request containing source and params.

        Returns:
            SourceIngestionResponseDTO with ingestion results.

        Raises:
            DomainException: If ingestion fails.
        """
        ...
