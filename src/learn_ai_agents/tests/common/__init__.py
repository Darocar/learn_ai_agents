"""Test common utilities and fake implementations.

This package provides:
- Fake adapters for external services (database, LLM, vector store, tracer)
- Base test case with helper methods
- Test utilities

The fake adapters replace real connection classes:
- FakeDatabaseClient → MongoEngineAdapter/PyMongoAsyncAdapter
- FakeChatModelProvider → LangchainGroqChatModelAdapter
- FakeVectorStoreAdapter → QdrantVectorStoreRepository
- FakeAgentTracer → OpikAgentTracerAdapter
"""

# Fake adapters (replacements for real connection classes)
from .fake_database import FakeDatabaseClient, FakeEngine, FakeMotorClient, FakePyMongoClient
from .fake_llm_adapter import FakeChatModelProvider
from .fake_vector_store import FakeVectorStoreAdapter
from .fake_tracer import FakeAgentTracer

# Test helpers
from .test_helpers import patch_helper_generation

__all__ = [
    # Fake adapters
    "FakeDatabaseClient",
    "FakeEngine",
    "FakeMotorClient",
    "FakePyMongoClient",
    "FakeChatModelProvider",
    "FakeVectorStoreAdapter",
    "FakeAgentTracer",
    # Helpers
    "patch_helper_generation",
]
