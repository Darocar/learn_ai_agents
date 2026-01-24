"""Discovery use case implementation.

This module implements the business logic for discovering system resources.
"""

from learn_ai_agents.application.dtos.discovery.discovery import (
    AgentDTO,
    AgentInfoDTO,
    AgentsResponseDTO,
    AllResourcesResponseDTO,
    ComponentDTO,
    ComponentInfoDTO,
    ComponentsResponseDTO,
    UseCaseDTO,
    UseCaseInfoDTO,
    UseCasesResponseDTO,
)
from learn_ai_agents.application.inbound_ports.discovery.discovery import DiscoveryPort
from learn_ai_agents.domain.ports.agents.resource_discovery import ResourceDiscoveryPort


class DiscoveryUseCase(DiscoveryPort):
    """Use case for discovering system resources.

    This use case orchestrates resource discovery by using the
    ResourceDiscoveryPort and converting domain models to DTOs.

    Attributes:
        discovery_service: The service for discovering resources.
    """

    def __init__(self, discovery_service: ResourceDiscoveryPort):
        """Initialize the discovery use case.

        Args:
            discovery_service: Service for discovering resources.
        """
        self.discovery_service = discovery_service

    def discover_components(self) -> ComponentsResponseDTO:
        """Discover all available components.

        Returns:
            ComponentsResponseDTO with all components organized by type.
        """
        components_dict = self.discovery_service.discover_components()

        # Convert domain models to DTOs
        dto_components = {}
        for comp_type, components in components_dict.items():
            dto_components[comp_type] = [
                ComponentDTO(
                    ref=comp.ref,
                    info=ComponentInfoDTO(
                        framework=comp.info.framework,
                        family=comp.info.family,
                        instance=comp.info.instance,
                    ),
                    api_key="**********" if comp.api_key_present else None,
                    params=comp.params,
                )
                for comp in components
            ]

        return ComponentsResponseDTO(components=dto_components)

    def discover_agents(self) -> AgentsResponseDTO:
        """Discover all available agents.

        Returns:
            AgentsResponseDTO with list of all agents.
        """
        agents = self.discovery_service.discover_agents()

        # Convert domain models to DTOs
        dto_agents = [
            AgentDTO(
                ref=agent.ref,
                info=AgentInfoDTO(name=agent.info.name, description=agent.info.description),
                components=agent.components,
            )
            for agent in agents
        ]

        return AgentsResponseDTO(agents=dto_agents)

    def discover_use_cases(self) -> UseCasesResponseDTO:
        """Discover all available use cases.

        Returns:
            UseCasesResponseDTO with list of all use cases.
        """
        use_cases = self.discovery_service.discover_use_cases()

        # Convert domain models to DTOs
        dto_use_cases = [
            UseCaseDTO(
                ref=uc.ref,
                info=UseCaseInfoDTO(
                    name=uc.info.name,
                    description=uc.info.description,
                    path_prefix=uc.info.path_prefix,
                ),
                components=uc.components,
            )
            for uc in use_cases
        ]

        return UseCasesResponseDTO(use_cases=dto_use_cases)

    def discover_all(self) -> AllResourcesResponseDTO:
        """Discover all system resources.

        Returns:
            AllResourcesResponseDTO with all resources.
        """
        all_resources = self.discovery_service.discover_all()

        # Convert components
        dto_components = {}
        for comp_type, components in all_resources.components.items():
            dto_components[comp_type] = [
                ComponentDTO(
                    ref=comp.ref,
                    info=ComponentInfoDTO(
                        framework=comp.info.framework,
                        family=comp.info.family,
                        instance=comp.info.instance,
                    ),
                    api_key="**********" if comp.api_key_present else None,
                    params=comp.params,
                )
                for comp in components
            ]

        # Convert agents
        dto_agents = [
            AgentDTO(
                ref=agent.ref,
                info=AgentInfoDTO(name=agent.info.name, description=agent.info.description),
                components=agent.components,
            )
            for agent in all_resources.agents
        ]

        # Convert use cases
        dto_use_cases = [
            UseCaseDTO(
                ref=uc.ref,
                info=UseCaseInfoDTO(
                    name=uc.info.name,
                    description=uc.info.description,
                    path_prefix=uc.info.path_prefix,
                ),
                components=uc.components,
            )
            for uc in all_resources.use_cases
        ]

        return AllResourcesResponseDTO(components=dto_components, agents=dto_agents, use_cases=dto_use_cases)
