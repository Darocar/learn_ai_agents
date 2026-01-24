"""Application container for dependency injection.

This module provides the main application container that composes all
components, agents, and use cases using dependency injection.
"""

# infrastructure/bootstrap/app_container.py
from dataclasses import dataclass

from learn_ai_agents.logging import get_logger
from learn_ai_agents.settings import AppSettings
from typing_extensions import Self

from .agents_container import AgentsContainer
from .components_container import ComponentsContainer
from .use_cases_container import UseCasesContainer

logger = get_logger(__name__)


@dataclass
class AppContainer:
    """Main application container for dependency injection.

    This container orchestrates the composition of all application layers:
    - Components (LLMs, tools, etc.)
    - Agents (AI processing engines)
    - Use Cases (business logic)

    Attributes:
        settings: The application settings used to build this container.
        components: Container for infrastructure components (LLMs, etc.).
        agents: Container for agent instances.
        use_cases: Container for use case instances.
    """

    settings: AppSettings
    components: ComponentsContainer
    agents: AgentsContainer
    use_cases: UseCasesContainer

    @classmethod
    async def build(cls, settings: AppSettings) -> Self:
        """Build and initialize the complete application container.

        Creates all containers in the correct dependency order:
        components (with databases connected) → agents → use cases.

        Args:
            settings: AppSettings instance to use for building the container.

        Returns:
            Fully initialized AppContainer instance.
        """

        logger.info("🔧 Building application components...")
        components = await ComponentsContainer.create(settings)

        logger.info("🤖 Initializing agents...")
        agents = AgentsContainer.create(settings, components)

        logger.info("📦 Setting up use cases...")
        use_cases = UseCasesContainer.create(settings, agents, components)

        logger.info("✅ Container build complete")
        return cls(settings, components, agents, use_cases)

    async def shutdown(self) -> None:
        """Shutdown the container and dispose of resources.

        Ensures proper cleanup of long-lived resources like LLM clients,
        database connections, etc.
        """
        logger.info("🧹 Cleaning up resources...")
        # make sure to dispose long-lived stuff (LLMs, stores, etc.)
        await self.components.shutdown()
        logger.info("✅ Resources cleaned up")
