"""MongoDB repository implementation for documents using Odmantic.

This module implements document persistence using the repository pattern
with Odmantic for type-safe MongoDB operations.
"""

from learn_ai_agents.application.outbound_ports.content_indexer.repositories.document_repository import (
    DocumentRepositoryPort,
)
from learn_ai_agents.application.outbound_ports.database import DatabaseClient
from learn_ai_agents.domain.models.content_indexer.source_ingestion import Document
from .models import DocumentModel
from learn_ai_agents.infrastructure.outbound.base_persistence import (
    BaseMongoModelRepository,
)
from learn_ai_agents.logging import get_logger

logger = get_logger(__name__)


class MongoDocumentRepository(BaseMongoModelRepository[DocumentModel], DocumentRepositoryPort):
    """MongoDB implementation of the DocumentRepositoryPort using Odmantic.

    This adapter implements the DocumentRepositoryPort by inheriting from
    BaseMongoModelRepository and handling the mapping between domain
    Document objects and ODM DocumentModel models.
    """

    def __init__(self, database: DatabaseClient):
        """Initialize the MongoDB document repository.

        Args:
            database: The database client instance (MongoEngineAdapter).
        """
        super().__init__(database.get_engine(), DocumentModel)
        logger.info("MongoDB document repository initialized with Odmantic")

    async def save_document(self, document: Document) -> Document:
        """Save a document to the repository.

        Args:
            document: The domain Document to save.

        Returns:
            The saved document with updated ID.
        """
        logger.debug(f"Saving document with document_id={document.document_id}")

        # Map domain Document to ODM DocumentModel
        doc_model = DocumentModel(  # type: ignore[call-arg]
            document_id=document.document_id,
            content=document.content,
            metadata=document.metadata,
            character_name=document.character_name,
        )

        # Save using base repository
        saved_model = await self.save_one(doc_model)

        # Map back to domain Document
        return Document(
            document_id=saved_model.document_id,
            content=saved_model.content,
            metadata=saved_model.metadata,
            character_name=saved_model.character_name,
        )

    async def get_document_by_id(self, document_id: str) -> Document | None:
        """Retrieve a document by its ID.

        Args:
            document_id: The ID of the document to retrieve.

        Returns:
            The domain Document if found, None otherwise.
        """
        logger.debug(f"Fetching document with id={document_id}")

        doc_model = await self.get_by_id(document_id)
        if doc_model is None:
            return None

        # Map ODM DocumentModel to domain Document
        return Document(
            document_id=doc_model.document_id,
            content=doc_model.content,
            metadata=doc_model.metadata,
            character_name=doc_model.character_name,
        )

    async def find_documents_by_document_id(self, document_id: str) -> list[Document]:
        """Find all documents associated with a content request.

        Args:
            document_id: The ID of the content request.

        Returns:
            List of domain Documents matching the request ID.
        """
        logger.debug(f"Finding documents with document_id={document_id}")

        doc_models = await self.find_by(document_id=document_id)

        # Map ODM DocumentModels to domain Documents
        return [
            Document(
                document_id=doc.document_id,
                content=doc.content,
                metadata=doc.metadata,
                character_name=doc.character_name,
            )
            for doc in doc_models
        ]

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document by its ID.

        Args:
            document_id: The ID of the document to delete.

        Returns:
            True if deleted, False if not found.
        """
        logger.debug(f"Deleting document with id={document_id}")
        return await self.delete_by_id(document_id)

    async def upsert_document(self, document: Document) -> Document:
        """Upsert a document to the repository.

        Updates existing document (matched by document_id and character_name) or inserts a new one.

        Args:
            document: The domain Document to upsert.

        Returns:
            The upserted document.
        """
        logger.debug(
            f"Upserting document with document_id={document.document_id}, character_name={document.character_name}"
        )

        # Find existing document by document_id and character_name
        existing_docs = await self.find_by(document_id=document.document_id, character_name=document.character_name)

        if existing_docs:
            # Update existing document
            existing_model = existing_docs[0]
            existing_model.content = document.content
            existing_model.metadata = document.metadata
            from datetime import datetime

            existing_model.updated_at = datetime.now()

            saved_model = await self.save_one(existing_model)
            logger.debug(
                f"Updated document with document_id={document.document_id}, character_name={document.character_name}"
            )
        else:
            # Insert new document
            doc_model = DocumentModel(  # type: ignore[call-arg]
                document_id=document.document_id,
                content=document.content,
                metadata=document.metadata,
                character_name=document.character_name,
            )
            saved_model = await self.save_one(doc_model)
            logger.debug(
                f"Inserted new document with document_id={document.document_id}, character_name={document.character_name}"
            )

        # Map back to domain Document
        return Document(
            document_id=saved_model.document_id,
            content=saved_model.content,
            metadata=saved_model.metadata,
            character_name=saved_model.character_name,
        )
