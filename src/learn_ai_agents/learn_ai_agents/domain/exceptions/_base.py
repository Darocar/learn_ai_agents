"""Domain exceptions for the Learn AI Agents application.

This module defines custom exception classes for domain-specific Exceptions.
"""
# --- Base Exception ----------------------------------------------
class AppException(Exception):
    """Base class for all app-specific Exceptions."""
    def __init__(self, message: str = "", *, details: dict[str, object] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


# --- Domain / business rules ------------------------------------

class BusinessRuleException(AppException):
    """
    Business rule or invariant violation.
    """


# --- Components / infrastructure (DB, vector store, LLM clients) --

class ComponentException(AppException):
    """
    Technical Exception in a component (DB, vector store, LLM client, etc.).

    Adapter code should translate external library exceptions into these.
    
    Args:
        component_type: The type/name of the component raising the exception (e.g., 'MongoEngineAdapter').
        message: The error message.
        details: Additional context details.
    """
    
    def __init__(self, component_type: str, message: str = "", *, details: dict[str, object] | None = None):
        details = details or {}
        details["component_type"] = component_type
        super().__init__(message, details=details)
        self.component_type = component_type


# --- Agents (LangChain / LangGraph layer) ------------------------

class AgentException(AppException):
    """
    Exceptions in the agent orchestration layer (LangChain / LangGraph / tools).
    
    Args:
        agent_component: The agent component raising the exception (e.g., 'agent', 'llm', 'tool', 'middleware').
        message: The error message.
        details: Additional context details.
    """
    
    def __init__(self, agent_component: str, message: str = "", *, details: dict[str, object] | None = None):
        details = details or {}
        details["agent_component"] = agent_component
        super().__init__(message, details=details)
        self.agent_component = agent_component


# --- Use cases / application services ----------------------------

class UseCaseException(AppException):
    """
    Exceptions in use-case orchestration (incorrect workflow, preconditions, etc.).
    """
