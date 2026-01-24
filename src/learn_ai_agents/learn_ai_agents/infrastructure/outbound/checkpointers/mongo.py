"""MongoDB checkpointer adapter for LangGraph.

This module provides a MongoDB implementation of checkpointing for LangGraph agents.
"""

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.mongodb.aio import AsyncMongoDBSaver
from learn_ai_agents.application.outbound_ports.database import DatabaseClient
from learn_ai_agents.logging import get_logger

from . import BaseLangChainCheckpointerAdapter

logger = get_logger(__name__)


class MongoCheckpointerAdapter(BaseLangChainCheckpointerAdapter):
    """MongoDB checkpointer adapter for LangGraph agents.

    This adapter wraps the AsyncMongoDBSaver to provide a consistent interface
    for checkpointing in LangGraph agents using MongoDB persistence.
    """

    @staticmethod
    def build(**kwargs) -> BaseCheckpointSaver:
        """Factory method to build the MongoDB checkpointer.

        Args:
            **kwargs: Configuration parameters including:
                - database: DatabaseClient instance (PyMongoAsyncAdapter).
                - db_name: Name of the database to use for checkpoints.
                - checkpoint_collection_name: Name of the collection to store checkpoints.

        Returns:
            BaseCheckpointSaver: AsyncMongoDBSaver instance ready to use.
        """
        database = kwargs.get("database")
        db_name = kwargs.get("db_name")
        checkpoint_collection_name = kwargs.get("checkpoint_collection_name")

        if not all([database, db_name, checkpoint_collection_name]):
            raise ValueError("database, db_name, and checkpoint_collection_name are required")

        if not isinstance(database, DatabaseClient):
            raise TypeError(f"database must be a DatabaseClient instance, got {type(database)}")

        logger.info(f"Creating MongoDB checkpointer for {db_name}.{checkpoint_collection_name}")

        # Get the PyMongo async client from the database adapter
        pymongo_client = database.get_client()  # type: ignore

        checkpointer = AsyncMongoDBSaver(
            client=pymongo_client,
            db_name=db_name,  # type: ignore
            checkpoint_collection_name=checkpoint_collection_name,  # type: ignore
        )
        logger.debug("MongoDB checkpointer created successfully")
        return checkpointer
