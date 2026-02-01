import datetime
import difflib
import filecmp
import inspect
import json
import logging
import os
import shutil
import unittest
import uuid
from contextlib import ExitStack, contextmanager
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, cast
from unittest.mock import AsyncMock, MagicMock, patch

import yaml

from ...common.test_helpers import patch_helper_generation


logger = logging.getLogger(__name__)


class EndpointBaseTestCase(unittest.IsolatedAsyncioTestCase):
    """Minimalist base test case focused on settings and test utilities.

    RESPONSIBILITIES:
    ----------------
    - Load and manage test settings (test_settings.yaml)
    - Provide test data loading utilities
    - Provide snapshot/assertion utilities
    - Provide helper patching utilities (UUIDs, timestamps)

    WHAT IT DOES NOT DO:
    -------------------
    - Does NOT initialize components or adapters
    - Does NOT mock repositories or services
    - Does NOT start databases or external services

    WHY?
    ----
    Component initialization happens naturally through the application's
    bootstrap/lifespan. Tests should patch adapter classes when needed
    using standard unittest.mock.patch at the test level.

    TESTING PHILOSOPHY:
    ------------------
    Mock at the adapter layer (connection classes), not repositories:

    Application Code (unchanged)
        ↓
    Real Repositories (unchanged)
        ↓
    Adapter Classes ← Patch these in individual tests
        ↓
    External Services

    USAGE EXAMPLE:
    -------------
    ```python
    from tests.common import FakeDatabaseClient

    class TestMyFeature(BaseTestCase):
        async def test_with_patched_adapter(self):
            # Patch the adapter class
            with patch('module.MongoEngineAdapter', FakeDatabaseClient):
                # Run your test with the endpoint/lifespan
                # Component initialization happens naturally
                result = await use_case.execute(params)
                self.assertIsNotNone(result)
    ```
    """

    expected_data_dir = "expected_data"

    ##############################################################################
    # Unittest initialization methods
    ##############################################################################

    def __init__(
        self,
        methodName: str = "runTest",
    ) -> None:
        # Get the directory of the actual test class file, not the base class
        test_class_file = inspect.getfile(self.__class__)
        self.test_dir = os.path.dirname(os.path.abspath(test_class_file))
        super().__init__(methodName)

    async def asyncSetUp(self):
        """Initialize basic test setup.

        Sets up cleanup callbacks and test directory context.
        Does NOT initialize components - that happens through app bootstrap.
        """
        self._cleanup_callbacks = []

    async def asyncTearDown(self):
        """Clean up test resources.

        Runs any registered cleanup callbacks.
        """
        for cleanup in reversed(self._cleanup_callbacks):
            try:
                cleanup()
            except Exception as e:
                logger.warning(f"Cleanup failed: {e}")
        self._cleanup_callbacks.clear()

    ##############################################################################
    # Public methods
    ##############################################################################

    def get_test_dir(self) -> str:
        return self.test_dir

    def get_test_name(self) -> Tuple[str, str]:
        stack = inspect.stack()

        for stack_item in stack:
            if stack_item.function.startswith("test_"):
                return stack_item.filename, stack_item.function

        return "<None>", "<None>"

    def load_test_data(self, file_name: str, format: Optional[str] = None):
        file_path = f"{self.test_dir}/{file_name}"

        with open(file_path, "r") as in_file:
            content = in_file.read()

            if format == "json":
                return json.loads(content)
            elif format in ["yaml", "yml"]:
                return yaml.load(content, Loader=yaml.Loader)

            return content

    def prepare_expected_data_dir(self, test_name: Optional[str] = None):
        test_function = test_name
        effective_test_filename = ""
        if not test_function:
            test_filename, test_function = self.get_test_name()
            effective_test_filename = test_filename.split("/")[-1].split(".")[0] + "/"

        output_dir = f"{self.test_dir}/{self.expected_data_dir}/{effective_test_filename}{test_function}"

        logger.debug(f"Test Assert dir: {output_dir}")

        os.makedirs(output_dir, exist_ok=True)

        return output_dir

    def get_settings(
        self, test_settings_file: str = "data/test_settings.yaml", merge: bool = False
    ) -> Dict[str, Any]:
        """Load settings for testing, optionally merging with test-specific overrides.

        This method always loads the main settings.yaml from the application root.
        If a test settings file exists, it can either replace or merge with main settings.

        Args:
            test_settings_file: Path to test settings file relative to test_dir.
                              Defaults to "data/test_settings.yaml".
            merge: If True and test settings exist, deep merge test settings with global settings.
                   If False and test settings exist, use only test settings (default).

        Returns:
            Dictionary containing settings based on merge behavior.

        Behavior:
            - If test settings file doesn't exist: Returns main settings.yaml
            - If test settings exist and merge=False (default): Returns only test settings
            - If test settings exist and merge=True: Deep merges test settings with main settings.yaml
              (test settings take precedence)

        Example:
            # Use only test settings (main settings.yaml must still exist)
            settings = self.get_settings()

            # Merge test settings with main settings.yaml
            settings = self.get_settings(merge=True)

            app = create_app(app_settings=AppSettings(**settings))
        """
        # Load main settings.yaml from application root (always required)
        main_settings_path = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.dirname(self.test_dir)))
            ),
            "settings.yaml",
        )

        if not os.path.exists(main_settings_path):
            raise FileNotFoundError(
                f"Global settings.yaml not found at {main_settings_path}"
            )

        with open(main_settings_path, "r") as f:
            main_settings = yaml.safe_load(f) or {}

        # Check if test settings file exists
        test_settings_path = os.path.join(self.test_dir, test_settings_file)

        if not os.path.exists(test_settings_path):
            # No test settings, return main settings
            return self._resolve_test_dir_tokens(main_settings)

        # Load test settings
        with open(test_settings_path, "r") as f:
            test_settings = yaml.safe_load(f) or {}

        # Apply merge logic
        if merge:
            # Deep merge: main settings as base, test settings override
            merged = self._deep_merge(main_settings, test_settings)
            return self._resolve_test_dir_tokens(merged)
        else:
            # Use only test settings
            return self._resolve_test_dir_tokens(test_settings)

    @contextmanager
    def patch_app_helpers(
        self,
        uuid_prefix: str = "test-uuid",
        timestamp_start: Optional[datetime.datetime] = datetime.datetime(
            2024, 1, 1, 0, 0, 0
        ),
        timestamp_increment_seconds: int = 1,
    ) -> Iterator:
        """Patch Helper.generate_uuid() and Helper.generate_timestamp() for deterministic tests.

        Args:
            uuid_prefix: Prefix for generated UUIDs (will be uuid_prefix-001, uuid_prefix-002, etc.).
            timestamp_start: Starting timestamp (defaults to 2024-01-01 00:00:00).
            timestamp_increment_seconds: Seconds to add for each new timestamp.

        Yields:
            FakeHelper instance for manual control if needed.

        Example:
            with self.patch_app_helpers(uuid_prefix="doc") as helper:
                # All Helper.generate_uuid() calls return doc-001, doc-002, etc.
                document = Document(content="test", character_name="test")
                assert document.document_id == "doc-001"
        """
        with patch_helper_generation(
            uuid_prefix=uuid_prefix,
            timestamp_start=timestamp_start,
            timestamp_increment_seconds=timestamp_increment_seconds,
        ) as helper:
            yield helper

    ##############################################################################
    # Private methods
    ##############################################################################

    def _resolve_test_dir_tokens(self, obj: Any) -> Any:
        """Recursively replace ${TEST_DIR} tokens with actual test directory path.

        Args:
            obj: Object to process (dict, list, str, or primitive).

        Returns:
            Object with ${TEST_DIR} tokens replaced.
        """
        if isinstance(obj, dict):
            return {
                key: self._resolve_test_dir_tokens(value) for key, value in obj.items()
            }
        elif isinstance(obj, list):
            return [self._resolve_test_dir_tokens(item) for item in obj]
        elif isinstance(obj, str):
            return obj.replace("${TEST_DIR}", self.test_dir)
        else:
            return obj

    def _deep_merge(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deep merge two dictionaries, with override values taking precedence.

        Args:
            base: Base dictionary
            override: Override dictionary (takes precedence)

        Returns:
            Merged dictionary with override values taking precedence.

        Example:
            base = {"a": 1, "b": {"c": 2, "d": 3}}
            override = {"b": {"d": 4, "e": 5}, "f": 6}
            result = {"a": 1, "b": {"c": 2, "d": 4, "e": 5}, "f": 6}
        """
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                # Recursively merge nested dictionaries
                result[key] = self._deep_merge(result[key], value)
            else:
                # Override takes precedence
                result[key] = value

        return result

    def _dump(self, file_path: str, data, ext: Optional[str] = None):
        """Serialize and dump data to a file.

        Automatically detects format from file extension or explicit ext parameter.
        Handles dataclasses, Pydantic models, dicts, lists, and primitives.

        Args:
            file_path: Target file path.
            data: Data to serialize (dataclass, Pydantic model, dict, list, etc.).
            ext: Optional explicit extension override ('json', 'yaml', 'yml').
        """
        # Determine format
        if ext is None:
            ext = os.path.splitext(file_path)[1].lstrip(".")

        # Convert data to serializable format
        serializable_data = self._make_serializable(data)

        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Write to file
        with open(file_path, "w") as f:
            if ext == "json":
                json.dump(serializable_data, f, indent=2, default=str)
            elif ext in ["yaml", "yml"]:
                yaml.safe_dump(
                    serializable_data,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                )
            else:
                # Plain text
                f.write(str(serializable_data))

    def _make_serializable(self, obj: Any) -> Any:
        """Convert objects to JSON/YAML serializable format.

        Args:
            obj: Object to convert.

        Returns:
            Serializable representation.
        """
        # Handle None, primitives
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj

        # Handle datetime
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()

        # Handle UUID
        if isinstance(obj, uuid.UUID):
            return str(obj)

        # Handle dataclasses
        if is_dataclass(obj) and not isinstance(obj, type):
            return self._make_serializable(asdict(obj))

        # Handle Pydantic models (have model_dump method)
        if hasattr(obj, "model_dump") and callable(getattr(obj, "model_dump", None)):
            return self._make_serializable(obj.model_dump(exclude_none=True))  # type: ignore[attr-defined]

        # Handle dictionaries
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}

        # Handle lists/tuples
        if isinstance(obj, (list, tuple)):
            return [self._make_serializable(item) for item in obj]

        # Fall back to string representation
        try:
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            return str(obj)

    def assert_objects(
        self, expected_dir: str, prefix: str, objs: list, forced: bool = False
    ):
        """Assert that objects match expected snapshots.

        Compares a list of objects against saved snapshots in the expected directory.
        Each object is saved as {prefix}_{index}.yaml and compared.

        Args:
            expected_dir: Directory containing expected snapshot files.
            prefix: Prefix for snapshot filenames (e.g., 'chunk', 'message').
            objs: List of objects to compare against snapshots.
            forced: If True, regenerate expected files instead of comparing.

        Raises:
            AssertionError: If objects don't match expected snapshots.
        """
        os.makedirs(expected_dir, exist_ok=True)

        for idx, obj in enumerate(objs):
            expected_file = f"{expected_dir}/{prefix}_{idx}.yaml"
            serializable_obj = self._make_serializable(obj)

            if forced or not os.path.exists(expected_file):
                # Generate/regenerate expected file
                self._dump(expected_file, serializable_obj, ext="yaml")
                logger.info(f"Generated expected snapshot: {expected_file}")
                if not forced:
                    logger.warning(
                        f"Expected file didn't exist, created: {expected_file}"
                    )
            else:
                # Load expected and compare
                with open(expected_file, "r") as f:
                    expected_data = yaml.safe_load(f)

                # Compare
                if serializable_obj != expected_data:
                    # Generate detailed diff
                    expected_str = yaml.safe_dump(
                        expected_data, default_flow_style=False, sort_keys=False
                    )
                    actual_str = yaml.safe_dump(
                        serializable_obj, default_flow_style=False, sort_keys=False
                    )

                    diff = "\n".join(
                        difflib.unified_diff(
                            expected_str.splitlines(keepends=True),
                            actual_str.splitlines(keepends=True),
                            fromfile=f"expected/{prefix}_{idx}.yaml",
                            tofile=f"actual/{prefix}_{idx}.yaml",
                            lineterm="",
                        )
                    )

                    self.fail(
                        f"\n{prefix}_{idx} doesn't match expected snapshot!\n"
                        f"Expected file: {expected_file}\n"
                        f"Diff:\n{diff}\n\n"
                        f"To regenerate snapshots, run with forced=True"
                    )
