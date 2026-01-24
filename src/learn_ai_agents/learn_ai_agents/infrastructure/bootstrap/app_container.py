"""Application dependency injection container."""

import os

from learn_ai_agents.application.use_cases.basic_answer.basic_answer import BasicAnswerUseCase
from learn_ai_agents.infrastructure.outbound.agents.basic_answer import LangChainBasicAnswerAgent
from learn_ai_agents.infrastructure.outbound.llms.groq import GroqChatModelProvider
from learn_ai_agents.logging import get_logger
from learn_ai_agents.settings import AppSettings

logger = get_logger(__name__)


class AppContainer:
    """Container for application dependencies."""

    def __init__(self, settings: AppSettings):
        """Initialize container with settings.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self._basic_answer_use_case: BasicAnswerUseCase | None = None

    def get_basic_answer_use_case(self) -> BasicAnswerUseCase:
        """Build and return BasicAnswerUseCase with all dependencies.

        Returns:
            Configured use case instance
        """
        if self._basic_answer_use_case is None:
            logger.info("🔧 Building BasicAnswerUseCase with dependencies...")

            # Get API key from environment
            groq_api_key = os.getenv("GROQ_API_KEY")
            if not groq_api_key:
                raise ValueError("GROQ_API_KEY environment variable not set")

            # Build outbound adapters
            llm_provider = GroqChatModelProvider(
                api_key=groq_api_key,
                model_name="llama-3.3-70b-versatile",
                temperature=0.7,
            )

            agent_engine = LangChainBasicAnswerAgent(chat_model_provider=llm_provider)

            # Build use case with injected dependencies
            self._basic_answer_use_case = BasicAnswerUseCase(agent=agent_engine)

            logger.info("✅ BasicAnswerUseCase built successfully")

        return self._basic_answer_use_case
