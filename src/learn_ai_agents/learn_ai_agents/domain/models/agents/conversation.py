from datetime import datetime
from dataclasses import dataclass
from typing import Optional


from .messages import Message, Role
from learn_ai_agents.infrastructure.helpers.generators import Helper


@dataclass
class Conversation:
    """
    Represents a conversation history with optional system instructions.

    A conversation is a sequence of messages that provides context for the agent.
    This domain object manages the conversation state and provides methods
    for common operations.

    Attributes:
        instructions: Optional system-level message that sets agent behavior
        messages: Ordered list of messages in the conversation

    Example:
        conversation = Conversation(
            instructions=Message(Role.SYSTEM, "You are a helpful assistant"),
            messages=[]
        )
        conversation.add_message(Role.USER, "Hello!")
    """

    conversation_id: str
    messages: list[Message]
    conversation_started_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.conversation_started_at is None:
            object.__setattr__(self, 'conversation_started_at', Helper.generate_timestamp())

    def add_message(self, role: Role, content: str) -> None:
        """
        Add a new message to the conversation.

        This is a domain operation that maintains the conversation's integrity.

        Args:
            role: The role of the message sender
            content: The message content
        """
        self.messages.append(Message(role, content, Helper.generate_timestamp()))

    def get_last_message(self) -> Message | None:
        """
        Retrieve the most recent message in the conversation.

        This is useful for getting the latest response or checking conversation state.

        Returns:
            The last message if the conversation has messages, None otherwise
        """
        if self.messages:
            return self.messages[-1]
        return None
