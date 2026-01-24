"""FastAPI application factory.

This module provides the application factory function for creating
FastAPI app instances. It serves as the composition root where all
configuration and dependency injection will be wired together.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from learn_ai_agents.logging import get_logger
from learn_ai_agents.settings import AppSettings

logger = get_logger(__name__)


def create_app(app_settings: AppSettings) -> FastAPI:
    """Create and configure the FastAPI application.

    This is the composition root of the hexagonal architecture.
    As the application grows, this is where:
    - Dependency injection containers will be built
    - Routers will be registered
    - Middleware will be configured
    - Exception handlers will be set up

    Args:
        app_settings: Application settings instance for configuration.

    Returns:
        Configured FastAPI application instance.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Manage application lifecycle (startup and shutdown).

        This context manager handles:
        - Startup: Initialize resources, connect to databases, etc.
        - Shutdown: Clean up resources, close connections, etc.

        Args:
            app: The FastAPI application instance.

        Yields:
            Control during the application's running state.
        """
        logger.info("🚀 Starting Learn AI Agents application...")
        
        # TODO: Initialize resources here in future branches
        # - Build dependency injection container
        # - Connect to databases
        # - Initialize LLM clients
        # - Set up tracing
        
        logger.info("✅ Application startup complete")

        try:
            yield
        finally:
            logger.info("🛑 Shutting down application...")
            
            # TODO: Clean up resources here in future branches
            # - Close database connections
            # - Shutdown LLM clients
            # - Flush tracing buffers
            
            logger.info("✅ Application shutdown complete")

    # Create FastAPI app with lifecycle management
    app = FastAPI(
        title="Learn AI Agents",
        description="A didactic project for learning AI agent development with Hexagonal Architecture",
        version="0.1.0",
        lifespan=lifespan,
    )

    # TODO: Register routers here in future branches
    # Example:
    # from learn_ai_agents.infrastructure.inbound.api import health_router
    # app.include_router(health_router)

    logger.info("✅ Application created successfully")

    return app

