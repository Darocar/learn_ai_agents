"""Fake chat history persistence adapter for testing.

This module provides an in-memory fake implementation of chat history storage.
No actual persistence happens - all operations are no-ops or in-memory only.
"""

from typing import List, Optional

from learn_ai_agents.domain.models.agents.messages import Message


class FakeChatHistoryStore:
    """Fake chat history store for testing.
    
    Replaces MongoChatHistoryStore with an in-memory implementation.
    All save operations are no-ops, making tests fast and isolated.
    """
    
    def __init__(self, database_ref: Optional[str] = None, **kwargs):
        """Initialize fake chat history store.
        
        Args:
            database_ref: Database reference (ignored).
            **kwargs: Additional arguments (ignored).
        """
        self.database_ref = database_ref
        self._history: dict[str, List[Message]] = {}
    
    async def save_message(
        self, 
        conversation_id: str, 
        message: Message
    ) -> None:
        """Fake save message operation (no-op or in-memory).
        
        Args:
            conversation_id: Conversation identifier.
            message: Message to save.
        """
        if conversation_id not in self._history:
            self._history[conversation_id] = []
        self._history[conversation_id].append(message)
    
    async def get_messages(
        self, 
        conversation_id: str,
        limit: Optional[int] = None
    ) -> List[Message]:
        """Fake get messages operation.
        
        Args:
            conversation_id: Conversation identifier.
            limit: Maximum number of messages to return.
            
        Returns:
            List of messages (from in-memory storage).
        """
        messages = self._history.get(conversation_id, [])
        if limit:
            return messages[-limit:]
        return messages
    
    async def delete_conversation(self, conversation_id: str) -> None:
        """Fake delete conversation operation.
        
        Args:
            conversation_id: Conversation identifier.
        """
        if conversation_id in self._history:
            del self._history[conversation_id]
    
    async def clear_all(self) -> None:
        """Clear all stored messages (useful for test cleanup)."""
        self._history.clear()
    
    def get_history(self, conversation_id: str) -> List[Message]:
        """Get conversation history (synchronous helper for tests).
        
        Args:
            conversation_id: Conversation identifier.
            
        Returns:
            List of messages.
        """
        return self._history.get(conversation_id, [])
