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
from learn_ai_agents.application.outbound_ports.agents.tools import ToolPort
from learn_ai_agents.domain.models.agents.config import Config
from learn_ai_agents.domain.models.agents.messages import ChunkDelta, Message, Role
from learn_ai_agents.infrastructure.helpers.generators import Helper
from learn_ai_agents.infrastructure.outbound.agents.langchain_fwk.helpers import (
    chunk_to_domain,
    content_to_text,
    lc_message_to_domain,
    to_domain_message,
    to_lc_config,
    to_lc_messages,
)
from learn_ai_agents.logging import get_logger

from .._base import BaseLangChainAgent
from .nodes import thinking_node, tool_node, should_continue
from .prompts import ADDING_TOOLS_PROMPT_TEMPLATE
from .state import State

logger = get_logger(__name__)


class AddingToolsLangchainAgent(BaseLangChainAgent):
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
        tools: dict[str, ToolPort],
        checkpointer: BaseCheckpointSaver | None = None,
        chat_history_persistence: ChatHistoryStorePort | None = None,
    ) -> None:
        """Initialize the adding tools agent.

        Args:
            config: Configuration dictionary for the agent.
            llms: Dictionary of LLM providers keyed by alias.
            tools: Dictionary of tool adapters keyed by name.
            checkpointer: Optional checkpointer for conversation state persistence.
            chat_history_persistence: Optional chat history store for message persistence.
            **kwargs: Additional keyword arguments (e.g., databases for backward compatibility).
        """
        # Store the checkpointer if provided
        self.checkpointer = checkpointer

        super().__init__(config=config, llms=llms, chat_history_persistence=chat_history_persistence, tools=tools)

    def _load_config(self, config: dict) -> None:
        """Load agent-specific configuration.

        Args:
            config: Configuration dictionary containing agent settings.
        """
        self.system_prompt: str = ADDING_TOOLS_PROMPT_TEMPLATE
        # These config values are now optional since checkpointer is injected
        self.database_name = config.get("database_name", "learn_ai_agents")
        self.checkpoints_collection = config.get("checkpoints_collection", "checkpoints")
        self.enable_checkpointing = config.get("enable_checkpointing", True)

    def _configure_nodes(self) -> None:
        """Configure agent nodes for the LangGraph.

        Sets up the conversation node that processes messages using the LLM.
        """
        self.thinking_node = partial(
            thinking_node,
            llms=self.llms,
            tools=list(self.tools_by_name.values()) if self.tools_by_name else None,
        )
        self.tool_node = partial(
            tool_node,
            tools_by_name=self.tools_by_name,
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
        graph_builder.add_node("thinking_node", self.thinking_node)
        graph_builder.add_node("tool_node", self.tool_node)

        # Define edges: START -> thinking_node -> conditional
        graph_builder.add_edge(START, "thinking_node")
        graph_builder.add_conditional_edges(
            "thinking_node",
            should_continue,
            {
                "tool_node": "tool_node",
                "__END__": END,
            },
        )
        graph_builder.add_edge("tool_node", "thinking_node")

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

        # Store the count of input messages
        input_message_count = len(lc_messages)

        # Invoke graph asynchronously
        logger.debug("Async invoking LangGraph...")
        result = await self.graph.ainvoke({"messages": lc_messages}, config=lc_config)

        # Get all result messages
        result_messages = result["messages"]
        result_message_count = len(result_messages)

        # Calculate the difference to identify new messages (tool calls, tool results, etc.)
        new_message_count = result_message_count - input_message_count
        logger.info(
            f"Graph generated {new_message_count} new messages (input: {input_message_count}, output: {result_message_count})"
        )

        # Extract the final assistant response
        ai_message = result_messages[-1]
        text = content_to_text(getattr(ai_message, "content", ai_message))
        logger.info(f"Agent response generated: {len(text)} characters")

        response_message = to_domain_message(kind="assistant", content=text)

        # Store the user message first
        await self._store_message(config.conversation_id, new_message)

        # Store intermediate messages (tool calls and tool results) if any
        if new_message_count > 1:
            # The new messages are from input_message_count to result_message_count-1
            # (excluding the final assistant message which we'll store separately)
            intermediate_messages = result_messages[input_message_count:-1]
            logger.info(f"Storing {len(intermediate_messages)} intermediate messages (tool interactions)")

            for lc_msg in intermediate_messages:
                try:
                    domain_msg = lc_message_to_domain(lc_msg)
                    await self._store_message(config.conversation_id, domain_msg)
                    logger.debug(f"Stored intermediate message: {domain_msg.role}")
                except Exception as e:
                    logger.error(f"Failed to convert/store intermediate message: {e}")

        # Store the final assistant response
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

        # Store the count of input messages
        input_message_count = len(lc_messages)

        # Stream graph asynchronously
        logger.debug("Starting async LangGraph stream...")
        chunk_count = 0
        all_result_messages = []
        final_ai_message_text = None

        async for event in self.graph.astream({"messages": lc_messages}, config=lc_config, stream_mode="values"):
            # Extract all messages from the event
            if "messages" in event and len(event["messages"]) > 0:
                all_result_messages = event["messages"]
                last_msg = event["messages"][-1]

                # Only yield chunks from AIMessage (final assistant response)
                if isinstance(last_msg, AIMessage):
                    text = content_to_text(last_msg.content)
                    final_ai_message_text = text
                    chunk_count += 1
                    yield chunk_to_domain(text)

        logger.debug(f"Async stream complete: {chunk_count} chunks generated")

        # Calculate message difference
        result_message_count = len(all_result_messages)
        new_message_count = result_message_count - input_message_count
        logger.info(
            f"Graph generated {new_message_count} new messages (input: {input_message_count}, output: {result_message_count})"
        )

        # Store the user message first
        await self._store_message(config.conversation_id, new_message)

        # Store intermediate messages (tool calls and tool results) if any
        if new_message_count > 1:
            # The new messages are from input_message_count to result_message_count-1
            # (excluding the final assistant message which we'll store separately)
            intermediate_messages = all_result_messages[input_message_count:-1]
            logger.info(f"Storing {len(intermediate_messages)} intermediate messages (tool interactions)")

            for lc_msg in intermediate_messages:
                try:
                    domain_msg = lc_message_to_domain(lc_msg)
                    await self._store_message(config.conversation_id, domain_msg)
                    logger.debug(f"Stored intermediate message: {domain_msg.role}")
                except Exception as e:
                    logger.error(f"Failed to convert/store intermediate message: {e}")

        # Store the final assistant response
        if final_ai_message_text:
            response_message = to_domain_message(kind="assistant", content=final_ai_message_text)
            await self._store_message(config.conversation_id, response_message)
