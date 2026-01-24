"""Container for managing use case instances.

This module provides the container responsible for creating and managing
use case instances with their agent dependencies.
"""

# infrastructure/bootstrap/usecases_container.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from learn_ai_agents.logging import get_logger
from typing_extensions import Self

from ._utils import import_class_from_string
from .agents_container import AgentsContainer


from .components_container import ComponentsContainer
from learn_ai_agents.settings import AppSettings

logger = get_logger(__name__)


@dataclass
class UseCasesContainer:
    """Container for managing use case instances.

    This container creates and manages use case instances, injecting
    the required agent dependencies.

    Attributes:
        settings: The application settings to use for use case resolution.
        _use_cases: Dictionary of use case instances keyed by name.
    """

    settings: AppSettings
    _use_cases: dict[str, Any]

    @classmethod
    def create(cls, settings: AppSettings, agents: AgentsContainer, components: ComponentsContainer | None = None) -> Self:
        """Create the use cases container with all configured use cases.

        Instantiates all use cases with their required dependencies
        based on configuration from settings.

        Args:
            settings: The application settings to use for use case resolution.
            agents: The agents container for dependency injection.
            components: The components container for dependency injection (optional).

        Returns:
            Initialized UseCasesContainer with all use cases.
        """
        use_cases: dict[str, Any] = {}

        # Iterate through all configured use cases
        for use_case_key, use_case_cfg in settings.use_cases.items():
            logger.info(f"Setting up use case: {use_case_key} ({use_case_cfg.info.name})")

            use_case_cls = import_class_from_string(use_case_cfg.constructor.module_class)

            # Build kwargs for use case constructor dynamically
            kwargs: dict[str, Any] = {}

            # Resolve all component types dynamically
            if use_case_cfg.constructor.components:
                components_dict = use_case_cfg.constructor.components.model_dump(exclude_none=True)
                for component_type, component_refs in components_dict.items():
                    if component_type == "agents":
                        # Special handling for agents - resolve from agents container
                        resolved_components = {
                            alias: agents.get(ref.replace("agents.", "")) for alias, ref in component_refs.items()
                        }
                        # If there's only one agent with alias 'agent', pass it directly
                        if len(resolved_components) == 1 and "agent" in resolved_components:
                            kwargs["agent"] = resolved_components["agent"]
                        else:
                            kwargs[component_type] = resolved_components
                    else:
                        # Handle other component types (content_retriever, document_repository, etc.)
                        # Resolve from components container if available
                        resolved_components = {}
                        for alias, ref in component_refs.items():
                            if components:
                                resolved_components[alias] = components.get(ref)
                            else:
                                logger.warning(f"Components container not available, passing ref: {ref}")
                                resolved_components[alias] = ref

                        # If there's only one component with matching alias, pass it directly
                        if len(resolved_components) == 1 and component_type in resolved_components:
                            kwargs[component_type] = resolved_components[component_type]
                        else:
                            kwargs[component_type] = resolved_components

            # Instantiate the use case with all dependencies as kwargs
            use_case = use_case_cls(**kwargs)
            use_cases[use_case_key] = use_case
            logger.debug(f"Use case initialized: {use_case_key}")

        return cls(settings, use_cases)

    def get(self, name: str) -> Any:
        """Retrieve a use case by name.

        Args:
            name: The use case identifier.

        Returns:
            The requested use case instance.
        """
        return self._use_cases[name]

    def list_agent_answer_use_cases(self) -> dict[str, Any]:
        """List all use cases that implement AgentAnswerPort.

        This method filters the use cases to return only those that follow
        the AgentAnswerPort protocol (duck typing check for required methods).

        Returns:
            Dictionary of use case instances that implement AgentAnswerPort,
            keyed by their identifiers.
        """

        agent_use_cases = {}
        for name, use_case in self._use_cases.items():
            # Check if the use case implements the AgentAnswerPort protocol
            # by verifying it has the required methods
            if (
                hasattr(use_case, "invoke")
                and hasattr(use_case, "stream")
                and callable(use_case.invoke)
                and callable(use_case.stream)
            ):
                agent_use_cases[name] = use_case

        return agent_use_cases
