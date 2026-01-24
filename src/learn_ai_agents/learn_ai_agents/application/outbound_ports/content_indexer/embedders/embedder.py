"""Outbound port for embedder operations.

This module defines the port (interface) for generating embeddings from text
using various embedding models.
"""

from typing import Protocol


class EmbedderPort(Protocol):
    """Protocol defining the interface for embedder operations.

    This port defines how the application layer generates embeddings from text
    without depending on specific embedding implementations (OpenAI, Sentence
    Transformers, Cohere, etc.).

    Step 2 of the content indexing pipeline: Vectorization
    """

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors, one per input text.
            Each embedding is a list of floats.

        Raises:
            DomainException: If embedding generation fails.
        """
        ...

    def get_dimensions(self) -> int:
        """Get the dimensionality of embeddings produced by this embedder.

        Returns:
            The number of dimensions in each embedding vector.
        """
        ...

    def get_model_name(self) -> str:
        """Get the name/identifier of the embedding model.

        Returns:
            The model name (e.g., "text-embedding-3-small", "all-MiniLM-L6-v2").
        """
        ...
