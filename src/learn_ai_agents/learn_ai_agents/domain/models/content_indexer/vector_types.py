"""Domain types for vector storage.

This module defines domain-level types and enumerations related to vector storage
that are independent of any specific vector database implementation.
"""

from enum import Enum


class VectorDistanceMetric(Enum):
    """Distance metrics for vector similarity search.

    These metrics define how similarity between vectors is calculated.
    They are domain concepts independent of any specific vector database.

    Attributes:
        COSINE: Cosine similarity (1 - cosine distance). Best for normalized vectors.
        DOT: Dot product similarity. Faster than cosine, good for normalized vectors.
        EUCLID: Euclidean distance (L2). Measures straight-line distance.
        MANHATTAN: Manhattan distance (L1). Sum of absolute differences.
    """

    COSINE = "COSINE"
    DOT = "DOT"
    EUCLID = "EUCLID"
    MANHATTAN = "MANHATTAN"

    @classmethod
    def get_default(cls) -> "VectorDistanceMetric":
        """Get the default distance metric for vector search.

        Returns:
            The default distance metric (COSINE).
        """
        return cls.COSINE
