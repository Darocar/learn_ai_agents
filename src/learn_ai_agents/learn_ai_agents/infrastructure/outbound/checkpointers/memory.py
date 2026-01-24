"""In-memory checkpointer adapter for LangGraph.

This module provides an in-memory implementation of checkpointing for LangGraph agents.
Useful for development and testing.
"""

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from learn_ai_agents.logging import get_logger

from . import BaseLangChainCheckpointerAdapter

logger = get_logger(__name__)


class MemoryCheckpointerAdapter(BaseLangChainCheckpointerAdapter):
    """In-memory checkpointer adapter for LangGraph agents.

    This adapter wraps the MemorySaver to provide checkpointing in memory.
    Useful for development and testing where persistence is not required.
    """

    @staticmethod
    def build(**kwargs) -> BaseCheckpointSaver:
        """Factory method to build the in-memory checkpointer.

        Args:
            **kwargs: Configuration parameters (none required for memory checkpointer).

        Returns:
            BaseCheckpointSaver: MemorySaver instance ready to use.
        """
        logger.info("Creating in-memory checkpointer")
        checkpointer = MemorySaver()
        logger.debug("In-memory checkpointer created successfully")
        return checkpointer
