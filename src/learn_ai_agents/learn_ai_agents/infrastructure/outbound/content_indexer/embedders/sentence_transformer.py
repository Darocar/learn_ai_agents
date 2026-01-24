"""Sentence Transformer embedder adapter implementation.

This module provides an adapter for the Sentence Transformers library,
implementing the EmbedderPort interface for generating embeddings.
"""

from sentence_transformers import SentenceTransformer

from learn_ai_agents.application.outbound_ports.content_indexer.embedders.embedder import (
    EmbedderPort,
)
from learn_ai_agents.domain.exceptions import (
    ComponentBuildingException,
    ComponentOperationException,
)
from learn_ai_agents.logging import get_logger

logger = get_logger(__name__)


class SentenceTransformerEmbedder(EmbedderPort):
    """Adapter for Sentence Transformers embedding models.

    This adapter wraps the Sentence Transformers library to provide embeddings
    for text chunks. It supports various pre-trained models from the Sentence
    Transformers repository.

    Attributes:
        model: The loaded Sentence Transformer model.
        model_name: The name/identifier of the model.
        device: The device to run the model on ('cpu', 'cuda', 'mps').
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", device: str = "cuda"):
        """Initialize the Sentence Transformer embedder.

        Args:
            model_name: Name of the Sentence Transformers model to use.
                       Default is "all-MiniLM-L6-v2" (384 dimensions).
            device: Device to run the model on ('cpu', 'cuda', 'mps').
                   Default is 'cpu'.

        Raises:
            DomainException: If model loading fails.
        """
        self.model_name = model_name
        self.device = device

        try:
            logger.info(f"Loading Sentence Transformer model: {model_name} on {device}")
            self.model = SentenceTransformer(model_name, device=device)
            logger.info(f"Successfully loaded model with {self.get_dimensions()} dimensions")
        except Exception as e:
            error_msg = f"Failed to load Sentence Transformer model '{model_name}' on device '{device}': {e}"
            logger.error(error_msg)
            raise ComponentBuildingException(
                component_type="embedder",
                message=error_msg,
                details={"adapter": "SentenceTransformerEmbedder", "model_name": model_name, "device": device, "error": str(e)}
            ) from e

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
        if not texts:
            logger.warning("Received empty texts list for embedding")
            raise ComponentOperationException(
                component_type="embedder",
                message="No texts provided for embedding.",
                details={"adapter": "SentenceTransformerEmbedder"}
            )

        try:
            logger.debug(f"Generating embeddings for {len(texts)} texts")

            # Sentence Transformers encode method is synchronous
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=False,
            )

            # Convert numpy arrays to lists
            result = embeddings.tolist()

            logger.debug(f"Successfully generated {len(result)} embeddings")
            return result

        except Exception as e:
            error_msg = f"Failed to generate embeddings: {e}"
            logger.error(error_msg)
            raise ComponentOperationException(
                component_type="embedder",
                message=error_msg,
                details={"adapter": "SentenceTransformerEmbedder", "model_name": self.model_name, "error": str(e)}
            ) from e

    def get_dimensions(self) -> int:
        """Get the dimensionality of embeddings produced by this embedder.

        Returns:
            The number of dimensions in each embedding vector.
        """
        dimensions = self.model.get_sentence_embedding_dimension()
        if dimensions is None:
            raise ComponentOperationException(
                component_type="embedder",
                message=f"Unable to determine embedding dimensions for model '{self.model_name}'",
                details={"adapter": "SentenceTransformerEmbedder", "model_name": self.model_name}
            )
        return dimensions

    def get_model_name(self) -> str:
        """Get the name/identifier of the embedding model.

        Returns:
            The model name (e.g., "all-MiniLM-L6-v2").
        """
        return self.model_name
