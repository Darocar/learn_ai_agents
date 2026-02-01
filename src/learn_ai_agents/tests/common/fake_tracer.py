"""Fake tracer adapter for testing.

This module provides a no-op fake implementation of agent tracing.
Records traces in memory without sending data to external services.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml


class FakeAgentTracer:
    """Fake agent tracer for testing.
    
    Replaces OpikAgentTracerAdapter with a no-op tracer.
    Records traces in memory for inspection during tests.
    """
    
    def __init__(self, api_key: str = "fake-key", workspace: str = "fake-workspace", 
                 project_name: str = "test-project", **kwargs):
        """Initialize fake tracer.
        
        Args:
            api_key: Fake API key (ignored).
            workspace: Fake workspace (ignored).
            project_name: Fake project name (ignored).
            **kwargs: Additional arguments (ignored).
        """
        self.api_key = api_key
        self.workspace = workspace
        self.project_name = project_name
        self._traces: List[Dict[str, Any]] = []
    
    def get_tracer(self, thread_id: str) -> "FakeAgentTracer":
        """Return self as the tracer.
        
        Args:
            thread_id: Thread ID for tracing (ignored).
            
        Returns:
            Self (fake tracer).
        """
        return self
    
    def trace(self, *args, **kwargs) -> "FakeAgentTracer":
        """Fake trace context manager.
        
        Returns:
            Self for context manager protocol.
        """
        return self
    
    def __enter__(self):
        """Enter fake trace context.
        
        Returns:
            Self.
        """
        return self
    
    def __exit__(self, *args):
        """Exit fake trace context.
        
        Args:
            *args: Exception info (ignored).
        """
        pass
    
    def log(self, event: str, data: Dict[str, Any]) -> None:
        """Fake log operation.
        
        Args:
            event: Event name.
            data: Event data.
        """
        self._traces.append({"event": event, "data": data})
    
    def get_traces(self) -> List[Dict[str, Any]]:
        """Get all recorded traces.
        
        Returns:
            List of trace dictionaries.
        """
        return self._traces.copy()
    
    def clear_traces(self) -> None:
        """Clear all recorded traces."""
        self._traces.clear()
