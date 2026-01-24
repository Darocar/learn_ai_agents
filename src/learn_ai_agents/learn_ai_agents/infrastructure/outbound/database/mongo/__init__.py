"""MongoDB database adapters.

This module provides database adapters for MongoDB using different clients:
- MongoEngineAdapter: Uses Motor + Odmantic for ODM operations
- PyMongoAsyncAdapter: Uses PyMongo's AsyncMongoClient for components requiring it
"""

from .mongo_engine import MongoEngineAdapter
from .pymongo_async import PyMongoAsyncAdapter

__all__ = [
    "MongoEngineAdapter",
    "PyMongoAsyncAdapter",
]
