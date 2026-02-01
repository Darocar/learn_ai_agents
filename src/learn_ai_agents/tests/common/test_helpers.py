"""Test helper utilities for mocking and deterministic testing.

This module provides context managers and utilities for patching ID generation
to make tests reproducible and deterministic.
"""

from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Generator, Optional
from unittest.mock import patch


class FakeHelper:
    """Generator for deterministic UUIDs and timestamps in tests.
    
    This class can be used as a drop-in replacement for the Helper class
    since it provides static methods that match the Helper interface.
    """
    
    # Class-level state for generating deterministic values
    uuid_prefix: str = "test-uuid"
    uuid_counter: int = 0
    timestamp_start: datetime = datetime(2024, 1, 1, 0, 0, 0)
    timestamp_counter: int = 0
    timestamp_increment: timedelta = timedelta(seconds=1)
    
    @classmethod
    def configure(
        cls,
        uuid_prefix: str = "test-uuid",
        timestamp_start: Optional[datetime] = None,
        timestamp_increment_seconds: int = 1
    ):
        """Configure the deterministic generator.
        
        Args:
            uuid_prefix: Prefix for generated UUIDs (will be uuid_prefix-001, uuid_prefix-002, etc.).
            timestamp_start: Starting timestamp (defaults to 2024-01-01 00:00:00).
            timestamp_increment_seconds: Seconds to add for each new timestamp.
        """
        cls.uuid_prefix = uuid_prefix
        cls.uuid_counter = 0
        cls.timestamp_start = timestamp_start or datetime(2024, 1, 1, 0, 0, 0)
        cls.timestamp_counter = 0
        cls.timestamp_increment = timedelta(seconds=timestamp_increment_seconds)
    
    @staticmethod
    def generate_uuid() -> str:
        """Generate a deterministic UUID string.
        
        Returns:
            A predictable UUID string like 'test-uuid-001', 'test-uuid-002', etc.
        """
        FakeHelper.uuid_counter += 1
        return f"{FakeHelper.uuid_prefix}-{FakeHelper.uuid_counter:03d}"
    
    @staticmethod
    def generate_timestamp() -> datetime:
        """Generate a deterministic timestamp.
        
        Returns:
            A predictable datetime that increments with each call.
        """
        timestamp = FakeHelper.timestamp_start + (FakeHelper.timestamp_counter * FakeHelper.timestamp_increment)
        FakeHelper.timestamp_counter += 1
        return timestamp
    
    @classmethod
    def reset(cls) -> None:
        """Reset counters to initial state."""
        cls.uuid_counter = 0
        cls.timestamp_counter = 0


@contextmanager
def patch_helper_generation(
    uuid_prefix: str = "test-uuid",
    timestamp_start: Optional[datetime] = None,
    timestamp_increment_seconds: int = 1
) -> Generator[type[FakeHelper], None, None]:
    """Context manager to patch Helper class with FakeHelper.
    
    This ensures all ID and timestamp generation in the code uses deterministic values
    for reproducible tests. FakeHelper provides the same static method interface as Helper.
    
    Args:
        uuid_prefix: Prefix for generated UUIDs.
        timestamp_start: Starting timestamp (defaults to 2024-01-01 00:00:00).
        timestamp_increment_seconds: Seconds to add for each new timestamp.
        
    Yields:
        FakeHelper class for manual control if needed.
        
    Example:
        ```python
        with patch_helper_generation() as FakeHelper:
            # All Helper.generate_uuid() calls will return test-uuid-001, test-uuid-002, etc.
            # All Helper.generate_timestamp() calls will return 2024-01-01 00:00:00, 00:00:01, etc.
            document = Document(content="test", character_name="test")
            assert document.document_id == "test-uuid-001"
        ```
    """
    # Configure FakeHelper with the desired settings
    FakeHelper.configure(
        uuid_prefix=uuid_prefix,
        timestamp_start=timestamp_start,
        timestamp_increment_seconds=timestamp_increment_seconds
    )
    
    # Patch the Helper class with FakeHelper class (not an instance)
    with patch(
        'learn_ai_agents.infrastructure.helpers.generators.Helper',
        FakeHelper
    ):
        yield FakeHelper