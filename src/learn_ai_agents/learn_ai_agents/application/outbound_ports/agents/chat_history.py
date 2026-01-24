from typing import Protocol

from learn_ai_agents.domain.models.agents.conversation import Conversation
from learn_ai_agents.domain.models.agents.messages import Message


class ChatHistoryStorePort(Protocol):
    """Port interface for chat history storage operations."""

    async def save_message(self, conversation_id: str, message: Message) -> None:
        """Save the conversation history.

        Args:
            conversation_id: Unique identifier for the conversation.
            messages: List of message dictionaries to store.
        """
        ...

    async def load_conversation(self, conversation_id: str) -> Conversation:
        """Load the conversation history.

        Args:
            conversation_id: Unique identifier for the conversation.

        Returns:
            Conversation: The loaded conversation object.
        """
        ...
