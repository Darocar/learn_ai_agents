"""Document splitting use case implementation.

This module implements the business logic for splitting documents into
chunks using various splitting strategies and storing them in the repository.
"""

from typing import Dict

from learn_ai_agents.application.dtos.content_indexer.document_splitting import (
    DocumentSplittingRequestDTO,
    DocumentSplittingResponseDTO,
    ChunkMetadataDTO,
)
from learn_ai_agents.application.inbound_ports.content_indexer.document_splitting import (
    DocumentSplittingInboundPort,
)
from learn_ai_agents.application.outbound_ports.content_indexer.repositories.document_repository import (
    DocumentRepositoryPort,
)
from learn_ai_agents.application.outbound_ports.content_indexer.repositories.chunk_repository import (
    ChunkRepositoryPort,
)
from learn_ai_agents.application.outbound_ports.content_indexer.splitters.chunk_splitter import (
    ChunkSplitterPort,
)

from learn_ai_agents.domain.exceptions._base import BusinessRuleException
from learn_ai_agents.logging import get_logger

logger = get_logger(__name__)


class DocumentSplittingUseCase(DocumentSplittingInboundPort):
    """Use case for splitting documents into chunks.

    This use case orchestrates the document splitting process by:
    1. Retrieving documents by document_id
    2. Splitting each document using the specified splitter
    3. Storing the resulting chunks in the repository

    Attributes:
        document_repository: Port for retrieving documents.
        chunk_repository: Port for storing chunks.
        splitter: Port for splitting documents into chunks.
    """

    def __init__(
        self,
        document_repository: DocumentRepositoryPort,
        chunk_repository: ChunkRepositoryPort,
        document_splitters: Dict[str, ChunkSplitterPort],
    ):
        """Initialize the document splitting use case.

        Args:
            document_repository: Port for retrieving documents.
            chunk_repository: Port for storing chunks.
            splitter: Port for splitting documents into chunks.
        """
        self.document_repository = document_repository
        self.chunk_repository = chunk_repository
        self.document_splitters: Dict[str, ChunkSplitterPort] = document_splitters
        logger.info("DocumentSplittingUseCase initialized")

    async def split_documents(self, request: DocumentSplittingRequestDTO) -> DocumentSplittingResponseDTO:
        """Split documents by document_id into chunks and store them.

        Args:
            request: The document splitting request containing document_id and parameters.

        Returns:
            DocumentSplittingResponseDTO with splitting results.

        Raises:
            DomainException: If retrieval, splitting, or storage fails.
        """
        logger.info(f"Starting document splitting for document_id: {request.document_id}")

        # 1. Retrieve all documents with the given document_id
        documents = await self.document_repository.find_documents_by_document_id(request.document_id)

        if not documents:
            raise BusinessRuleException(f"No documents found with document_id: {request.document_id}")

        logger.debug(f"Found {len(documents)} document(s) to process")

        # 2. Split each document into chunks
        all_chunks = []
        chunk_metadata_list = []
        document_splitter = self.document_splitters.get(request.splitter_approach)
        if not document_splitter:
            raise BusinessRuleException(f"Splitter not found for approach: {request.splitter_approach}")
        for document in documents:
            logger.debug(f"Splitting document {document.document_id}")

            try:
                # Split the document using the configured splitter
                chunks = document_splitter.split_document(document, request.splitter_approach)

                logger.debug(f"Document {document.document_id} split into {len(chunks)} chunks")

                # Collect chunks for batch storage
                all_chunks.extend(chunks)

                # Prepare metadata for response
                for chunk in chunks:
                    metadata = chunk.metadata or {}
                    chunk_metadata = ChunkMetadataDTO(
                        chunk_id=chunk.chunk_id,
                        document_id=chunk.document_id,
                        split_index=chunk.split_index,
                        chunk_size=metadata.get("chunk_size", len(chunk.content)),
                        splitter=metadata.get("splitter", "unknown"),
                        h1_title=metadata.get("h1_title"),
                        h2_header=metadata.get("h2_header"),
                    )
                    chunk_metadata_list.append(chunk_metadata)

            except Exception as e:
                logger.error(f"Failed to split document {document.document_id}: {str(e)}")
                raise BusinessRuleException(f"Document splitting failed for document {document.document_id}: {str(e)}") from e

        # 3. Upsert all chunks in the repository (create or update)
        logger.debug(f"Upserting {len(all_chunks)} chunks in repository")

        try:
            saved_chunks = await self.chunk_repository.upsert_chunks(all_chunks)
            logger.info(f"Successfully upserted {len(saved_chunks)} chunks for document_id: {request.document_id}")
        except Exception as e:
            logger.error(f"Failed to upsert chunks: {str(e)}")
            raise BusinessRuleException(f"Chunk upsert failed: {str(e)}") from e

        # 4. Return response
        return DocumentSplittingResponseDTO(
            document_id=request.document_id,
            total_chunks_created=len(saved_chunks),
            chunks=chunk_metadata_list,
            message=f"Successfully split {len(documents)} document(s) into {len(saved_chunks)} chunk(s)",
        )
