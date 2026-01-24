"""Dependency injection for FastAPI controllers.

This module provides dependency injection functions for FastAPI routes,
following the hexagonal architecture by injecting use cases.
"""

from fastapi import Request
from learn_ai_agents.application.use_cases.agents.basic_answer.basic_answer import (
    BasicAnswerUseCase,
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
