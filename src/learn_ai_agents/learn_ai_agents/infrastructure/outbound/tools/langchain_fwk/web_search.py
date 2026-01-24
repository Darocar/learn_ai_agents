# learn_ai_agents/infrastructure/outbound/tools/langchain_fwk/math_expression.py

from typing import Any

from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_community.tools import DuckDuckGoSearchResults

from learn_ai_agents.application.outbound_ports.agents.tools import ToolPort


class WebSearchInput(BaseModel):
    query: str = Field(
        ...,
        description="A search query string to search the web, e.g. 'latest AI news'.",
    )


class LangChainWebSearchToolAdapter(ToolPort):
    """Adapter that exposes 'web_search' as a LangChain tool."""

    name = "duckduckgo_results_json"
    description = "Search the web using DuckDuckGo search engine."

    def __init__(self, **_: Any) -> None:
        # Accept **params from YAML even if you don't use them yet
        ...

    def get_tool(self) -> BaseTool:
        """Return a LangChain StructuredTool instance."""
        return DuckDuckGoSearchResults()
