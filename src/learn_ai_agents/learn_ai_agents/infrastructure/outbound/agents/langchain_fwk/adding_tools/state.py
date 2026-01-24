"""State definition for the adding memory agent.

This module defines the graph state used by the LangGraph-based adding memory agent.
"""

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class State(TypedDict):
    """Graph state definition for the adding memory agent.

    Attributes:
        messages: List of conversation messages with reducer for merging.
    """

    messages: Annotated[list[BaseMessage], add_messages]
