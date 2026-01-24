"""Settings-based resource discovery implementation.

This module provides the concrete implementation of the resource discovery
service that reads from the application settings/configuration.
"""

from learn_ai_agents.domain.models.agents.discovery import (
    Agent,
    AgentInfo,
    Component,
    ComponentInfo,
    SystemResources,
    UseCase,
    UseCaseInfo,
)
from learn_ai_agents.domain.ports.agents.resource_discovery import ResourceDiscoveryPort
from learn_ai_agents.settings import AppSettings


class SettingsResourceDiscovery(ResourceDiscoveryPort):
    """Settings-based resource discovery implementation.

    This service implements resource discovery by reading from
    the application settings and converting to domain models.
    
    Attributes:
        settings: The application settings instance to use for discovery.
    """
    
    def __init__(self, settings: AppSettings):
        """Initialize the settings resource discovery service.
        
        Args:
            settings: The application settings instance.
        """
        self.settings = settings

    def discover_components(self) -> dict[str, list[Component]]:
        """Discover all available components.

        Returns:
            Dictionary mapping component type to list of Component domain models.
        """
        result: dict[str, list[Component]] = {}

        for comp_type, frameworks in self.settings.components.items():
            component_list = []

            for framework, families in frameworks.items():
                for family_name, family in families.items():
                    # Check if family has api_key
                    family_has_api_key = family.constructor.api_key is not None

                    for instance_name, instance_cfg in family.instances.items():
                        component = Component(
                            ref=f"{comp_type}.{framework}.{family_name}.{instance_name}",
                            info=ComponentInfo(
                                framework=framework,
                                family=family_name,
                                instance=instance_name,
                            ),
                            api_key_present=family_has_api_key,
                            params=instance_cfg.params,
                        )
                        component_list.append(component)

            result[comp_type] = component_list

        return result

    def discover_agents(self) -> list[Agent]:
        """Discover all available agents.

        Returns:
            List of Agent domain models.
        """
        result: list[Agent] = []

        for framework, agents in self.settings.agents.items():
            for agent_name, agent_cfg in agents.items():
                # Get components if available
                components_dict = None
                if agent_cfg.constructor.components:
                    components_dict = agent_cfg.constructor.components.model_dump(exclude_none=True)

                agent = Agent(
                    ref=f"agents.{framework}.{agent_name}",
                    info=AgentInfo(name=agent_cfg.info.name, description=agent_cfg.info.description),
                    components=components_dict,
                )
                result.append(agent)

        return result

    def discover_use_cases(self) -> list[UseCase]:
        """Discover all available use cases.

        Returns:
            List of UseCase domain models.
        """
        result: list[UseCase] = []

        for use_case_name, use_case_cfg in self.settings.use_cases.items():
            # Get components if available
            components_dict = None
            if use_case_cfg.constructor.components:
                components_dict = use_case_cfg.constructor.components.model_dump(exclude_none=True)

            use_case = UseCase(
                ref=use_case_name,
                info=UseCaseInfo(
                    name=use_case_cfg.info.name,
                    description=use_case_cfg.info.description,
                    path_prefix=use_case_cfg.info.path_prefix,
                ),
                components=components_dict,
            )
            result.append(use_case)

        return result

    def discover_all(self) -> SystemResources:
        """Discover all system resources.

        Returns:
            SystemResources domain model containing all resources.
        """
        return SystemResources(
            components=self.discover_components(),
            agents=self.discover_agents(),
            use_cases=self.discover_use_cases(),
        )
