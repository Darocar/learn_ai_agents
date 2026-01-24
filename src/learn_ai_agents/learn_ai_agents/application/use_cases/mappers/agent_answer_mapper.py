"""Mapper utilities for converting between DTOs and domain models.

This module provides mapping functions to translate between application-layer
DTOs and domain-layer models, maintaining separation of concerns.
"""

from learn_ai_agents.application.dtos.agents.basic_answer import (
    AnswerRequestDTO,
    AnswerResultDTO,
    AssistantMessageDTO,
)
from learn_ai_agents.domain.models.agents.config import Config
from learn_ai_agents.domain.models.agents.messages import Message, Role
from datetime import datetime


class Mapper:
    """Mapper class for converting between DTOs and domain models.

    This class provides static methods to convert between application-layer
    DTOs (Data Transfer Objects) and domain-layer models, ensuring clean
    separation between layers in the hexagonal architecture.
    """

    @staticmethod
    def dto_to_message(dto: AnswerRequestDTO) -> Message:
        """Convert an answer request DTO to a domain message.

        Args:
            dto: The answer request DTO containing the user's message.

        Returns:
            A domain Message object with the user's content.
        """
        return Message(
            role=Role.USER,
            content=dto.message,
            timestamp=datetime.now(),
        )

    @staticmethod
    def message_to_dto(message: Message, config: Config) -> AnswerResultDTO:
        """Convert a domain message to an answer result DTO.

        Args:
            message: The domain message containing the assistant's response.
            config: The configuration containing conversation metadata.

        Returns:
            An AnswerResultDTO containing the formatted response.
        """
        assistant_message_dto = AssistantMessageDTO(role="assistant", content=message.content)
        return AnswerResultDTO(
            message=assistant_message_dto,
            conversation_id=config.conversation_id,  # Adjust as needed based on your DTO structure
        )

    @staticmethod
    def config_dto_to_config(dto: AnswerRequestDTO) -> Config:
        """Convert a request DTO's configuration to a domain Config.

        Args:
            dto: The answer request DTO containing configuration.

        Returns:
            A domain Config object.
        """
        return Config(conversation_id=dto.config.conversation_id)
