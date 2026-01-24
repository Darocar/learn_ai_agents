"""PyMongo Async Database Adapter.

This module provides the MongoDB implementation using PyMongo's AsyncMongoClient.
It's specifically designed for components that require PyMongo's async client,
such as LangGraph's AsyncMongoDBSaver for checkpointing.
"""

from pymongo import AsyncMongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from learn_ai_agents.application.outbound_ports.database import DatabaseClient
from learn_ai_agents.domain.exceptions import ComponentConnectionException, ComponentOperationException
from learn_ai_agents.logging import get_logger

logger = get_logger(__name__)


class PyMongoAsyncAdapter(DatabaseClient):
    """PyMongo async adapter implementing the DatabaseClient port.

    This adapter manages async connections to MongoDB using PyMongo's AsyncMongoClient.
    It's designed for components that specifically require PyMongo's client type,
    such as LangGraph's checkpointing system.

    Note: Use MongoEngineAdapter for Odmantic-based repositories.

    Attributes:
        uri: MongoDB connection URI.
        database_name: Name of the database to use.
        _client: The PyMongo AsyncMongoClient instance (None when disconnected).
    """

    def __init__(self, uri: str, database_name: str = "learn_ai_agents"):
        """Initialize the PyMongo async adapter.

        Args:
            uri: MongoDB connection URI (e.g., 'mongodb://user:pass@host:port/db?authSource=admin').
            database_name: Name of the database to use. Defaults to 'learn_ai_agents'.
        """
        self.uri = uri
        self.database_name = database_name
        self._client: AsyncMongoClient | None = None
        logger.info(f"PyMongo async adapter initialized for database: {database_name}")

    async def connect(self) -> None:
        """Establish async connection to MongoDB.

        Raises:
            ComponentConnectionException: If unable to connect to MongoDB.
        """
        if self._client is not None:
            logger.warning("PyMongo client already connected. Skipping connection.")
            return

        try:
            logger.info("Connecting to MongoDB (PyMongo)...")
            self._client = AsyncMongoClient(
                self.uri,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
            )
            # Verify connection by pinging the server
            await self._client.admin.command("ping")
            logger.info("✅ Successfully connected to MongoDB (PyMongo)")

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"❌ Failed to connect to MongoDB (PyMongo): {e}")
            self._client = None
            raise ComponentConnectionException(
                component_type="database_engine",
                message=f"Failed to connect to MongoDB (PyMongo): {e}",
                details={"adapter": "PyMongoAsyncAdapter", "uri": self.uri, "database": self.database_name, "error": str(e)}
            ) from e

    async def disconnect(self) -> None:
        """Close the MongoDB connection.

        This method is idempotent and can be called multiple times safely.
        
        Raises:
            ComponentOperationException: If an error occurs during disconnection.
        """
        if self._client is None:
            logger.debug("PyMongo client already disconnected.")
            return

        try:
            logger.info("Disconnecting from MongoDB (PyMongo)...")
            await self._client.close()
            self._client = None
            logger.info("✅ Successfully disconnected from MongoDB (PyMongo)")
        except Exception as e:
            logger.error(f"Error during PyMongo disconnection: {e}")
            # Still set client to None even if close fails
            self._client = None
            raise ComponentOperationException(
                component_type="database_engine",
                message=f"Error during PyMongo disconnection: {e}",
                details={"adapter": "PyMongoAsyncAdapter", "database": self.database_name, "error": str(e)}
            ) from e

    def get_client(self) -> AsyncMongoClient:
        """Get the PyMongo AsyncMongoClient instance.

        Returns:
            The active PyMongo AsyncMongoClient.

        Raises:
            ComponentOperationException: If the client is not connected.

        Note:
            This client is specifically for components that require PyMongo's
            AsyncMongoClient type, such as LangGraph's AsyncMongoDBSaver.
        """
        if self._client is None:
            raise ComponentOperationException(
                component_type="database_engine",
                message="PyMongo client is not connected. Call connect() first.",
                details={"adapter": "PyMongoAsyncAdapter", "database": self.database_name}
            )
        return self._client

    async def __aenter__(self):
        """Async context manager entry - connects to MongoDB."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - disconnects from MongoDB."""
        await self.disconnect()
        return False  # Don't suppress exceptions
