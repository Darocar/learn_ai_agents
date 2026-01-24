"""Main entry point for the Learn AI Agents application.

This module provides the CLI runner for starting the development server.
"""

import logging

import uvicorn

from learn_ai_agents.logging import get_logger, setup_logging

# Initialize logging first thing
setup_logging(level=logging.INFO, use_colors=True)
logger = get_logger(__name__)


def run() -> None:
    """Run the FastAPI application server.

    Starts the Uvicorn server with hot-reload enabled for development.
    The server runs on all interfaces (0.0.0.0) on port 8000.
    """
    logger.info("Starting server on http://0.0.0.0:8000")
    # Run by module path so --reload works
    uvicorn.run(
        "learn_ai_agents.asgi:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    run()
