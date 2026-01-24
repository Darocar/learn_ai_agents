"""Basic answer agent implementation using LangChain.

This module implements a simple question-answering agent using the LangChain framework.
"""

from collections.abc import AsyncGenerator

from learn_ai_agents.application.outbound_ports.agents.llm_model import ChatModelProvider
from learn_ai_agents.domain.models.agents.config import Config
from learn_ai_agents.domain.models.agents.messages import ChunkDelta, Message, Role
from learn_ai_agents.infrastructure.helpers.generators import Helper
from learn_ai_agents.infrastructure.outbound.agents.langchain_fwk.helpers import (
    chunk_to_domain,
    content_to_text,
    to_domain_message,
    to_lc_config,
    to_lc_messages,
)
from learn_ai_agents.logging import get_logger

from .._base import BaseLangChainAgent
from .prompts import BASIC_ANSWER_PROMPT_TEMPLATE

logger = get_logger(__name__)


class BasicAnswerLangChainAgent(BaseLangChainAgent):
    """A basic question-answering agent using LangChain.

    This agent provides simple, direct answers to user questions using
    a language model. It applies a system prompt and processes messages
    through a LangChain chat model.

    Attributes:
        system_prompt: The system-level instruction for the agent.
        chain: The LangChain runnable (chat model).
    """

    def __init__(
        self,
        *,
        config: dict,
        llms: dict[str, ChatModelProvider],
    ) -> None:
        """Initialize the basic answer agent.

        Args:
            config: Configuration dictionary for the agent.
            llms: Dictionary of LLM providers keyed by alias.
        """
        super().__init__(config=config, llms=llms)

    def _load_config(self, config: dict) -> None:
        """Load agent-specific configuration.

        Args:
            config: Configuration dictionary containing agent settings.
        """
        self.system_prompt: str = BASIC_ANSWER_PROMPT_TEMPLATE

    def _configure_nodes(self) -> None:
        """Configure agent nodes.

        This basic agent doesn't use graph nodes, so this is a no-op.
        """
        # Configure any specific nodes for the basic answer agent here
        pass

    def _build_graph(self) -> None:
        """Build the agent's processing chain.

        For this simple agent, we just use the default LLM directly.
        """
        self.chain = self.llms["default"].get_model()

    async def ainvoke(self, new_message: Message, config: Config, **kwargs) -> Message:
        """Process a message asynchronously and return the complete response.

        Args:
            new_message: The user's message to process.
            config: Configuration containing conversation context.

        Returns:
            The agent's response message.

        Raises:
            ValueError: If the agent chain has not been built.
        """
        logger.info(f"Async invoking agent with message: {new_message.content[:100]}...")

        lc_messages = to_lc_messages([new_message])
        lc_config = to_lc_config(config)
        if self.system_prompt:
            lc_messages.insert(
                0,
                to_lc_messages(
                    [Message(role=Role.SYSTEM, content=self.system_prompt, timestamp=Helper.generate_timestamp())]
                )[0],
            )

        if self.chain is None:
            raise ValueError("The agent chain has not been built.")

        logger.debug("Async calling LLM chain...")
        lc_reply = await self.chain.ainvoke(input=lc_messages, config=lc_config)

        text = content_to_text(getattr(lc_reply, "content", lc_reply))
        logger.info(f"Agent response generated: {len(text)} characters")
        return to_domain_message(kind="assistant", content=text)

    async def astream(self, new_message: Message, config: Config) -> AsyncGenerator[ChunkDelta, None]:  # type: ignore
        """Process a message and stream the response asynchronously in real-time chunks.

        Args:
            new_message: The user's message to process.
            config: Configuration containing conversation context.

        Yields:
            ChunkDelta objects containing response fragments.

        Raises:
            ValueError: If the agent chain has not been built.
        """
        logger.info(f"Async streaming agent response for message: {new_message.content[:100]}...")

        lc_messages = to_lc_messages([new_message])
        lc_config = to_lc_config(config)

        if self.system_prompt:
            lc_messages.insert(
                0,
                to_lc_messages(
                    [Message(role=Role.SYSTEM, content=self.system_prompt, timestamp=Helper.generate_timestamp())]
                )[0],
            )

        if self.chain is None:
            raise ValueError("The agent chain has not been built.")

        logger.debug("Starting async LLM stream...")
        chunk_count = 0
        async for chunk in self.chain.astream(input=lc_messages, config=lc_config):
            raw = getattr(chunk, "content", chunk)
            text = content_to_text(raw)
            chunk_count += 1
            yield chunk_to_domain(text)

        logger.debug(f"Async stream complete: {chunk_count} chunks generated")
