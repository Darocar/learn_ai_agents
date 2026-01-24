"""Basic answer use case implementation."""

from collections.abc import AsyncIterator

from learn_ai_agents.application.dtos.agents.basic_answer import (
    AnswerRequestDTO,
    AnswerResultDTO,
    AnswerStreamEventDTO,
)
from learn_ai_agents.application.inbound_ports.agents.basic_answer import BasicAnswerPort
from learn_ai_agents.application.outbound_ports.agents.agent_engine import AgentEngine
from learn_ai_agents.logging import get_logger

from .mapper import Mapper

logger = get_logger(__name__)


class BasicAnswerUseCase(BasicAnswerPort):
    """Use case for handling basic question-answering requests."""

    def __init__(self, agent: AgentEngine):
        """Initialize with an injected agent engine."""
        self.agent = agent
        self.mapper = Mapper()

    async def ainvoke(self, cmd: AnswerRequestDTO) -> AnswerResultDTO:
        """Handle an asynchronous question-answering request."""
        logger.info(f"Processing async invoke request: {cmd.message[:100]}...")

        input_message = self.mapper.dto_to_message(dto=cmd)
        input_config = self.mapper.config_dto_to_config(dto=cmd)

        logger.debug("Calling agent.ainvoke...")
        response = await self.agent.ainvoke(
            new_message=input_message,
            config=input_config,
        )

        result = self.mapper.message_to_dto(
            message=response,
            config=input_config,
        )

        logger.info("Async invoke request completed successfully")
        return result

    async def astream(self, cmd: AnswerRequestDTO) -> AsyncIterator[AnswerStreamEventDTO]:  # type: ignore
        """Handle an asynchronous streaming question-answering request."""
        logger.info(f"Processing async stream request: {cmd.message[:100]}...")

        input_message = self.mapper.dto_to_message(dto=cmd)
        input_config = self.mapper.config_dto_to_config(dto=cmd)

        logger.debug("Starting agent async stream...")
        chunk_count = 0
        async for chunk in self.agent.astream(  # type: ignore
            new_message=input_message,
            config=input_config,
        ):
            if chunk.text is not None:
                chunk_count += 1
                yield AnswerStreamEventDTO(
                    kind="delta",
                    delta=chunk.text,
                )

        logger.info(f"Async stream request completed: {chunk_count} chunks sent")
        yield AnswerStreamEventDTO(
            kind="done",
            delta=None,
        )
