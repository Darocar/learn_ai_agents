"""Container for managing agent instances.

This module provides the container responsible for creating and managing
AI agent instances with their dependencies.
"""

# infrastructure/bootstrap/agents_container.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from learn_ai_agents.application.outbound_ports.agents.agent_engine import AgentEngine
from learn_ai_agents.logging import get_logger
from typing_extensions import Self

from ._utils import import_class_from_string
from .components_container import ComponentsContainer

from learn_ai_agents.settings import AppSettings

logger = get_logger(__name__)


@dataclass
class AgentsContainer:
    """Container for managing agent instances.

    This container creates and manages AI agent instances based on
    configuration, injecting required dependencies (LLMs, tools, etc.).

    Attributes:
        settings: The application settings to use for agent resolution.
        _agents: Dictionary of agent instances keyed by name.
    """

    settings: AppSettings
    _agents: dict[str, Any]

    @classmethod
    def create(cls, settings: AppSettings, components: ComponentsContainer) -> Self:
        """Create the agents container with all configured agents.

        Reads agent configurations from settings and instantiates each
        agent with its required components.

        Args:
            settings: The application settings to use for agent resolution.
            components: The components container for dependency injection.

        Returns:
            Initialized AgentsContainer with all agents.
        """
        agents: dict[str, Any] = {}

        # Iterate through frameworks (e.g., 'langchain')
        for framework, framework_agents in settings.agents.items():
            # Iterate through agents in this framework
            for agent_key, agent_cfg in framework_agents.items():
                full_key = f"{framework}.{agent_key}"
                logger.info(f"Initializing agent: {full_key} ({agent_cfg.info.name})")

                agent_cls = import_class_from_string(agent_cfg.constructor.module_class)

                # Build kwargs for agent constructor
                kwargs: dict[str, Any] = {"config": {}}

                # Merge additional config from constructor.config if present
                if agent_cfg.constructor.config:
                    kwargs["config"].update(agent_cfg.constructor.config)

                # Resolve and inject all component types dynamically
                if agent_cfg.constructor.components:
                    components_dict = agent_cfg.constructor.components.model_dump(exclude_none=True)
                    for component_type, component_refs in components_dict.items():
                        # Check if component_refs is a dict (multiple components) or string (single component)
                        if isinstance(component_refs, dict):
                            # Multiple components: component_refs is like {'default': 'llms.langchain.groq.default'}
                            resolved_components = {alias: components.get(ref) for alias, ref in component_refs.items()}
                            kwargs[component_type] = resolved_components
                        else:
                            # Single component: component_refs is a string like 'checkpointers.mongo.saver.default'
                            resolved_component = components.get(component_refs)
                            kwargs[component_type] = resolved_component

                # Instantiate agent with all components as kwargs
                agent = agent_cls(**kwargs)

                # Store with fully qualified key: framework.agent_name
                agents[full_key] = agent
                logger.debug(f"Agent initialized successfully: {full_key}")

        return cls(settings, agents)

    def get(self, name: str) -> AgentEngine:
        """Retrieve an agent by name.

        Args:
            name: The agent identifier.

        Returns:
            The requested agent instance.
        """
        return self._agents[name]
