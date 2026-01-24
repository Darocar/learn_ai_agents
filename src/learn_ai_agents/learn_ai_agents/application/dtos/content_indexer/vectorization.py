"""Data Transfer Objects for Vectorization functionality.

This module defines the DTOs used for vectorizing document chunks
and storing them in a vector database.
"""

from pydantic import BaseModel, Field


class VectorizationRequestDTO(BaseModel):
    """Request DTO for vectorization.

    This DTO contains the information needed to vectorize document chunks.
    The vectorization strategy is determined by the injected embedder adapter.

    Attributes:
        document_id: The document ID of the chunks to vectorize.
        vectorization_approach: The vectorization/embedding approach to use.
    """

    document_id: str = Field(
        ...,
        description="The document ID to identify which chunks to vectorize",
    )
    vectorization_approach: str = Field(
        ...,
        description="The vectorization/embedding approach to use",
        examples=["openai", "sentence-transformers"],
    )


class VectorizationResponseDTO(BaseModel):
    """Response DTO for vectorization.

    This DTO is returned after successfully vectorizing and storing chunks.

    Attributes:
        document_id: The document ID of the processed chunks.
        total_vectors_created: Total number of vectors created and stored.
        vectors: List of metadata for each created vector.
        message: A success message.
    """

    document_id: str = Field(..., description="The document ID of processed chunks")
    total_vectors_created: int = Field(..., description="Total number of vectors created and stored")
    message: str = Field(default="Chunks vectorized successfully")
