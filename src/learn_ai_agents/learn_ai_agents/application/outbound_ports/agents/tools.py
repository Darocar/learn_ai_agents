# learn_ai_agents/domain/outbound_ports/tools.py
from typing import Any, Protocol


class ToolPort(Protocol):
    """Port for exposing a tool to an agent.

    Each framework adapter will return its own concrete tool type
    (LangChain BaseTool, PydanticAI Tool, etc.).
    """

    name: str
    description: str

    def get_tool(self) -> Any:
        """Return the underlying framework-specific tool object."""
        ...
