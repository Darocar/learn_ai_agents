"""Mapper utilities for DTO ↔ Domain model conversion."""

from learn_ai_agents.application.dtos.basic_answer import (
    AnswerRequestDTO,
    AnswerResultDTO,
    AssistantMessageDTO,
)
from learn_ai_agents.domain.models.config import Config
from learn_ai_agents.domain.models.messages import Message, Role


class Mapper:
    """Converts between DTOs and domain models."""

    @staticmethod
    def dto_to_message(dto: AnswerRequestDTO) -> Message:
        """Convert answer request DTO to a domain Message."""
        return Message(
            role=Role.USER,
            content=dto.message,
        )

    @staticmethod
    def message_to_dto(message: Message, config: Config) -> AnswerResultDTO:
        """Convert domain Message and Config to response DTO."""
        assistant_message_dto = AssistantMessageDTO(
            role="assistant",
            content=message.content,
        )
        return AnswerResultDTO(
            message=assistant_message_dto,
            conversation_id=config.conversation_id,
        )

    @staticmethod
    def config_dto_to_config(dto: AnswerRequestDTO) -> Config:
        """Convert request DTO's configuration to domain Config."""
        return Config(conversation_id=dto.config.conversation_id)
