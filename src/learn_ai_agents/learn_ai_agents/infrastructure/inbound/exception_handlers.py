"""Centralized exception handlers for FastAPI.

This module defines exception handlers that map domain exceptions to appropriate HTTP responses.
"""

import logging
from enum import Enum
from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse

from learn_ai_agents.domain.exceptions._base import (
    AppException,
    BusinessRuleException,
    ComponentException,
    AgentException,
)
from learn_ai_agents.domain.exceptions.domain import (
    ResourceNotFoundException,
    InvalidRequestException,
    SourceContentFormatException,
)
from learn_ai_agents.domain.exceptions.components import (
    ComponentBuildingException,
    ComponentConnectionException,
    ComponentOperationException,
    ComponentNotAvailableException,
    ComponentValidationException,
)
from learn_ai_agents.domain.exceptions.agents import (
    AgentBuildingException,
    AgentExecutionException,
    LLMCallException,
)

logger = logging.getLogger(__name__)


class ErrorType(str, Enum):
    """Enumeration of error types returned in API responses."""

    # Business Rule Errors
    BUSINESS_RULE_VIOLATION = "BusinessRuleViolation"
    RESOURCE_NOT_FOUND = "ResourceNotFound"
    INVALID_REQUEST = "InvalidRequest"
    UNSUPPORTED_CONTENT_FORMAT = "UnsupportedContentFormat"

    # Component Errors
    COMPONENT_VALIDATION_ERROR = "ComponentValidationError"
    SERVICE_OPERATION_ERROR = "ServiceOperationError"
    SERVICE_UNAVAILABLE = "ServiceUnavailable"

    # Agent Errors
    AGENT_EXECUTION_ERROR = "AgentExecutionError"
    AGENT_ERROR = "AgentError"

    # Generic Errors
    INTERNAL_SERVER_ERROR = "InternalServerError"


def _sanitize_details(details: dict[str, Any]) -> dict[str, Any]:
    """
    Sanitize exception details for API responses.
    Removes sensitive information and ensures all values are JSON serializable.
    """
    sanitized: dict[str, Any] = {}
    sensitive_keys = {"password", "token", "secret", "api_key", "credentials"}

    for key, value in details.items():
        if key.lower() in sensitive_keys:
            continue

        # Convert non-serializable types to strings
        if isinstance(value, (str, int, float, bool, type(None), list, dict)):
            sanitized[key] = value
        else:
            sanitized[key] = str(value)

    return sanitized


def _create_error_response(
    status_code: int,
    error_type: ErrorType,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    """
    Create a standardized error response.
    """
    error_content: dict[str, Any] = {
        "type": error_type.value,
        "message": message,
    }

    if details:
        error_content["details"] = _sanitize_details(details)

    content: dict[str, Any] = {"error": error_content}

    return JSONResponse(
        status_code=status_code,
        content=content,
    )


# --- Business Rule Exceptions (Client Errors) ---


async def business_rule_exception_handler(
    request: Request, exc: BusinessRuleException
) -> JSONResponse:
    """
    Handler for business rule violations.
    Returns HTTP 400 Bad Request.
    """
    logger.warning(
        "Business rule violation",
        extra={
            "path": request.url.path,
            "error_message": exc.message,
            "details": exc.details,
        },
    )

    return _create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        error_type=ErrorType.BUSINESS_RULE_VIOLATION,
        message=exc.message or "Business rule violation",
        details=exc.details,
    )


async def resource_not_found_exception_handler(
    request: Request, exc: ResourceNotFoundException
) -> JSONResponse:
    """
    Handler for resource not found errors.
    Returns HTTP 404 Not Found.
    """
    logger.info(
        "Resource not found",
        extra={
            "path": request.url.path,
            "error_message": exc.message,
            "details": exc.details,
        },
    )

    return _create_error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        error_type=ErrorType.RESOURCE_NOT_FOUND,
        message=exc.message or "Resource not found",
        details=exc.details,
    )


async def invalid_request_exception_handler(
    request: Request, exc: InvalidRequestException
) -> JSONResponse:
    """
    Handler for invalid request parameters.
    Returns HTTP 422 Unprocessable Entity.
    """
    logger.warning(
        "Invalid request",
        extra={
            "path": request.url.path,
            "error_message": exc.message,
            "details": exc.details,
        },
    )

    return _create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_type=ErrorType.INVALID_REQUEST,
        message=exc.message or "Invalid request parameters",
        details=exc.details,
    )


async def source_content_format_exception_handler(
    request: Request, exc: SourceContentFormatException
) -> JSONResponse:
    """
    Handler for invalid content format errors.
    Returns HTTP 415 Unsupported Media Type.
    """
    logger.warning(
        "Unsupported content format",
        extra={
            "path": request.url.path,
            "error_message": exc.message,
            "details": exc.details,
        },
    )

    return _create_error_response(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        error_type=ErrorType.UNSUPPORTED_CONTENT_FORMAT,
        message=exc.message or "Unsupported content format",
        details=exc.details,
    )


# --- Component Exceptions (Server Errors) ---


async def component_validation_exception_handler(
    request: Request, exc: ComponentValidationException
) -> JSONResponse:
    """
    Handler for component validation errors (invalid configuration/parameters).
    Returns HTTP 400 Bad Request.
    """
    logger.error(
        "Component validation error",
        extra={
            "path": request.url.path,
            "component_type": exc.component_type,
            "error_message": exc.message,
            "details": exc.details,
        },
    )

    return _create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        error_type=ErrorType.COMPONENT_VALIDATION_ERROR,
        message=exc.message or "Component received invalid parameters",
        details={"component_type": exc.component_type},
    )


async def component_operation_exception_handler(
    request: Request, exc: ComponentOperationException
) -> JSONResponse:
    """
    Handler for component operation errors (queries, processing, disconnection).
    Returns HTTP 503 Service Unavailable.
    """
    logger.error(
        "Component operation error",
        extra={
            "path": request.url.path,
            "component_type": exc.component_type,
            "error_message": exc.message,
            "details": exc.details,
        },
        exc_info=True,
    )

    return _create_error_response(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        error_type=ErrorType.SERVICE_OPERATION_ERROR,
        message="A service operation failed. Please try again later.",
        details={"component_type": exc.component_type},
    )


async def component_exception_handler(
    request: Request, exc: ComponentException
) -> JSONResponse:
    """
    Handler for component/infrastructure errors.
    Returns HTTP 503 Service Unavailable.
    """
    logger.error(
        "Component error",
        extra={
            "path": request.url.path,
            "component_type": exc.component_type,
            "error_message": exc.message,
            "details": exc.details,
        },
        exc_info=True,
    )

    # Determine more specific status based on exception type
    if isinstance(exc, ComponentNotAvailableException):
        user_message = (
            "A required service is temporarily unavailable. Please try again later."
        )
    elif isinstance(exc, ComponentConnectionException):
        user_message = (
            "Failed to connect to a required service. Please try again later."
        )
    elif isinstance(exc, ComponentBuildingException):
        user_message = "Service initialization failed. Please contact support."
    else:
        user_message = "A service error occurred. Please try again later."

    return _create_error_response(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        error_type=ErrorType.SERVICE_UNAVAILABLE,
        message=user_message,
        details={"component_type": exc.component_type},
    )


# --- Agent Exceptions (Server Errors) ---


async def agent_execution_exception_handler(
    request: Request, exc: AgentExecutionException
) -> JSONResponse:
    """
    Handler for agent execution errors (runtime errors during graph execution).
    Returns HTTP 503 Service Unavailable.
    """
    logger.error(
        "Agent execution error",
        extra={
            "path": request.url.path,
            "agent_component": exc.agent_component,
            "error_message": exc.message,
            "details": exc.details,
        },
        exc_info=True,
    )

    # Provide user-friendly message
    user_message = exc.message or "Agent execution failed. Please try again."

    # Include full exception details plus agent_component
    response_details: dict[str, object] = {"agent_component": exc.agent_component}
    if exc.details:
        response_details.update(exc.details)

    return _create_error_response(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        error_type=ErrorType.AGENT_EXECUTION_ERROR,
        message=user_message,
        details=response_details,
    )


async def agent_exception_handler(
    request: Request, exc: AgentException
) -> JSONResponse:
    """
    Handler for agent errors (fallback for non-execution agent errors).
    Returns HTTP 503 Service Unavailable.
    """
    logger.error(
        "Agent error",
        extra={
            "path": request.url.path,
            "agent_component": exc.agent_component,
            "error_message": exc.message,
            "details": exc.details,
        },
        exc_info=True,
    )

    # Provide user-friendly messages based on agent component
    if isinstance(exc, LLMCallException):
        user_message = "The AI service is experiencing issues. Please try again later."
    elif isinstance(exc, AgentBuildingException):
        user_message = "Agent initialization failed. Please contact support."
    else:
        user_message = exc.message or "Agent execution failed. Please try again."

    return _create_error_response(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        error_type=ErrorType.AGENT_ERROR,
        message=user_message,
        details={"agent_component": exc.agent_component},
    )


# --- Generic App Exception Handler ---


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Fallback handler for any unhandled AppException.
    Returns HTTP 500 Internal Server Error.
    """
    logger.error(
        "Unhandled app exception",
        extra={
            "path": request.url.path,
            "error_message": exc.message,
            "details": exc.details,
        },
        exc_info=True,
    )

    return _create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_type=ErrorType.INTERNAL_SERVER_ERROR,
        message="An unexpected error occurred. Please try again later.",
        details={},
    )


# --- Generic Exception Handler ---


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Fallback handler for any unexpected exception.
    Returns HTTP 500 Internal Server Error.
    """
    logger.exception(
        "Unexpected exception",
        extra={
            "path": request.url.path,
            "exception_type": type(exc).__name__,
        },
    )

    return _create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_type=ErrorType.INTERNAL_SERVER_ERROR,
        message="An unexpected error occurred. Please contact support.",
        details={},
    )


def register_exception_handlers(app) -> None:
    """
    Register all exception handlers with the FastAPI application.

    Order matters: Register more specific exceptions before generic ones.
    """
    # Business rule exceptions (most specific first)
    app.add_exception_handler(
        ResourceNotFoundException, resource_not_found_exception_handler
    )
    app.add_exception_handler(
        InvalidRequestException, invalid_request_exception_handler
    )
    app.add_exception_handler(
        SourceContentFormatException, source_content_format_exception_handler
    )
    app.add_exception_handler(BusinessRuleException, business_rule_exception_handler)

    # Component exceptions (specific before generic)
    app.add_exception_handler(
        ComponentValidationException, component_validation_exception_handler
    )
    app.add_exception_handler(
        ComponentOperationException, component_operation_exception_handler
    )
    app.add_exception_handler(ComponentException, component_exception_handler)

    # Agent exceptions (specific before generic)
    app.add_exception_handler(
        AgentExecutionException, agent_execution_exception_handler
    )
    app.add_exception_handler(AgentException, agent_exception_handler)

    # Generic app exception
    app.add_exception_handler(AppException, app_exception_handler)

    # Fallback for any unexpected exception
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Exception handlers registered successfully")
