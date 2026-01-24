from dataclasses import dataclass
from typing import List

from .document_chunk import DocumentChunk


@dataclass(frozen=True)
class VectorizedDocumentChunk(DocumentChunk):
    """
    Represents a vectorized chunk of a document.

    Attributes:
        vector: The vector representation of the document chunk.
    """

    vector: List[float]
    dimensions: int

    def __post_init__(self):
        """Validate the embedding."""
        if len(self.vector) != self.dimensions:
            raise ValueError(f"Vector length {len(self.vector)} does not match declared dimensions {self.dimensions}")
