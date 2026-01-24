"""MongoDB repository implementation for chat history using Odmantic.

This module implements the chat history persistence using the
repository pattern with Odmantic for type-safe MongoDB operations.
"""

from learn_ai_agents.application.outbound_ports.agents.chat_history import ChatHistoryStorePort
from learn_ai_agents.application.outbound_ports.database import DatabaseClient
from learn_ai_agents.domain.models.agents.conversation import Conversation
from learn_ai_agents.domain.models.agents.messages import Message, Role
from learn_ai_agents.infrastructure.outbound.base_persistence import BaseMongoModelRepository
from learn_ai_agents.infrastructure.outbound.chat_history.mongo.models import (
    ConversationModel,
    ConversationMessageModel,
)
from learn_ai_agents.logging import get_logger

logger = get_logger(__name__)


class MongoChatHistoryStore(BaseMongoModelRepository[ConversationModel], ChatHistoryStorePort):
    """MongoDB implementation of the ChatHistoryStore port using Odmantic.

    This adapter implements the ChatHistoryStore port by inheriting from
    BaseMongoModelRepository and handling the mapping between domain
    Conversation/Message objects and ODM ConversationDocument models.
    """

    def __init__(self, database: DatabaseClient):
        """Initialize the MongoDB chat history store.

        Args:
            database: The database client instance (MongoEngineAdapter).
        """
        super().__init__(database.get_engine(), ConversationModel)
        logger.info("MongoDB chat history store initialized with Odmantic")

    async def save_message(self, conversation_id: str, message: Message) -> None:
        """Save a message to the conversation history in MongoDB.

        Args:
            conversation_id: Unique identifier for the conversation.
            message: The message to store.
        """
        logger.debug(f"Saving message to conversation {conversation_id}")

        # Find existing conversation document
        docs = await self.find_by(conversation_id=conversation_id)

        odm_message = ConversationMessageModel(
            role=message.role.value,  # Enum → str
            content=message.content,
            timestamp=message.timestamp,
            metadata=message.metadata or {},
        )

        if docs:
            # Update existing conversation
            doc = docs[0]
            doc.messages.append(odm_message)
            await self.save_one(doc)
            logger.debug(f"Updated conversation {conversation_id} with new message")
        else:
            # Create new conversation document
            doc = ConversationModel(  # type: ignore
                conversation_id=conversation_id,
                messages=[odm_message],
            )
            await self.save_one(doc)
            logger.debug(f"Created new conversation {conversation_id}")

    async def load_conversation(self, conversation_id: str) -> Conversation:
        logger.debug(f"Loading conversation {conversation_id}")

        docs = await self.find_by(conversation_id=conversation_id)

        if not docs:
            logger.debug(f"No conversation found for {conversation_id}, returning empty")
            return Conversation(conversation_id=conversation_id, messages=[])

        doc = docs[0]
        messages = [
            Message(
                role=Role(msg.role),
                content=msg.content,
                timestamp=msg.timestamp,
                metadata=getattr(msg, "metadata", None),
            )
            for msg in doc.messages
        ]

        logger.debug(f"Loaded {len(messages)} messages for conversation {conversation_id}")
        return Conversation(conversation_id=conversation_id, messages=messages)
