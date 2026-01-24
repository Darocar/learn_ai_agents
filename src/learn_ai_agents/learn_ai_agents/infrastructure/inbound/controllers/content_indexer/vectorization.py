"""Router for vectorization operations.

This module provides endpoints for vectorizing document chunks
and storing them in a vector database.
"""

from fastapi import APIRouter, Depends, HTTPException

from learn_ai_agents.application.dtos.content_indexer.vectorization import (
    VectorizationRequestDTO,
    VectorizationResponseDTO,
)
from learn_ai_agents.application.use_cases.content_indexer.vectorization.use_case import (
    VectorizationUseCase,
)
from learn_ai_agents.domain.exceptions._base import BusinessRuleException
from learn_ai_agents.logging import get_logger
from learn_ai_agents.settings import UseCaseConfig

from ..dependencies import get_vectorization_use_case

logger = get_logger(__name__)


def get_router(use_case_config: UseCaseConfig) -> APIRouter:
    """Create and configure the router for vectorization endpoints.
    
    Args:
        use_case_config: Configuration for this use case including path prefix and metadata.
        
    Returns:
        Configured APIRouter instance.
    """
    router = APIRouter(prefix=use_case_config.info.path_prefix, tags=["/05_content_indexer"])

    @router.post("/vectorize", response_model=VectorizationResponseDTO)
    async def vectorize_chunks(
        request: VectorizationRequestDTO,
        use_case: VectorizationUseCase = Depends(get_vectorization_use_case),
    ) -> VectorizationResponseDTO:
        """
        Vectorize document chunks and store them in a vector database.

        This endpoint:
        1. Retrieves all chunks for the specified document_id
        2. Generates embeddings using the specified vectorization approach
        3. Stores the chunks with their embeddings in the vector database

        Args:
            request: Vectorization request with document_id and approach.
            use_case: Injected use case dependency.

        Returns:
            VectorizationResponseDTO with vectorization results.

        Raises:
            HTTPException: If vectorization fails.

        Example request:
            {
                "document_id": "507f1f77bcf86cd799439011",
                "vectorization_approach": "sentence_transformers"
            }

        Example response:
            {
                "document_id": "507f1f77bcf86cd799439011",
                "total_vectors_created": 42,
                "message": "Successfully vectorized 42 chunk(s) and stored in vector database"
            }
        """
        logger.info(f"POST /vectorize - document_id: {request.document_id}, approach: {request.vectorization_approach}")

        try:
            result = await use_case.vectorize_chunks(request)
            logger.info(
                f"Vectorization successful - document_id: {result.document_id}, "
                f"vectors created: {result.total_vectors_created}"
            )
            return result
        except BusinessRuleException as e:
            logger.error(f"Domain error during vectorization: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Unexpected error during vectorization: {e}")
            raise HTTPException(status_code=500, detail="Internal server error during vectorization")

    return router
