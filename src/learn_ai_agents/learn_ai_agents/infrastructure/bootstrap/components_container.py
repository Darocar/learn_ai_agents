"""Container for managing infrastructure components.

This module provides the container responsible for creating and managing
infrastructure components like LLMs, databases, and other external services.
"""

# infrastructure/bootstrap/components_container.py
from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Any, Dict

from learn_ai_agents.logging import get_logger
from pydantic import SecretStr
from typing_extensions import Self

from ._utils import import_class_from_string
from learn_ai_agents.settings import AppSettings

logger = get_logger(__name__)


@dataclass
class ComponentsContainer:
    """Container for managing infrastructure components.

    This container lazily creates and caches infrastructure components
    (LLMs, databases, etc.) as singletons, ensuring efficient resource usage.

    Attributes:
        settings: The application settings to use for component resolution.
        _cache: Cache of instantiated components.
        _lock: Thread lock for safe concurrent access.
    """

    settings: AppSettings
    _cache: dict[str, Any]
    _lock: RLock

    @classmethod
    async def create(cls, settings: AppSettings) -> Self:
        """Create a new components container.

        Args:
            settings: The application settings to use for component resolution.

        Returns:
            Initialized ComponentsContainer.
        """
        container = cls(settings=settings, _cache={}, _lock=RLock())
        return container

    def get(self, ref: str) -> Any:
        """Retrieve or create a component instance.

        Components are lazily created on first access and cached for reuse.
        Reference formats supported: 'llms.langchain.groq.default' or with
        different separators ('/', '-').

        Args:
            ref: Component reference string (e.g., 'llms.langchain.groq.default').

        Returns:
            The requested component instance.
        """
        # normalize key to dotted
        key = ref.replace("/", ".").replace("-", ".")
        with self._lock:
            if key in self._cache:
                logger.debug(f"Retrieved cached component: {key}")
                return self._cache[key]

            logger.info(f"Creating component: {key}")
            module_class, cfg = self.settings.resolve_ref(ref, "component")
            # Allow factory classes with .build(name?, cfg?) or plain constructors
            instance = self._instantiate(module_class, cfg)
            self._cache[key] = instance
            logger.debug(f"Component created and cached: {key}")
            return instance

    def _instantiate(self, module_class: str, cfg: Dict[str, Any]) -> Any:
        """Instantiate a component from its module class path.

        Extracts secret values from SecretStr objects before passing to constructor.
        Resolves component references (ending with _ref).

        Tries multiple instantiation patterns:
        1. Factory .build() method with **cfg
        2. Factory .create() method with **cfg
        3. Direct constructor with **kwargs (most common)
        4. Direct constructor with config=dict (fallback)

        Args:
            module_class: Fully qualified class path.
            cfg: Configuration dictionary (may contain SecretStr objects and component refs).

        Returns:
            Instantiated component.
        """
        # Extract secret values from SecretStr objects and resolve component references
        resolved_cfg: Dict[str, Any] = {}
        for key, value in cfg.items():
            if isinstance(value, SecretStr):
                resolved_cfg[key] = value.get_secret_value()
                logger.debug(f"Resolved SecretStr for key: {key}")
            elif key.endswith("_ref") and isinstance(value, str):
                # Resolve component references - strip _ref suffix to get the actual parameter name
                param_name = key[:-4]  # Remove '_ref' suffix
                component_instance = self.get(value)
                resolved_cfg[param_name] = component_instance
                logger.debug(f"Resolved {key} -> {param_name} to component instance from {value}")
            else:
                resolved_cfg[key] = value

        logger.debug(f"Instantiating {module_class} with params: {list(resolved_cfg.keys())}")

        obj = import_class_from_string(module_class)

        # Try factory methods first
        build = getattr(obj, "build", None)
        if callable(build):
            logger.debug("Using factory build() method")
            return build(**resolved_cfg)

        create = getattr(obj, "create", None)
        if callable(create):
            logger.debug("Using factory create() method")
            return create(**resolved_cfg)

        # Try direct constructor with kwargs (most common pattern)
        try:
            logger.debug("Using direct constructor with **kwargs")
            return obj(**resolved_cfg)
        except TypeError as e:
            # Some components might accept a 'config' dict parameter instead
            if "unexpected keyword argument" in str(e):
                logger.debug(f"Constructor with **kwargs failed: {e}")
                logger.debug("Trying constructor with config parameter")
                try:
                    return obj(config=resolved_cfg)
                except TypeError:
                    logger.error(f"Failed to instantiate {module_class} with both **kwargs and config parameter")
                    raise e  # Raise the original error
            raise

    async def shutdown(self) -> None:
        """Shutdown and dispose of all cached components.

        Calls close/aclose methods on components that support them
        for graceful resource cleanup.
        """
        with self._lock:
            # Clean up all components
            for key, component in self._cache.items():
                # Try cleanup methods
                for method_name in ("aclose", "close"):
                    method = getattr(component, method_name, None)
                    if callable(method):
                        try:
                            logger.debug(f"Closing component: {key}")
                            if method_name == "aclose":
                                await method()  # type: ignore
                            else:
                                method()
                        except Exception as e:
                            logger.error(f"Error closing {key}: {e}")
            self._cache.clear()
