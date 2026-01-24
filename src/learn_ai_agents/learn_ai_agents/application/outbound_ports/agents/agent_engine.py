"""Outbound port for AI agent engine."""

from collections.abc import AsyncGenerator
from typing import Protocol

from learn_ai_agents.domain.models.agents.config import Config
from learn_ai_agents.domain.models.agents.messages import ChunkDelta, Message


class AgentEngine(Protocol):
    """Protocol for AI agent engines."""

    async def ainvoke(self, new_message: Message, config: Config, **kwargs) -> Message:
        """Process a message asynchronously and return the complete response."""
        ...

    async def astream(self, new_message: Message, config: Config, **kwargs) -> AsyncGenerator[ChunkDelta, None]:
        """Process a message and stream the response asynchronously in real-time chunks."""
        yield ChunkDelta()  # Makes this an async generator for type checking
        ...
