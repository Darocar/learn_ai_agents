"""Outbound port for LLM provider access."""

from typing import Any, Protocol


class ChatModelProvider(Protocol):
    """Protocol for providing chat-based language models."""

    def get_model(self) -> Any:
        """Get a configured chat model instance."""
        ...
