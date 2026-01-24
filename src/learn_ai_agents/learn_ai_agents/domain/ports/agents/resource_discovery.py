"""Domain port for resource discovery.

This module defines the port (interface) for discovering system resources.
This is a domain port for internal abstraction, not an outbound port for
external systems.
"""

from abc import ABC, abstractmethod

from learn_ai_agents.domain.models.agents.discovery import (
    Agent,
    Component,
    SystemResources,
    UseCase,
)


class ResourceDiscoveryPort(ABC):
    """Port for discovering system resources.

    This abstract interface defines the contract for discovering
    components, agents, and use cases from the system configuration.
    This is an internal domain abstraction.
    """

    @abstractmethod
    def discover_components(self) -> dict[str, list[Component]]:
        """Discover all available components.

        Returns:
            Dictionary mapping component type to list of components.
        """
        ...

    @abstractmethod
    def discover_agents(self) -> list[Agent]:
        """Discover all available agents.

        Returns:
            List of available agents.
        """
        ...

    @abstractmethod
    def discover_use_cases(self) -> list[UseCase]:
        """Discover all available use cases.

        Returns:
            List of available use cases.
        """
        ...

    @abstractmethod
    def discover_all(self) -> SystemResources:
        """Discover all system resources.

        Returns:
            SystemResources containing all components, agents, and use cases.
        """
        ...
