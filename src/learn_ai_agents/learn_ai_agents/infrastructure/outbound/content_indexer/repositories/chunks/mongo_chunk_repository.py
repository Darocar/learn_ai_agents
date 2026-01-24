"""MongoDB repository implementation for chunks using Odmantic.

This module implements chunk persistence using the repository pattern
with Odmantic for type-safe MongoDB operations.
"""

from datetime import datetime

from learn_ai_agents.application.outbound_ports.content_indexer.repositories.chunk_repository import (
    ChunkRepositoryPort,
)
from learn_ai_agents.application.outbound_ports.database import DatabaseClient
from learn_ai_agents.domain.models.content_indexer.document_chunk import DocumentChunk
from .models import ChunkModel
from learn_ai_agents.infrastructure.outbound.base_persistence import (
    BaseMongoModelRepository,
)
from learn_ai_agents.logging import get_logger

logger = get_logger(__name__)


class MongoChunkRepository(BaseMongoModelRepository[ChunkModel], ChunkRepositoryPort):
    """MongoDB implementation of the ChunkRepositoryPort using Odmantic.

    This adapter implements the ChunkRepositoryPort by inheriting from
    BaseMongoModelRepository and handling the mapping between domain
    DocumentChunk objects and ODM ChunkModel models.
    """

    def __init__(self, database: DatabaseClient):
        """Initialize the MongoDB chunk repository.

        Args:
            database: The database client instance (MongoEngineAdapter).
        """
        super().__init__(database.get_engine(), ChunkModel)
        logger.info("MongoDB chunk repository initialized with Odmantic")

    async def save_chunk(self, chunk: DocumentChunk) -> DocumentChunk:
        """Save a document chunk to the repository.

        Args:
            chunk: The domain DocumentChunk to save.

        Returns:
            The saved chunk with updated ID.
        """
        logger.debug(f"Saving chunk for document_id={chunk.document_id}")

        # Map domain DocumentChunk to ODM ChunkModel
        chunk_model = ChunkModel(  # type: ignore[call-arg]
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            split_index=chunk.split_index,
            content=chunk.content,
            metadata=chunk.metadata,
            character_name=chunk.character_name,
        )

        # Save using base repository
        saved_model = await self.save_one(chunk_model)

        # Map back to domain DocumentChunk
        return DocumentChunk(
            chunk_id=saved_model.chunk_id,
            document_id=saved_model.document_id,
            split_index=saved_model.split_index,
            content=saved_model.content,
            metadata=saved_model.metadata,
            character_name=saved_model.character_name,
        )

    async def save_chunks(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        """Save multiple document chunks to the repository.

        Args:
            chunks: List of domain DocumentChunks to save.

        Returns:
            List of saved chunks with updated IDs.
        """
        if not chunks:
            return []

        logger.debug(f"Saving {len(chunks)} chunks")

        # Map domain DocumentChunks to ODM ChunkModels
        chunk_models = [
            ChunkModel(  # type: ignore[call-arg]
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                split_index=chunk.split_index,
                content=chunk.content,
                metadata=chunk.metadata,
                character_name=chunk.character_name,
            )
            for chunk in chunks
        ]

        # Save using base repository
        saved_models = await self.save_many(chunk_models)

        # Map back to domain DocumentChunks
        return [
            DocumentChunk(
                chunk_id=model.chunk_id,
                document_id=model.document_id,
                split_index=model.split_index,
                content=model.content,
                metadata=model.metadata,
                character_name=model.character_name,
            )
            for model in saved_models
        ]

    async def get_chunk_by_id(self, chunk_id: str) -> DocumentChunk | None:
        """Retrieve a chunk by its ID.

        Args:
            chunk_id: The ID of the chunk to retrieve.

        Returns:
            The domain DocumentChunk if found, None otherwise.
        """
        logger.debug(f"Fetching chunk with id={chunk_id}")

        chunk_model = await self.get_by_id(chunk_id)
        if chunk_model is None:
            return None

        # Map ODM ChunkModel to domain DocumentChunk
        return DocumentChunk(
            chunk_id=chunk_model.chunk_id,
            document_id=chunk_model.document_id,
            split_index=chunk_model.split_index,
            content=chunk_model.content,
            metadata=chunk_model.metadata,
            character_name=chunk_model.character_name,
        )

    async def find_chunks_by_document_id(self, document_id: str) -> list[DocumentChunk]:
        """Find all chunks belonging to a specific document.

        Args:
            document_id: The ID of the parent document.

        Returns:
            List of domain DocumentChunks belonging to the document.
        """
        logger.debug(f"Finding chunks for document_id={document_id}")

        chunk_models = await self.find_by(document_id=document_id)

        # Map ODM ChunkModels to domain DocumentChunks
        return [
            DocumentChunk(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                split_index=chunk.split_index,
                content=chunk.content,
                metadata=chunk.metadata,
                character_name=chunk.character_name,
            )
            for chunk in chunk_models
        ]

    async def delete_chunks_by_document_id(self, document_id: str) -> int:
        """Delete all chunks belonging to a specific document.

        Args:
            document_id: The ID of the parent document.

        Returns:
            Number of chunks deleted.
        """
        logger.debug(f"Deleting chunks for document_id={document_id}")

        # Find all chunks for this document
        chunks = await self.find_by(document_id=document_id)

        # Delete each chunk
        delete_count = 0
        for chunk in chunks:
            deleted = await self.delete_by_id(str(chunk.id))
            if deleted:
                delete_count += 1

        logger.info(f"Deleted {delete_count} chunks for document_id={document_id}")
        return delete_count

    async def upsert_chunks(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        """Upsert multiple document chunks to the repository.

        Updates existing chunks (matched by chunk_id) or inserts new ones.

        Args:
            chunks: List of domain DocumentChunks to upsert.

        Returns:
            List of upserted chunks.
        """
        if not chunks:
            return []

        logger.debug(f"Upserting {len(chunks)} chunks")

        upserted_chunks = []
        for chunk in chunks:
            # Find existing chunk by chunk_id
            existing_chunks = await self.find_by(chunk_id=chunk.chunk_id)

            if existing_chunks:
                # Update existing chunk
                existing_model = existing_chunks[0]
                existing_model.document_id = chunk.document_id
                existing_model.split_index = chunk.split_index
                existing_model.content = chunk.content
                existing_model.metadata = chunk.metadata
                existing_model.character_name = chunk.character_name
                existing_model.updated_at = datetime.now()

                saved_model = await self.save_one(existing_model)
                logger.debug(f"Updated chunk with chunk_id={chunk.chunk_id}")
            else:
                # Insert new chunk
                chunk_model = ChunkModel(  # type: ignore[call-arg]
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    split_index=chunk.split_index,
                    content=chunk.content,
                    metadata=chunk.metadata,
                    character_name=chunk.character_name,
                )
                saved_model = await self.save_one(chunk_model)
                logger.debug(f"Inserted new chunk with chunk_id={chunk.chunk_id}")

            # Map back to domain
            upserted_chunks.append(
                DocumentChunk(
                    chunk_id=saved_model.chunk_id,
                    document_id=saved_model.document_id,
                    split_index=saved_model.split_index,
                    content=saved_model.content,
                    metadata=saved_model.metadata,
                    character_name=saved_model.character_name,
                )
            )

        logger.info(f"Successfully upserted {len(upserted_chunks)} chunks")
        return upserted_chunks

    async def search_similar_chunks(
        self, query_vector: list[float], limit: int = 10, min_similarity: float = 0.0
    ) -> list[tuple[DocumentChunk, float]]:
        """Search for chunks similar to the query vector.

        Note:
            This is a placeholder implementation. For production use,
            you should either:
            1. Use MongoDB Atlas Vector Search (requires Atlas cluster)
            2. Integrate with a dedicated vector database (Qdrant, Weaviate, etc.)
            3. Implement a simple cosine similarity search (slow for large datasets)

        Args:
            query_vector: The embedding vector to search with.
            limit: Maximum number of results to return.
            min_similarity: Minimum similarity score threshold.

        Returns:
            List of (chunk, similarity_score) tuples, ordered by similarity.

        Raises:
            NotImplementedError: Vector search not yet implemented.
        """
        logger.warning("Vector search not yet implemented for MongoDB")
        raise NotImplementedError(
            "Vector search requires MongoDB Atlas Vector Search or integration "
            "with a dedicated vector database. This will be implemented when "
            "adding vector embedding capabilities."
        )
