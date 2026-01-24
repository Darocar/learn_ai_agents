"""Outbound port for vector store repository operations.

This module defines the port (interface) for vector storage operations
in a vector database like Qdrant.
"""

from typing import Protocol, List, Dict

from learn_ai_agents.domain.models.content_indexer.document_chunk import DocumentChunk


class VectorStoreRepositoryPort(Protocol):
    """Protocol defining the interface for vector store repository operations.

    This port defines how the application layer stores and searches document
    chunks with embeddings in a vector database.
    """

    async def upsert_vectors(self, document_id: str, chunks: List[DocumentChunk], vectors: List[List[float]]) -> None:
        """Upsert document chunks with their vectors to the vector store.

        Args:
            document_id: The document ID to create collection for.
            chunks: List of DocumentChunk domain objects.
            vectors: List of embedding vectors corresponding to each chunk.

        Raises:
            DomainException: If storage fails.
        """
        ...

    async def search_similar(self, document_id: str, query_vector: list[float], limit: int = 5) -> List[Dict]:
        """Search for chunks similar to the query vector.

        Args:
            document_id: The document ID to search within.
            query_vector: The embedding vector to search with.
            limit: Maximum number of results to return.

        Returns:
            List of payload dictionaries containing chunk metadata.

        Raises:
            DomainException: If search fails.
        """
        ...

    async def delete_collection(self, document_id: str) -> None:
        """Delete the entire collection for a specific document.

        Args:
            document_id: The document ID whose collection to delete.

        Raises:
            DomainException: If deletion fails.
        """
        ...

    async def create_collection_if_not_exists(
        self, document_id: str, vector_size: int, distance: str = "COSINE"
    ) -> None:
        """Create collection if it doesn't exist.

        Args:
            document_id: The document ID to create collection for.
            vector_size: Dimensionality of the embedding vectors.
            distance: Distance metric (COSINE, DOT, EUCLID, MANHATTAN).

        Raises:
            DomainException: If creation fails.
        """
        ...

    async def get_personality(self, document_id: str) -> str:
        """Get the personality chunk for a character.

        Searches for a chunk with h2_header == '## Personality' in the metadata.

        Args:
            document_id: The document ID to search in.

        Returns:
            The personality content as a string.

        Raises:
            DomainException: If personality chunk not found or search fails.
        """
        ...
