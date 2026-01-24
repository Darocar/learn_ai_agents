"""Checkpointer adapters for LangGraph agents.

This module provides a base class and implementations for different checkpointing
strategies in LangGraph agents.
"""

from abc import ABC, abstractmethod

from langgraph.checkpoint.base import BaseCheckpointSaver


class BaseLangChainCheckpointerAdapter(ABC):
    """Base class for LangGraph checkpointer adapters.

    All checkpointer adapters must inherit from this class and implement
    the build method that returns a BaseCheckpointSaver instance.
    """

    @staticmethod
    @abstractmethod
    def build(**kwargs) -> BaseCheckpointSaver:
        """Factory method to build a checkpointer.

        Args:
            **kwargs: Configuration parameters for the checkpointer.

        Returns:
            BaseCheckpointSaver: A LangGraph checkpointer instance.
        """
        ...
