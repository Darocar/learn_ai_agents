"""Data Transfer Objects for Document Splitting functionality.

This module defines the DTOs used for splitting documents into chunks
for vector storage and retrieval.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class DocumentSplittingRequestDTO(BaseModel):
    """Request DTO for document splitting.

    This DTO contains the information needed to split a document
    into chunks. The splitting strategy is determined by the injected
    splitter adapter.

    Attributes:
        document_id: The document ID of the document(s) to split.
        splitter_approach: The splitting approach to use.
    """

    document_id: str = Field(
        ...,
        description="The document ID to identify which document(s) to split",
    )
    splitter_approach: str = Field(
        ...,
        description="The splitting approach to use",
        examples=["markdown"],
    )


class ChunkMetadataDTO(BaseModel):
    """DTO for chunk metadata.

    Attributes:
        chunk_id: Unique identifier combining document_id:splitter_approach:split_index.
        document_id: The ID of the parent document.
        split_index: Index of this chunk within the document.
        chunk_size: Size of this chunk in characters.
        splitter: The splitter type used.
        h1_title: The H1 header this chunk belongs to (if applicable).
        h2_header: The H2 header this chunk belongs to (if applicable).
    """

    chunk_id: str
    document_id: str
    split_index: int
    chunk_size: int
    splitter: str
    h1_title: Optional[str] = None
    h2_header: Optional[str] = None


class DocumentSplittingResponseDTO(BaseModel):
    """Response DTO for document splitting.

    This DTO is returned after successfully splitting document(s) into chunks.

    Attributes:
        document_id: The document ID of the processed document(s).
        documents_processed: Number of documents that were processed.
        total_chunks_created: Total number of chunks created across all documents.
        chunks: List of metadata for each created chunk.
        message: A success message.
    """

    document_id: str = Field(..., description="The document ID of processed documents")
    total_chunks_created: int = Field(..., description="Total number of chunks created")
    chunks: List[ChunkMetadataDTO] = Field(..., description="Metadata for all created chunks")
    message: str = Field(default="Documents split successfully")
