"""Character chat agent implementation using LangGraph and vector search.

This module implements a character chat agent that uses RAG (Retrieval-Augmented
Generation) to chat as a BG3 character using information from a vector database.
Uses LangChain v1.0 runtime context injection for dynamic configuration.
"""

import json
from collections.abc import AsyncGenerator
from typing import Any, Dict, List, cast

from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, ModelRequest
from learn_ai_agents.application.outbound_ports.agents.tracing import AgentTracingPort
from ..middlewares.persist_messages import PersistMessagesMiddleware
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langgraph.checkpoint.base import BaseCheckpointSaver

from learn_ai_agents.application.outbound_ports.agents.chat_history import ChatHistoryStorePort
from learn_ai_agents.application.outbound_ports.agents.llm_model import ChatModelProvider
from learn_ai_agents.application.outbound_ports.agents.tools import ToolPort
from learn_ai_agents.domain.models.agents.config import Config
from learn_ai_agents.domain.models.agents.messages import ChunkDelta, Message
from learn_ai_agents.infrastructure.outbound.agents.langchain_fwk.helpers import (
    chunk_to_domain,
    content_to_text,
    extract_tool_calls,
    safe_jsonable,
    to_domain_message,
    to_lc_config,
    to_lc_messages,
    to_lc_state,
)
from learn_ai_agents.infrastructure.outbound.tools.langchain_fwk.vector_search import (
    VectorSearchContext,
)
from learn_ai_agents.logging import get_logger

from .._base import BaseLangChainAgent
from .prompts import CHARACTER_CHAT_SYSTEM_PROMPT_TEMPLATE

logger = get_logger(__name__)


class TracingLangchainAgent(BaseLangChainAgent):
    """A character chat agent with vector search capabilities.

    This agent uses LangGraph's StateGraph to manage conversation flow and
    a vector search tool to retrieve character-specific information from
    a Qdrant vector database. The agent maintains character persona and
    uses RAG to provide accurate, in-character responses.

    Uses LangChain v1.0 runtime context injection to pass document_id
    dynamically to the vector search tool at invocation time.

    Attributes:
        system_prompt_template: Template for the character-specific system prompt.
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
        tracer: AgentTracingPort | None = None,
    ) -> None:
        """Initialize the character chat agent.

        Args:
            config: Configuration dictionary for the agent.
            llms: Dictionary of LLM providers keyed by alias.
            tools: Dictionary of tool adapters keyed by name (must include vector_search).
            checkpointer: Optional checkpointer for conversation state persistence.
            chat_history_persistence: Optional chat history store for message persistence.
        """
        # Store the checkpointer before calling super().__init__
        self.checkpointer = checkpointer

        # Validate that vector_search tool is present
        if "vector_search" not in tools:
            raise ValueError("Character chat agent requires a 'vector_search' tool")

        super().__init__(
            config=config,
            llms=llms,
            chat_history_persistence=chat_history_persistence,
            tools=tools,
            tracer=tracer,
        )

    # ============================================================================
    # Abstract methods implementation (configuration & setup)
    # ============================================================================

    def _load_config(self, config: dict) -> None:
        """Load agent-specific configuration.

        Args:
            config: Configuration dictionary containing agent settings.
        """
        self.system_prompt_template: str = CHARACTER_CHAT_SYSTEM_PROMPT_TEMPLATE
        self.database_name = config.get("database_name", "learn_ai_agents")
        self.checkpoints_collection = config.get("checkpoints_collection", "checkpoints")
        self.enable_checkpointing = config.get("enable_checkpointing", True)
        self.enable_tracing = config.get("enable_tracing", False)

    def _configure_nodes(self) -> None:
        """Configure LLM and tools for create_agent.

        We keep this method name to satisfy BaseLangChainAgent,
        but it no longer builds explicit graph nodes.
        """
        self.model = self.llms["default"].get_model()
        self.langchain_tools = list(self.tools_by_name.values()) if self.tools_by_name else []

    def _build_graph(self) -> None:
        """Build the create_agent graph and store it in self.chain.

        Uses:
        - VectorSearchContext as context_schema (document_id + character info)
        - dynamic_prompt middleware to generate the system prompt per character
        - optional LangGraph checkpointer for short-term memory
        """
        logger.debug("Building character chat agent with create_agent and context_schema...")

        @dynamic_prompt
        def character_prompt(request: ModelRequest) -> str:
            """Dynamic system prompt based on runtime context.

            Runs before each model call. Uses the same helper as ainvoke.
            """
            ctx = cast(VectorSearchContext, request.runtime.context)
            return self._build_character_system_prompt(ctx)

        agent_kwargs: Dict[str, Any] = {
            "name": "Tracing Agent",
            "model": self.model,
            "tools": self.langchain_tools,
            "context_schema": VectorSearchContext,
            "middleware": [character_prompt, PersistMessagesMiddleware(self.chat_history_persistence)],
        }

        # Reuse your optional checkpointer for short-term memory
        if getattr(self, "enable_checkpointing", False) and getattr(self, "checkpointer", None):
            agent_kwargs["checkpointer"] = self.checkpointer

        # create_agent returns a Runnable (backed by LangGraph under the hood)
        self.graph = create_agent(**agent_kwargs)
        logger.debug("Character chat agent created with create_agent")

    # ============================================================================
    # Private helper methods
    # ============================================================================

    def _build_character_system_prompt(self, ctx: VectorSearchContext) -> str:
        """Single source of truth for the character system prompt.

        Args:
            ctx: VectorSearchContext containing character_name and personality.

        Returns:
            Formatted system prompt string.
        """
        return CHARACTER_CHAT_SYSTEM_PROMPT_TEMPLATE.format(
            character_name=ctx.character_name,
            personality=ctx.personality,
        )

    # Message persistence moved to middleware; helpers removed from agent

    # System prompt storage is handled by middleware; removed from agent

    # Conversation persistence moved to middleware; removed from agent

    # ============================================================================
    # Public methods (AgentEngine protocol implementation)
    # ============================================================================

    async def ainvoke(
        self,
        new_message: Message,
        config: Config,
        **kwargs: Any,
    ) -> Message:
        """Process a message asynchronously.

        Args:
            new_message: The user's message to process.
            config: Configuration containing conversation context.
            **kwargs: Must include 'character_name', 'document_id', and 'personality'.

        Returns:
            The assistant's response message.

        Raises:
            ValueError: If the agent graph has not been built or required params missing.
        """
        if self.graph is None:
            raise ValueError("The agent has not been built.")

        character_name = kwargs.get("character_name")
        document_id = kwargs.get("document_id")
        personality = kwargs.get("personality")

        if not document_id:
            raise ValueError("document_id is required for character chat")
        if not character_name:
            raise ValueError("character_name is required for character chat")
        if not personality:
            raise ValueError("personality is required for character chat")

        logger.info(
            "Async invoking character chat agent as '%s': %s...",
            character_name,
            new_message.content[:100],
        )

        # Runtime context used by tools + dynamic system prompt
        context = VectorSearchContext(
            document_id=document_id,
            character_name=character_name,
            personality=personality,
            conversation_id=config.conversation_id,
        )

        # system prompt persistence is handled by middleware now

        # --- build LC state -------------------------------------------
        lc_messages = to_lc_messages([new_message])
        input_message_count = len(lc_messages)

        lc_state = to_lc_state(lc_messages)
        lc_config = to_lc_config(config)
        if self.enable_tracing and self.tracer is not None:
            lc_config["callbacks"] = [self.tracer.get_tracer(thread_id=config.conversation_id)]

        result_state = await self.graph.ainvoke(
            lc_state,
            config=lc_config,
            context=context,
        )

        # Extract tool calls
        tool_calls = extract_tool_calls(result_state["messages"], input_message_count)

        last_lc_msg = result_state["messages"][-1]
        text = content_to_text(getattr(last_lc_msg, "content", last_lc_msg))
        logger.info("Character response generated: %d characters", len(text))

        # Create response message with tool_calls in metadata
        response_message = to_domain_message(
            kind="assistant",
            content=text,
            metadata={"tool_calls": tool_calls} if tool_calls else None,
        )

        # message persistence handled by middleware; no-op here

        return response_message

    async def astream(
        self,
        new_message: Message,
        config: Config,
        **kwargs: Any,
    ) -> AsyncGenerator[ChunkDelta, None]:
        """Process a message and stream the response asynchronously.

        Args:
            new_message: The user's message to process.
            config: Configuration containing conversation context.
            **kwargs: Must include 'character_name', 'document_id', and 'personality'.

        Yields:
            ChunkDelta objects containing response fragments.

        Raises:
            ValueError: If the agent graph has not been built or required params missing.
        """
        if self.graph is None:
            raise ValueError("The agent graph has not been built.")

        character_name = kwargs.get("character_name")
        document_id = kwargs.get("document_id")
        personality = kwargs.get("personality")

        if not document_id:
            raise ValueError("document_id is required for character chat")
        if not character_name:
            raise ValueError("character_name is required for character chat")
        if not personality:
            raise ValueError("personality is required for character chat")

        logger.info(
            "Async streaming character chat agent as '%s': %s...",
            character_name,
            new_message.content[:100],
        )

        # Runtime context used by tools + dynamic system prompt
        context = VectorSearchContext(
            document_id=document_id,
            character_name=character_name,
            personality=personality,
            conversation_id=config.conversation_id,
        )

        # system prompt persistence is handled by middleware now

        # --- build LC state -------------------------------------------
        lc_messages = to_lc_messages([new_message])

        lc_state = to_lc_state(lc_messages)
        lc_config = to_lc_config(config)

        # --- stream with context --------------------------------------
        logger.debug(
            "Starting async character chat token-level stream with document_id=%s...",
            document_id,
        )
        chunk_count = 0

        if self.enable_tracing and self.tracer is not None:
            lc_config["callbacks"] = [self.tracer.get_tracer(thread_id=config.conversation_id)]

        # Use astream_events for token-level streaming
        async for event in self.graph.astream_events(
            lc_state,
            config=lc_config,
            context=context,
            version="v2",
        ):
            kind = event.get("event")
            if kind == "on_tool_start":
                tool_name = event.get("name")
                raw_input = event.get("data", {}).get("input")
                if isinstance(raw_input, dict) and "runtime" in raw_input:
                    raw_input = {k: v for k, v in raw_input.items() if k != "runtime"}
                tool_input_safe = safe_jsonable(raw_input)
                logger.debug(f"Tool started: {tool_name}")
                yield ChunkDelta(
                    kind="tool_start",
                    tool_name=str(tool_name) if tool_name else None,
                    tool_input=tool_input_safe,
                )
            elif kind == "on_tool_end":
                tool_name = event.get("name")
                raw_output = event.get("data", {}).get("output")
                tool_output_safe = safe_jsonable(raw_output)
                logger.debug(f"Tool ended: {tool_name}")
                yield ChunkDelta(
                    kind="tool_end",
                    tool_name=str(tool_name) if tool_name else None,
                    tool_output=tool_output_safe,
                )
            elif kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content"):
                    text = content_to_text(chunk.content)
                    if text:
                        chunk_count += 1
                        yield chunk_to_domain(text)

        logger.debug("Async stream complete: %d chunks generated", chunk_count)

        # conversation persistence handled by middleware; nothing to do here
