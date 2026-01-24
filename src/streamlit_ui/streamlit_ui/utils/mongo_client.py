"""MongoDB utilities for direct database access from Streamlit UI."""

from typing import List, Dict, Any, Optional
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorClient


class MongoConversationStore:
    """Helper class to interact with MongoDB conversation storage."""
    
    def __init__(self, mongo_uri: str, database_name: str):
        """Initialize MongoDB client.
        
        Args:
            mongo_uri: MongoDB connection URI
            database_name: Name of the database
        """
        self.client: AsyncIOMotorClient = AsyncIOMotorClient(mongo_uri)
        self.db = self.client[database_name]
        self.collection = self.db["conversations"]
    
    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a conversation by ID.
        
        Args:
            conversation_id: The conversation identifier
            
        Returns:
            Dictionary with conversation data or None if not found
        """
        return await self.collection.find_one({"conversation_id": conversation_id})
    
    async def get_messages(self, conversation_id: str) -> List[Dict[str, str]]:
        """Get messages from a conversation formatted for Streamlit.
        
        Args:
            conversation_id: The conversation identifier
            
        Returns:
            List of message dictionaries with 'role' and 'content' keys
        """
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            return []
        
        messages = []
        for msg in conversation.get("messages", []):
            # Convert role to Streamlit format (user/assistant)
            role = msg.get("role", "user")
            if role == "human":
                role = "user"
            elif role == "ai":
                role = "assistant"
            
            messages.append({
                "role": role,
                "content": msg.get("content", ""),
                "timestamp": msg.get("timestamp", 0.0)
            })
        
        return messages
    
    async def get_all_conversation_ids(self) -> List[str]:
        """Get all conversation IDs from the database.
        
        Returns:
            List of conversation IDs
        """
        cursor = self.collection.find({}, {"conversation_id": 1, "_id": 0})
        conversations = await cursor.to_list(length=None)
        return [conv["conversation_id"] for conv in conversations]
    
    async def get_conversation_summary(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of a conversation.
        
        Args:
            conversation_id: The conversation identifier
            
        Returns:
            Dictionary with conversation summary information
        """
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            return None
        
        messages = conversation.get("messages", [])
        
        return {
            "conversation_id": conversation_id,
            "message_count": len(messages),
            "first_message_time": messages[0].get("timestamp") if messages else None,
            "last_message_time": messages[-1].get("timestamp") if messages else None,
            "messages": messages
        }
    
    def close(self):
        """Close the MongoDB client connection."""
        self.client.close()


class MongoCharacterStore:
    """Helper class to interact with MongoDB character documents storage."""
    
    def __init__(self, mongo_uri: str, database_name: str):
        """Initialize MongoDB client.
        
        Args:
            mongo_uri: MongoDB connection URI
            database_name: Name of the database
        """
        self.client: AsyncIOMotorClient = AsyncIOMotorClient(mongo_uri)
        self.db = self.client[database_name]
        self.collection = self.db["documents_bg3_characters"]
    
    async def get_available_characters(self) -> List[str]:
        """Fetch unique character names from documents collection.
        
        Returns:
            Sorted list of character names
        """
        characters = await self.collection.distinct("character_name")
        return sorted(characters)
    
    async def get_documents_for_character(self, character_name: str) -> List[str]:
        """Fetch available document_ids for a specific character.
        
        Args:
            character_name: Name of the character
            
        Returns:
            Sorted list of document IDs for the character
        """
        documents = await self.collection.distinct(
            "document_id", 
            {"character_name": character_name}
        )
        return sorted(documents)
    
    def close(self):
        """Close the MongoDB client connection."""
        self.client.close()
