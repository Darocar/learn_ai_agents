"""Hierarchical markdown text splitter adapter.

This module implements document splitting using a hierarchical approach:
1. First splits by markdown headers (##, ###, etc.) to preserve document structure
2. Then applies recursive character splitting on chunks that exceed size limits
"""

import re
from learn_ai_agents.application.outbound_ports.content_indexer.splitters.chunk_splitter import (
    ChunkSplitterPort,
)
from learn_ai_agents.domain.models.content_indexer.source_ingestion import Document
from learn_ai_agents.domain.models.content_indexer.document_chunk import DocumentChunk
from learn_ai_agents.domain.exceptions._base import BusinessRuleException
from learn_ai_agents.logging import get_logger

logger = get_logger(__name__)


class MarkdownHierarchicalSplitter(ChunkSplitterPort):
    """Adapter for splitting markdown documents by H1 sections, then by H2 subsections.

    This splitter splits by H1 headers (major sections), and for each H1 section,
    creates separate chunks for each H2 subsection. Each chunk contains:
    H1 (section title) + H2 (subsection title) + content under that H2.

    Attributes:
        chunk_size: Target size for each chunk in characters.
        chunk_overlap: Number of characters to overlap between chunks.
    """

    def __init__(
        self,
        chunk_size: int = 1500,
        chunk_overlap: int = 200,
        header_levels: int = 4,
        recursive_separators: list[str] | None = None,
    ):
        """Initialize the hierarchical markdown splitter.

        Args:
            chunk_size: Target size for each chunk in characters (default: 1500).
            chunk_overlap: Number of characters to overlap between chunks (default: 200).
            header_levels: Ignored, kept for compatibility.
            recursive_separators: Ignored, kept for compatibility.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Pattern to match H1 headers
        self.h1_pattern = re.compile(r"^(#\s+.+)$", re.MULTILINE)
        # Pattern to match H2 headers
        self.h2_pattern = re.compile(r"^(##\s+.+)$", re.MULTILINE)

        logger.info(
            f"MarkdownHierarchicalSplitter initialized with chunk_size={chunk_size}, "
            f"chunk_overlap={chunk_overlap}, splitting by H1 sections then H2 subsections"
        )

    def split_document(self, document: Document, splitter_approach: str) -> list[DocumentChunk]:
        """Split a markdown document by H1 sections, then by H2 subsections.

        Args:
            document: The Document to be split.
            splitter_approach: The name/key of the splitter approach being used.

        Returns:
            List of DocumentChunk objects with sequential split_index values.

        Raises:
            DomainException: If splitting fails or document content is invalid.
        """
        logger.info(f"Splitting markdown document {document.document_id} using {splitter_approach}")

        if not isinstance(document.content, str):
            raise BusinessRuleException("Document content must be a string for markdown splitting")

        if not document.content.strip():
            logger.warning(f"Document {document.document_id} has empty content")
            return []

        # Split by H1 sections first
        h1_sections = self._split_by_h1(document.content)
        logger.debug(f"Split document into {len(h1_sections)} H1 sections")

        # For each H1 section, split by H2 subsections and create chunks
        chunks = []
        chunk_index = 0

        for h1_section in h1_sections:
            h1_title = h1_section["h1_header"]
            h1_content = h1_section["content"]

            # Split this H1 section by H2 subsections
            h2_subsections = self._split_by_h2(h1_content)

            if not h2_subsections:
                # No H2 subsections, create a single chunk with just H1 + content
                chunk_text = f"{h1_title}\n\n{h1_content}" if h1_content else h1_title
                chunk_id = f"{document.document_id}:{splitter_approach}:{chunk_index}"

                # Extract simplified metadata from document
                doc_meta = document.metadata or {}
                chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=document.document_id,
                    split_index=chunk_index,
                    content=chunk_text,
                    metadata={
                        "chunk_size": len(chunk_text),
                        "splitter": "markdown_h1_h2",
                        "h1_title": h1_title,
                        "h2_header": None,
                        "url": doc_meta.get("url"),
                        "source": doc_meta.get("source"),
                        "title": doc_meta.get("title"),
                        "character_name": doc_meta.get("character_name"),
                    },
                    character_name=document.character_name,
                )
                chunks.append(chunk)
                chunk_index += 1
            else:
                # Create a chunk for each H2 subsection
                for h2_section in h2_subsections:
                    chunk_parts = [h1_title]

                    if h2_section["h2_header"]:
                        chunk_parts.append(h2_section["h2_header"])
                    if h2_section["content"]:
                        chunk_parts.append(h2_section["content"])

                    chunk_text = "\n\n".join(chunk_parts)
                    chunk_id = f"{document.document_id}:{splitter_approach}:{chunk_index}"

                    # Extract simplified metadata from document
                    doc_meta = document.metadata or {}
                    chunk = DocumentChunk(
                        chunk_id=chunk_id,
                        document_id=document.document_id,
                        split_index=chunk_index,
                        content=chunk_text,
                        metadata={
                            "chunk_size": len(chunk_text),
                            "splitter": "markdown_h1_h2",
                            "h1_title": h1_title,
                            "h2_header": h2_section["h2_header"],
                            "url": doc_meta.get("url"),
                            "source": doc_meta.get("source"),
                            "title": doc_meta.get("title"),
                            "character_name": doc_meta.get("character_name"),
                        },
                        character_name=document.character_name,
                    )
                    chunks.append(chunk)
                    chunk_index += 1

        logger.info(f"Split markdown document {document.document_id} into {len(chunks)} chunks")
        return chunks

    def _split_by_h1(self, text: str) -> list[dict[str, str]]:
        """Split text by H1 headers.

        Args:
            text: The markdown text to split.

        Returns:
            List of dictionaries with 'h1_header' and 'content' keys.
        """
        # Find all H1 header positions
        h1_headers = list(self.h1_pattern.finditer(text))

        if not h1_headers:
            # No H1 headers found, return entire text as one section
            if text.strip():
                return [{"h1_header": "", "content": text.strip()}]
            return []

        sections = []

        # Process each H1 section
        for i, h1_match in enumerate(h1_headers):
            h1_text = h1_match.group(1).strip()
            start_pos = h1_match.end()

            # Find end position (start of next H1 or end of text)
            if i + 1 < len(h1_headers):
                end_pos = h1_headers[i + 1].start()
            else:
                end_pos = len(text)

            # Extract section content (excluding the H1 line itself)
            content = text[start_pos:end_pos].strip()

            sections.append(
                {
                    "h1_header": h1_text,
                    "content": content,
                }
            )

        return sections

    def _split_by_h2(self, text: str) -> list[dict[str, str | None]]:
        """Split text by H2 headers (without removing H1s).

        Args:
            text: The markdown text to split.

        Returns:
            List of dictionaries with 'h2_header' and 'content' keys.
        """
        # Find all H2 header positions
        h2_headers = list(self.h2_pattern.finditer(text))

        if not h2_headers:
            # No H2 headers found
            return []

        sections = []

        # Process each H2 section
        for i, h2_match in enumerate(h2_headers):
            h2_text = h2_match.group(1).strip()
            start_pos = h2_match.end()

            # Find end position (start of next H2 or H1, or end of text)
            # We need to stop at H1 to avoid bleeding into next major section
            end_pos = len(text)

            # Check for next H2
            if i + 1 < len(h2_headers):
                end_pos = h2_headers[i + 1].start()

            # Also check if there's an H1 before the next H2 (shouldn't happen in our structure)
            h1_after = self.h1_pattern.search(text, start_pos)
            if h1_after and h1_after.start() < end_pos:
                end_pos = h1_after.start()

            # Extract section content (excluding the H2 line itself)
            content = text[start_pos:end_pos].strip()

            sections.append(
                {
                    "h2_header": h2_text,
                    "content": content,
                }
            )

        return sections
