from ._base import AgentException


# --- Family/Hierarchical Exceptions ---

class AgentBuildingException(AgentException):
    """
    Base exception for errors during agent construction/initialization.
    Use this family for build-time errors (graph building, configuration validation, etc.).
    """
    pass


class AgentExecutionException(AgentException):
    """
    Base exception for errors during agent execution.
    Use this family for runtime errors (graph execution, state processing, recursion limits, LLM calls, tool calls, etc.).
    """
    pass


# --- Specific Agent Exceptions ---

class LLMCallException(AgentExecutionException):
    """
    Exception raised when there is an error during an LLM call.
    Inherits from AgentExecutionException as LLM calls are part of agent execution.
    """
    pass