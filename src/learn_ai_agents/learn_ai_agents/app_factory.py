"""FastAPI application factory.

This module provides the application factory function for creating
FastAPI app instances with dependency injection.
"""

import importlib
from collections.abc import Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI

from learn_ai_agents.infrastructure.bootstrap.app_container import AppContainer
from learn_ai_agents.infrastructure.inbound.controllers.discovery import discovery
from learn_ai_agents.logging import get_logger
from learn_ai_agents.settings import AppSettings

logger = get_logger(__name__)


def load_callable(import_path: str) -> Callable:
    """Dynamically load a callable from an import path.

    Args:
        import_path: Import path in format 'module.path:function_name'
            e.g., 'learn_ai_agents.infrastructure.inbound.controllers.agents.basic_answer:get_router'

    Returns:
        The loaded callable function.

    Raises:
        ValueError: If import path format is invalid.
        ImportError: If module cannot be imported.
        AttributeError: If function not found in module.
    """
    if ":" not in import_path:
        raise ValueError(f"Invalid import path '{import_path}'. Expected format 'module:function'")

    module_path, function_name = import_path.rsplit(":", 1)
    module = importlib.import_module(module_path)
    return getattr(module, function_name)


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
        logger.info("Building dependency injection container...")

        # Build dependency injection container
        container = await AppContainer.build(settings=app_settings)

        # Initialize dependency injection
        app.state.container = container

        logger.info("✅ Application startup complete")

        try:
            yield
        finally:
            logger.info("🛑 Shutting down application...")

            # Clean up resources
            await container.shutdown()

            logger.info("✅ Application shutdown complete")

    # Create FastAPI app with lifecycle management
    app = FastAPI(
        title="Learn AI Agents",
        description="A didactic project for learning AI agent development with Hexagonal Architecture",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Dynamically register routers from settings
    logger.info("🔌 Registering routers...")

    for use_case_name, use_case_cfg in app_settings.use_cases.items():
        # Skip if no router_factory defined
        if not use_case_cfg.info.router_factory:
            logger.debug(f"⏭️  Skipping {use_case_name} (no router_factory defined)")
            continue

        try:
            # Load the router factory function dynamically
            get_router = load_callable(use_case_cfg.info.router_factory)

            # Get the use case configuration
            cfg = app_settings.resolve_ref(use_case_name, "use_case")

            # Call the factory to get the router and register it
            router = get_router(cfg)
            app.include_router(router)

            logger.info(f"✅ Registered router for use case: {use_case_name}")
        except Exception as e:
            logger.error(f"❌ Failed to register router for {use_case_name}: {e}")
            raise

    logger.info("✅ All routers registered")
    
    # Register discovery router (not in use_cases but always available)
    app.include_router(discovery.router, prefix="/api", tags=["discovery"])
    logger.info("✅ Discovery router registered")
    
    logger.info("✅ Application created successfully")

    return app
