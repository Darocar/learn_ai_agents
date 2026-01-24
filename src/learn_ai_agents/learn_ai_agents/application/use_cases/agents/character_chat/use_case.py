"""Character chat use case implementation.

This module implements the core business logic for chatting with BG3 characters
using RAG (Retrieval-Augmented Generation). It orchestrates between the
application's DTOs and the domain's agent engine with vector search capabilities.
"""

from collections.abc import AsyncIterator

from learn_ai_agents.application.dtos.agents.character_chat import (
    CharacterChatRequestDTO,
    CharacterChatResultDTO,
    CharacterChatStreamEventDTO,
)
from learn_ai_agents.application.inbound_ports.agents.character_chat import CharacterChatPort
from learn_ai_agents.application.outbound_ports.agents.agent_engine import AgentEngine
from learn_ai_agents.application.outbound_ports.content_indexer.repositories.vector_store_repository import (
    VectorStoreRepositoryPort,
)
from learn_ai_agents.logging import get_logger

from learn_ai_agents.application.use_cases.mappers.character_chat_mapper import Mapper

logger = get_logger(__name__)


class CharacterChatUseCase(CharacterChatPort):
    """Use case for chatting with BG3 characters using RAG.

    This class implements the CharacterChatPort interface and serves as the
    application layer's primary orchestrator for character chat functionality.
    It translates between DTOs (used at the API boundary) and domain models
    (used by the agent engine).

    The agent in this use case has access to a vector search tool that retrieves
    relevant character information from a Qdrant vector database to provide
    accurate, character-specific responses.

    Attributes:
        agent: The agent engine responsible for generating character responses.
        embedder: Embedder for generating query vectors.
        vector_store: Vector store for retrieving personality information.
        mapper: Utility for converting between DTOs and domain models.
    """

    def __init__(
        self,
        agent: AgentEngine,
        vector_store: VectorStoreRepositoryPort,
    ):
        """Initialize the use case with an agent engine and vector store.

        Args:
            agent: The agent engine to use for generating character responses.
            embedder: Embedder port for generating query vectors.
            vector_store: Vector store port for retrieving personality information.
        """
        self.agent = agent
        self.vector_store = vector_store
        self.mapper = Mapper()
        logger.info("Initialized CharacterChatUseCase")

    async def ainvoke(self, cmd: CharacterChatRequestDTO) -> CharacterChatResultDTO:
        """Handle an asynchronous character chat request.

        This method processes a user's message to a BG3 character and returns
        a complete answer. The agent uses vector search to retrieve relevant
        character information from the knowledge base.

        Args:
            cmd: The chat request containing the user's message, character name,
                and document ID for RAG.

        Returns:
            The chat result containing the character's response.
        """
        logger.info(f"Processing async invoke for character '{cmd.character_name}': {cmd.message[:100]}...")
        logger.debug(f"Using document_id: {cmd.document_id}")

        # Retrieve character personality
        personality = await self.get_personality(cmd.document_id)

        input_message = self.mapper.dto_to_message(dto=cmd)
        input_config = self.mapper.config_dto_to_config(dto=cmd)

        logger.debug("Calling agent.ainvoke with vector search support...")
        response = await self.agent.ainvoke(
            new_message=input_message,
            config=input_config,
            character_name=cmd.character_name,
            document_id=cmd.document_id,
            personality=personality,
        )

        result = self.mapper.message_to_dto(
            message=response,
            config=input_config,
            character_name=cmd.character_name,
        )

        logger.info(f"Async invoke for character '{cmd.character_name}' completed successfully")
        return result

    async def astream(self, cmd: CharacterChatRequestDTO) -> AsyncIterator[CharacterChatStreamEventDTO]:  # type: ignore
        """Handle an asynchronous streaming character chat request.

        This method processes a user's message to a BG3 character and yields
        the response in real-time chunks. The agent uses vector search to
        retrieve relevant character information during the process.

        Args:
            cmd: The chat request containing the user's message, character name,
                and document ID for RAG.

        Yields:
            Stream events containing response deltas and completion signals.
        """
        logger.info(f"Processing async stream for character '{cmd.character_name}': {cmd.message[:100]}...")
        logger.debug(f"Using document_id: {cmd.document_id}")

        # Retrieve character personality
        personality = await self.get_personality(cmd.document_id)

        input_message = self.mapper.dto_to_message(dto=cmd)
        input_config = self.mapper.config_dto_to_config(dto=cmd)

        logger.debug("Starting agent async stream with vector search support...")
        chunk_count = 0
        async for chunk in self.agent.astream(  # type: ignore
            new_message=input_message,
            config=input_config,
            character_name=cmd.character_name,
            document_id=cmd.document_id,
            personality=personality,
        ):
            # Handle different chunk kinds
            if chunk.kind == "text" and chunk.text is not None:
                chunk_count += 1
                yield CharacterChatStreamEventDTO(
                    kind="delta",
                    delta=chunk.text,
                )
            elif chunk.kind == "tool_start":
                logger.debug(f"Tool started: {chunk.tool_name}")
                yield CharacterChatStreamEventDTO(
                    kind="tool_start",
                    tool_name=chunk.tool_name,
                    tool_input=chunk.tool_input,
                )
            elif chunk.kind == "tool_end":
                logger.debug(f"Tool ended: {chunk.tool_name}")
                yield CharacterChatStreamEventDTO(
                    kind="tool_end",
                    tool_name=chunk.tool_name,
                    tool_output=chunk.tool_output,
                )
            elif chunk.kind == "done":
                logger.debug("Stream marked as done by agent")
                break

        logger.info(f"Async stream for character '{cmd.character_name}' completed: {chunk_count} chunks sent")
        yield CharacterChatStreamEventDTO(
            kind="done",
            delta=None,
        )

    async def get_personality(self, document_id: str) -> str:
        """Retrieve character personality from vector store.

        Args:
            document_id: The document ID (collection name) to search.

        Returns:
            The personality text retrieved from the vector store, or a default message.
        """
        logger.debug(f"Retrieving personality from collection: {document_id}")
        personality = await self.vector_store.get_personality(document_id=document_id)

        if personality is None:
            logger.warning(f"No personality found for document_id: {document_id}")
            return "No specific personality information available."

        logger.debug(f"Retrieved personality: {len(personality)} characters")
        return personality
