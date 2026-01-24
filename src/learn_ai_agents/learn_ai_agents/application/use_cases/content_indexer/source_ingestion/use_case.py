"""Content ingestion use case implementation.

This module implements the business logic for ingesting content from
various sources and storing it in the document repository.
"""

from uuid import uuid4
from learn_ai_agents.application.dtos.content_indexer.source_ingestion import (
    SourceIngestionRequestDTO,
    SourceIngestionResponseDTO,
    DocumentMetadataDTO,
)
from learn_ai_agents.application.inbound_ports.content_indexer.source_ingestion import (
    SourceIngestionInboundPort,
)
from learn_ai_agents.application.outbound_ports.content_indexer.source_ingestion.source_ingestion import (
    SourceIngestionPort,
)
from learn_ai_agents.application.outbound_ports.content_indexer.repositories.document_repository import (
    DocumentRepositoryPort,
)
from learn_ai_agents.domain.models.content_indexer.source_ingestion import ContentRequest
from learn_ai_agents.logging import get_logger

logger = get_logger(__name__)


class SourceIngestionUseCase(SourceIngestionInboundPort):
    """Use case for ingesting content from various sources.

    This use case orchestrates content retrieval and storage by using
    the SourceIngestionPort to fetch content and DocumentRepositoryPort
    to persist it.

    Attributes:
        source_ingestion: Port for retrieving content from sources.
        document_repository: Port for storing documents.
    """

    def __init__(
        self,
        source_ingestion: SourceIngestionPort,
        document_repository: DocumentRepositoryPort,
    ):
        """Initialize the content ingestion use case.

        Args:
            source_ingestion: Port for retrieving content from sources.
            document_repository: Port for storing documents.
        """
        self.source_ingestion = source_ingestion
        self.document_repository = document_repository
        logger.info("SourceIngestionUseCase initialized")

    async def ingest_content(self, request: SourceIngestionRequestDTO) -> SourceIngestionResponseDTO:
        """Ingest content from a source and store it in MongoDB.

        Args:
            request: The content ingestion request containing source and params.

        Returns:
            ContentIngestionResponseDTO with ingestion results.

        Raises:
            DomainException: If retrieval or storage fails.
        """
        logger.info(f"Starting content ingestion from source: {request.source}")

        # Create domain ContentRequest
        content_request = ContentRequest(
            document_id=request.document_id if request.document_id else str(uuid4()),
            source=request.source,
            params=request.params,
            character_name=request.character_name,
        )

        # Retrieve content using the adapter
        logger.debug(f"Retrieving content with document_id: {content_request.document_id}")
        document = self.source_ingestion.retrieve_content(content_request)

        # Upsert document in MongoDB (create or update)
        logger.debug(f"Upserting document for document_id: {document.document_id}")
        saved_document = await self.document_repository.upsert_document(document)

        # Prepare metadata DTO
        metadata_dto = DocumentMetadataDTO(
            url=saved_document.metadata.get("url") if saved_document.metadata else None,
            title=(saved_document.metadata.get("title") if saved_document.metadata else None),
            description=(saved_document.metadata.get("description") if saved_document.metadata else None),
            content_type=(saved_document.metadata.get("content_type") if saved_document.metadata else None),
            source=(saved_document.metadata.get("source") if saved_document.metadata else None),
            character_name=saved_document.character_name,
        )

        # Calculate content length
        content_length = (
            len(saved_document.content) if isinstance(saved_document.content, str) else len(saved_document.content)
        )

        logger.info(
            f"Content ingestion completed. Document ID: {saved_document.document_id}, "
            f"Request ID: {saved_document.document_id}, Length: {content_length}"
        )

        return SourceIngestionResponseDTO(
            document_id=saved_document.document_id,
            content_length=content_length,
            metadata=metadata_dto,
        )
