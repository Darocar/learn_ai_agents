"""Dependency injection for FastAPI controllers.

This module provides dependency injection functions for FastAPI routes,
following the hexagonal architecture by injecting use cases.
"""

from fastapi import Request
from learn_ai_agents.application.use_cases.agents.basic_answer.basic_answer import (
    BasicAnswerUseCase,
)
from learn_ai_agents.application.use_cases.agents.adding_memory.use_case import (
    AddingMemoryUseCase,
)
from learn_ai_agents.application.use_cases.agents.adding_tools.use_case import (
    AddingToolsUseCase,
)
from learn_ai_agents.application.use_cases.agents.agent_tracing.use_case import (
    AgentTracingUseCase,
)
from learn_ai_agents.application.use_cases.agents.character_chat.use_case import (
    CharacterChatUseCase,
)
from learn_ai_agents.application.use_cases.agents.robust.use_case import (
    RobustUseCase,
)
from learn_ai_agents.application.use_cases.content_indexer.source_ingestion import (
    SourceIngestionUseCase,
)
from learn_ai_agents.application.use_cases.content_indexer.document_splitting.use_case import (
    DocumentSplittingUseCase,
)
from learn_ai_agents.application.use_cases.content_indexer.vectorization.use_case import (
    VectorizationUseCase,
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


def get_adding_memory_use_case(request: Request) -> AddingMemoryUseCase:
    """Get the Adding Memory use case instance.

    This dependency retrieves the AddingMemoryUseCase from the application container.

    Args:
        request: FastAPI request object containing the app state.

    Returns:
        AddingMemoryUseCase instance.
    """
    container = request.app.state.container
    return container.use_cases.get("adding_memory")


def get_adding_tools_use_case(request: Request) -> AddingToolsUseCase:
    """Get the Adding Tools use case instance.

    This dependency retrieves the AddingToolsUseCase from the application container.

    Args:
        request: FastAPI request object containing the app state.

    Returns:
        AddingToolsUseCase instance.
    """
    container = request.app.state.container
    return container.use_cases.get("adding_tools")


def get_character_chat_use_case(request: Request) -> CharacterChatUseCase:
    """Get the Character Chat use case instance.

    This dependency retrieves the CharacterChatUseCase from the application container.

    Args:
        request: FastAPI request object containing the app state.

    Returns:
        CharacterChatUseCase instance.
    """
    container = request.app.state.container
    return container.use_cases.get("character_chat")


def get_agent_tracing_use_case(request: Request) -> AgentTracingUseCase:
    """Get the Agent Tracing use case instance.

    This dependency retrieves the AgentTracingUseCase from the application container.

    Args:
        request: FastAPI request object containing the app state.

    Returns:
        AgentTracingUseCase instance.
    """
    container = request.app.state.container
    return container.use_cases.get("agent_tracing")


def get_robust_use_case(request: Request) -> RobustUseCase:
    """Get the Robust Agent use case instance.

    This dependency retrieves the RobustUseCase from the application container.

    Args:
        request: FastAPI request object containing the app state.

    Returns:
        RobustUseCase instance.
    """
    container = request.app.state.container
    return container.use_cases.get("robust")


def get_source_ingestion_use_case(request: Request) -> SourceIngestionUseCase:
    """Get the Source Ingestion use case instance."""
    container = request.app.state.container
    return container.use_cases.get("source_ingestion")


def get_document_splitting_use_case(request: Request) -> DocumentSplittingUseCase:
    """Get the Document Splitting use case instance."""
    container = request.app.state.container
    return container.use_cases.get("document_splitting")


def get_vectorization_use_case(request: Request) -> VectorizationUseCase:
    """Get the Vectorization use case instance."""
    container = request.app.state.container
    return container.use_cases.get("vectorization")


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
