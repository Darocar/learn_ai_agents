"""Helper class for generating UUIDs and timestamps.

This module provides a centralized location for ID and timestamp generation,
making it easy to mock these values in tests for deterministic behavior.
"""

from datetime import datetime
from uuid import uuid4


class Helper:
    """Static helper class for generating IDs and timestamps.
    
    This class provides static methods that can be easily mocked in tests
    to produce deterministic values. By centralizing ID generation here,
    we avoid scattered uuid4() and datetime.now() calls throughout the codebase.
    
    Usage:
        # In production code:
        document_id = Helper.generate_uuid()
        timestamp = Helper.generate_timestamp()
        
        # In tests:
        with patch('path.to.Helper.generate_uuid', return_value='fixed-uuid'):
            # Your test code here
    """
    
    @staticmethod
    def generate_uuid() -> str:
        """Generate a new UUID string.
        
        Returns:
            A UUID4 string representation.
        """
        return str(uuid4())
    
    @staticmethod
    def generate_timestamp() -> datetime:
        """Generate current timestamp.
        
        Returns:
            Current datetime.
        """
        return datetime.now()
