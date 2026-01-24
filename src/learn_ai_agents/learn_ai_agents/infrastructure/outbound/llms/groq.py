"""Groq LLM adapter using LangChain."""

from typing import Any

from langchain_groq import ChatGroq

from learn_ai_agents.application.outbound_ports.llm_model import ChatModelProvider


class GroqChatModelProvider(ChatModelProvider):
    """Groq implementation of ChatModelProvider using LangChain."""

    def __init__(self, api_key: str, model_name: str = "llama-3.3-70b-versatile", temperature: float = 0.7):
        """Initialize Groq provider.

        Args:
            api_key: Groq API key
            model_name: Model identifier (default: llama-3.3-70b-versatile)
            temperature: Sampling temperature (0.0-1.0)
        """
        self._api_key = api_key
        self._model_name = model_name
        self._temperature = temperature

    def get_model(self) -> Any:
        """Get configured ChatGroq instance."""
        return ChatGroq(
            api_key=self._api_key,
            model=self._model_name,
            temperature=self._temperature,
        )
