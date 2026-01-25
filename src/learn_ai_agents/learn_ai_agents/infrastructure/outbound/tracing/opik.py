import opik
from opik.integrations.langchain import OpikTracer
from learn_ai_agents.application.outbound_ports.agents.tracing import AgentTracingPort


class OpikAgentTracerAdapter(AgentTracingPort):
    """Opik implementation of the AgentTracingPort."""

    def __init__(self, api_key: str, workspace: str, project_name: str) -> None:
        """Initialize the Opik tracer adapter."""
        opik.configure(
            api_key=api_key,
            workspace=workspace,
        )
        self.project_name = project_name

    def get_tracer(self, thread_id: str) -> OpikTracer:
        """Return the underlying Opik tracer object."""
        opik_tracer = OpikTracer(
            project_name=self.project_name,
            thread_id=thread_id,
        )
        return opik_tracer
