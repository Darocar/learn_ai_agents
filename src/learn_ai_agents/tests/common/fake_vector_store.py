"""Fake vector store adapter for testing.

This module provides a simplified in-memory fake vector store.
Loads data from vector_chunks.json and returns first X elements for search.
Supports error simulation for testing error handling scenarios.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Union, Optional

from learn_ai_agents.domain.models.content_indexer.document_chunk import DocumentChunk
from learn_ai_agents.domain.exceptions import (
    ComponentConnectionException,
    ComponentOperationException,
)

logger = logging.getLogger(__name__)


class FakeVectorStoreAdapter:
    """Simplified fake vector store adapter for testing.

    Loads collections from vector_chunks.json with format:
    {
        "collection_name": [
            {"payload": {...}, "vector": [...]},
            ...
        ]
    }

    Search returns first X elements from the collection (no actual similarity calculation).
    Supports error simulation via _simulate_error() for testing error handling.
    """

    def __init__(
        self,
        host: str = "fake-host",
        port: int = 6333,
        vector_size: int = 384,
        distance: str = "COSINE",
        **kwargs,
    ):
        """Initialize fake vector store.

        Args:
            host: Fake host (ignored).
            port: Fake port (ignored).
            vector_size: Dimensionality of vectors.
            distance: Distance metric (ignored in fake implementation).
            **kwargs: Additional arguments (ignored).
        """
        self.host = host
        self.port = port
        self.vector_size = vector_size
        self.distance = distance
        self._collections: Dict[str, List[Dict]] = {}
        self._error_to_raise: Optional[BaseException] = None
        self._skip_error_for_personality: bool = False

    def _simulate_error(self, operation: str = "search") -> None:
        """Raise simulated error if configured.

        Args:
            operation: The operation being performed (for error message context).

        Raises:
            BaseException: If error simulation is configured.
        """
        if self._error_to_raise is not None:
            logger.error(
                f"FakeVectorStore: Raising simulated error for {operation}: {self._error_to_raise}"
            )
            raise self._error_to_raise

    def set_error(
        self, error: Optional[BaseException], skip_for_personality: bool = False
    ) -> None:
        """Configure an error to raise on next operation.

        Args:
            error: Exception to raise, or None to clear error simulation.
            skip_for_personality: If True, don't raise error for get_personality() calls.
        """
        self._error_to_raise = error
        self._skip_error_for_personality = skip_for_personality

    async def search_similar(
        self, document_id: str, query_vector: List[float], limit: int = 5
    ) -> List[dict]:
        """Search for similar vectors (simplified: returns first X elements).

        Args:
            document_id: Document ID (collection name).
            query_vector: Query embedding vector (ignored).
            limit: Maximum number of results.

        Returns:
            List of payload dictionaries (first X elements from collection).

        Raises:
            ComponentOperationException: If error simulation is configured.
        """
        logger.debug(
            f"FakeVectorStore.search_similar called for document_id={document_id}"
        )
        self._simulate_error("search_similar")

        if document_id not in self._collections:
            return []

        # Simply return the first X payloads (no actual similarity calculation)
        return [item["payload"] for item in self._collections[document_id][:1]]

    async def get_personality(self, document_id: str) -> str:
        """Retrieve personality from fake collection.

        Args:
            document_id: Document ID for collection.

        Returns:
            Personality content or default message.

        Raises:
            ComponentOperationException: If error simulation is configured.
        """
        # Skip error simulation if flag is set
        if not self._skip_error_for_personality:
            self._simulate_error("get_personality")

        if document_id not in self._collections:
            return "No specific personality information available."

        # Search for personality chunk in metadata
        for item in self._collections[document_id]:
            metadata = item["payload"].get("metadata", {})
            if metadata.get("h2_header") == "## Personality":
                return item["payload"].get(
                    "content", "No specific personality information available."
                )

        return "No specific personality information available."

    async def load_from_file(self, file_path: Union[str, Path]) -> None:
        """Load collections from vector_chunks.json.

        Expected format:
        {
            "collection_name": [
                {"payload": {...}, "vector": [...]},
                ...
            ]
        }

        Args:
            file_path: Path to vector_chunks.json file.
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Vector chunks file not found: {file_path}")

        with open(file_path, "r") as f:
            data = json.load(f)

        # Load each collection
        for collection_name, items in data.items():
            self._collections[collection_name] = items
