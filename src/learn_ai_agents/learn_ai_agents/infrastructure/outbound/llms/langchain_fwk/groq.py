"""Groq LLM adapter for LangChain.

This module provides an adapter for using Groq's language models through LangChain.
"""

# src/learn_ai_agents/infrastructure/outbound/llms/langchain_groq.py
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq

from learn_ai_agents.application.outbound_ports.agents.llm_model import ChatModelProvider
from learn_ai_agents.logging import get_logger

logger = get_logger(__name__)


class LangchainGroqChatModelAdapter(ChatModelProvider):
    """Outbound adapter for Groq chat models via LangChain.

    This adapter implements the ChatModelProvider protocol to provide
    access to Groq's language models through the LangChain framework.

    Attributes:
        _model: The underlying LangChain ChatGroq model instance.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize the Groq adapter with configuration.

        Args:
            config: Configuration dictionary containing:
                - temperature: Sampling temperature for generation.
                - api_key: Groq API key for authentication.
        """
        logger.info("Initializing Groq LLM adapter")
        logger.debug(f"Model: llama-3.3-70b-versatile, Temperature: {config.get('temperature', 0.1)}")

        self._model = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=config.get("temperature", 0.1),
            api_key=config["api_key"],
        )

        logger.info("Groq LLM adapter initialized successfully")

    def get_model(self) -> BaseChatModel:
        """Retrieve the configured Groq chat model.

        Returns:
            The LangChain ChatGroq model instance.
        """
        return self._model
