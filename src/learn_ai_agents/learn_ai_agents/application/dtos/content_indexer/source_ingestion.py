"""Data Transfer Objects for Content Ingestion functionality.

This module defines the DTOs used for content ingestion operations,
including web scraping and document storage.
"""

from typing import Any

from pydantic import BaseModel, Field


class SourceIngestionRequestDTO(BaseModel):
    """Request DTO for content ingestion.

    This DTO crosses the API boundary and contains the information needed
    to retrieve and store content from various sources.

    Attributes:
        source: The source type (e.g., "web", "file", "db").
        params: Parameters specific to the source (e.g., {"url": "https://..."}).
        character_name: Optional character name for BG3 character ingestion.
    """

    document_id: str = Field(
        ...,
        description="Unique identifier for the document",
    )
    source: str = Field(
        ...,
        description="The source type for content retrieval",
        examples=["web", "file", "db"],
    )
    params: dict[str, Any] = Field(
        ...,
        description="Source-specific parameters",
        examples=[{"url": "https://example.com"}],
    )
    character_name: str = Field(
        ...,
        description="Character name for BG3 character ingestion",
    )


class DocumentMetadataDTO(BaseModel):
    """DTO for document metadata.

    Attributes:
        url: The source URL (for web content).
        title: The document title if available.
        description: The document description if available.
        content_type: The content type of the source.
        source: The source type.
        character_name: Character name for BG3 characters.
    """

    url: str | None = None
    title: str | None = None
    description: str | None = None
    content_type: str | None = None
    source: str | None = None
    character_name: str


class SourceIngestionResponseDTO(BaseModel):
    """Response DTO for content ingestion.

    This DTO is returned after successfully ingesting content.

    Attributes:
        document_id: The ID of the stored document.
        document_id: The ID of the content request.
        content_length: The length of the content in characters.
        metadata: Metadata about the ingested content.
        message: A success message.
    """

    document_id: str = Field(..., description="The ID of the stored document")
    content_length: int = Field(..., description="Length of content in characters")
    metadata: DocumentMetadataDTO = Field(..., description="Document metadata")
    message: str = Field(default="Content ingested successfully")
