"""Base class for LangChain-based agents.

This module provides the abstract base class for all LangChain agent implementations.
"""

from abc import abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

from langchain_core.runnables import Runnable

from learn_ai_agents.application.outbound_ports.agents.agent_engine import AgentEngine
from learn_ai_agents.application.outbound_ports.agents.llm_model import ChatModelProvider
from learn_ai_agents.domain.models.agents.config import Config
from learn_ai_agents.domain.models.agents.messages import ChunkDelta, Message
from learn_ai_agents.logging import get_logger

logger = get_logger(__name__)


class BaseLangChainAgent(AgentEngine):
    """Abstract base class for LangChain-based agent implementations.

    This class provides a template for creating agents using the LangChain
    framework. It implements the AgentEngine protocol and defines the
    lifecycle methods that concrete agents must implement.

    Attributes:
        chain: Optional LangChain runnable chain for simple agents.
        llms: Dictionary of LLM providers keyed by alias.
    """

    chain: Runnable | None

    def __init__(
        self,
        *,
        config: dict,
        llms: dict[str, ChatModelProvider],
    ) -> None:
        """Initialize the agent with configuration and LLM providers.

        Args:
            config: Configuration dictionary for the agent.
            llms: Dictionary of LLM providers keyed by alias (e.g., 'default').
        """
        logger.debug(f"Initializing {self.__class__.__name__}")
        self.llms = llms
        self._load_config(config)
        self._configure_nodes()
        self._build_graph()
        logger.debug(f"{self.__class__.__name__} initialized successfully")

    @abstractmethod
    def _load_config(self, config: dict) -> None:
        """Load agent-specific configuration.

        Args:
            config: Configuration dictionary to load.
        """
        ...

    @abstractmethod
    def _configure_nodes(self) -> None:
        """Configure agent nodes (for LangGraph-based agents).

        Override this to set up graph nodes, edges, and state.
        """
        ...


    @abstractmethod
    def _build_graph(self) -> None:
        """Build the agent's processing graph or chain.

        Override this to construct the LangChain chain or LangGraph.
        """
        ...

    @abstractmethod
    async def ainvoke(self, new_message: Message, config: Config, **kwargs: Any) -> Message:
        """Process a message asynchronously.

        Args:
            new_message: The user's message to process.
            config: Configuration for the invocation.

        Returns:
            The agent's response message.
        """
        ...

    @abstractmethod
    async def astream(self, new_message: Message, config: Config, **kwargs: Any) -> AsyncGenerator[ChunkDelta, None]:
        """Process a message with async streaming response.

        Args:
            new_message: The user's message to process.
            config: Configuration for the stream.

        Yields:
            Response chunks as ChunkDelta objects.
        """
        yield ChunkDelta()  # Makes this an async generator for type checking
