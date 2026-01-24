"""Router for content ingestion operations.

This module provides endpoints for ingesting content from various sources
(web, files, etc.) and storing them in the document repository.
"""

from fastapi import APIRouter, Depends, HTTPException

from learn_ai_agents.application.dtos.content_indexer.document_splitting import (
    DocumentSplittingRequestDTO,
    DocumentSplittingResponseDTO,
)
from learn_ai_agents.application.use_cases.content_indexer.document_splitting.use_case import (
    DocumentSplittingUseCase,
)
from learn_ai_agents.domain.exceptions._base import BusinessRuleException
from learn_ai_agents.logging import get_logger
from learn_ai_agents.settings import UseCaseConfig

from ..dependencies import get_document_splitting_use_case

logger = get_logger(__name__)


def get_router(use_case_config: UseCaseConfig) -> APIRouter:
    """Create and configure the router for document splitting endpoints.
    
    Args:
        use_case_config: Configuration for this use case including path prefix and metadata.
        
    Returns:
        Configured APIRouter instance.
    """
    router = APIRouter(prefix=use_case_config.info.path_prefix, tags=["/05_content_indexer"])

    @router.post("/split_document", response_model=DocumentSplittingResponseDTO)
    async def split_document(
        request: DocumentSplittingRequestDTO,
        use_case: DocumentSplittingUseCase = Depends(get_document_splitting_use_case),
    ) -> DocumentSplittingResponseDTO:
        """
        Endpoint to split documents into chunks for vector storage.
        Args:
            request: DTO containing the request ID of the document(s) to split.
            use_case: The DocumentSplittingUseCase instance injected via dependency.
        Returns:
            DocumentSplittingResponseDTO with the results of the splitting operation.
        Raises:
            HTTPException: If splitting fails due to domain errors.
        Example request:
            {
                "document_id": "abc123",
                "params": {
                    "splitter_type": "markdown_splitter"
                }
        """
        logger.info(f"Received document splitting request: {request}")
        try:
            response = await use_case.split_documents(request)
            logger.info(f"Document splitting successful for document_id: {request.document_id}")
            return response
        except BusinessRuleException as e:
            logger.error(f"Document splitting failed for document_id: {request.document_id} - {e}")
            raise HTTPException(status_code=400, detail=str(e)) from e

    return router
