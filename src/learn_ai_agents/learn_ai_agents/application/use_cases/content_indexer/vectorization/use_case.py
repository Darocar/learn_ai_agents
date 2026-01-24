"""Vectorization use case implementation.

This module implements the business logic for vectorizing document chunks
and storing them in a vector database.
"""

from typing import Dict

from learn_ai_agents.application.dtos.content_indexer.vectorization import (
    VectorizationRequestDTO,
    VectorizationResponseDTO,
)
from learn_ai_agents.application.inbound_ports.content_indexer.vectorization import (
    VectorizationInboundPort,
)
from learn_ai_agents.application.outbound_ports.content_indexer.repositories.chunk_repository import (
    ChunkRepositoryPort,
)
from learn_ai_agents.application.outbound_ports.content_indexer.embedders.embedder import (
    EmbedderPort,
)
from learn_ai_agents.application.outbound_ports.content_indexer.repositories.vector_store_repository import (
    VectorStoreRepositoryPort,
)

from learn_ai_agents.domain.exceptions._base import BusinessRuleException
from learn_ai_agents.logging import get_logger

logger = get_logger(__name__)


class VectorizationUseCase(VectorizationInboundPort):
    """Use case for vectorizing document chunks.

    This use case orchestrates the vectorization process by:
    1. Retrieving chunks by document_id from the chunk repository
    2. Generating embeddings for each chunk using the specified embedder
    3. Storing the chunks with their embeddings in the vector store

    Attributes:
        chunk_repository: Port for retrieving document chunks.
        embedders: Dictionary of embedders by approach name.
        vector_store: Repository port for storing chunks with embeddings in vector database.
    """

    def __init__(
        self,
        chunk_repository: ChunkRepositoryPort,
        embedders: Dict[str, EmbedderPort],
        vector_store: VectorStoreRepositoryPort,
    ):
        """Initialize the vectorization use case.

        Args:
            chunk_repository: Port for retrieving document chunks.
            embedders: Dictionary of embedders by approach name.
            vector_store: Port for storing chunks with embeddings.
        """
        self.chunk_repository = chunk_repository
        self.embedders: Dict[str, EmbedderPort] = embedders
        self.vector_store = vector_store
        logger.info("VectorizationUseCase initialized")

    async def vectorize_chunks(self, request: VectorizationRequestDTO) -> VectorizationResponseDTO:
        """Vectorize chunks by document_id and store them in the vector database.

        Args:
            request: The vectorization request containing document_id and parameters.

        Returns:
            VectorizationResponseDTO with vectorization results.

        Raises:
            DomainException: If retrieval, embedding generation, or storage fails.
        """
        logger.info(
            f"Starting vectorization for document_id: {request.document_id} "
            f"with approach: {request.vectorization_approach}"
        )

        # 1. Retrieve all chunks with the given document_id
        chunks = await self.chunk_repository.find_chunks_by_document_id(request.document_id)

        if not chunks:
            raise BusinessRuleException(f"No chunks found with document_id: {request.document_id}")

        logger.debug(f"Found {len(chunks)} chunk(s) to vectorize")

        # 2. Get the appropriate embedder
        embedder = self.embedders.get(request.vectorization_approach)
        if not embedder:
            raise BusinessRuleException(f"Embedder not found for approach: {request.vectorization_approach}")

        # 3. Generate embeddings for all chunks
        try:
            logger.debug(f"Generating embeddings using {embedder.get_model_name()}")
            texts = [chunk.content for chunk in chunks]
            embeddings = await embedder.embed_texts(texts)

            if len(embeddings) != len(chunks):
                raise BusinessRuleException(f"Embedding count mismatch: expected {len(chunks)}, got {len(embeddings)}")

            logger.debug(
                f"Successfully generated {len(embeddings)} embeddings with {embedder.get_dimensions()} dimensions"
            )
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {str(e)}")
            raise BusinessRuleException(f"Embedding generation failed: {str(e)}") from e

        # 4. Enrich chunks with embedding model metadata
        embedding_model_metadata = {
            "model_name": embedder.get_model_name(),
            "dimensions": embedder.get_dimensions(),
            "vectorization_approach": request.vectorization_approach,
        }

        # Add embedding metadata to each chunk's metadata
        enriched_chunks = []
        for chunk in chunks:
            # Create a copy of metadata and add embedding info
            chunk_metadata = chunk.metadata.copy() if chunk.metadata else {}
            chunk_metadata["embedding_model"] = embedding_model_metadata

            # Create new chunk with enriched metadata
            from learn_ai_agents.domain.models.content_indexer.document_chunk import DocumentChunk

            enriched_chunk = DocumentChunk(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                split_index=chunk.split_index,
                content=chunk.content,
                metadata=chunk_metadata,
                character_name=chunk.character_name,
            )
            enriched_chunks.append(enriched_chunk)

        # 5. Store enriched chunks with embeddings in the vector store
        try:
            logger.debug(f"Storing {len(enriched_chunks)} chunks in vector store")
            await self.vector_store.upsert_vectors(
                document_id=request.document_id, chunks=enriched_chunks, vectors=embeddings
            )

            logger.info(f"Successfully stored {len(enriched_chunks)} vectors for document_id: {request.document_id}")
        except Exception as e:
            logger.error(f"Failed to store vectors: {str(e)}")
            raise BusinessRuleException(f"Vector storage failed: {str(e)}") from e

        # 6. Return response
        return VectorizationResponseDTO(
            document_id=request.document_id,
            total_vectors_created=len(enriched_chunks),
            message=f"Successfully vectorized {len(chunks)} chunk(s) and stored in vector database",
        )
