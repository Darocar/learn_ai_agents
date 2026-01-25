"""State definition for the character chat agent.

This module defines the graph state used by the LangGraph-based character chat agent.
"""

from typing import Annotated, TypedDict
from dataclasses import dataclass

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class State(TypedDict):
    """Graph state definition for the character chat agent.

    Attributes:
        messages: List of conversation messages with reducer for merging.
    """

    messages: Annotated[list[BaseMessage], add_messages]


# infrastructure/outbound/tools/langchain_fwk/vector_search.py


@dataclass
class VectorSearchContext:
    """
    Runtime context shared by tools and middleware.

    This lives in the LangGraph runtime (LangChain v1 agent),
    not in your domain layer.

    Fields:
        document_id: Qdrant collection / document identifier.
        character_name: Name of the BG3 character.
        personality: Character personality description.
    """

    document_id: str
    character_name: str
    personality: str
    conversation_id: str
