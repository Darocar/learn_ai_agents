"""Node functions for the adding memory agent.

This module contains the processing nodes used in the LangGraph workflow.
"""

from learn_ai_agents.application.outbound_ports.agents.llm_model import ChatModelProvider
from learn_ai_agents.infrastructure.outbound.agents.langchain_fwk.helpers import content_to_text
from learn_ai_agents.logging import get_logger

from .state import State

logger = get_logger(__name__)


def chatbot_node(
    state: State,
    llms: dict[str, ChatModelProvider],
) -> dict:
    """Process messages through the LLM.

    Args:
        state: Current graph state with messages.
        llms: Dictionary of LLM providers keyed by alias.
        chat_history_persistence: Optional chat history store for message persistence.

    Returns:
        Dictionary with the AI response message.
    """
    logger.debug(f"Chatbot node processing {len(state['messages'])} messages")
    llm = llms["default"].get_model()
    response = llm.invoke(state["messages"])
    logger.debug(f"LLM response: {content_to_text(response.content)[:100]}...")
    return {"messages": [response]}
