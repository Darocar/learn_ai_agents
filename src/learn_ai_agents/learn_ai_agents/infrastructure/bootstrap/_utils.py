"""Utility functions for bootstrap containers.

This module provides common utility functions used across different
bootstrap containers for dependency injection and component instantiation.
"""

import importlib
from typing import Any


def import_class_from_string(path: str) -> type[Any]:
    """Dynamically import and return a class from a fully qualified module path.

    This utility enables configuration-driven component instantiation by
    loading classes specified as strings in configuration files.

    Args:
        path: Fully qualified Python path to the class
            (e.g., 'module.submodule.ClassName' or
            'learn_ai_agents.infrastructure.outbound.llms.langchain_fwk.groq.GroqAdapter').

    Returns:
        The class object (not an instance).

    Raises:
        ImportError: If the module cannot be imported.
        AttributeError: If the class name doesn't exist in the module.

    Examples:
        >>> cls = import_class_from_string('pathlib.Path')
        >>> isinstance(cls, type)
        True
        >>> cls.__name__
        'Path'

        >>> MyClass = import_class_from_string('my_module.MyClass')
        >>> instance = MyClass()  # Create an instance of the imported class
    """
    module_path, _, class_name = path.rpartition(".")
    module = importlib.import_module(module_path)
    return getattr(module, class_name)
