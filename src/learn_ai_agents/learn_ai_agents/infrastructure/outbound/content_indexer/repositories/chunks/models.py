"""Odmantic models for document chunk persistence.

This module defines the ODM models for chunk storage.
"""

from typing import Any, Optional
from datetime import datetime

from odmantic import Model, Field, config


class ChunkModel(Model):
    """Odmantic model for document chunk persistence (RAG).

    This model represents the storage structure for document chunks in MongoDB.
    It maps to the domain DocumentChunk model.

    Attributes:
        chunk_id: Composite identifier: document_id:splitter_approach:split_index.
        document_id: Reference to the parent document.
        split_index: Index of this chunk within the parent document.
        content: The text content of this chunk.
        metadata: Optional metadata (chunk position, overlap info, etc.).
        character_name: Character name for BG3 characters.
    """

    chunk_id: str
    document_id: str
    split_index: int
    content: str
    metadata: Optional[dict[str, Any]] = None
    character_name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(),
    )

    model_config = config.ODMConfigDict({"collection": "chunks_bg3_characters"})
