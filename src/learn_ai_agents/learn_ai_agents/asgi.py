"""ASGI application entrypoint for production.

This module creates the ASGI application instance used by production
servers (uvicorn, gunicorn, etc.).
"""

import logging

from learn_ai_agents.app_factory import create_app
from learn_ai_agents.logging import get_logger, setup_logging
from learn_ai_agents.settings import AppSettings

# Initialize logging before creating the app
setup_logging(level=logging.INFO, use_colors=True)
logger = get_logger(__name__)

# Production ASGI application instance
# This is only executed when running the server, not during test imports
app = create_app(AppSettings())
