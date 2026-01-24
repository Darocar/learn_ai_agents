"""FastAPI controller for basic answer endpoint."""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from learn_ai_agents.application.dtos.agents.basic_answer import (
    AnswerRequestDTO,
    AnswerResultDTO,
)
from learn_ai_agents.application.use_cases.agents.basic_answer.basic_answer import BasicAnswerUseCase
from learn_ai_agents.logging import get_logger
from learn_ai_agents.settings import UseCaseConfig
from ..dependencies import get_basic_answer_use_case

logger = get_logger(__name__)


def get_router(use_case_config: UseCaseConfig) -> APIRouter:
    """Create and configure the router for basic answer endpoints.

    Args:
        use_case_config: Configuration for this use case including path prefix and metadata.

    Returns:
        Configured APIRouter instance.
    """
    router = APIRouter(prefix=use_case_config.info.path_prefix, tags=[use_case_config.info.path_prefix])

    @router.post("/ainvoke", response_model=AnswerResultDTO)
    async def ainvoke(
        dto: AnswerRequestDTO,
        use_case: BasicAnswerUseCase = Depends(get_basic_answer_use_case),
    ) -> AnswerResultDTO:
        """Answer a question with complete response.

        Args:
            dto: Question and configuration
            use_case: Injected use case instance

        Returns:
            Complete answer from the assistant
        """
        logger.info(f"POST /ainvoke - conversation_id: {dto.config.conversation_id}")
        logger.debug(f"Message: {dto.message[:100]}...")

        result = await use_case.ainvoke(dto)

        logger.info(f"POST /ainvoke completed - conversation_id: {dto.config.conversation_id}")
        return result

    @router.post("/astream")
    async def astream(
        dto: AnswerRequestDTO,
        use_case: BasicAnswerUseCase = Depends(get_basic_answer_use_case),
    ):
        """Answer a question with streaming response.

        Args:
            dto: Question and configuration
            use_case: Injected use case instance

        Returns:
            StreamingResponse with text chunks
        """
        logger.info(f"POST /astream - conversation_id: {dto.config.conversation_id}")
        logger.debug(f"Message: {dto.message[:100]}...")

        async def _gen():
            async for ev in use_case.astream(dto):  # type: ignore
                yield f"data: {ev.model_dump_json()}\n\n".encode()
            logger.info(f"POST /astream completed - conversation_id: {dto.config.conversation_id}")

        return StreamingResponse(_gen(), media_type="text/event-stream")

    return router
