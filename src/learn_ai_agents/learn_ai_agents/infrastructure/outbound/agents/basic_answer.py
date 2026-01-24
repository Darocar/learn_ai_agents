"""LangChain-based agent engine for basic Q&A."""

from collections.abc import Iterable

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from learn_ai_agents.application.outbound_ports.agent_engine import AgentEngine
from learn_ai_agents.application.outbound_ports.llm_model import ChatModelProvider
from learn_ai_agents.domain.models.config import Config
from learn_ai_agents.domain.models.messages import ChunkDelta, Message, Role


class LangChainBasicAnswerAgent(AgentEngine):
    """LangChain implementation of AgentEngine for basic Q&A."""

    def __init__(self, chat_model_provider: ChatModelProvider):
        """Initialize with a chat model provider.

        Args:
            chat_model_provider: Provider that supplies the LLM instance
        """
        self._chat_model_provider = chat_model_provider

    def invoke(self, new_message: Message, config: Config) -> Message:
        """Process message and return complete response."""
        # Get LLM instance
        llm = self._chat_model_provider.get_model()

        # Convert domain Message to LangChain format
        messages = self._convert_to_langchain_messages([new_message])

        # Invoke LLM
        response: AIMessage = llm.invoke(messages)

        # Convert back to domain Message
        return Message(role=Role.ASSISTANT, content=response.content)

    def stream(self, new_message: Message, config: Config) -> Iterable[ChunkDelta]:
        """Process message and stream response in chunks."""
        # Get LLM instance
        llm = self._chat_model_provider.get_model()

        # Convert domain Message to LangChain format
        messages = self._convert_to_langchain_messages([new_message])

        # Stream from LLM
        for chunk in llm.stream(messages):
            if chunk.content:
                yield ChunkDelta(text=chunk.content)

    def _convert_to_langchain_messages(self, domain_messages: list[Message]) -> list:
        """Convert domain Messages to LangChain message format."""
        langchain_messages = []
        for msg in domain_messages:
            if msg.role == Role.SYSTEM:
                langchain_messages.append(SystemMessage(content=msg.content))
            elif msg.role == Role.USER:
                langchain_messages.append(HumanMessage(content=msg.content))
            elif msg.role == Role.ASSISTANT:
                langchain_messages.append(AIMessage(content=msg.content))
        return langchain_messages
