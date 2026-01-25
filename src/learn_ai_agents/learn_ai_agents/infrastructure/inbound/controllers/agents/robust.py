"""FastAPI controller for robust agent endpoints.

This module implements the HTTP API endpoints for the robust agent
using RAG (Retrieval-Augmented Generation). It serves as the inbound adapter
in the hexagonal architecture.

This is a robust version with enhanced tracing and monitoring capabilities.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from learn_ai_agents.application.dtos.agents.character_chat import CharacterChatRequestDTO
from learn_ai_agents.application.use_cases.agents.robust.use_case import RobustUseCase
from learn_ai_agents.logging import get_logger
from learn_ai_agents.settings import UseCaseConfig

from ..dependencies import get_robust_use_case

logger = get_logger(__name__)


def get_router(use_case_config: UseCaseConfig) -> APIRouter:
    """Create and configure the router for robust agent endpoints.
    
    Args:
        use_case_config: Configuration for this use case including path prefix and metadata.
        
    Returns:
        Configured APIRouter instance.
    """
    router = APIRouter(prefix=use_case_config.info.path_prefix, tags=[use_case_config.info.path_prefix])

    @router.post("/ainvoke")
    async def ainvoke(
        dto: CharacterChatRequestDTO,
        use_case: RobustUseCase = Depends(get_robust_use_case),
    ):
        """Handle asynchronous character chat requests with robust agent.

        This endpoint processes a user's message to a BG3 character and returns
        a complete answer. The robust agent uses vector search to retrieve relevant
        character information from the knowledge base to provide accurate,
        in-character responses with enhanced tracing and monitoring.

        Args:
            dto: The chat request containing the message, character name, and document ID.
            use_case: Injected use case dependency for processing the request.

        Returns:
            CharacterChatResultDTO containing the character's response.
        """
        logger.info(f"POST /ainvoke - conversation_id: {dto.config.conversation_id}, character: {dto.character_name}")
        logger.debug(f"Message: {dto.message[:100]}...")

        result = await use_case.ainvoke(dto)

        logger.info(
            f"POST /ainvoke completed - conversation_id: {dto.config.conversation_id}, character: {dto.character_name}"
        )
        return result

    @router.post("/astream")
    async def astream(
        dto: CharacterChatRequestDTO,
        use_case: RobustUseCase = Depends(get_robust_use_case),
    ):
        """Handle async streaming character chat requests with robust agent.

        This endpoint processes a user's message to a BG3 character and streams
        the response in real-time using Server-Sent Events (SSE). The robust agent
        uses vector search to retrieve relevant character information and maintains
        the character's personality throughout the conversation with enhanced
        tracing capabilities.

        Args:
            dto: The chat request containing the message, character name, and document ID.
            use_case: Injected use case dependency for processing the request.

        Returns:
            StreamingResponse with text/event-stream content type.
        """
        logger.info(f"POST /astream - conversation_id: {dto.config.conversation_id}, character: {dto.character_name}")
        logger.debug(f"Message: {dto.message[:100]}...")

        async def _gen():
            async for ev in use_case.astream(dto):  # type: ignore
                yield f"data: {ev.model_dump_json()}\n\n".encode()
            logger.info(
                f"POST /astream completed - conversation_id: {dto.config.conversation_id}, character: {dto.character_name}"
            )

        return StreamingResponse(_gen(), media_type="text/event-stream")

    return router
