"""FastAPI application factory.

This module provides the application factory function for creating
FastAPI app instances with dependency injection.
"""

import importlib
import logging
from contextlib import asynccontextmanager
from typing import Callable, Any

from fastapi import FastAPI

from learn_ai_agents.infrastructure.bootstrap.app_container import AppContainer
from learn_ai_agents.infrastructure.inbound.controllers.discovery import discovery
from learn_ai_agents.infrastructure.inbound.exception_handlers import (
    register_exception_handlers,
)
from learn_ai_agents.settings import AppSettings
from learn_ai_agents.logging import get_logger

logger = get_logger(__name__)


def load_callable(import_path: str) -> Callable:
    """Dynamically load a callable from an import path.
    
    Args:
        import_path: Import path in format 'module.path:function_name'
            e.g., 'learn_ai_agents.controllers.robust:get_router'
    
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

    This is the composition root where all configuration and dependency
    injection is wired together. Settings are resolved here and pushed
    into controllers via router factories.

    Args:
        app_settings: AppSettings instance to use for application configuration.

    Returns:
        Configured FastAPI application instance.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Manage application lifecycle (startup and shutdown).

        This context manager handles:
        - Startup: Building the dependency injection container and connecting databases
        - Shutdown: Cleaning up resources (LLM clients, connections, etc.)

        Args:
            app: The FastAPI application instance.

        Yields:
            Control during the application's running state.
        """
        logger.info("🚀 Starting Learn AI Agents application...")
        logger.info("Building dependency injection container...")

        # Build container with the provided settings (compose components→connect databases→agents→use cases)
        container = await AppContainer.build(settings=app_settings)
        app.state.container = container  # store for later access

        logger.info("✅ Application startup complete")

        try:
            yield
        finally:
            logger.info("🛑 Shutting down application...")
            await container.shutdown()  # close clients/resources
            logger.info("✅ Application shutdown complete")

    app = FastAPI(lifespan=lifespan)

    # Register centralized exception handlers
    register_exception_handlers(app)

    # ---- Dynamically register routers from settings ----
    logger.info("🔌 Registering routers...")

    # Discovery router (always included)
    app.include_router(discovery.router)

    # Dynamically register use case routers based on settings configuration
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
            # Re-raise in production to fail fast, or make this configurable
            raise

    logger.info("✅ All routers registered")

    return app
