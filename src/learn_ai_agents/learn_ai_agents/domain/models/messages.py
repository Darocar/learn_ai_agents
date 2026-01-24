"""Domain models for messages and conversations."""

import enum
from dataclasses import dataclass


class Role(enum.Enum):
    """Role of a message sender (system, user, assistant, tool)."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """A single message in a conversation."""

    role: Role
    content: str


@dataclass
class Conversation:
    """A conversation history with optional system instructions."""

    instructions: Message | None
    messages: list[Message]

    def add_message(self, role: Role, content: str) -> None:
        """Add a new message to the conversation."""
        self.messages.append(Message(role, content))

    def get_last_message(self) -> Message | None:
        """Get the most recent message, or None if conversation is empty."""
        if self.messages:
            return self.messages[-1]
        return None


@dataclass(frozen=True)
class ChunkDelta:
    """A single chunk in a streaming LLM response."""

    text: str | None = None
