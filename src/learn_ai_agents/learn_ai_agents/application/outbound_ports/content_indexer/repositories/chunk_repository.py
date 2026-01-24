"""Outbound port for chunk repository operations.

This module defines the port (interface) for document chunk persistence operations
in a traditional database (separate from vector storage).
"""

from typing import Protocol

from learn_ai_agents.domain.models.content_indexer.document_chunk import DocumentChunk


class ChunkRepositoryPort(Protocol):
    """Protocol defining the interface for chunk repository operations.

    This port defines how the application layer persists chunks in a traditional
    database for metadata and relationship management, separate from vector storage.
    """

    async def save_chunk(self, chunk: DocumentChunk) -> DocumentChunk:
        """Save a document chunk to the repository.

        Args:
            chunk: The DocumentChunk to save.

        Returns:
            The saved chunk with updated ID.

        Raises:
            DomainException: If save fails.
        """
        ...

    async def save_chunks(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        """Save multiple document chunks to the repository.

        Args:
            chunks: List of DocumentChunks to save.

        Returns:
            List of saved chunks with updated IDs.

        Raises:
            DomainException: If save fails.
        """
        ...

    async def get_chunk_by_id(self, chunk_id: str) -> DocumentChunk | None:
        """Retrieve a chunk by its ID.

        Args:
            chunk_id: The ID of the chunk to retrieve.

        Returns:
            The DocumentChunk if found, None otherwise.

        Raises:
            DomainException: If retrieval fails.
        """
        ...

    async def find_chunks_by_document_id(self, document_id: str) -> list[DocumentChunk]:
        """Find all chunks belonging to a specific document.

        Args:
            document_id: The ID of the parent document.

        Returns:
            List of DocumentChunks belonging to the document.

        Raises:
            DomainException: If retrieval fails.
        """
        ...

    async def delete_chunks_by_document_id(self, document_id: str) -> int:
        """Delete all chunks belonging to a specific document.

        Args:
            document_id: The ID of the parent document.

        Returns:
            Number of chunks deleted.

        Raises:
            DomainException: If deletion fails.
        """
        ...

    async def upsert_chunks(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        """Upsert multiple document chunks to the repository.

        Updates existing chunks (matched by chunk_id) or inserts new ones.

        Args:
            chunks: List of DocumentChunks to upsert.

        Returns:
            List of upserted chunks.

        Raises:
            DomainException: If upsert fails.
        """
        ...
