"""
Configuration System for Learn AI Agents

This module implements a sophisticated configuration system using Pydantic Settings.
It demonstrates several advanced patterns:

1. **Environment Variable Expansion**: Variables like ${GROQ_API_KEY} in YAML files
   are automatically expanded from .env files or system environment.

2. **Multi-Source Configuration**: Combines settings from:
   - Constructor arguments (highest priority)
   - .env files
   - Environment variables
   - YAML configuration files
   - Docker secrets (lowest priority)

3. **Type-Safe Configuration**: Uses Pydantic models to ensure configuration validity.

4. **Component Resolution**: Provides a registry system to resolve component references
   like 'llms.langchain.groq.default' to actual class paths and configurations.

This follows the Hexagonal Architecture principle of keeping configuration concerns
at the infrastructure layer while providing a clean interface for the application layer.
"""

from __future__ import annotations

import os
import re
from collections import ChainMap
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

from learn_ai_agents.logging import get_logger

logger = get_logger(__name__)

_VAR_RE = re.compile(r"\$(\w+)|\$\{([^}]+)\}")


def expandvars_with_secrets(
    text: str,
    *,
    env: Mapping[str, str],
    secrets_dir: Path,
    strip_secret_trailing_newline: bool = True,
) -> str:
    """
    Expand $VAR / ${VAR} using:
      1) env mapping (OS env takes priority if you pass ChainMap(os.environ, dotenv_vars))
      2) Docker secrets files: <secrets_dir>/<VAR>
    Unknown variables are left unchanged, like os.path.expandvars().

    Docker/Compose secrets are mounted as files (e.g., /run/secrets/<name>) and do not set env vars directly.
    """

    def repl(m: re.Match[str]) -> str:
        var = m.group(1) or m.group(2)
        if not var:
            return m.group(0)

        v = env.get(var)
        if v is not None:
            return v

        secret_path = secrets_dir / var
        if secret_path.is_file():
            s = secret_path.read_text(encoding="utf-8")
            return s.rstrip("\n") if strip_secret_trailing_newline else s

        return m.group(0)

    return _VAR_RE.sub(repl, text)


# ---------- Configuration Schema ----------
# These models define the structure of our configuration


# ========== COMPONENTS CONFIGURATION ==========
class ComponentConstructor(BaseModel):
    """Constructor information for a component family.

    Attributes:
        module_class: The fully qualified Python path to the implementation class
            (e.g., 'learn_ai_agents.infrastructure.outbound.llms.langchain_fwk.groq.LangchainGroqChatModelAdapter').
        api_key: Secret API key for authentication (shared across all instances in this family).
    """

    module_class: str
    api_key: SecretStr | None = None


class ComponentInstance(BaseModel):
    """Configuration for a specific component instance.

    Attributes:
        params: Parameters to pass to the component constructor.
    """

    params: dict[str, Any]


class ProviderFamily(BaseModel):
    """Represents a family of component implementations.

    For example, all Groq LLM instances (default, high-temp, etc.) would
    belong to one provider family.

    Attributes:
        constructor: Constructor information including module_class.
        instances: Named instances with their specific parameters
            (e.g., {'default': {'params': {'api_key': '...', 'temperature': 0.1}}}).
    """

    constructor: ComponentConstructor
    instances: dict[str, ComponentInstance]


# Type alias for the entire component tree structure
# Example: components.llms.langchain.groq
ComponentsTree = dict[str, dict[str, dict[str, ProviderFamily]]]


# ========== AGENTS CONFIGURATION ==========
class AgentComponents(BaseModel):
    """Defines which components an agent uses.

    Maps component types to their references. This is flexible to support
    any type of component (llms, tools, databases, retrievers, etc.).

    Attributes:
        llms: Dictionary mapping alias to LLM component reference string
            (e.g., {'default': 'llms.langchain.groq.default'}).
        tools: Dictionary mapping alias to tool component reference string.
        databases: Dictionary mapping alias to database component reference string.
        Any other component types can be added dynamically.
    """

    llms: dict[str, str] | None = None
    tools: dict[str, str] | None = None
    databases: dict[str, str] | None = None
    retrievers: dict[str, str] | None = None

    class Config:
        extra = "allow"  # Allow additional fields for future component types


class AgentInfo(BaseModel):
    """Metadata information for an agent.

    Attributes:
        name: Human-readable agent name.
        description: Brief description of what this agent does.
    """

    name: str
    description: str


class AgentConstructor(BaseModel):
    """Constructor information for an agent.

    Attributes:
        module_class: Fully qualified Python path to the agent implementation class.
        components: Component references this agent needs (LLMs, tools, etc.).
        config: Additional configuration parameters for the agent (e.g., database_name, collection names).
    """

    module_class: str
    components: AgentComponents | None = None
    config: dict[str, Any] | None = None


class AgentConfig(BaseModel):
    """Configuration for a specific agent.

    Defines an agent's metadata, constructor, and required components.

    Attributes:
        info: Agent metadata (name, description).
        constructor: Constructor information including module_class and components.
    """

    info: AgentInfo
    constructor: AgentConstructor


# Type alias for the entire agents tree structure
# Example: agents.langchain.basic_answer
AgentsTree = dict[str, dict[str, AgentConfig]]


# ========== USE CASES CONFIGURATION ==========
class UseCaseComponents(BaseModel):
    """Defines which components a use case uses.

    Maps component types to their references. For use cases, this typically
    includes agents but can also include other components.

    Attributes:
        agents: Dictionary mapping alias to agent reference string
            (e.g., {'agent': 'agents.langchain.basic_answer'}).
        Any other component types can be added dynamically.
    """

    agents: dict[str, str] | None = None

    class Config:
        extra = "allow"  # Allow additional fields for future component types


class UseCaseInfo(BaseModel):
    """Metadata information for a use case.

    Attributes:
        name: Human-readable use case name.
        description: Brief description of what this use case does.
        path_prefix: API path prefix for this use case's endpoints (e.g., '/basic-answer').
        router_factory: Import path to router factory function (e.g., 'module.path:function_name').
    """

    name: str
    description: str
    path_prefix: str
    router_factory: str | None = (
        None  # e.g., "learn_ai_agents.infrastructure.inbound.controllers.agents.robust:get_router"
    )


class UseCaseConstructor(BaseModel):
    """Constructor information for a use case.

    Attributes:
        module_class: Fully qualified Python path to the use case implementation class.
        components: Component references this use case needs (agents, etc.).
        config: Additional configuration parameters for the use case (e.g., retry_policy, timeout).
    """

    module_class: str
    components: UseCaseComponents | None = None
    config: dict[str, Any] | None = None


class UseCaseConfig(BaseModel):
    """Configuration for a specific use case.

    Defines a use case's metadata, constructor, and required components.

    Attributes:
        info: Use case metadata (name, description).
        constructor: Constructor information including module_class and components.
    """

    info: UseCaseInfo
    constructor: UseCaseConstructor


# Type alias for the entire use cases tree structure
# Example: use_cases.basic_answer
UseCasesTree = dict[str, UseCaseConfig]


# ========== YAML CONFIGURATION SOURCE ==========
# Custom Pydantic settings source for loading YAML with environment variable expansion


class EnvExpandingYamlSettingsSource(PydanticBaseSettingsSource):
    """Custom Pydantic settings source that loads YAML with environment variable expansion.

    This source integrates with Pydantic Settings to provide configuration from
    YAML files with automatic environment variable substitution.

    The source performs these steps:
    1. Reads the settings.yaml file
    2. Expands ${VAR_NAME} placeholders using OS env + .env + Docker secrets
    4. Provides the expanded data to Pydantic for validation

    This allows settings.yaml to contain:
        api_key: ${GROQ_API_KEY}

    Which gets automatically resolved from environment variables, .env file, or Docker secrets.

    Key design decisions:
    - .env values participate in settings resolution via dotenv_settings (Pydantic's normal pipeline)
    - YAML ${VAR} expansion uses OS env + .env + Docker secrets (/run/secrets/<NAME>)
    - Environment variables have higher priority than .env values

    Attributes:
        yaml_path: Path to the YAML configuration file.
        data: Parsed and expanded configuration dictionary.
    """

    def __init__(
        self,
        settings_cls: type[BaseSettings],
        yaml_path: Path,
        extra_env_for_expand: Mapping[str, str | None] | None = None,
    ):
        """Initialize the YAML settings source.

        Args:
            settings_cls: The Pydantic settings class being configured.
            yaml_path: Path to the YAML configuration file.
            extra_env_for_expand: Additional environment variables (from .env) to use
                for YAML expansion. These are temporarily added to os.environ during
                expansion without permanently modifying the process environment.
        """
        super().__init__(settings_cls)
        self.yaml_path = yaml_path
        extra_env_for_expand = extra_env_for_expand or {}

        # Read YAML file (or use empty dict if it doesn't exist)
        if yaml_path.exists():
            text = yaml_path.read_text(encoding="utf-8")

            # Build env mapping where OS env wins over .env values
            dotenv_vars: dict[str, str] = {k: v for k, v in extra_env_for_expand.items() if v is not None}
            env_for_expand = ChainMap(os.environ, dotenv_vars)

            secrets_dir = Path(os.getenv("SECRETS_DIR", "/run/secrets"))
            expanded_text = expandvars_with_secrets(
                text,
                env=env_for_expand,
                secrets_dir=secrets_dir,
            )
            data = yaml.safe_load(expanded_text) or {}
        else:
            data = {}

        # Store the parsed and expanded dictionary
        self.data = data

    def get_field_value(self, field, field_name: str) -> tuple[Any, str, bool]:
        key = field.alias or field_name
        value_is_complex = self.field_is_complex(field)
        if key in self.data:
            return self.data[key], key, value_is_complex
        return None, key, value_is_complex

    def __call__(self) -> dict[str, Any]:
        """Return the entire data dictionary when the source is called.

        Returns:
            The complete parsed configuration dictionary.
        """
        return self.data


# ========== MAIN SETTINGS CLASS ==========
# Application settings with multi-source configuration support


class AppSettings(BaseSettings):
    """Main application settings with multi-source configuration.

    This class uses Pydantic Settings to load configuration from multiple sources
    with a defined priority order. Configuration can come from:
    - Constructor arguments (highest priority)
    - .env files
    - Environment variables
    - YAML configuration files
    - Docker secrets (lowest priority)

    The settings support environment variable expansion in YAML files, allowing
    sensitive data like API keys to be stored in environment variables while
    maintaining readable configuration files.

    Attributes:
        components: Registry of all available components organized by type,
            framework, and family (e.g., components.llms.langchain.groq).
        agents: Registry of all available agents organized by framework
            (e.g., agents.langchain.basic_answer).
        use_cases: Registry of all available use cases
            (e.g., use_cases.basic_answer).
        agents: Configuration for all agents in the system, keyed by agent name.
    """

    # Provide defaults so we can instantiate AppSettings() without arguments
    components: ComponentsTree = Field(default_factory=dict)
    agents: AgentsTree = Field(default_factory=dict)
    use_cases: UseCasesTree = Field(default_factory=dict)

    model_config = SettingsConfigDict(extra="ignore", env_file=".env", case_sensitive=True)

    @classmethod
    def settings_customise_sources(
        cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings
    ):
        """Customize settings sources with proper priority and YAML expansion support.

        Priority order (highest to lowest):
        1. Constructor arguments (init_settings)
        2. Environment variables (env_settings)
        3. .env file (dotenv_settings)
        4. Docker secrets (file_secret_settings)  -> overrides YAML for actual settings fields
        5. YAML configuration file (yaml_source)

        Notes:
        - DotEnvSettingsSource reads env_file from model_config and exposes .env vars.
        - YAML expansion uses OS env + .env vars + /run/secrets/<NAME>.
        """
        sources = [init_settings, file_secret_settings]

        # Build YAML source with .env-powered variable expansion
        default_yaml_path = Path(__file__).resolve().parent.parent / "settings.yaml"
        yaml_path = Path(os.getenv("SETTINGS_YAML_PATH", str(default_yaml_path)))

        # Read raw dotenv vars (from model_config.env_file)
        # DotEnvSettingsSource inherits EnvSettingsSource and exposes env_vars
        raw_dotenv_vars = dotenv_settings.env_vars # type: ignore

        init_kwargs = getattr(init_settings, "init_kwargs", {}) or {}
        if not init_kwargs:
            logger.info(f"Loading settings from YAML: {yaml_path}")
            yaml_source = EnvExpandingYamlSettingsSource(
                settings_cls=settings_cls,
                yaml_path=yaml_path,
                extra_env_for_expand=raw_dotenv_vars,
            )
            sources.append(yaml_source)
        return tuple(sources)

    def resolve_ref(self, ref: str, ref_type: str = "component") -> Any:
        """Resolve references to their configuration or module class.

        This is a generic resolver that handles components, agents, and use cases.

        Args:
            ref: The reference string to resolve.
            ref_type: Type of reference - 'component', 'agent', or 'use_case'.

        Returns:
            For components: Tuple of (module_class, config_dict)
            For agents: AgentConfig object
            For use_cases: UseCaseConfig object

        Raises:
            ValueError: If reference format is invalid for the specified type.
            KeyError: If the reference cannot be resolved.

        Examples:
            >>> # Resolve a component
            >>> settings.resolve_ref('llms.langchain.groq.default', 'component')
            ('learn_ai_agents...GroqAdapter', {'api_key': '...', 'temperature': 0.1})

            >>> # Resolve an agent
            >>> settings.resolve_ref('agents.langchain.basic_answer', 'agent')
            AgentConfig(info=..., constructor=...)

            >>> # Resolve a use case
            >>> settings.resolve_ref('basic_answer', 'use_case')
            UseCaseConfig(info=..., constructor=...)
        """
        # Normalize separator to '.'
        normalized_ref = ref.replace("/", ".").replace("-", ".")

        if ref_type == "component":
            return self._resolve_component(normalized_ref)
        elif ref_type == "agent":
            return self._resolve_agent(normalized_ref)
        elif ref_type == "use_case":
            return self._resolve_use_case(normalized_ref)
        else:
            raise ValueError(f"Invalid ref_type '{ref_type}'. Must be 'component', 'agent', or 'use_case'.")

    def _resolve_component(self, ref: str) -> tuple[str, dict[str, Any]]:
        """Internal method to resolve component references.

        Component format: <component_type>.<framework>.<family>.<instance>

        Returns the module_class and a config dict that may contain SecretStr objects.
        The actual secret values should be extracted at component build time.
        """
        parts = ref.split(".")

        if len(parts) != 4:
            raise ValueError(f"Invalid component reference '{ref}'. Expected 4 parts.")

        comp_type, framework, family, instance = parts

        try:
            provider_family = self.components[comp_type][framework][family]
            module_class = provider_family.constructor.module_class
            instance_cfg = provider_family.instances[instance]

            # Build config dictionary with api_key from constructor (as SecretStr)
            cfg = dict(instance_cfg.params)
            if provider_family.constructor.api_key is not None:
                cfg["api_key"] = provider_family.constructor.api_key
                logger.debug(f"Resolved component '{ref}' with api_key from constructor")

            return module_class, cfg
        except KeyError as e:
            raise KeyError(f"Could not resolve component '{ref}': missing {e}") from e

    def _resolve_agent(self, ref: str) -> AgentConfig:
        """Internal method to resolve agent references.

        Agent format: <framework>.<agent_name> or agents.<framework>.<agent_name>
        """
        # Remove 'agents.' prefix if present
        if ref.startswith("agents."):
            ref = ref[7:]

        parts = ref.split(".")

        if len(parts) != 2:
            raise ValueError(f"Invalid agent reference '{ref}'. Expected 2 parts (framework.agent_name).")

        framework, agent_name = parts

        try:
            return self.agents[framework][agent_name]
        except KeyError as e:
            raise KeyError(f"Could not resolve agent '{ref}': missing {e}") from e

    def _resolve_use_case(self, ref: str) -> UseCaseConfig:
        """Internal method to resolve use case references.

        Use case format: <use_case_name>
        """
        try:
            return self.use_cases[ref]
        except KeyError as e:
            raise KeyError(f"Could not resolve use case '{ref}': missing {e}") from e

    def list_components(self) -> dict[str, Any]:
        """List all available components with their complete configuration.

        Returns:
            Dictionary with component types as keys, each containing a list of components
            with their reference, info, and configuration.

        Example:
            >>> settings.list_components()
            {
                'llms': [
                    {
                        'ref': 'llms.langchain.groq.default',
                        'info': {
                            'framework': 'langchain',
                            'family': 'groq',
                            'instance': 'default'
                        },
                        'api_key': '**********',
                        'params': {'temperature': 0.1}
                    }
                ]
            }
        """
        result: dict[str, list] = {}

        for comp_type, frameworks in self.components.items():
            component_list = []

            for framework, families in frameworks.items():
                for family_name, family in families.items():
                    # Add api_key info at family level if present
                    family_has_api_key = family.constructor.api_key is not None

                    for instance_name, instance_cfg in family.instances.items():
                        component_item: dict[str, Any] = {
                            "ref": f"{comp_type}.{framework}.{family_name}.{instance_name}",
                            "info": {"framework": framework, "family": family_name, "instance": instance_name},
                            "params": instance_cfg.params,
                        }

                        # Add api_key if present at constructor level
                        if family_has_api_key:
                            component_item["api_key"] = "**********"

                        component_list.append(component_item)

            result[comp_type] = component_list

        return result

    def list_agents(self) -> list[dict[str, Any]]:
        """List all available agents with their complete metadata and configuration.

        Returns:
            List of agents with their reference, info, and component dependencies.

        Example:
            >>> settings.list_agents()
            [
                {
                    'ref': 'agents.langchain.basic_answer',
                    'info': {
                        'name': 'Basic Answer Agent',
                        'description': 'An agent that provides basic answers...'
                    },
                    'components': {
                        'llms': {
                            'default': 'llms.langchain.groq.default'
                        }
                    }
                }
            ]
        """
        result: list[dict[str, Any]] = []

        for framework, agents in self.agents.items():
            for agent_name, agent_cfg in agents.items():
                agent_item: dict[str, Any] = {
                    "ref": f"agents.{framework}.{agent_name}",
                    "info": {
                        "name": agent_cfg.info.name,
                        "description": agent_cfg.info.description,
                    },
                }

                # Add components information if available
                if agent_cfg.constructor.components:
                    components_dict = agent_cfg.constructor.components.model_dump(exclude_none=True)
                    if components_dict:
                        agent_item["components"] = components_dict

                result.append(agent_item)

        return result

    def list_use_cases(self) -> dict[str, Any]:
        """List all available use cases with their complete metadata and configuration.

        Returns:
            Dictionary with use case names as keys, containing their complete info.

        Example:
            >>> settings.list_use_cases()
            {
                'basic_answer': {
                    'name': 'Basic Answer Use Case',
                    'description': 'A use case that provides...',
                    'path_prefix': '/basic-answer',
                    'module_class': 'learn_ai_agents.application...',
                    'components': {
                        'agents': {
                            'agent': 'agents.langchain.basic_answer'
                        }
                    }
                }
            }
        """
        result: dict[str, Any] = {}
        for use_case_name, use_case_cfg in self.use_cases.items():
            use_case_info: dict[str, Any] = {
                "name": use_case_cfg.info.name,
                "description": use_case_cfg.info.description,
                "path_prefix": use_case_cfg.info.path_prefix,
                "module_class": use_case_cfg.constructor.module_class,
            }

            # Add components information if available
            if use_case_cfg.constructor.components:
                components_dict = use_case_cfg.constructor.components.model_dump(exclude_none=True)
                if components_dict:
                    use_case_info["components"] = components_dict

            result[use_case_name] = use_case_info
        return result
