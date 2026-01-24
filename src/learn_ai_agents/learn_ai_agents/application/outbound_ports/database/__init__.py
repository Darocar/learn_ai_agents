"""Database client ports.

This module defines the port (interface) for database client operations.
"""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class DatabaseClient(Protocol):
    """Port interface for database client operations.

    This protocol defines the contract for database connection management
    and access to the underlying client/engine.
    """

    async def connect(self) -> None:
        """Establish connection to the database.

        Raises:
            ConnectionError: If unable to connect to the database.
        """
        ...

    async def disconnect(self) -> None:
        """Close the database connection.

        This method is idempotent and can be called multiple times safely.
        """
        ...

    def get_engine(self) -> Any:
        """Get the database engine/client instance.

        Returns:
            The active database engine (e.g., AIOEngine for MongoDB with Odmantic).

        Raises:
            RuntimeError: If the client is not connected.
        """
        ...
