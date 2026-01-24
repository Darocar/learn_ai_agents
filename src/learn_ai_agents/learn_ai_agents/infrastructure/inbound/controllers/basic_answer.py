"""FastAPI controller for basic answer endpoint."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from learn_ai_agents.application.dtos.basic_answer import (
    AnswerRequestDTO,
    AnswerResultDTO,
)
from learn_ai_agents.application.inbound_ports.basic_answer import BasicAnswerPort
from learn_ai_agents.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


def get_basic_answer_use_case(request: Request) -> BasicAnswerPort:
    """Get BasicAnswerUseCase from application container.

    Args:
        request: FastAPI request with app state

    Returns:
        BasicAnswerPort instance
    """
    container = request.app.state.container
    return container.get_basic_answer_use_case()


@router.post("/basic-answer", response_model=AnswerResultDTO)
def answer_question(
    dto: AnswerRequestDTO,
    use_case: BasicAnswerPort = Depends(get_basic_answer_use_case),
) -> AnswerResultDTO:
    """Answer a question with complete response.

    Args:
        dto: Question and configuration
        use_case: Injected use case instance

    Returns:
        Complete answer from the assistant
    """
    logger.info(f"POST /chat/basic-answer - conversation_id: {dto.config.conversation_id}")
    logger.debug(f"Message: {dto.message[:100]}...")

    result = use_case.invoke(dto)

    logger.info(f"POST /chat/basic-answer completed - conversation_id: {dto.config.conversation_id}")
    return result


@router.post("/basic-answer/stream")
def stream_answer(
    dto: AnswerRequestDTO,
    use_case: BasicAnswerPort = Depends(get_basic_answer_use_case),
):
    """Answer a question with streaming response.

    Args:
        dto: Question and configuration
        use_case: Injected use case instance

    Returns:
        Server-sent events stream of answer chunks
    """
    logger.info(f"POST /chat/basic-answer/stream - conversation_id: {dto.config.conversation_id}")
    logger.debug(f"Message: {dto.message[:100]}...")

    def event_generator():
        for event in use_case.stream(dto):
            yield f"data: {event.model_dump_json()}\n\n"
        logger.info(f"POST /chat/basic-answer/stream completed - conversation_id: {dto.config.conversation_id}")

    return StreamingResponse(event_generator(), media_type="text/event-stream")
