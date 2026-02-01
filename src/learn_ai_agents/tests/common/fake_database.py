"""Fake database adapters for testing.

This module provides in-memory fake implementations of database clients.
Real repositories can use these fake engines without any changes.
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union
from copy import deepcopy

import yaml


class FakeEngine:
    """Fake Odmantic AIOEngine for testing.
    
    This mimics the interface expected by MongoEngine repositories.
    Real repositories can use this fake engine without any changes,
    as it provides the same interface as Odmantic's AIOEngine.
    
    The fake engine stores data in-memory and supports:
    - save(model) / save_all(models)
    - find(model_cls, *conditions)
    - find_one(model_cls, *conditions)
    - delete(model)
    - count(model_cls, *conditions)
    """
    
    def __init__(self):
        """Initialize fake engine with in-memory storage."""
        self._collections: Dict[str, Dict[str, Any]] = {}
    
    async def save(self, instance: Any) -> Any:
        """Save a model instance (mimics AIOEngine.save).
        
        Args:
            instance: Model instance to save.
            
        Returns:
            The saved instance (with ID set if it was None).
        """
        collection = type(instance).__name__
        if collection not in self._collections:
            self._collections[collection] = {}
        
        # Generate ID if not present
        if not hasattr(instance, 'id') or instance.id is None:
            instance.id = str(len(self._collections[collection]) + 1)
        
        doc_id = instance.id
        self._collections[collection][doc_id] = deepcopy(instance)
        return instance
    
    async def save_all(self, instances: List[Any]) -> List[Any]:
        """Save multiple model instances (mimics AIOEngine.save_all).
        
        Args:
            instances: List of model instances to save.
            
        Returns:
            List of saved instances.
        """
        saved = []
        for instance in instances:
            saved.append(await self.save(instance))
        return saved
    
    async def find(self, model_cls: type, *conditions) -> List[Any]:
        """Find model instances matching conditions (mimics AIOEngine.find).
        
        Args:
            model_cls: The model class to search for.
            *conditions: Query conditions (e.g., Model.field == value).
            
        Returns:
            List of matching model instances.
        """
        collection = model_cls.__name__
        if collection not in self._collections:
            return []
        
        all_instances = list(self._collections[collection].values())
        
        # If no conditions, return all
        if not conditions:
            return all_instances
        
        # Filter by conditions
        results = []
        for instance in all_instances:
            if self._matches_conditions(instance, conditions):
                results.append(instance)
        
        return results
    
    async def find_one(self, model_cls: type, *conditions) -> Optional[Any]:
        """Find one model instance matching conditions (mimics AIOEngine.find_one).
        
        Args:
            model_cls: The model class to search for.
            *conditions: Query conditions (e.g., Model.field == value).
            
        Returns:
            First matching instance or None.
        """
        results = await self.find(model_cls, *conditions)
        return results[0] if results else None
    
    async def delete(self, instance: Any) -> None:
        """Delete a model instance (mimics AIOEngine.delete).
        
        Args:
            instance: Model instance to delete.
        """
        collection = type(instance).__name__
        doc_id = getattr(instance, 'id', None)
        if collection in self._collections and doc_id in self._collections[collection]:
            del self._collections[collection][doc_id]
    
    async def count(self, model_cls: type, *conditions) -> int:
        """Count model instances matching conditions (mimics AIOEngine.count).
        
        Args:
            model_cls: The model class to count.
            *conditions: Query conditions (e.g., Model.field == value).
            
        Returns:
            Number of matching instances.
        """
        results = await self.find(model_cls, *conditions)
        return len(results)
    
    def _matches_conditions(self, instance: Any, conditions: tuple) -> bool:
        """Check if an instance matches all query conditions.
        
        Args:
            instance: Model instance to check.
            conditions: Tuple of query conditions.
            
        Returns:
            True if all conditions match, False otherwise.
        """
        for condition in conditions:
            # Extract field name and value from condition
            # Odmantic conditions are typically like: Model.field == value
            # We need to evaluate them against the instance
            if hasattr(condition, 'left') and hasattr(condition, 'right'):
                # Binary comparison (field == value)
                field_name = condition.left.key_name if hasattr(condition.left, 'key_name') else None
                expected_value = condition.right
                
                if field_name:
                    actual_value = getattr(instance, field_name, None)
                    if actual_value != expected_value:
                        return False
            else:
                # For simple conditions, try to evaluate directly
                # This is a fallback for cases where we can't parse the condition
                try:
                    # Try to get field name from string representation
                    condition_str = str(condition)
                    if '==' in condition_str:
                        # Simple equality check
                        parts = condition_str.split('==')
                        if len(parts) == 2:
                            field_name = parts[0].strip().split('.')[-1]
                            expected_value = parts[1].strip().strip("'\"")
                            actual_value = getattr(instance, field_name, None)
                            if str(actual_value) != expected_value:
                                return False
                except Exception:
                    # If we can't parse the condition, skip it
                    pass
        
        return True
    
    def load_from_file(self, file_path: Union[str, Path], model_cls: Type) -> None:
        """Load model instances from a JSON file.
        
        Expected JSON format:
        - Single dict: {"field1": "value1", ...} → one model instance
        - List of dicts: [{...}, {...}] → multiple model instances
        
        Handles MongoDB special fields like $oid and $date.
        
        Args:
            file_path: Path to JSON file with model data.
            model_cls: The model class to instantiate.
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        def clean_dict(d: dict) -> dict:
            """Remove MongoDB special fields and handle special types."""
            cleaned = {}
            for key, value in d.items():
                if key == '_id':
                    continue
                if isinstance(value, dict):
                    if '$oid' in value:
                        cleaned[key] = value['$oid']
                    elif '$date' in value:
                        cleaned[key] = value['$date']
                    else:
                        cleaned[key] = value
                else:
                    cleaned[key] = value
            return cleaned
        
        # Process data
        if isinstance(data, list):
            instances = [model_cls(**clean_dict(item)) for item in data]
        else:
            instances = [model_cls(**clean_dict(data))]
        
        # Save all instances
        asyncio.run(self.save_all(instances))


class FakeMotorClient:
    """Fake Motor AsyncIOMotorClient for testing.
    
    This mimics the interface expected by components that use Motor directly.
    """
    
    def __init__(self, uri: str = "fake://localhost", database_name: str = "test_db", **kwargs):
        """Initialize fake Motor client.
        
        Args:
            uri: Fake connection URI (ignored).
            database_name: Name of the database to use.
            **kwargs: Additional arguments (ignored).
        """
        self.uri = uri
        self.database_name = database_name
        self._databases: Dict[str, Any] = {}
    
    def __getitem__(self, name: str) -> Dict[str, Any]:
        """Get a fake database."""
        if name not in self._databases:
            self._databases[name] = {}
        return self._databases[name]
    
    def get_database(self, name: str) -> Dict[str, Any]:
        """Get a fake database."""
        return self[name]
    
    def close(self) -> None:
        """Fake close operation."""
        pass
    
    @property
    def admin(self):
        """Fake admin interface."""
        class FakeAdmin:
            async def command(self, cmd: str):
                return {"ok": 1}
        return FakeAdmin()


class FakePyMongoClient:
    """Fake PyMongo AsyncMongoClient for testing.
    
    This mimics the interface expected by LangGraph's AsyncMongoDBSaver.
    """
    
    def __init__(self, uri: str = "fake://localhost", database_name: str = "test_db", **kwargs):
        """Initialize fake PyMongo client.
        
        Args:
            uri: Fake connection URI (ignored).
            database_name: Name of the database to use.
            **kwargs: Additional arguments (ignored).
        """
        self.uri = uri
        self.database_name = database_name
        self._databases: Dict[str, Any] = {}
    
    def __getitem__(self, name: str) -> Dict[str, Any]:
        """Get a fake database."""
        if name not in self._databases:
            self._databases[name] = {}
        return self._databases[name]
    
    async def close(self) -> None:
        """Fake close operation."""
        pass
    
    @property
    def admin(self):
        """Fake admin interface."""
        class FakeAdmin:
            async def command(self, cmd: str):
                return {"ok": 1}
        return FakeAdmin()


class FakeDatabaseClient:
    """Fake DatabaseClient adapter for testing.
    
    Replaces both MongoEngineAdapter and PyMongoAsyncAdapter.
    Returns fake engines/clients that work in-memory without database connections.
    
    Real repositories can use this adapter's engines without any changes!
    """
    
    def __init__(self, uri: str = "fake://localhost", database_name: str = "test_db", **kwargs):
        """Initialize fake database client.
        
        Args:
            uri: Fake connection URI (ignored).
            database_name: Name of the database to use.
            **kwargs: Additional arguments (ignored).
        """
        self.uri = uri
        self.database_name = database_name
        self._connected = False
        self._engine = FakeEngine()
        self._motor_client = FakeMotorClient(uri, database_name)
        self._pymongo_client = FakePyMongoClient(uri, database_name)
    
    async def connect(self) -> None:
        """Fake connect operation - no actual connection made."""
        self._connected = True
    
    async def disconnect(self) -> None:
        """Fake disconnect operation."""
        self._connected = False
    
    def get_engine(self) -> FakeEngine:
        """Get the fake Odmantic engine.
        
        Real repositories use this engine and work without changes!
        
        Returns:
            FakeEngine instance for use by repositories.
        """
        return self._engine
    
    def get_motor_client(self) -> FakeMotorClient:
        """Get the fake Motor client.
        
        Returns:
            FakeMotorClient instance for components needing Motor.
        """
        return self._motor_client
    
    def get_client(self) -> FakePyMongoClient:
        """Get the fake PyMongo client.
        
        Returns:
            FakePyMongoClient instance for components needing PyMongo.
        """
        return self._pymongo_client
    
    def load_from_file(self, file_path: Union[str, Path], model_cls: Type) -> None:
        """Load model instances from a JSON file into the fake engine.
        
        Expected JSON format:
        - Single dict: {"field1": "value1", ...} → one model instance
        - List of dicts: [{...}, {...}] → multiple model instances
        
        Args:
            file_path: Path to JSON file with model data.
            model_cls: The model class to instantiate.
        """
        self._engine.load_from_file(file_path, model_cls)
