"""Outbound port for document repository operations.

This module defines the port (interface) for document persistence operations,
following the hexagonal architecture pattern.
"""

from typing import Protocol

from learn_ai_agents.domain.models.content_indexer.source_ingestion import Document


class DocumentRepositoryPort(Protocol):
    """Protocol defining the interface for document repository operations.

    This port defines how the application layer interacts with document
    persistence without depending on specific storage implementations.
    """

    async def save_document(self, document: Document) -> Document:
        """Save a document to the repository.

        Args:
            document: The domain Document to save.

        Returns:
            The saved document with updated ID.
        """
        ...

    async def get_document_by_id(self, document_id: str) -> Document | None:
        """Retrieve a document by its ID.

        Args:
            document_id: The ID of the document to retrieve.

        Returns:
            The domain Document if found, None otherwise.
        """
        ...

    async def find_documents_by_document_id(self, document_id: str) -> list[Document]:
        """Find all documents associated with a content request.

        Args:
            document_id: The ID of the content request.
        Returns:
            List of domain Documents matching the document ID.
        """
        ...

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document by its ID.

        Args:
            document_id: The ID of the document to delete.

        Returns:
            True if deleted, False if not found.
        """
        ...

    async def upsert_document(self, document: Document) -> Document:
        """Upsert a document to the repository.

        Updates existing document (matched by document_id and character_name) or inserts a new one.

        Args:
            document: The domain Document to upsert.

        Returns:
            The upserted document.

        Raises:
            DomainException: If upsert fails.
        """
        ...
