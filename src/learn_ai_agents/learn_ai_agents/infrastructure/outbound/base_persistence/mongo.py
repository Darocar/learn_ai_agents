"""Generic base repository for Odmantic Model-based persistence.

This module provides a generic repository pattern implementation for MongoDB
using Odmantic. It serves as a base class for all concrete repositories.
"""

from typing import Any, Generic, TypeVar

from learn_ai_agents.domain.exceptions import ComponentOperationException
from learn_ai_agents.logging import get_logger
from odmantic import AIOEngine, Model

logger = get_logger(__name__)

TModel = TypeVar("TModel", bound=Model)


class BaseMongoModelRepository(Generic[TModel]):
    """Generic repository for Odmantic Model-based persistence.

    This class provides common CRUD operations for any Odmantic Model.
    It lives in the infrastructure layer and should not be exposed to
    the domain or application layers directly.

    Type Parameters:
        TModel: The Odmantic Model type this repository manages.

    Attributes:
        _engine: The Odmantic AIOEngine for database operations.
        _model_cls: The Odmantic Model class this repository manages.
    """

    def __init__(self, engine: AIOEngine, model_cls: type[TModel]):
        """Initialize the repository.

        Args:
            engine: The Odmantic AIOEngine instance.
            model_cls: The Odmantic Model class to manage.
        """
        self._engine = engine
        self._model_cls = model_cls
        logger.debug(f"Initialized repository for {model_cls.__name__}")

    @property
    def model_cls(self) -> type[TModel]:
        """Get the model class this repository manages.

        Returns:
            The Odmantic Model class.
        """
        return self._model_cls

    async def save_one(self, model: TModel) -> TModel:
        """Save a single model instance to the database.

        Args:
            model: The model instance to save.

        Returns:
            The saved model instance (with updated ID if new).
            
        Raises:
            ComponentOperationException: If database save operation fails.
        """
        try:
            logger.debug(f"Saving {self._model_cls.__name__} to database")
            saved_model = await self._engine.save(model)
            logger.debug(f"Successfully saved {self._model_cls.__name__}")
            return saved_model
        except Exception as e:
            logger.error(f"Failed to save {self._model_cls.__name__}: {e}")
            raise ComponentOperationException(
                component_type="repository",
                message=f"Failed to save {self._model_cls.__name__} to database: {e}",
                details={"model_class": self._model_cls.__name__, "error": str(e)}
            ) from e

    async def save_many(self, models: list[TModel]) -> list[TModel]:
        """Save multiple model instances to the database.

        Args:
            models: List of model instances to save.

        Returns:
            List of saved model instances.
            
        Raises:
            ComponentOperationException: If database save operation fails.
        """
        if not models:
            logger.debug("No models to save")
            return []

        try:
            logger.debug(f"Saving {len(models)} {self._model_cls.__name__} instances")
            saved_models = await self._engine.save_all(models)
            logger.debug(f"Successfully saved {len(saved_models)} instances")
            return saved_models
        except Exception as e:
            logger.error(f"Failed to save {len(models)} {self._model_cls.__name__} instances: {e}")
            raise ComponentOperationException(
                component_type="repository",
                message=f"Failed to save {len(models)} {self._model_cls.__name__} instances to database: {e}",
                details={"model_class": self._model_cls.__name__, "count": len(models), "error": str(e)}
            ) from e

    async def get_by_id(self, id_: str) -> TModel | None:
        """Retrieve a model instance by its ID.

        Args:
            id_: The ID of the model to retrieve.

        Returns:
            The model instance if found, None otherwise.
            
        Raises:
            ComponentOperationException: If database query operation fails.
        """
        try:
            logger.debug(f"Fetching {self._model_cls.__name__} with id={id_}")
            # Odmantic uses the 'id' field internally
            model = await self._engine.find_one(self._model_cls, self._model_cls.id == id_)
            if model:
                logger.debug(f"Found {self._model_cls.__name__} with id={id_}")
            else:
                logger.debug(f"No {self._model_cls.__name__} found with id={id_}")
            return model
        except Exception as e:
            logger.error(f"Failed to fetch {self._model_cls.__name__} with id={id_}: {e}")
            raise ComponentOperationException(
                component_type="repository",
                message=f"Failed to fetch {self._model_cls.__name__} from database: {e}",
                details={"model_class": self._model_cls.__name__, "id": id_, "error": str(e)}
            ) from e

    async def find_by(self, **filters: Any) -> list[TModel]:
        """Find model instances matching the given filters.

        Args:
            **filters: Field-value pairs to filter by.

        Returns:
            List of matching model instances.
            
        Raises:
            ComponentOperationException: If database query operation fails.
        """
        try:
            logger.debug(f"Finding {self._model_cls.__name__} with filters: {filters}")

            # Build query using Odmantic query syntax
            # For simple equality filters, we can use the model fields directly
            query_conditions = []
            for field_name, value in filters.items():
                if hasattr(self._model_cls, field_name):
                    field = getattr(self._model_cls, field_name)
                    query_conditions.append(field == value)

            if query_conditions:
                # Combine conditions with AND
                results = await self._engine.find(self._model_cls, *query_conditions)
            else:
                # No filters - return all
                results = await self._engine.find(self._model_cls)

            logger.debug(f"Found {len(results)} {self._model_cls.__name__} instances")
            return results
        except Exception as e:
            logger.error(f"Failed to find {self._model_cls.__name__} with filters {filters}: {e}")
            raise ComponentOperationException(
                component_type="repository",
                message=f"Failed to query {self._model_cls.__name__} from database: {e}",
                details={"model_class": self._model_cls.__name__, "filters": filters, "error": str(e)}
            ) from e

    async def delete_by_id(self, id_: str) -> bool:
        """Delete a model instance by its ID.

        Args:
            id_: The ID of the model to delete.

        Returns:
            True if deleted, False if not found.
            
        Raises:
            ComponentOperationException: If database delete operation fails.
        """
        try:
            logger.debug(f"Deleting {self._model_cls.__name__} with id={id_}")
            model = await self.get_by_id(id_)
            if model is None:
                logger.debug(f"No {self._model_cls.__name__} found with id={id_} to delete")
                return False

            await self._engine.delete(model)
            logger.debug(f"Successfully deleted {self._model_cls.__name__} with id={id_}")
            return True
        except ComponentOperationException:
            # Re-raise ComponentOperationException from get_by_id
            raise
        except Exception as e:
            logger.error(f"Failed to delete {self._model_cls.__name__} with id={id_}: {e}")
            raise ComponentOperationException(
                component_type="repository",
                message=f"Failed to delete {self._model_cls.__name__} from database: {e}",
                details={"model_class": self._model_cls.__name__, "id": id_, "error": str(e)}
            ) from e

    async def count(self, **filters: Any) -> int:
        """Count model instances matching the given filters.

        Args:
            **filters: Field-value pairs to filter by.

        Returns:
            Number of matching instances.
            
        Raises:
            ComponentOperationException: If database count operation fails.
        """
        try:
            logger.debug(f"Counting {self._model_cls.__name__} with filters: {filters}")

            # Build query using Odmantic query syntax
            query_conditions = []
            for field_name, value in filters.items():
                if hasattr(self._model_cls, field_name):
                    field = getattr(self._model_cls, field_name)
                    query_conditions.append(field == value)

            if query_conditions:
                count = await self._engine.count(self._model_cls, *query_conditions)
            else:
                count = await self._engine.count(self._model_cls)

            logger.debug(f"Count result: {count}")
            return count
        except Exception as e:
            logger.error(f"Failed to count {self._model_cls.__name__} with filters {filters}: {e}")
            raise ComponentOperationException(
                component_type="repository",
                message=f"Failed to count {self._model_cls.__name__} in database: {e}",
                details={"model_class": self._model_cls.__name__, "filters": filters, "error": str(e)}
            ) from e
