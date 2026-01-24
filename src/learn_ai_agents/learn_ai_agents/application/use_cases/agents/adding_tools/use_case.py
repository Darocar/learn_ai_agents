"""Adding tools use case implementation.

This module implements the core business logic for handling requests that
require external tool usage. It orchestrates between the application's DTOs
and the domain's agent engine with tool capabilities.
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


class AddingToolsUseCase(AgentAnswerPort):
    """Use case for handling requests that use external tools.

    This class implements the AgentAnswerPort interface and serves as the
    application layer's primary orchestrator for tool-augmented functionality.
    It translates between DTOs (used at the API boundary) and domain models
    (used by the agent engine).

    The agent in this use case has access to external tools like web search,
    math expression evaluation, and other utilities to provide more
    comprehensive and accurate responses.

    Attributes:
        agent: The agent engine responsible for generating responses using tools.
        mapper: Utility for converting between DTOs and domain models.
    """

    def __init__(self, agent: AgentEngine):
        """Initialize the use case with an agent engine.

        Args:
            agent: The agent engine to use for generating answers with tool support.
        """
        self.agent = agent
        self.mapper = Mapper()

    async def ainvoke(self, cmd: AnswerRequestDTO) -> AnswerResultDTO:
        """Handle an asynchronous question-answering request with tool support.

        This method processes a user's question and returns a complete answer.
        The agent may use external tools (web search, calculations, etc.) to
        provide accurate responses. Tool usage is logged and stored in chat history.

        Args:
            cmd: The answer request containing the user's question and configuration.

        Returns:
            The answer result containing the assistant's response.
        """
        logger.info(f"Processing async invoke request with tools: {cmd.message[:100]}...")

        input_message = self.mapper.dto_to_message(dto=cmd)
        input_config = self.mapper.config_dto_to_config(dto=cmd)

        logger.debug("Calling agent.ainvoke with tool support...")
        response = await self.agent.ainvoke(
            new_message=input_message,
            config=input_config,
        )

        result = self.mapper.message_to_dto(
            message=response,
            config=input_config,
        )

        logger.info("Async invoke request with tools completed successfully")
        return result

    async def astream(self, cmd: AnswerRequestDTO) -> AsyncIterator[AnswerStreamEventDTO]:  # type: ignore
        """Handle an asynchronous streaming question-answering request with tool support.

        This method processes a user's question and yields the response
        in real-time chunks. The agent may use tools during the process,
        and tool interactions are logged and stored.

        Args:
            cmd: The answer request containing the user's question and configuration.

        Yields:
            Stream events containing response deltas and completion signals.
        """
        logger.info(f"Processing async stream request with tools: {cmd.message[:100]}...")

        input_message = self.mapper.dto_to_message(dto=cmd)
        input_config = self.mapper.config_dto_to_config(dto=cmd)

        logger.debug("Starting agent async stream with tool support...")
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

        logger.info(f"Async stream request with tools completed: {chunk_count} chunks sent")
        yield AnswerStreamEventDTO(
            kind="done",
            delta=None,
        )
