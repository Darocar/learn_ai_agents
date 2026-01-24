"""Repository ports for content indexer."""

from .chunk_repository import ChunkRepositoryPort
from .document_repository import DocumentRepositoryPort

__all__ = [
    "ChunkRepositoryPort",
    "DocumentRepositoryPort",
]
