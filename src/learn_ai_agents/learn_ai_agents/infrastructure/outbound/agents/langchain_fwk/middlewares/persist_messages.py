"""Async-only persist middleware for LangChain agents.

This middleware implements `awrap_model_call` and `awrap_tool_call` (async
hooks) so it can be used when invoking agents asynchronously via
`ainvoke()`/`astream()`.

Behavior:
- Before model/tool: snapshot input count and persist the incoming message or
  tool input when possible.
- After model/tool: persist newly appended messages and tool outputs.

Persistence is awaited (not fire-and-forget) to provide stronger guarantees
about ordering and durability in async flows.
"""

from __future__ import annotations

import inspect
import logging

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import ToolMessage

from learn_ai_agents.infrastructure.outbound.agents.langchain_fwk.helpers import (
    lc_message_to_domain,
)
from learn_ai_agents.application.outbound_ports.agents.chat_history import (
    ChatHistoryStorePort,
)

logger = logging.getLogger(__name__)


class PersistMessagesMiddleware(AgentMiddleware):
    """Async middleware that persists messages before/after model and tools."""

    def __init__(self, chat_history_persistence: ChatHistoryStorePort | None):
        self.chat_history_persistence = chat_history_persistence

    async def awrap_model_call(self, request, handler):
        state = request.state
        conv_id = getattr(request.runtime.context, "conversation_id", None)

        try:
            messages = state.get("messages", [])
            msg_count = len(messages)
        except Exception:
            messages = []
            msg_count = 0

        # Persist incoming user message if present
        if self.chat_history_persistence and conv_id and msg_count:
            last = messages[-1]
            # Skip persisting tool messages here; tool outputs are
            # persisted in `awrap_tool_call` to preserve ordering and
            # avoid double-saving when the tool output is later
            # included in the model's response messages.
            if not isinstance(last, ToolMessage):
                domain_msg = lc_message_to_domain(last)
                # Let ComponentException propagate - fail fast on persistence errors
                await self.chat_history_persistence.save_message(conv_id, domain_msg)

        # Execute model (handler may be sync or async)
        response = handler(request)
        if inspect.isawaitable(response):
            response = await response

        # Persist newly appended messages
        new_msgs = response.result
        if self.chat_history_persistence and conv_id and new_msgs:
            for m in new_msgs:
                # ToolMessage instances are already persisted by
                # `awrap_tool_call`. Skip them here to prevent
                # duplicate storage.
                if isinstance(m, ToolMessage):
                    continue
                domain_msg = lc_message_to_domain(m)
                # Let ComponentException propagate - fail fast on persistence errors
                await self.chat_history_persistence.save_message(conv_id, domain_msg)

        return response

    async def awrap_tool_call(self, request, handler):
        conv_id = getattr(request.runtime.context, "conversation_id", None)

        # Execute tool (may be sync or async)
        result = handler(request)
        if inspect.isawaitable(result):
            result = await result

        # Persist tool output if it's a ToolMessage
        if isinstance(result, ToolMessage):
            if self.chat_history_persistence and conv_id:
                domain_msg = lc_message_to_domain(result)
                # Let ComponentException propagate - fail fast on persistence errors
                await self.chat_history_persistence.save_message(conv_id, domain_msg)

        return result
