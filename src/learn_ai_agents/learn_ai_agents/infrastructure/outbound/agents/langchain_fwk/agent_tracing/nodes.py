"""Node functions for the character chat agent.

This module contains the processing nodes used in the LangGraph workflow.
"""

from datetime import datetime
from typing import Dict, List, Literal, Optional

from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool

from learn_ai_agents.application.outbound_ports.agents.llm_model import ChatModelProvider
from learn_ai_agents.infrastructure.outbound.agents.langchain_fwk.helpers import content_to_text
from learn_ai_agents.infrastructure.helpers.generators import Helper
from learn_ai_agents.logging import get_logger

from .state import State

logger = get_logger(__name__)


def thinking_node(
    state: State,
    llms: Dict[str, ChatModelProvider],
    tools: Optional[List[BaseTool]],
) -> dict:
    """Process messages through the LLM with character context.

    Args:
        state: Current graph state with messages.
        llms: Dictionary of LLM providers keyed by alias.
        tools: List of available tools (including vector search).

    Returns:
        Dictionary with the AI response message.
    """
    logger.debug(f"Character chat thinking node processing {len(state['messages'])} messages")
    llm = llms["default"].get_model()
    llm = llm.bind_tools(tools) if tools else llm
    response = llm.invoke(state["messages"])

    # Add timestamp to response metadata
    if not hasattr(response, "additional_kwargs") or response.additional_kwargs is None:
        response.additional_kwargs = {}
    response.additional_kwargs["ts"] = Helper.generate_timestamp()

    logger.debug(f"LLM response: {content_to_text(response.content)[:100]}...")
    return {"messages": [response]}


def tool_node(
    state: State,
    tools_by_name: Dict[str, BaseTool],
) -> dict:
    """Execute tool calls (primarily vector search).

    Args:
        state: Current graph state with messages.
        tools_by_name: Dictionary of tools keyed by name.

    Returns:
        Dictionary with tool response messages.
    """
    result = []
    tool_calls = getattr(state["messages"][-1], "tool_calls", [])

    logger.debug(f"Executing {len(tool_calls)} tool calls")

    for tool_call in tool_calls:
        tool = tools_by_name[tool_call["name"]]
        logger.debug(f"Invoking tool: {tool_call['name']}")
        observation = tool.invoke(tool_call["args"])
        message = ToolMessage(
            content=observation,
            tool_call_id=tool_call["id"],
            additional_kwargs={"ts": Helper.generate_timestamp()},
        )
        result.append(message)

    return {"messages": result}


def should_continue(state: State) -> Literal["tool_node", "__END__"]:
    """Decide whether to continue with tool execution or end.

    Args:
        state: Current graph state with messages.

    Returns:
        Next node to execute or end signal.
    """
    messages = state["messages"]
    last_message = messages[-1]

    # If the LLM makes a tool call, execute the tool
    if getattr(last_message, "tool_calls", []):
        logger.debug("LLM requested tool calls, routing to tool_node")
        return "tool_node"

    # Otherwise, we're done (reply to user)
    logger.debug("No tool calls, ending conversation turn")
    return "__END__"
