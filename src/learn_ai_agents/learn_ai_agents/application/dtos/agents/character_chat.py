"""Data Transfer Objects for BG3 Character Chat functionality.

This module defines the DTOs (Data Transfer Objects) used for chatting with
Baldur's Gate 3 characters using RAG (Retrieval-Augmented Generation).
"""

from __future__ import annotations

from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class CharacterChatConfigDTO(BaseModel):
    """Configuration for the character chat request.

    Attributes:
        conversation_id: Unique identifier for the conversation thread.
            Defaults to a new UUID if not provided.
    """

    conversation_id: str = Field(default_factory=lambda: str(uuid4()))


class CharacterChatRequestDTO(BaseModel):
    """Request DTO for BG3 character chat.

    This DTO crosses the API boundary and contains everything needed to
    chat with a BG3 character using RAG.

    Attributes:
        config: Configuration for the chat request, including conversation ID.
        message: The user's message to the character.
        character_name: Name of the BG3 character to chat with.
        document_id: ID of the document/collection to use as knowledge source.
    """

    config: CharacterChatConfigDTO = Field(
        default_factory=CharacterChatConfigDTO,
        description="Configuration for the chat request.",
    )
    message: str = Field(..., description="The user's message to the character.")
    character_name: str = Field(..., description="Name of the BG3 character to chat with.")
    document_id: str = Field(
        ...,
        description="Document ID to use as knowledge source for the character.",
    )


class ToolCallDTO(BaseModel):
    """DTO representing a tool call made by the agent.

    Attributes:
        name: The name of the tool that was called.
        args: The input arguments passed to the tool.
        output: The output returned by the tool.
    """

    name: str
    args: dict[str, Any] | None = None
    output: Any | None = None


class AssistantMessageDTO(BaseModel):
    """DTO representing a message from the assistant.

    Attributes:
        role: Always set to "assistant" to identify the message source.
        content: The assistant's response text.
    """

    role: Literal["assistant"] = "assistant"
    content: str


class CharacterChatResultDTO(BaseModel):
    """Result DTO containing the character's response.

    Attributes:
        conversation_id: The conversation thread identifier.
        message: The character's message containing the answer.
        character_name: Name of the character who responded.
        tool_calls: Optional list of tools that were called during response generation.
    """

    conversation_id: str
    message: AssistantMessageDTO
    character_name: str
    tool_calls: list[ToolCallDTO] | None = None


class CharacterChatStreamEventDTO(BaseModel):
    """Stream event DTO for real-time streaming responses.

    Used with Server-Sent Events (SSE) or NDJSON to stream partial
    responses as they're generated.

    Attributes:
        kind: Event type - "delta" for partial content, "tool_start" for tool execution start,
              "tool_end" for tool execution completion, "done" for stream completion.
        delta: Partial content fragment (for "delta" events).
        tool_name: Name of the tool being executed (for "tool_start" and "tool_end" events).
        tool_input: Input arguments for the tool (for "tool_start" events).
        tool_output: Output from the tool (for "tool_end" events).
    """

    kind: Literal["delta", "tool_start", "tool_end", "done"] = "delta"
    delta: str | None = None
    tool_name: str | None = None
    tool_input: Any | None = None
    tool_output: Any | None = None
