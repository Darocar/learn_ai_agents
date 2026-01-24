"""Dependency injection for FastAPI controllers.

This module provides dependency injection functions for FastAPI routes,
following the hexagonal architecture by injecting use cases.
"""

from fastapi import Request
from learn_ai_agents.application.use_cases.agents.basic_answer.basic_answer import (
    BasicAnswerUseCase,
)
from learn_ai_agents.application.use_cases.discovery.use_case import DiscoveryUseCase
from learn_ai_agents.domain.services.agents.settings_resource_discovery import (
    SettingsResourceDiscovery,
)


def get_basic_answer_use_case(request: Request) -> BasicAnswerUseCase:
    """Get the Basic Answer use case instance.

    This dependency retrieves the BasicAnswerUseCase from the application container.

    Args:
        request: FastAPI request object containing the app state.

    Returns:
        BasicAnswerUseCase instance.
    """
    container = request.app.state.container
    return container.use_cases.get("basic_answer")


def get_discovery_use_case(request: Request) -> DiscoveryUseCase:
    """Get the Discovery use case instance.

    This dependency creates a new DiscoveryUseCase with the settings discovery service.
    Discovery doesn't need to be in the container as it's stateless and lightweight.
    
    Args:
        request: The FastAPI request object.

    Returns:
        DiscoveryUseCase instance.
    """
    container = request.app.state.container
    discovery_service = SettingsResourceDiscovery(settings=container.settings)
    return DiscoveryUseCase(discovery_service=discovery_service)
