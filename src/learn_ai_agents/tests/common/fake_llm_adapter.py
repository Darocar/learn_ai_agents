"""Fake LLM adapter for testing.

This module provides in-memory fake implementations of LLM providers.
Returns deterministic responses without making external API calls.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Self, Union, Iterator, Deque
from collections import deque

import groq

from langchain_core.messages import AIMessage
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.language_models import BaseChatModel


class ScriptedIterator(Iterator[AIMessage]):
    """Iterator that can yield AIMessage objects or raise scripted exceptions.

    This allows simulating Groq API errors (like APIConnectionError or
    AuthenticationError) at specific points in the conversation flow.
    """

    def __init__(self, steps: list[Union[AIMessage, BaseException]]):
        """Initialize with a list of steps (messages or exceptions).

        Args:
            steps: List of AIMessage objects or BaseException instances to yield/raise.
        """
        self._steps: Deque[Union[AIMessage, BaseException]] = deque(steps)

    def __iter__(self) -> "ScriptedIterator":
        """Return iterator instance."""
        return self

    def __next__(self) -> AIMessage:
        """Return next message or raise scripted exception.

        Returns:
            Next AIMessage in the sequence.

        Raises:
            BaseException: If the next step is an exception.
            AssertionError: If script is exhausted with no more steps.
        """
        if not self._steps:
            raise AssertionError("Fake LLM script exhausted (no more steps).")

        step = self._steps.popleft()
        if isinstance(step, BaseException):
            raise step
        return step

    def __repr__(self) -> str:
        """Return deterministic representation without memory address.

        Returns:
            String representation of the iterator.
        """
        return f"ScriptedIterator(steps={len(self._steps)} remaining)"


def _groq_exc_from_spec(spec: dict[str, Any]) -> BaseException:
    """Build a Groq exception from JSON specification.

    Args:
        spec: Dictionary with 'type', 'message', and optional 'status_code'.

    Returns:
        Groq exception instance (APIConnectionError, AuthenticationError, etc.).
    """
    import httpx

    exc_type = spec.get("type")
    message = spec.get("message", "")
    status_code = spec.get("status_code", 500)

    # Create mock httpx objects needed by Groq exceptions
    if exc_type == "APIConnectionError":
        # APIConnectionError needs: message (keyword), request (keyword, required)
        mock_request = httpx.Request(
            "POST", "https://api.groq.com/openai/v1/chat/completions"
        )
        return groq.APIConnectionError(message=message, request=mock_request)

    elif exc_type == "AuthenticationError":
        # AuthenticationError needs: message (positional), response (keyword, required), body (keyword, required)
        mock_request = httpx.Request(
            "POST", "https://api.groq.com/openai/v1/chat/completions"
        )
        mock_response = httpx.Response(status_code=status_code, request=mock_request)
        return groq.AuthenticationError(message, response=mock_response, body=None)

    else:
        # Fallback for unknown types
        return RuntimeError(message)


class FakeChatModel(GenericFakeChatModel):
    """Custom fake chat model that extends GenericFakeChatModel.

    Provides additional functionality for testing, including support for
    tool binding and custom response handling.
    """

    def bind_tools(self, tools: Any, **kwargs) -> Self:
        """Bind tools to the model (no-op for fake model).

        Args:
            tools: Tools to bind (ignored).
            **kwargs: Additional arguments (ignored).

        Returns:
            Self for method chaining.
        """
        return self

    def __repr__(self) -> str:
        """Return deterministic representation without internal state.

        Returns:
            String representation of the fake chat model.
        """
        return "FakeChatModel()"

    def __str__(self) -> str:
        """Return deterministic string representation without internal state.

        Returns:
            String representation of the fake chat model.
        """
        return "FakeChatModel()"


class FakeChatModelProvider:
    """Fake ChatModelProvider adapter for testing.

    Replaces LangchainGroqChatModelAdapter and similar LLM providers.
    Returns a fake chat model that doesn't make API calls.

    This adapter can be used as a drop-in replacement in the bootstrap
    container, allowing real use cases and agents to work with fake LLMs.

    Supports simulating Groq API errors via JSON specifications.
    """

    def __init__(self, file_path: Optional[Union[str, Path]] = None, **kwargs):
        """Initialize fake chat model provider.

        Args:
            file_path: Optional path to JSON file with responses and/or errors.
            **kwargs: Additional arguments (ignored).
        """
        self._fake_model = FakeChatModel(
            messages=ScriptedIterator([AIMessage(content="")])
        )
        if file_path is not None:
            self._load_from_file(file_path)

    def get_model(self) -> BaseChatModel:
        """Get the fake chat model.

        Real agents and use cases call this method and get a working
        fake model that returns deterministic responses.

        Returns:
            FakeChatModel instance that returns deterministic responses.
        """
        return self._fake_model

    def _load_from_file(self, file_path: Union[str, Path]) -> None:
        """Load responses from a JSON file.

        Supports both regular AIMessage objects and error specifications.
        Error specs should have the format: {"__error__": {"type": "...", "message": "..."}}.

        Args:
            file_path: Path to JSON file with responses and/or errors.
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(
                f"LLM response file not found: {file_path}\n"
                f"Make sure the path is correct and uses ${{TEST_DIR}} token if relative to test directory."
            )

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        steps: list[Union[AIMessage, BaseException]] = []

        for item in data:
            # Parse error steps
            if "__error__" in item:
                steps.append(_groq_exc_from_spec(item["__error__"]))
            else:
                steps.append(AIMessage(**item))

        # Set ScriptedIterator with steps
        self._fake_model.messages = ScriptedIterator(steps)
