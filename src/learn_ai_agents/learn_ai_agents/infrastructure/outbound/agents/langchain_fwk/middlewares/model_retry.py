import logging
import traceback

from typing import Callable, Dict, Any, Awaitable

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse

from learn_ai_agents.domain.exceptions import LLMCallException

logger = logging.getLogger(__name__)

class ModelRetryMiddleware(AgentMiddleware):
    """Middleware to add retry logic to model requests.

    This middleware intercepts model requests and applies a retry policy
    based on the provided configuration. It retries failed requests according
    to the specified maximum attempts, backoff multiplier, and initial delay.

    Attributes:
        max_attempts: Maximum number of retry attempts.
        backoff_multiplier: Multiplier for exponential backoff.
        initial_delay_ms: Initial delay in milliseconds before the first retry.
    """

    def __init__(self, max_attempts: int, backoff_multiplier: float, initial_delay_ms: int):
        """Initialize the ModelRetryMiddleware with retry policy parameters.

        Args:
            max_attempts: Maximum number of retry attempts.
            backoff_multiplier: Multiplier for exponential backoff.
            initial_delay_ms: Initial delay in milliseconds before the first retry.
        """
        super().__init__()
        self.max_attempts = max_attempts
        self.backoff_multiplier = backoff_multiplier
        self.initial_delay_ms = initial_delay_ms

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        """Wrap the model call with retry logic."""
        for attempt in range(self.max_attempts):
            try:
                return await handler(request)
            except Exception as e:
                traceback_str = traceback.format_exc()
                if attempt == self.max_attempts - 1:
                    raise LLMCallException(
                        agent_component="llm",
                        message="Maximum retry attempts reached for model call.",
                        details={
                            "middleware": "ModelRetryMiddleware",
                            "attempts": self.max_attempts,
                            "error": str(e),
                            "llm_model": request.model,
                        },
                    )
                logger.error(f"Retry {attempt + 1}/{self.max_attempts} after error: {e}")
        
        raise LLMCallException(
            agent_component="llm",
            message="Failed to complete model call after retries.",
            details={"middleware": "ModelRetryMiddleware", "llm_model": request.model},
        )