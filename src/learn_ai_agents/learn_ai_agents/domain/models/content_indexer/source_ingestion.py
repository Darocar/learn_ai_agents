from dataclasses import dataclass, field
from typing import Any, Dict
from datetime import datetime

from learn_ai_agents.infrastructure.helpers.generators import Helper


@dataclass(frozen=True)
class ContentRequest:
    """Domain-level description of the content you want."""

    character_name: str
    document_id: str = field(default_factory=Helper.generate_uuid)
    source: str | None = None  # "web", "file", "db" ... if you need it
    params: Dict[str, Any] | None = None  # extra options (headers, section, etc.)
    created_at: datetime = field(default_factory=Helper.generate_timestamp)


@dataclass(frozen=True)
class Document:
    """Domain-level description of retrieved content."""

    content: str | bytes
    character_name: str
    metadata: Dict[str, Any] | None = None  # extra info about the content
    document_id: str = field(default_factory=Helper.generate_uuid)
