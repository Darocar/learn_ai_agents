"""MongoDB Database Adapter with Odmantic Engine.

This module provides the MongoDB implementation of the DatabaseClient port.
It handles connection management and provides access to the Odmantic AIOEngine
for use by repositories and the raw Motor client for components like checkpointers.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from learn_ai_agents.application.outbound_ports.database import DatabaseClient
from learn_ai_agents.domain.exceptions import ComponentConnectionException, ComponentOperationException
from learn_ai_agents.logging import get_logger

logger = get_logger(__name__)


class MongoEngineAdapter(DatabaseClient):
    """MongoDB adapter implementing the DatabaseClient port using Motor + Odmantic.

    This adapter manages async connections to MongoDB and provides:
    - AIOEngine (Odmantic) for repositories
    - Motor client for checkpointers and raw operations

    Attributes:
        uri: MongoDB connection URI.
        database_name: Name of the database to use.
        _motor_client: The Motor async MongoDB client instance (None when disconnected).
        _engine: The Odmantic AIOEngine instance (None when disconnected).
    """

    def __init__(self, uri: str, database_name: str = "learn_ai_agents"):
        """Initialize the MongoDB engine adapter.

        Args:
            uri: MongoDB connection URI (e.g., 'mongodb://user:pass@host:port/db?authSource=admin').
            database_name: Name of the database to use. Defaults to 'learn_ai_agents'.
        """
        self.uri = uri
        self.database_name = database_name
        self._motor_client: AsyncIOMotorClient | None = None
        self._engine: AIOEngine | None = None
        logger.info(f"MongoDB engine adapter initialized for database: {database_name}")

    async def connect(self) -> None:
        """Establish async connection to MongoDB and initialize Odmantic engine.

        Raises:
            ComponentConnectionException: If unable to connect to MongoDB.
        """
        if self._motor_client is not None:
            logger.warning("MongoDB client already connected. Skipping connection.")
            return

        try:
            logger.info("Connecting to MongoDB...")
            self._motor_client = AsyncIOMotorClient(
                self.uri,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
            )
            # Verify connection by pinging the server
            await self._motor_client.admin.command("ping")
            logger.info("✅ Successfully connected to MongoDB")

            # Initialize Odmantic engine
            self._engine = AIOEngine(
                client=self._motor_client,
                database=self.database_name,
            )
            logger.info("✅ Odmantic AIOEngine initialized")

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            self._motor_client = None
            self._engine = None
            raise ComponentConnectionException(
                component_type="database_engine",
                message=f"Failed to connect to MongoDB: {e}",
                details={"adapter": "MongoEngineAdapter", "uri": self.uri, "database": self.database_name, "error": str(e)}
            ) from e

    async def disconnect(self) -> None:
        """Close the MongoDB connection.

        This method is idempotent and can be called multiple times safely.
        
        Raises:
            ComponentOperationException: If an error occurs during disconnection.
        """
        if self._motor_client is None:
            logger.debug("MongoDB client already disconnected.")
            return

        try:
            logger.info("Disconnecting from MongoDB...")
            self._motor_client.close()
            self._motor_client = None
            self._engine = None
            logger.info("✅ Successfully disconnected from MongoDB")
        except Exception as e:
            logger.error(f"Error during MongoDB disconnection: {e}")
            # Still set clients to None even if close fails
            self._motor_client = None
            self._engine = None
            raise ComponentOperationException(
                component_type="database_engine",
                message=f"Error during MongoDB disconnection: {e}",
                details={"adapter": "MongoEngineAdapter", "database": self.database_name, "error": str(e)}
            ) from e

    def get_engine(self) -> AIOEngine:
        """Get the Odmantic AIOEngine instance.

        Returns:
            The active Odmantic AIOEngine for repository operations.

        Raises:
            ComponentOperationException: If the engine is not initialized (not connected).

        Note:
            This engine should be used by repositories for ODM operations.
        """
        if self._engine is None:
            raise ComponentOperationException(
                component_type="database_engine",
                message="MongoDB engine is not initialized. Call connect() first.",
                details={"adapter": "MongoEngineAdapter", "database": self.database_name}
            )
        return self._engine

    def get_motor_client(self) -> AsyncIOMotorClient:
        """Get the raw Motor async MongoDB client instance.

        Returns:
            The active async Motor MongoDB client.

        Raises:
            ComponentOperationException: If the client is not connected.

        Note:
            This client can be used directly by components like LangGraph's
            AsyncMongoDBSaver for checkpointing.
        """
        if self._motor_client is None:
            raise ComponentOperationException(
                component_type="database_engine",
                message="MongoDB client is not connected. Call connect() first.",
                details={"adapter": "MongoEngineAdapter", "database": self.database_name}
            )
        return self._motor_client

    async def __aenter__(self):
        """Async context manager entry - connects to MongoDB."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - disconnects from MongoDB."""
        await self.disconnect()
        return False  # Don't suppress exceptions
