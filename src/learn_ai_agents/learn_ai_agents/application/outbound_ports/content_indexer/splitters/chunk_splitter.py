"""Outbound port for document chunk splitting.

This module defines the port (interface) for splitting documents into smaller
chunks using various strategies.
"""

from typing import Protocol

from learn_ai_agents.domain.models.content_indexer.source_ingestion import Document
from learn_ai_agents.domain.models.content_indexer.document_chunk import DocumentChunk


class ChunkSplitterPort(Protocol):
    """Protocol defining the interface for document splitting services.

    This port defines how the application layer splits documents into chunks
    without depending on specific splitting implementations or libraries.

    Step 2 of the content indexing pipeline: Document Splitting
    """

    def split_document(self, document: Document, splitter_approach: str) -> list[DocumentChunk]:
        """Split a document into smaller chunks.

        Args:
            document: The Document to be split.
            splitter_approach: The name/key of the splitter approach being used.

        Returns:
            List of DocumentChunk objects with sequential split_index values.

        Raises:
            DomainException: If splitting fails.
        """
        ...
