"""Router for discovering available system resources.

This module provides endpoints to discover all available components,
agents, and use cases in the system following hexagonal architecture.
"""

from fastapi import APIRouter, Depends
from learn_ai_agents.application.dtos.discovery.discovery import (
    AgentsResponseDTO,
    AllResourcesResponseDTO,
    ComponentsResponseDTO,
    UseCasesResponseDTO,
)
from learn_ai_agents.application.use_cases.discovery.use_case import DiscoveryUseCase
from learn_ai_agents.logging import get_logger

from ..dependencies import get_discovery_use_case

logger = get_logger(__name__)

router = APIRouter(prefix="/discover", tags=["Discovery"])


@router.get("/components", response_model=ComponentsResponseDTO)
async def discover_components(use_case: DiscoveryUseCase = Depends(get_discovery_use_case)) -> ComponentsResponseDTO:
    """
    Discover all available components in the system.

    Returns all configured components organized by type as a list,
    including reference, info, API key (masked), and instance parameters.

    Returns:
        ComponentsResponseDTO: Components organized by type.

    Example response:
        {
            "components": {
                "llms": [
                    {
                        "ref": "llms.langchain.groq.default",
                        "info": {
                            "framework": "langchain",
                            "family": "groq",
                            "instance": "default"
                        },
                        "api_key": "**********",
                        "params": {
                            "temperature": 0.1
                        }
                    }
                ]
            }
        }
    """
    logger.info("GET /discover/components")
    result = use_case.discover_components()
    logger.debug(f"Returned {sum(len(comps) for comps in result.components.values())} components")
    return result


@router.get("/agents", response_model=AgentsResponseDTO)
async def discover_agents(use_case: DiscoveryUseCase = Depends(get_discovery_use_case)) -> AgentsResponseDTO:
    """
    Discover all available agents in the system.

    Returns all configured agents as a list with complete metadata,
    including reference, info, and component dependencies.

    Returns:
        AgentsResponseDTO: List of all agents.

    Example response:
        {
            "agents": [
                {
                    "ref": "agents.langchain.basic_answer",
                    "info": {
                        "name": "Basic Answer Agent",
                        "description": "An agent that provides basic answers..."
                    },
                    "components": {
                        "llms": {
                            "default": "llms.langchain.groq.default"
                        }
                    }
                }
            ]
        }
    """
    logger.info("GET /discover/agents")
    result = use_case.discover_agents()
    logger.debug(f"Returned {len(result.agents)} agents")
    return result


@router.get("/use-cases", response_model=UseCasesResponseDTO)
async def discover_use_cases(use_case: DiscoveryUseCase = Depends(get_discovery_use_case)) -> UseCasesResponseDTO:
    """
    Discover all available use cases in the system.

    Returns all configured use cases as a list with complete metadata,
    including reference, info, path prefixes, and component dependencies.

    Returns:
        UseCasesResponseDTO: List of all use cases.

    Example response:
        {
            "use_cases": [
                {
                    "ref": "basic_answer",
                    "info": {
                        "name": "Basic Answer Use Case",
                        "description": "A use case that provides...",
                        "path_prefix": "/01_basic_answer"
                    },
                    "components": {
                        "agents": {
                            "agent": "agents.langchain.basic_answer"
                        }
                    }
                }
            ]
        }
    """
    logger.info("GET /discover/use-cases")
    result = use_case.discover_use_cases()
    logger.debug(f"Returned {len(result.use_cases)} use cases")
    return result


@router.get("/all", response_model=AllResourcesResponseDTO)
async def discover_all(use_case: DiscoveryUseCase = Depends(get_discovery_use_case)) -> AllResourcesResponseDTO:
    """
    Discover all available resources in the system.

    Returns a comprehensive view of all components, agents, and use cases.

    Returns:
        AllResourcesResponseDTO: All system resources.

    Example response:
        {
            "components": {...},
            "agents": [...],
            "use_cases": [...]
        }
    """
    logger.info("GET /discover/all")
    result = use_case.discover_all()
    total_components = sum(len(comps) for comps in result.components.values())
    logger.debug(
        f"Returned all resources: {total_components} components, "
        f"{len(result.agents)} agents, {len(result.use_cases)} use cases"
    )
    return result
