"""Qdrant vector store repository implementation.

This module implements vector storage using Qdrant, following the repository pattern.
Based on the Qdrant neural search tutorial.
"""

from typing import Any
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from learn_ai_agents.application.outbound_ports.content_indexer.repositories.vector_store_repository import (
    VectorStoreRepositoryPort,
)
from learn_ai_agents.domain.exceptions import ComponentConnectionException, ResourceNotFoundException, ComponentNotAvailableException, ComponentOperationException
from learn_ai_agents.domain.models.content_indexer import VectorDistanceMetric
from learn_ai_agents.domain.models.content_indexer.document_chunk import DocumentChunk
from learn_ai_agents.logging import get_logger

logger = get_logger(__name__)


class QdrantVectorStoreRepository(VectorStoreRepositoryPort):
    """Qdrant implementation of the VectorStoreRepositoryPort.

    This adapter implements vector storage using Qdrant with basic operations:
    - Creating collections dynamically per document_id
    - Upserting vectors with payloads
    - Searching for similar vectors
    - Deleting collections

    Collections are created dynamically based on document_id passed to methods.
    Collection naming format: document_chunks_{document_id}

    Attributes:
        qdrant_client: The Qdrant client instance.
        vector_size: Dimensionality of the embedding vectors.
        distance: Distance metric to use.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        vector_size: int = 384,
        distance: str = "COSINE",
    ):
        """Initialize the Qdrant vector store repository.

        Args:
            host: Qdrant server host.
            port: Qdrant server port.
            vector_size: Dimensionality of the embedding vectors.
            distance: Distance metric (COSINE, DOT, EUCLID, MANHATTAN).
        """
        self.host = host
        self.port = port
        self.vector_size = vector_size

        # Convert string/enum distance to Qdrant Distance enum
        self.distance = self._convert_to_qdrant_distance(distance)

        # Initialize Qdrant client
        try:
            self.qdrant_client = QdrantClient(host=host, port=port)
            logger.info(f"Connected to Qdrant at {host}:{port}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {str(e)}")
            raise ComponentConnectionException(component_type="vector_store", message=f"Qdrant connection failed: {str(e)}") from e

    def _convert_to_qdrant_distance(self, distance: str | VectorDistanceMetric) -> Distance:
        """Convert domain distance metric to Qdrant Distance enum.

        Args:
            distance: Distance metric as string or VectorDistanceMetric enum.

        Returns:
            Qdrant Distance enum value.

        Raises:
            ValueError: If distance metric is invalid.
        """
        # Convert to VectorDistanceMetric if string
        if isinstance(distance, str):
            try:
                distance = VectorDistanceMetric(distance.upper())
            except ValueError:
                raise ValueError(
                    f"Invalid distance metric '{distance}'. Must be one of: {[m.value for m in VectorDistanceMetric]}"
                )

        # Map domain metric to Qdrant Distance
        distance_map = {
            VectorDistanceMetric.COSINE: Distance.COSINE,
            VectorDistanceMetric.DOT: Distance.DOT,
            VectorDistanceMetric.EUCLID: Distance.EUCLID,
            VectorDistanceMetric.MANHATTAN: Distance.MANHATTAN,
        }

        return distance_map[distance]

    def _get_collection_name(self, document_id: str) -> str:
        """Build collection name from document_id.

        Args:
            document_id: The document ID to use in collection name.

        Returns:
            Collection name in format: {document_id}
        """
        return document_id

    def _ensure_collection(self, document_id: str) -> None:
        """Create the collection if it doesn't exist.

        Args:
            document_id: The document ID to create collection for.
        """
        collection_name = self._get_collection_name(document_id)
        try:
            if not self.qdrant_client.collection_exists(collection_name):
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=self.distance,
                    ),
                )
                logger.info(
                    f"Created Qdrant collection '{collection_name}' "
                    f"with vector_size={self.vector_size}, distance={self.distance}"
                )
            else:
                logger.debug(f"Collection '{collection_name}' already exists")
        except Exception as e:
            logger.error(f"Failed to create collection: {str(e)}")
            raise ResourceNotFoundException(resource_type="vector_store_collection", resource_id=collection_name) from e

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
        collection_name = self._get_collection_name(document_id)
        try:
            if not self.qdrant_client.collection_exists(collection_name):
                distance_enum = self._convert_to_qdrant_distance(distance)
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=distance_enum,
                    ),
                )
                logger.info(
                    f"Created collection '{collection_name}' with vector_size={vector_size}, distance={distance}"
                )
            else:
                logger.debug(f"Collection '{collection_name}' already exists")
        except Exception as e:
            logger.error(f"Failed to create collection: {str(e)}")
            raise ComponentNotAvailableException(component_type="vector_store", message=f"Collection creation failed: {str(e)}", details={"collection_name": collection_name, "document_id": document_id}) from e

    async def upsert_vectors(self, document_id: str, chunks: list[DocumentChunk], vectors: list[list[float]]) -> None:
        """Upsert document chunks with their vectors to Qdrant.

        This method follows the Qdrant tutorial pattern for uploading data.

        Args:
            document_id: The document ID to create collection for.
            chunks: List of DocumentChunk domain objects.
            vectors: List of embedding vectors corresponding to each chunk.

        Raises:
            DomainException: If storage fails or input validation fails.
        """
        if len(chunks) != len(vectors):
            raise ComponentOperationException(f"Chunk and vector count mismatch: {len(chunks)} vs {len(vectors)}")

        if not chunks:
            logger.warning("No chunks to upsert")
            return

        collection_name = self._get_collection_name(document_id)

        # Ensure collection exists for this document_id
        self._ensure_collection(document_id)

        logger.info(f"Upserting {len(chunks)} chunks to Qdrant collection '{collection_name}'")

        try:
            # Prepare points for upload
            points = []
            for chunk, vector in zip(chunks, vectors):
                # Validate embedding dimensions
                if len(vector) != self.vector_size:
                    raise ComponentOperationException(
                        f"Embedding dimension mismatch: expected {self.vector_size}, "
                        f"got {len(vector)} for chunk {chunk.chunk_id}"
                    )

                # Create payload with chunk data
                payload = {
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "split_index": chunk.split_index,
                    "content": chunk.content,
                    "character_name": chunk.character_name,
                    "metadata": chunk.metadata or {},
                }

                # Use chunk_id as the point ID for easy retrieval
                point = PointStruct(
                    id=str(uuid4()),
                    vector=vector,
                    payload=payload,
                )
                points.append(point)

            # Upload points to Qdrant (upsert = insert or update)
            operation_info = self.qdrant_client.upsert(
                collection_name=collection_name,
                points=points,
                wait=True,  # Wait for the operation to complete
            )

            logger.info(f"Successfully upserted {len(chunks)} chunks. Operation status: {operation_info.status}")

        except Exception as e:
            logger.error(f"Failed to upsert vectors to Qdrant: {str(e)}")
            raise ComponentOperationException(component_type="vector_store", message=f"Vector storage failed: {str(e)}") from e

    async def search_similar(self, document_id: str, query_vector: list[float], limit: int = 5) -> list[dict]:
        """Search for chunks similar to the query vector.

        Args:
            document_id: The document ID to search within.
            query_vector: The embedding vector to search with.
            limit: Maximum number of results to return (default: 5).

        Returns:
            List of payload dictionaries containing chunk metadata.

        Raises:
            DomainException: If search fails.
        """
        if len(query_vector) != self.vector_size:
            raise ComponentOperationException(
                f"Query vector dimension mismatch: expected {self.vector_size}, got {len(query_vector)}"
            )

        collection_name = self._get_collection_name(document_id)
        logger.debug(f"Searching for similar chunks in collection '{collection_name}' (limit={limit})")

        try:
            # Use query_points for search (as shown in your example)
            search_result = self.qdrant_client.query_points(
                collection_name=collection_name,
                query=query_vector,
                query_filter=None,  # No filters for now
                limit=limit,
            ).points

            # Extract payloads from search results
            payloads: list[dict[Any, Any]] = []
            for hit in search_result:
                if hit.payload:
                    payloads.append(dict(hit.payload))
                else:
                    payloads.append({})

            logger.info(f"Found {len(payloads)} similar chunks")
            return payloads

        except Exception as e:
            logger.error(f"Failed to search in Qdrant: {str(e)}")
            raise ComponentOperationException(component_type="vector_store", message=f"Vector search failed: {str(e)}") from e

    async def delete_collection(self, document_id: str) -> None:
        """Delete the entire collection for a specific document.

        Args:
            document_id: The document ID whose collection to delete.

        Raises:
            DomainException: If deletion fails.
        """
        collection_name = self._get_collection_name(document_id)
        logger.info(f"Deleting collection '{collection_name}'")

        try:
            self.qdrant_client.delete_collection(collection_name)
            logger.info(f"Successfully deleted collection '{collection_name}'")

        except Exception as e:
            logger.error(f"Failed to delete collection: {str(e)}")
            raise ComponentOperationException(component_type="vector_store", message=f"Collection deletion failed: {str(e)}") from e

    async def get_personality(self, document_id: str) -> str:
        """Retrieve character personality from the collection.

        Searches for chunks with metadata.h2_header == "## Personality" and returns
        the content of the first matching chunk.

        Args:
            document_id: The document ID (collection name) to search.

        Returns:
            The personality content if found, or a default message.

        Raises:
            DomainException: If search fails.
        """
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        collection_name = self._get_collection_name(document_id)
        logger.debug(f"Searching for personality in collection '{collection_name}'")

        try:
            # Check if collection exists
            if not self.qdrant_client.collection_exists(collection_name):
                logger.error(f"Collection '{collection_name}' does not exist")
                raise ResourceNotFoundException(
                    resource_type="vector_store_collection",
                    resource_id=collection_name
                )

            # Search for chunks with h2_header = "## Personality" in metadata
            scroll_result = self.qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="metadata.h2_header",
                            match=MatchValue(value="## Personality"),
                        )
                    ]
                ),
                limit=1,  # We only need the first match
            )

            if scroll_result[0]:  # Points found
                personality_chunk = scroll_result[0][0]
                if personality_chunk.payload is not None:
                    content = personality_chunk.payload.get("content", "")
                    logger.info(f"Found personality chunk (ID: {personality_chunk.id}) with {len(content)} characters")
                    return content if content else "No specific personality information available."
                else:
                    logger.warning("Personality chunk has no payload")
                    return "No specific personality information available."
            else:
                logger.warning(f"No personality chunk found in collection '{collection_name}'")
                return "No specific personality information available."

        except ResourceNotFoundException:
            # Let ResourceNotFoundException propagate unchanged
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve personality from Qdrant: {str(e)}")
            raise ComponentOperationException(component_type="vector_store", message=f"Personality retrieval failed: {str(e)}") from e