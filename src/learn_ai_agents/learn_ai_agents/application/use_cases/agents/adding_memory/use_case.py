"""Basic answer use case implementation.

This module implements the core business logic for handling basic question-answering
requests. It orchestrates between the application's DTOs and the domain's agent engine.
"""

from collections.abc import AsyncIterator

from learn_ai_agents.application.dtos.agents.basic_answer import (
    AnswerRequestDTO,
    AnswerResultDTO,
    AnswerStreamEventDTO,
)
from learn_ai_agents.application.inbound_ports.agents.agent_answer import AgentAnswerPort
from learn_ai_agents.application.outbound_ports.agents.agent_engine import AgentEngine
from learn_ai_agents.logging import get_logger

from learn_ai_agents.application.use_cases.mappers.agent_answer_mapper import Mapper

logger = get_logger(__name__)


class AddingMemoryUseCase(AgentAnswerPort):
    """Use case for handling basic question-answering requests.

    This class implements the BasicAnswerPort interface and serves as the
    application layer's primary orchestrator for question-answering functionality.
    It translates between DTOs (used at the API boundary) and domain models
    (used by the agent engine).

    Attributes:
        agent: The agent engine responsible for generating responses.
        mapper: Utility for converting between DTOs and domain models.
    """

    def __init__(self, agent: AgentEngine):
        """Initialize the use case with an agent engine.

        Args:
            agent: The agent engine to use for generating answers.
        """
        self.agent = agent
        self.mapper = Mapper()

    # ---- async non-streaming ----
    async def ainvoke(self, cmd: AnswerRequestDTO) -> AnswerResultDTO:
        """Handle an asynchronous question-answering request.

        This method processes a user's question and returns a complete answer.
        It converts the request DTO to domain models, invokes the agent,
        and converts the response back to a DTO.

        Args:
            cmd: The answer request containing the user's question and configuration.

        Returns:
            The answer result containing the assistant's response.
        """
        logger.info(f"Processing async invoke request: {cmd.message[:100]}...")

        input_message = self.mapper.dto_to_message(dto=cmd)
        input_config = self.mapper.config_dto_to_config(dto=cmd)

        logger.debug("Calling agent.ainvoke...")
        response = await self.agent.ainvoke(
            new_message=input_message,
            config=input_config,
        )

        # take the last assistant message (fallback to last if none tagged)
        result = self.mapper.message_to_dto(
            message=response,
            config=input_config,
        )

        logger.info("Async invoke request completed successfully")
        return result

    # ---- async streaming ----
    async def astream(self, cmd: AnswerRequestDTO) -> AsyncIterator[AnswerStreamEventDTO]:  # type: ignore
        """Handle an asynchronous streaming question-answering request.

        This method processes a user's question and yields the response
        in real-time chunks, enabling progressive UI updates.

        Args:
            cmd: The answer request containing the user's question and configuration.

        Yields:
            Stream events containing response deltas and completion signals.
        """
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
