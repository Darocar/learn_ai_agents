"""
Domain Models for Messages and Conversations

This module contains the core domain entities for messaging in our AI agent system.
These are PURE DOMAIN OBJECTS - they have no dependencies on external frameworks,
databases, or infrastructure concerns.

Following the Hexagonal Architecture principle: Domain models should represent
business concepts in their purest form, independent of how they're stored,
transmitted, or presented.

Key concepts:
- Message: A single message in a conversation (from user, assistant, or system)
- Conversation: A collection of messages with optional system instructions
- Role: Who is speaking (system, user, assistant, or tool)
- ChunkDelta: A streaming response fragment
"""

import enum
from dataclasses import dataclass
from typing import Any, Literal, Dict
from datetime import datetime


class Role(enum.Enum):
    """
    Represents the role/speaker in a conversation.

    This is a domain concept that transcends any specific LLM provider's format.
    We use this enum to maintain consistency across different LLM adapters.

    Attributes:
        SYSTEM: System-level instructions that guide the agent's behavior
        USER: Messages from the human user
        ASSISTANT: Messages from the AI assistant
        TOOL: Messages from tool executions (for function calling scenarios)
    """

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """
    A single message in a conversation.

    This is our core domain entity for communication. It's framework-agnostic
    and represents the essential information about a message regardless of
    which LLM provider we use.

    Attributes:
        role: Who is sending this message (system, user, assistant, or tool)
        content: The actual message content (text)
        timestamp: Unix timestamp of when the message was created
        metadata: Optional dictionary for additional metadata (e.g., tool_calls)

    Design Note: We use @dataclass for simplicity and immutability by default.
    In a more complex system, this might become a full class with behavior methods.
    """

    role: Role
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] | None = None


@dataclass(frozen=True)
class ChunkDelta:
    """
    Streaming event from the agent.

    When an LLM streams its response, each piece is represented as a ChunkDelta.
    This includes both text chunks and tool execution events.

    Attributes:
        kind: Event type - "text" for streamed LLM text (normal case),
              "tool_start" when a tool is about to be called,
              "tool_end" when a tool finished,
              "done" when stream completed.
        text: The text content for normal chunks (None for tool/done events)
        tool_name: Name of the tool being called (for tool_* events)
        tool_input: Input arguments for the tool (for tool_start)
        tool_output: Output from the tool (for tool_end)

    Design Note: We use frozen=True to make these immutable, as stream chunks
    should not be modified after creation.

    Examples:
        # Text chunk:
        ChunkDelta(kind="text", text="Hello")

        # Tool start:
        ChunkDelta(kind="tool_start", tool_name="search", tool_input={"query": "BG3"})

        # Tool end:
        ChunkDelta(kind="tool_end", tool_name="search", tool_output="Results...")

        # Stream done:
        ChunkDelta(kind="done")
    """

    kind: Literal["text", "tool_start", "tool_end", "done"] = "text"
    text: str | None = None
    tool_name: str | None = None
    tool_input: dict[str, Any] | None = None
    tool_output: Any | None = None
