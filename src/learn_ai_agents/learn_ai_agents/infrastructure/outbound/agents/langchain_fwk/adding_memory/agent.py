"""Adding memory agent implementation using LangGraph and MongoDB.

This module implements a conversational agent with memory capabilities using
LangGraph's StateGraph and MongoDB for persistence.
"""

from datetime import datetime
from collections.abc import AsyncGenerator
from functools import partial

from langchain_core.messages import AIMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from learn_ai_agents.application.outbound_ports.agents.chat_history import ChatHistoryStorePort
from learn_ai_agents.application.outbound_ports.agents.llm_model import ChatModelProvider
from learn_ai_agents.domain.models.agents.config import Config
from learn_ai_agents.domain.models.agents.messages import ChunkDelta, Message, Role
from learn_ai_agents.infrastructure.helpers.generators import Helper
from learn_ai_agents.infrastructure.outbound.agents.langchain_fwk.helpers import (
    chunk_to_domain,
    content_to_text,
    to_domain_message,
    to_lc_config,
    to_lc_messages,
)
from learn_ai_agents.logging import get_logger

from .._base import BaseLangChainAgent
from .nodes import chatbot_node
from .prompts import ADDING_MEMORY_PROMPT_TEMPLATE
from .state import State

logger = get_logger(__name__)


class AddingMemoryLangGraphAgent(BaseLangChainAgent):
    """A conversational agent with memory using LangGraph.

    This agent uses LangGraph's StateGraph to manage conversation flow and
    pluggable checkpointing for conversation state persistence. It also stores
    messages using the chat history port for explicit message persistence.

    Attributes:
        system_prompt: The system-level instruction for the agent.
        graph: The compiled LangGraph StateGraph.
        checkpointer: Checkpointer for conversation state (optional).
        enable_checkpointing: Flag to control whether checkpointing is enabled.
    """

    def __init__(
        self,
        *,
        config: dict,
        llms: dict[str, ChatModelProvider],
        checkpointer: BaseCheckpointSaver | None = None,
        chat_history_persistence: ChatHistoryStorePort | None = None,
    ) -> None:
        """Initialize the adding memory agent.

        Args:
            config: Configuration dictionary for the agent.
            llms: Dictionary of LLM providers keyed by alias.
            checkpointer: Optional checkpointer for conversation state persistence.
            chat_history_persistence: Optional chat history store for message persistence.
            **kwargs: Additional keyword arguments (e.g., databases for backward compatibility).
        """
        # Store the checkpointer if provided
        self.checkpointer = checkpointer

        super().__init__(config=config, llms=llms, chat_history_persistence=chat_history_persistence)

    def _load_config(self, config: dict) -> None:
        """Load agent-specific configuration.

        Args:
            config: Configuration dictionary containing agent settings.
        """
        self.system_prompt: str = ADDING_MEMORY_PROMPT_TEMPLATE
        # These config values are now optional since checkpointer is injected
        self.database_name = config.get("database_name", "learn_ai_agents")
        self.checkpoints_collection = config.get("checkpoints_collection", "checkpoints")
        self.enable_checkpointing = config.get("enable_checkpointing", True)

    def _configure_nodes(self) -> None:
        """Configure agent nodes for the LangGraph.

        Sets up the conversation node that processes messages using the LLM.
        """
        self.chatbot_node = partial(
            chatbot_node,
            llms=self.llms,
        )

    def _build_graph(self) -> None:
        """Build the agent's LangGraph processing graph.

        Creates a StateGraph with a single conversation node.
        Uses the injected checkpointer if available and enabled.
        """
        logger.debug("Building LangGraph...")

        # Build the graph
        graph_builder = StateGraph(State)

        # Add the chatbot node
        graph_builder.add_node("chatbot", self.chatbot_node)

        # Define edges: START -> chatbot -> END
        graph_builder.add_edge(START, "chatbot")
        graph_builder.add_edge("chatbot", END)

        # Compile with or without checkpointer
        if self.enable_checkpointing and self.checkpointer:
            self.graph = graph_builder.compile(checkpointer=self.checkpointer)
            logger.debug("LangGraph compiled successfully with checkpointing")
        else:
            self.graph = graph_builder.compile()
            if not self.enable_checkpointing:
                logger.debug("LangGraph compiled without checkpointing (disabled in config)")
            else:
                logger.debug("LangGraph compiled without checkpointing (no checkpointer provided)")

    async def _store_message(self, conversation_id: str, message: Message) -> None:
        """Store a message in chat history persistence.

        Args:
            conversation_id: The conversation identifier.
            message: The message to store.
        """
        if self.chat_history_persistence:
            try:
                await self.chat_history_persistence.save_message(conversation_id, message)
                logger.debug(f"Message stored in chat history for conversation {conversation_id}")
            except Exception as e:
                logger.error(f"Failed to store message in chat history: {e}")

    async def ainvoke(self, new_message: Message, config: Config, **kwargs) -> Message:
        """Process a message asynchronously and return the complete response.

        Args:
            new_message: The user's message to process.
            config: Configuration containing conversation context.

        Returns:
            The agent's response message.

        Raises:
            ValueError: If the agent graph has not been built.
        """
        logger.info(f"Async invoking agent with message: {new_message.content[:100]}...")

        if self.graph is None:
            raise ValueError("The agent graph has not been built.")

        # Check if this is a new conversation and store system prompt if needed
        if self.chat_history_persistence and self.system_prompt:
            conversation = await self.chat_history_persistence.load_conversation(config.conversation_id)
            if not conversation.messages:
                # New conversation - store system prompt
                system_message = Message(role=Role.SYSTEM, content=self.system_prompt, timestamp=Helper.generate_timestamp())
                await self._store_message(config.conversation_id, system_message)
                logger.debug(f"Stored system prompt for new conversation {config.conversation_id}")

        # Build messages with system prompt
        messages = []
        if self.system_prompt:
            messages.append(Message(role=Role.SYSTEM, content=self.system_prompt, timestamp=Helper.generate_timestamp()))
        messages.append(new_message)

        lc_messages = to_lc_messages(messages)
        lc_config = to_lc_config(config)

        # Invoke graph asynchronously
        logger.debug("Async invoking LangGraph...")
        result = await self.graph.ainvoke({"messages": lc_messages}, config=lc_config)

        # Extract response
        ai_message = result["messages"][-1]
        text = content_to_text(getattr(ai_message, "content", ai_message))
        logger.info(f"Agent response generated: {len(text)} characters")

        response_message = to_domain_message(kind="assistant", content=text)

        # Store messages asynchronously
        await self._store_message(config.conversation_id, new_message)
        await self._store_message(config.conversation_id, response_message)

        return response_message

    async def astream(self, new_message: Message, config: Config, **kwargs) -> AsyncGenerator[ChunkDelta, None]:
        """Process a message and stream the response asynchronously.

        Args:
            new_message: The user's message to process.
            config: Configuration containing conversation context.

        Yields:
            ChunkDelta objects containing response fragments.

        Raises:
            ValueError: If the agent graph has not been built.
        """
        logger.info(f"Async streaming agent response for message: {new_message.content[:100]}...")

        if self.graph is None:
            raise ValueError("The agent graph has not been built.")

        # Check if this is a new conversation and store system prompt if needed
        if self.chat_history_persistence and self.system_prompt:
            conversation = await self.chat_history_persistence.load_conversation(config.conversation_id)
            if not conversation.messages:
                # New conversation - store system prompt
                system_message = Message(role=Role.SYSTEM, content=self.system_prompt, timestamp=Helper.generate_timestamp())
                await self._store_message(config.conversation_id, system_message)
                logger.debug(f"Stored system prompt for new conversation {config.conversation_id}")

        # Build messages with system prompt
        messages = []
        if self.system_prompt:
            messages.append(Message(role=Role.SYSTEM, content=self.system_prompt, timestamp=Helper.generate_timestamp()))
        messages.append(new_message)

        lc_messages = to_lc_messages(messages)
        lc_config = to_lc_config(config)

        # Stream graph asynchronously
        logger.debug("Starting async LangGraph stream...")
        chunk_count = 0
        full_response = []

        async for event in self.graph.astream({"messages": lc_messages}, config=lc_config, stream_mode="values"):
            # Extract the last message from the event
            if "messages" in event and len(event["messages"]) > 0:
                last_msg = event["messages"][-1]
                if isinstance(last_msg, AIMessage):
                    text = content_to_text(last_msg.content)
                    full_response.append(text)
                    chunk_count += 1
                    yield chunk_to_domain(text)

        logger.debug(f"Async stream complete: {chunk_count} chunks generated")

        # Store messages after streaming completes
        if full_response:
            response_text = "".join(full_response) if len(full_response) > 1 else full_response[0]
            response_message = to_domain_message(kind="assistant", content=response_text)

            await self._store_message(config.conversation_id, new_message)
            await self._store_message(config.conversation_id, response_message)
