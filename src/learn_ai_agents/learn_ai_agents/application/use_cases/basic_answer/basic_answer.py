"""Basic answer use case implementation."""

from collections.abc import Iterable

from learn_ai_agents.application.dtos.basic_answer import (
    AnswerRequestDTO,
    AnswerResultDTO,
    AnswerStreamEventDTO,
)
from learn_ai_agents.application.inbound_ports.basic_answer import BasicAnswerPort
from learn_ai_agents.application.outbound_ports.agent_engine import AgentEngine

from .mapper import Mapper


class BasicAnswerUseCase(BasicAnswerPort):
    """Use case for handling basic question-answering requests."""

    def __init__(self, agent: AgentEngine):
        """Initialize with an injected agent engine."""
        self.agent = agent
        self.mapper = Mapper()

    def invoke(self, cmd: AnswerRequestDTO) -> AnswerResultDTO:
        """Process a question and return the complete answer."""
        # Map DTO → Domain
        input_message = self.mapper.dto_to_message(dto=cmd)
        input_config = self.mapper.config_dto_to_config(dto=cmd)

        # Call agent
        response = self.agent.invoke(
            new_message=input_message,
            config=input_config,
        )

        # Map Domain → DTO
        return self.mapper.message_to_dto(
            message=response,
            config=input_config,
        )

    def stream(self, cmd: AnswerRequestDTO) -> Iterable[AnswerStreamEventDTO]:
        """Process a question and stream the response in chunks."""
        # Map DTO → Domain
        input_message = self.mapper.dto_to_message(dto=cmd)
        input_config = self.mapper.config_dto_to_config(dto=cmd)

        # Stream from agent
        for chunk in self.agent.stream(
            new_message=input_message,
            config=input_config,
        ):
            if chunk.text is not None:
                yield AnswerStreamEventDTO(
                    kind="delta",
                    delta=chunk.text,
                )

        # Signal completion
        yield AnswerStreamEventDTO(
            kind="done",
            delta=None,
        )
