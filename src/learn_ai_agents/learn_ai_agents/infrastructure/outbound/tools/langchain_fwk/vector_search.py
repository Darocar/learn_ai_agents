"""LangChain Vector Search Tool Adapter.

This module provides a tool for searching character information using
vector similarity search in a Qdrant database. Uses LangChain v1.0
ToolRuntime injection for dynamic document_id configuration.
"""

from typing import Any

from langchain.tools import ToolRuntime, tool, BaseTool

from learn_ai_agents.infrastructure.outbound.agents.langchain_fwk.character_chat.state import VectorSearchContext, State
from learn_ai_agents.application.outbound_ports.agents.tools import ToolPort
from learn_ai_agents.application.outbound_ports.content_indexer.embedders.embedder import EmbedderPort
from learn_ai_agents.application.outbound_ports.content_indexer.repositories.vector_store_repository import (
    VectorStoreRepositoryPort,
)
from learn_ai_agents.logging import get_logger

logger = get_logger(__name__)


class LangChainVectorSearchToolAdapter(ToolPort):
    """Adapter that exposes vector search as a LangChain tool with ToolRuntime injection.

    This tool allows an agent to search for character information using
    semantic similarity search. The document_id is automatically injected
    at runtime via LangChain's ToolRuntime mechanism.

    Attributes:
        name: Tool name visible to the agent.
        description: Tool description for the agent to understand its purpose.
        embedder: Port for generating query embeddings.
        vector_store: Port for vector similarity search.
        _tool: The actual LangChain tool instance.
    """

    name = "vector_search"
    description = (
        "Search for relevant information about a character from their knowledge base. "
        "Use this tool when you need to find specific details, lore, abilities, or "
        "background information about the character to answer user questions accurately."
    )

    def __init__(
        self,
        embedder: EmbedderPort,
        vector_store: VectorStoreRepositoryPort,
        **_: Any,
    ) -> None:
        """Initialize the vector search tool.

        Args:
            embedder: Embedder port for generating query vectors.
            vector_store: Vector store port for similarity search.
            **_: Additional parameters (ignored, for YAML compatibility).
        """
        self.embedder = embedder
        self.vector_store = vector_store

        # Create the tool with ToolRuntime injection
        self._tool = self._create_tool()
        logger.info("Initialized LangChainVectorSearchToolAdapter with ToolRuntime injection")

    def _create_tool(self) -> BaseTool:
        """Create the LangChain tool with ToolRuntime injection.

        Returns:
            LangChain tool configured for vector search with runtime injection.
        """
        embedder = self.embedder
        vector_store = self.vector_store

        @tool
        async def vector_search(
            query: str,
            runtime: ToolRuntime[VectorSearchContext, State],
        ) -> str:
            """Search for relevant information about a character from their knowledge base.

            Use this tool when you need to find specific details, lore, abilities, or
            background information about the character to answer user questions accurately.

            Args:
                query: The search query to find relevant information about the character.
                runtime: Automatically injected by LangGraph with document_id context.

            Returns:
                Formatted string containing search results.
            """
            # Extract document_id from runtime context (automatically injected by LangGraph)
            document_id = runtime.context.document_id

            logger.info(f"Performing vector search for query: {query[:100]}... (document_id: {document_id})")

            # Generate embedding for the query
            query_embeddings = await embedder.embed_texts([query])
            query_vector = query_embeddings[0]

            # Search in the vector store using injected document_id
            results = await vector_store.search_similar(
                document_id=document_id,
                query_vector=query_vector,
                limit=2,
            )

            if not results:
                logger.info("No results found for query")
                return "No relevant information found for this query."

            # Format results for the agent
            formatted_results = []
            for idx, result in enumerate(results, 1):
                content = result.get("content", "")
                character_name = result.get("character_name", "Unknown")
                formatted_results.append(f"[Result {idx}] (Character: {character_name})\n{content}\n")

            output = "\n".join(formatted_results)
            logger.info(f"Found {len(results)} results")
            return output

        return vector_search

    def get_tool(self) -> BaseTool:
        """Return the LangChain tool with ToolRuntime injection.

        Returns:
            LangChain BaseTool configured for vector search with runtime injection.
        """
        return self._tool
