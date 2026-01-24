from typing import Protocol, Any


class AgentTracingPort(Protocol):
    """Protocol for agent tracing implementations."""

    def get_tracer(self, thread_id: str) -> Any:
        """Return the underlying framework-specific tracer object."""
        ...
