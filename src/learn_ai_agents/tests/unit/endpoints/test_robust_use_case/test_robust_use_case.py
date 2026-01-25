"""Tests for the robust agent endpoint with pre-loaded fake data.

This module demonstrates the robust testing pattern where:
1. We patch adapter classes (not repositories) with fake implementations
2. We pre-load data into fake databases before making API calls
3. We use AsyncClient with the real FastAPI app
4. We use test settings merged with defaults

Pattern:
    - Patch MongoEngineAdapter → FakeDatabaseClient
    - Patch LangchainGroqChatModelAdapter → FakeChatModelProvider
    - Pre-load documents/chunks into fake engine using repository models
    - Pre-configure LLM responses
    - Make API calls with AsyncClient
    - Assert results
"""

import os
from datetime import datetime
from unittest.mock import patch
from asgi_lifespan import LifespanManager
from httpx import AsyncClient, ASGITransport
from langchain_core.messages import AIMessage
import groq

from learn_ai_agents.app_factory import create_app
from learn_ai_agents.infrastructure.bootstrap.components_container import (
    ComponentsContainer,
)
from learn_ai_agents.infrastructure.outbound.content_indexer.repositories.documents.models import (
    DocumentModel,
)
from learn_ai_agents.infrastructure.outbound.content_indexer.repositories.chunks.models import (
    ChunkModel,
)
from learn_ai_agents.settings import AppSettings
from learn_ai_agents.domain.exceptions import (
    ComponentOperationException,
    AgentExecutionException,
)
from tests.common.fake_vector_store import FakeVectorStoreAdapter
from tests.unit.endpoints.base_test import EndpointBaseTestCase


class TestRobustEndpoint(EndpointBaseTestCase):
    """Test robust agent endpoint with pre-loaded fake data."""

    async def asyncSetUp(self):
        """Set up test fixtures and load test data."""
        await super().asyncSetUp()

        # Get paths to test data files (relative to test_dir)
        self.llm_response_file = "data/success_call/llm_response.json"
        self.vector_chunks_file = "data/success_call/vector_chunks.json"

    async def asyncTearDown(self):
        """Clean up test resources."""
        await super().asyncTearDown()

    async def test_ainvoke_with_preloaded_data(self):
        """Test /ainvoke endpoint with pre-loaded documents and chunks.

        This is the SUCCESS test case - uses data from success_call folder.

        This test demonstrates:
        1. Getting test settings (only test settings, no merge with global YAML)
        2. Creating the app with test settings
        3. Pre-loading data into fake database
        4. Configuring fake LLM responses from success_call/llm_response.json
        5. Making API call with AsyncClient
        6. Asserting results
        """

        # 1. Patch helpers for deterministic UUIDs/timestamps
        with self.patch_app_helpers():
            # 2. Get test settings (includes fake adapter configurations) and create app
            settings = self.get_settings()
            app = create_app(app_settings=AppSettings(**settings))

            # 3. Use LifespanManager to run app lifespan (builds AppContainer, sets app.state.container)
            async with LifespanManager(app):
                # Now it's safe to access app.state.container
                app_container = app.state.container  # AppContainer
                components = app_container.components  # ComponentsContainer

                # 4. Load LLM responses from success_call folder
                llm_adapter = components.get("llms.langchain.groq.default")
                llm_adapter._load_from_file(
                    self.test_dir + "/data/success_call/llm_response.json"
                )

                # 5. Pre-load data into fake vector store
                vector_store = components.get(
                    "vector_store_repository.qdrant.store.default"
                )
                assert isinstance(vector_store, FakeVectorStoreAdapter)
                await vector_store.load_from_file(
                    self.test_dir + "/" + self.vector_chunks_file
                )

                # 6. Create request data
                request_data = {
                    "message": "Tell me about your background and past",
                    "character_name": "Astarion",
                    "config": {
                        "conversation_id": "test-conv-001",
                    },
                    "document_id": "astarion_wiki",
                }

                # 7. Create HTTP client *inside* the same lifespan
                transport = ASGITransport(app=app)
                async with AsyncClient(
                    transport=transport, base_url="http://testserver"
                ) as client:
                    # 8. Make API call
                    response = await client.post(
                        "/07_robust/ainvoke", json=request_data
                    )

                    # 9. Assert results
                    self.assertEqual(response.status_code, 200)
                    result = response.json()

                    # Assert using snapshot comparison (stores in expected_data)
                    expected_dir = self.prepare_expected_data_dir()
                    self.assert_objects(
                        expected_dir, "response", [result], forced=False
                    )

    async def test_ainvoke_with_api_connection_error(self):
        """Test /ainvoke endpoint when Groq API returns APIConnectionError.

        This test simulates a network failure scenario where the Groq API
        server cannot be reached. The test verifies that:
        1. The fake LLM adapter correctly raises groq.APIConnectionError
        2. The error propagates properly through the application
        3. The endpoint returns appropriate error response
        """

        # 1. Patch helpers for deterministic UUIDs/timestamps
        with self.patch_app_helpers():
            # 2. Get test settings and create app
            settings = self.get_settings()
            app = create_app(app_settings=AppSettings(**settings))

            # 3. Use LifespanManager to run app lifespan
            async with LifespanManager(app):
                app_container = app.state.container
                components = app_container.components

                # 4. Configure LLM adapter to simulate APIConnectionError
                # This uses the api_connection_error/llm_response.json file
                llm_adapter = components.get("llms.langchain.groq.default")
                llm_adapter._load_from_file(
                    self.test_dir + "/data/api_connection_error/llm_response.json"
                )

                # 5. Create request data
                request_data = {
                    "message": "Tell me about your background and past",
                    "character_name": "Astarion",
                    "config": {
                        "conversation_id": "test-conv-002",
                    },
                    "document_id": "astarion_wiki",
                }

                # 6. Make API call and expect error
                transport = ASGITransport(app=app)
                async with AsyncClient(
                    transport=transport, base_url="http://testserver"
                ) as client:
                    # The endpoint should handle the error gracefully
                    # (or let it propagate - verify based on your error handling)
                    response = await client.post(
                        "/07_robust/ainvoke", json=request_data
                    )
                    # If your app catches and returns error response:
                    result = response.json()

                    # Assert using snapshot comparison
                    expected_dir = self.prepare_expected_data_dir()
                    self.assert_objects(
                        expected_dir, "response", [result], forced=False
                    )

    async def test_ainvoke_with_authentication_error(self):
        """Test /ainvoke endpoint when Groq API returns 401 AuthenticationError.

        This test simulates an authentication failure scenario where the
        API key is invalid. The test verifies that:
        1. The fake LLM adapter correctly raises groq.AuthenticationError
        2. The error includes status_code 401
        3. The error propagates or is handled appropriately
        """

        # 1. Patch helpers for deterministic UUIDs/timestamps
        with self.patch_app_helpers():
            # 2. Get test settings and create app
            settings = self.get_settings()
            app = create_app(app_settings=AppSettings(**settings))

            # 3. Use LifespanManager to run app lifespan
            async with LifespanManager(app):
                app_container = app.state.container
                components = app_container.components

                # 4. Configure LLM adapter to simulate AuthenticationError
                # This uses the authentication_error/llm_response.json file
                llm_adapter = components.get("llms.langchain.groq.default")
                llm_adapter._load_from_file(
                    self.test_dir + "/data/authentication_error/llm_response.json"
                )

                # 5. Create request data
                request_data = {
                    "message": "Tell me about your background and past",
                    "character_name": "Astarion",
                    "config": {
                        "conversation_id": "test-conv-003",
                    },
                    "document_id": "astarion_wiki",
                }

                # 6. Make API call and expect authentication error
                transport = ASGITransport(app=app)
                async with AsyncClient(
                    transport=transport, base_url="http://testserver"
                ) as client:
                    response = await client.post(
                        "/07_robust/ainvoke", json=request_data
                    )
                    # If your app catches and returns error response:
                    result = response.json()

                    # Assert using snapshot comparison
                    expected_dir = self.prepare_expected_data_dir()
                    self.assert_objects(
                        expected_dir, "response", [result], forced=False
                    )

    async def test_ainvoke_with_qdrant_connection_error(self):
        """Test /ainvoke endpoint when Qdrant vector store has connection issues.

        This test simulates a Qdrant database connection problem. The test verifies that:
        1. The fake vector store correctly raises ComponentOperationException
        2. The tool (vector_search) encounters the error when trying to search
        3. The tool retry policy is exhausted (max_retries: 2 = 3 total attempts)
        4. The error is handled appropriately by the application

        Note: The error is set once and will be raised on EVERY tool invocation,
        simulating a persistent connection failure that exhausts all retry attempts.
        """

        # 1. Patch helpers for deterministic UUIDs/timestamps
        with self.patch_app_helpers():
            # 2. Get test settings and create app
            settings = self.get_settings()
            app = create_app(app_settings=AppSettings(**settings))

            # 3. Use LifespanManager to run app lifespan
            async with LifespanManager(app):
                app_container = app.state.container
                components = app_container.components

                # 4. Load LLM responses (normal flow - will call vector_search tool)
                llm_adapter = components.get("llms.langchain.groq.default")
                llm_adapter._load_from_file(
                    self.test_dir + "/data/qdrant_connection_error/llm_response.json"
                )

                # 5. Configure vector store to simulate persistent connection error
                # This error will be raised on every search attempt (initial + retries)
                # Tool retry policy: max_retries: 2 → 3 total attempts before giving up
                vector_store = components.get(
                    "vector_store_repository.qdrant.store.default"
                )
                assert isinstance(vector_store, FakeVectorStoreAdapter)

                # Simulate Qdrant connection error that persists across all retry attempts
                # Skip the error for get_personality() so only search_similar() fails
                error_to_raise = ComponentOperationException(
                    component_type="vector_store",
                    message="Simulated Qdrant connection error: Could not connect to database",
                )
                vector_store.set_error(error_to_raise, skip_for_personality=True)
                print(f"🔴 TEST: Set error on vector_store: {error_to_raise}")
                print(
                    f"🔴 TEST: vector_store._error_to_raise = {vector_store._error_to_raise}"
                )
                print(
                    f"🔴 TEST: skip_for_personality = {vector_store._skip_error_for_personality}"
                )

                # 6. Create request data
                request_data = {
                    "message": "Tell me about your background and past",
                    "character_name": "Astarion",
                    "config": {
                        "conversation_id": "test-conv-004",
                    },
                    "document_id": "astarion_wiki",
                }

                # 7. Make API call and expect error response
                # The ComponentOperationException from vector_store gets wrapped
                # by the agent into an AgentExecutionException, which is then
                # caught by FastAPI exception handler and returned as HTTP 503
                transport = ASGITransport(app=app)
                async with AsyncClient(
                    transport=transport, base_url="http://testserver"
                ) as client:
                    response = await client.post(
                        "/07_robust/ainvoke", json=request_data
                    )

                    # Verify the error response
                    self.assertEqual(response.status_code, 503)  # Service Unavailable
                    result = response.json()

                    # Assert using snapshot comparison
                    expected_dir = self.prepare_expected_data_dir()
                    self.assert_objects(
                        expected_dir, "response", [result], forced=False
                    )
