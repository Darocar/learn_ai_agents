"""Domain models for discovery functionality.

This module defines the core domain models for discovering system resources
like components, agents, and use cases.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ComponentInfo:
    """Domain model for component discovery information.

    Attributes:
        framework: The framework name (e.g., 'langchain').
        family: The component family (e.g., 'groq').
        instance: The instance name (e.g., 'default').
    """

    framework: str
    family: str
    instance: str


@dataclass
class Component:
    """Domain model representing a discoverable component.

    Attributes:
        ref: Full reference path (e.g., 'llms.langchain.groq.default').
        info: Component information (framework, family, instance).
        api_key_present: Whether this component has an API key configured.
        params: Configuration parameters for this component instance.
    """

    ref: str
    info: ComponentInfo
    api_key_present: bool
    params: dict[str, Any]


@dataclass
class AgentInfo:
    """Domain model for agent information.

    Attributes:
        name: Human-readable agent name.
        description: Description of what the agent does.
    """

    name: str
    description: str


@dataclass
class Agent:
    """Domain model representing a discoverable agent.

    Attributes:
        ref: Full reference path (e.g., 'agents.langchain.basic_answer').
        info: Agent information (name, description).
        components: Component dependencies. Can be either:
            - Dict[str, str] for simple references (e.g., {"checkpointer": "ref"})
            - Dict[str, Dict[str, str]] for aliased references (e.g., {"llms": {"default": "ref"}})
    """

    ref: str
    info: AgentInfo
    components: dict[str, str | dict[str, str]] | None = None


@dataclass
class UseCaseInfo:
    """Domain model for use case information.

    Attributes:
        name: Human-readable use case name.
        description: Description of what the use case does.
        path_prefix: API path prefix for this use case.
    """

    name: str
    description: str
    path_prefix: str


@dataclass
class UseCase:
    """Domain model representing a discoverable use case.

    Attributes:
        ref: Reference name (e.g., 'basic_answer').
        info: Use case information (name, description, path_prefix).
        components: Component dependencies. Can be either:
            - Dict[str, str] for simple references
            - Dict[str, Dict[str, str]] for aliased references
    """

    ref: str
    info: UseCaseInfo
    components: dict[str, str | dict[str, str]] | None = None


@dataclass
class SystemResources:
    """Domain model for all system resources.

    Attributes:
        components: Dictionary of component type to list of components.
        agents: List of available agents.
        use_cases: List of available use cases.
    """

    components: dict[str, list[Component]]
    agents: list[Agent]
    use_cases: list[UseCase]
