"""FastAPI controller for adding tools endpoints.

This module implements the HTTP API endpoints for tool-augmented question-answering
functionality. It serves as the inbound adapter in the hexagonal architecture.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from learn_ai_agents.application.dtos.agents.basic_answer import AnswerRequestDTO
from learn_ai_agents.application.use_cases.agents.adding_tools.use_case import (
    AddingToolsUseCase,
)
from learn_ai_agents.logging import get_logger
from learn_ai_agents.settings import UseCaseConfig

from ..dependencies import get_adding_tools_use_case

logger = get_logger(__name__)


def get_router(use_case_config: UseCaseConfig) -> APIRouter:
    """Create and configure the router for adding tools endpoints.
    
    Args:
        use_case_config: Configuration for this use case including path prefix and metadata.
        
    Returns:
        Configured APIRouter instance.
    """
    router = APIRouter(prefix=use_case_config.info.path_prefix, tags=[use_case_config.info.path_prefix])

    @router.post("/ainvoke")
    async def ainvoke(
        dto: AnswerRequestDTO,
        use_case: AddingToolsUseCase = Depends(get_adding_tools_use_case),
    ):
        """Handle asynchronous question-answering requests with tool support.

        This endpoint processes a user's question and returns a complete answer.
        The agent may use external tools (web search, calculations, etc.) to
        provide accurate responses.

        Args:
            dto: The answer request containing the user's question.
            use_case: Injected use case dependency for processing the request.

        Returns:
            AnswerResultDTO containing the assistant's response.
        """
        logger.info(f"POST /ainvoke - conversation_id: {dto.config.conversation_id}")
        logger.debug(f"Message: {dto.message[:100]}...")

        result = await use_case.ainvoke(dto)

        logger.info(f"POST /ainvoke completed - conversation_id: {dto.config.conversation_id}")
        return result

    @router.post("/astream")
    async def astream(
        dto: AnswerRequestDTO,
        use_case: AddingToolsUseCase = Depends(get_adding_tools_use_case),
    ):
        """Handle async streaming question-answering requests with tool support.

        This endpoint processes a user's question and streams the response
        in real-time using Server-Sent Events (SSE). Tool usage is transparent
        to the client and logged in the conversation history.

        Args:
            dto: The answer request containing the user's question.
            use_case: Injected use case dependency for processing the request.

        Returns:
            StreamingResponse with text/event-stream content type.
        """
        logger.info(f"POST /astream - conversation_id: {dto.config.conversation_id}")
        logger.debug(f"Message: {dto.message[:100]}...")

        async def _gen():
            async for ev in use_case.astream(dto):  # type: ignore
                yield f"data: {ev.model_dump_json()}\n\n".encode()
            logger.info(f"POST /astream completed - conversation_id: {dto.config.conversation_id}")

        return StreamingResponse(_gen(), media_type="text/event-stream")

    return router
