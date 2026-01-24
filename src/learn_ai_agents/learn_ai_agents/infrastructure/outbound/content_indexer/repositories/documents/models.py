from typing import Any, Optional, Union
from datetime import datetime, timezone

from odmantic import Model, Field, config


class DocumentModel(Model):
    """Odmantic model for document persistence (RAG)."""

    document_id: str
    content: Union[str, bytes]
    metadata: Optional[dict[str, Any]] = None
    character_name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = config.ODMConfigDict({"collection": "documents_bg3_characters"})
