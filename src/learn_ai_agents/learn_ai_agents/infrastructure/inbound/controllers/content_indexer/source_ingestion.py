"""Router for content ingestion operations.

This module provides endpoints for ingesting content from various sources
(web, files, etc.) and storing them in the document repository.
"""

from fastapi import APIRouter, Depends, HTTPException

from learn_ai_agents.application.dtos.content_indexer.source_ingestion import (
    SourceIngestionRequestDTO,
    SourceIngestionResponseDTO,
)
from learn_ai_agents.application.use_cases.content_indexer.source_ingestion import (
    SourceIngestionUseCase,
)
from learn_ai_agents.domain.exceptions._base import BusinessRuleException
from learn_ai_agents.logging import get_logger
from learn_ai_agents.settings import UseCaseConfig

from ..dependencies import get_source_ingestion_use_case

logger = get_logger(__name__)


def get_router(use_case_config: UseCaseConfig) -> APIRouter:
    """Create and configure the router for source ingestion endpoints.
    
    Args:
        use_case_config: Configuration for this use case including path prefix and metadata.
        
    Returns:
        Configured APIRouter instance.
    """
    router = APIRouter(prefix=use_case_config.info.path_prefix, tags=["/05_content_indexer"])

    @router.post("/ingest", response_model=SourceIngestionResponseDTO)
    async def ingest_content(
        request: SourceIngestionRequestDTO,
        use_case: SourceIngestionUseCase = Depends(get_source_ingestion_use_case),
    ) -> SourceIngestionResponseDTO:
        """
        Ingest content from a source and store it in the document repository.

        This endpoint supports various content sources:
        - **web**: Retrieve content from a URL using web scraping
        - **file**: Upload and process file content (future)
        - **db**: Import content from a database (future)

        Args:
            request: Content ingestion request with source and parameters.
            use_case: Injected use case dependency.

        Returns:
            ContentIngestionResponseDTO with ingestion results.

        Raises:
            HTTPException: If ingestion fails.

        Example request for web source:
            {
                "source": "web",
                "params": {
                    "url": "https://example.com"
                }
            }

        Example response:
            {
                "document_id": "507f1f77bcf86cd799439011",
                "content_length": 15420,
                "metadata": {
                    "url": "https://example.com",
                    "title": "Example Domain",
                    "description": "Example website",
                    "content_type": "text/html; charset=UTF-8",
                    "source": "web"
                },
                "message": "Content ingested successfully"
            }
        """
        logger.info(f"POST /content/ingest - source: {request.source}")

        try:
            result = await use_case.ingest_content(request)
            logger.info(f"Content ingestion successful - document_id: {result.document_id}")
            return result
        except BusinessRuleException as e:
            logger.error(f"Domain error during content ingestion: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Unexpected error during content ingestion: {e}")
            raise HTTPException(status_code=500, detail="Internal server error during content ingestion")

    return router
