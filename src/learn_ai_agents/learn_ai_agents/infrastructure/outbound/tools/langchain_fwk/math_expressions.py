# learn_ai_agents/infrastructure/outbound/tools/langchain_fwk/math_expression.py

from typing import Any

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool, BaseTool

from learn_ai_agents.application.outbound_ports.agents.tools import ToolPort
from learn_ai_agents.infrastructure.outbound.tools.base.math_expressions import calculate_math_expression


class MathExpressionInput(BaseModel):
    math_expression: str = Field(
        ...,
        description="A mathematical expression to evaluate, e.g. '2 + 2 * 3'.",
    )


class LangChainMathExpressionToolAdapter(ToolPort):
    """Use this tool to evaluate mathematical expressions. Only numbers are allowed and operations. String placeholders are not supported."""

    name = "math_expression"
    description = "Evaluate a mathematical expression and return the numeric result."

    def __init__(self, **_: Any) -> None:
        # Accept **params from YAML even if you don't use them yet
        ...

    def get_tool(self) -> BaseTool:
        """Return a LangChain StructuredTool instance."""
        return StructuredTool.from_function(
            func=calculate_math_expression,
            name=self.name,
            description=self.description,
            args_schema=MathExpressionInput,
        )
