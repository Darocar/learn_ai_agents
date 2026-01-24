"""Inbound port for resource discovery use cases.

This module defines the port (interface) that controllers use to access
discovery functionality.
"""

from abc import ABC, abstractmethod

from learn_ai_agents.application.dtos.discovery.discovery import (
    AgentsResponseDTO,
    AllResourcesResponseDTO,
    ComponentsResponseDTO,
    UseCasesResponseDTO,
)


class DiscoveryPort(ABC):
    """Port for discovery use cases.

    This abstract interface defines the contract for discovery operations
    exposed to the API layer.
    """

    @abstractmethod
    def discover_components(self) -> ComponentsResponseDTO:
        """Discover all available components.

        Returns:
            ComponentsResponseDTO with all components organized by type.
        """
        ...

    @abstractmethod
    def discover_agents(self) -> AgentsResponseDTO:
        """Discover all available agents.

        Returns:
            AgentsResponseDTO with list of all agents.
        """
        ...

    @abstractmethod
    def discover_use_cases(self) -> UseCasesResponseDTO:
        """Discover all available use cases.

        Returns:
            UseCasesResponseDTO with list of all use cases.
        """
        ...

    @abstractmethod
    def discover_all(self) -> AllResourcesResponseDTO:
        """Discover all system resources.

        Returns:
            AllResourcesResponseDTO with all resources.
        """
        ...
