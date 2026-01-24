from dataclasses import dataclass
from typing import Dict, Optional, Any


@dataclass(frozen=True)
class DocumentChunk:
    """
    Represents a chunk of a document.

    Attributes:
        id: Unique identifier for the document chunk (MongoDB _id).
        chunk_id: Composite identifier: document_id:splitter_approach:split_index.
        content: The actual text content of the chunk.
        metadata: Optional metadata associated with the chunk.
        character_name: Character name for BG3 characters.
    """

    chunk_id: str
    document_id: str
    split_index: int
    content: str
    metadata: Optional[Dict[str, Any]]
    character_name: str
