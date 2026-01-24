# learn_ai_agents/infrastructure/outbound/tools/langchain_fwk/age_calculator.py

from typing import Any

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool, BaseTool

from learn_ai_agents.application.outbound_ports.agents.tools import ToolPort
from learn_ai_agents.infrastructure.outbound.tools.base.age_calculator import calculate_age


class AgeCalculatorInput(BaseModel):
    birth_date: str = Field(
        ...,
        description="Birth date in yyyy-mm-dd format, e.g. '1990-05-15'.",
    )


class LangChainAgeCalculatorToolAdapter(ToolPort):
    """Adapter that exposes 'age_calculator' as a LangChain tool."""

    name = "age_calculator"
    description = "Calculate a person's age based on their birth date. Returns the age in years."

    def __init__(self, **_: Any) -> None:
        # Accept **params from YAML even if you don't use them yet
        ...

    def get_tool(self) -> BaseTool:
        """Return a LangChain StructuredTool instance."""
        return StructuredTool.from_function(
            func=calculate_age,
            name=self.name,
            description=self.description,
            args_schema=AgeCalculatorInput,
        )
