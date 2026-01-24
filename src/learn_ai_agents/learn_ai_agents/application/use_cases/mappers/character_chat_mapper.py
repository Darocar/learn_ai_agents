"""Mapper utilities for converting between DTOs and domain models.

This module provides mapping functions to translate between application-layer
DTOs and domain-layer models for character chat functionality.
"""

from datetime import datetime

from learn_ai_agents.application.dtos.agents.character_chat import (
    AssistantMessageDTO,
    CharacterChatRequestDTO,
    CharacterChatResultDTO,
    ToolCallDTO,
)
from learn_ai_agents.domain.models.agents.config import Config
from learn_ai_agents.domain.models.agents.messages import Message, Role
from learn_ai_agents.infrastructure.helpers.generators import Helper


class Mapper:
    """Mapper class for converting between DTOs and domain models.

    This class provides static methods to convert between application-layer
    DTOs (Data Transfer Objects) and domain-layer models, ensuring clean
    separation between layers in the hexagonal architecture.
    """

    @staticmethod
    def dto_to_message(dto: CharacterChatRequestDTO) -> Message:
        """Convert a character chat request DTO to a domain message.

        Args:
            dto: The character chat request DTO containing the user's message.

        Returns:
            A domain Message object with the user's content.
        """
        return Message(
            role=Role.USER,
            content=dto.message,
            timestamp=Helper.generate_timestamp(),
        )

    @staticmethod
    def message_to_dto(
        message: Message,
        config: Config,
        character_name: str,
    ) -> CharacterChatResultDTO:
        """Convert a domain message to a character chat result DTO.

        Args:
            message: The domain message containing the character's response.
            config: The configuration containing conversation metadata.
            character_name: Name of the character who responded.

        Returns:
            A CharacterChatResultDTO containing the formatted response.
        """
        assistant_message_dto = AssistantMessageDTO(
            role="assistant",
            content=message.content,
        )

        # Extract tool_calls from message metadata
        raw_tool_calls = (message.metadata or {}).get("tool_calls") if message.metadata else None
        tool_calls_dto: list[ToolCallDTO] | None = None

        if raw_tool_calls:
            tool_calls_dto = [
                ToolCallDTO(
                    name=tc.get("name", "<unknown_tool>"),
                    args=tc.get("args"),
                    output=tc.get("output"),
                )
                for tc in raw_tool_calls
            ]

        return CharacterChatResultDTO(
            message=assistant_message_dto,
            conversation_id=config.conversation_id,
            character_name=character_name,
            tool_calls=tool_calls_dto,
        )

    @staticmethod
    def config_dto_to_config(dto: CharacterChatRequestDTO) -> Config:
        """Convert a request DTO's configuration to a domain Config.

        Args:
            dto: The character chat request DTO containing configuration.

        Returns:
            A domain Config object.
        """
        return Config(conversation_id=dto.config.conversation_id)
