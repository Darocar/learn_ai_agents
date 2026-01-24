"""DTOs for discovery functionality.

This module defines Data Transfer Objects for discovery endpoints.
"""

from typing import Any

from pydantic import BaseModel


class ComponentInfoDTO(BaseModel):
    """DTO for component information.

    Attributes:
        framework: The framework name.
        family: The component family.
        instance: The instance name.
    """

    framework: str
    family: str
    instance: str


class ComponentDTO(BaseModel):
    """DTO representing a component.

    Attributes:
        ref: Full reference path.
        info: Component information.
        api_key: Masked API key if present.
        params: Configuration parameters.
    """

    ref: str
    info: ComponentInfoDTO
    api_key: str | None = None
    params: dict[str, Any]


class ComponentsResponseDTO(BaseModel):
    """DTO for components discovery response.

    Attributes:
        components: Dictionary mapping component type to list of components.
    """

    components: dict[str, list[ComponentDTO]]


class AgentInfoDTO(BaseModel):
    """DTO for agent information.

    Attributes:
        name: Human-readable agent name.
        description: Description of the agent.
    """

    name: str
    description: str


class AgentDTO(BaseModel):
    """DTO representing an agent.

    Attributes:
        ref: Full reference path.
        info: Agent information.
        components: Component dependencies. Can be either:
            - Dict[str, str] for simple references (e.g., {"checkpointer": "ref"})
            - Dict[str, Dict[str, str]] for aliased references (e.g., {"llms": {"default": "ref"}})
    """

    ref: str
    info: AgentInfoDTO
    components: dict[str, str | dict[str, str]] | None = None


class AgentsResponseDTO(BaseModel):
    """DTO for agents discovery response.

    Attributes:
        agents: List of available agents.
    """

    agents: list[AgentDTO]


class UseCaseInfoDTO(BaseModel):
    """DTO for use case information.

    Attributes:
        name: Human-readable use case name.
        description: Description of the use case.
        path_prefix: API path prefix.
    """

    name: str
    description: str
    path_prefix: str


class UseCaseDTO(BaseModel):
    """DTO representing a use case.

    Attributes:
        ref: Reference name.
        info: Use case information.
        components: Component dependencies. Can be either:
            - Dict[str, str] for simple references
            - Dict[str, Dict[str, str]] for aliased references
    """

    ref: str
    info: UseCaseInfoDTO
    components: dict[str, str | dict[str, str]] | None = None


class UseCasesResponseDTO(BaseModel):
    """DTO for use cases discovery response.

    Attributes:
        use_cases: List of available use cases.
    """

    use_cases: list[UseCaseDTO]


class AllResourcesResponseDTO(BaseModel):
    """DTO for all resources discovery response.

    Attributes:
        components: Dictionary of component types to components.
        agents: List of agents.
        use_cases: List of use cases.
    """

    components: dict[str, list[ComponentDTO]]
    agents: list[AgentDTO]
    use_cases: list[UseCaseDTO]
