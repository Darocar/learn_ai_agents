"""Outbound port for AI agent engine."""

from collections.abc import Iterable
from typing import Protocol

from ...domain.models.config import Config
from ...domain.models.messages import ChunkDelta, Message


class AgentEngine(Protocol):
    """Protocol for AI agent engines."""

    def invoke(self, new_message: Message, config: Config) -> Message:
        """Process a message and return the agent's response."""
        ...

    def stream(self, new_message: Message, config: Config) -> Iterable[ChunkDelta]:
        """Process a message and stream the response in chunks."""
        ...
