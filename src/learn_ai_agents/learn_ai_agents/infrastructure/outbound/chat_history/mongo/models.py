from datetime import datetime
from typing import Any, Dict, List

from odmantic import Model, EmbeddedModel, config


class ConversationMessageModel(EmbeddedModel):
    role: str
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = {}


class ConversationModel(Model):
    conversation_id: str
    messages: List[ConversationMessageModel]

    model_config = config.ODMConfigDict({"collection": "conversations"})
