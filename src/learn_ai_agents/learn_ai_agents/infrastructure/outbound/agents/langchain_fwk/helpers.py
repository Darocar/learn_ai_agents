"""Helper functions for LangChain integration.

This module provides utilities for converting between domain models and
LangChain-specific types, enabling seamless integration with the LangChain framework.
"""

# Adjust imports to your package names
import json
from datetime import datetime
from collections.abc import Mapping
from typing import Any, Dict, List

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.runnables import RunnableConfig
from learn_ai_agents.domain.models.agents.config import Config
from learn_ai_agents.domain.models.agents.messages import ChunkDelta, Message, Role

# Map domain Role -> LangChain message class
ROLE_TO_LC: Mapping[Role, type[BaseMessage]] = {
    Role.SYSTEM: SystemMessage,
    Role.USER: HumanMessage,
    Role.ASSISTANT: AIMessage,
    Role.TOOL: ToolMessage,
}


def to_lc_state(
    messages: list[BaseMessage],
    **extra: Any,
) -> dict[str, Any]:
    """Build the agent state from LC messages + any extra fields.

    For now we only use 'messages', but this lets you add
    extra keys later without touching all callsites.

    Args:
        messages: List of LangChain BaseMessage objects.
        **extra: Additional state fields (for future extensibility).

    Returns:
        State dictionary compatible with AgentState.
    """
    state: dict[str, Any] = {"messages": messages}
    if extra:
        state.update(extra)
    return state


def to_lc_messages(messages: list[Message]) -> list[BaseMessage]:
    """Convert domain messages to LangChain BaseMessage instances.

    Translates our domain Message objects (with Role enum) into LangChain's
    message types for framework compatibility.

    Args:
        messages: List of domain Message objects to convert.

    Returns:
        List of LangChain BaseMessage instances.

    Raises:
        ValueError: If an unsupported role is encountered.
    """
    lc_msgs: list[BaseMessage] = []
    for m in messages:
        cls = ROLE_TO_LC.get(m.role)
        if cls is None:
            raise ValueError(f"Unsupported role: {m.role}")

        # ToolMessage typically requires a tool_call_id; for didactic cases use a placeholder.
        if cls is ToolMessage:
            lc_msgs.append(ToolMessage(content=m.content, tool_call_id="tool-unknown"))
        else:
            lc_msgs.append(cls(content=m.content))
    return lc_msgs


def to_domain_message(
    kind: str,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> Message:
    """Convert a string role and content to a domain Message.

    Args:
        kind: Role identifier (case-insensitive, e.g., 'assistant', 'user').
        content: The message content.
        metadata: Optional metadata dictionary (e.g., tool_calls).

    Returns:
        A domain Message object.

    Raises:
        ValueError: If the role string is invalid.
    """
    try:
        role = Role(kind.lower())  # validates and converts to enum
    except ValueError as e:
        raise ValueError(f"Unsupported role: {kind!r}") from e
    return Message(role=role, content=content, timestamp=datetime.now(), metadata=metadata)


def lc_message_to_domain(lc_message: BaseMessage) -> Message:
    """Convert a LangChain BaseMessage to a domain Message.

    Args:
        lc_message: LangChain message to convert.

    Returns:
        A domain Message object.

    Raises:
        ValueError: If the message type is unsupported.
    """
    # Determine the role based on message type
    metadata: Dict[str, Any] = {}
    if isinstance(lc_message, HumanMessage):
        role = Role.USER
    elif isinstance(lc_message, AIMessage):
        role = Role.ASSISTANT
        # Extract tool_calls if present
        if hasattr(lc_message, "tool_calls"):
            metadata["tool_calls"] = getattr(lc_message, "tool_calls", None)
        # Extract usage metadata if present
        if hasattr(lc_message, "usage_metadata"):
            metadata["usage_metadata"] = getattr(lc_message, "usage_metadata", None)
    elif isinstance(lc_message, SystemMessage):
        role = Role.SYSTEM
    elif isinstance(lc_message, ToolMessage):
        role = Role.TOOL
        # Extract tool name and input params if present
        if hasattr(lc_message, "tool_call_id"):
            metadata["tool_call_id"] = getattr(lc_message, "tool_call_id", None)
        if hasattr(lc_message, "name"):
            metadata["tool_name"] = getattr(lc_message, "name", None)
        if hasattr(lc_message, "parameters"):
            metadata["tool_input"] = getattr(lc_message, "parameters", None)
        # Extract usage metadata if present
        if hasattr(lc_message, "usage_metadata"):
            metadata["usage_metadata"] = getattr(lc_message, "usage_metadata", None)
    else:
        raise ValueError(f"Unsupported LangChain message type: {type(lc_message)}")

    # Extract content
    content = content_to_text(lc_message.content)

    # Extract timestamp from additional_kwargs if available, otherwise use current time
    timestamp = datetime.now()
    if hasattr(lc_message, "additional_kwargs") and lc_message.additional_kwargs:
        timestamp = lc_message.additional_kwargs.get("ts", timestamp)

    # If there is extra metadata in additional_kwargs, merge it
    if hasattr(lc_message, "additional_kwargs") and lc_message.additional_kwargs:
        for k, v in lc_message.additional_kwargs.items():
            if k != "ts":
                metadata[k] = v

    return Message(role=role, content=content, timestamp=timestamp, metadata=metadata)


def to_lc_config(config: Config) -> RunnableConfig:
    """Convert domain Config to LangChain-compatible configuration.

    Translates our domain configuration into the format expected by
    LangChain's runnable interface.

    Args:
        config: Domain configuration object.

    Returns:
        LangChain RunnableConfig dictionary.
    """
    # Example conversion; adapt as needed
    return RunnableConfig({"configurable": {"thread_id": config.conversation_id}})


def chunk_to_domain(text_fragment: str | None) -> ChunkDelta:
    """Convert a text fragment to a domain ChunkDelta.

    Args:
        text_fragment: The text fragment from a streaming response.

    Returns:
        A ChunkDelta domain object with kind="text".
    """
    return ChunkDelta(kind="text", text=text_fragment)


def content_to_text(content: Any) -> str:
    """Convert LangChain message content to plain text.

    LangChain message content can be a string, list of parts, or dictionary.
    This function performs best-effort coercion to plain text.

    Args:
        content: The content from a LangChain message (various types possible).

    Returns:
        Plain text string representation of the content.
    """
    if isinstance(content, str):
        return content

    # LC can return a list of parts: strings or dicts like {"type": "text", "text": "..."}
    if isinstance(content, list):
        parts: list[str] = []
        for p in content:
            if isinstance(p, str):
                parts.append(p)
            elif isinstance(p, dict):
                # Prefer common keys seen in LC content parts
                if "text" in p:
                    parts.append(str(p["text"]))
                elif "content" in p:
                    parts.append(str(p["content"]))
                else:
                    parts.append(json.dumps(p, ensure_ascii=False))
            else:
                parts.append(str(p))
        return "".join(parts)

    if isinstance(content, dict):
        # If it's a single dict part, extract text if present, otherwise JSON it
        if "text" in content:
            return str(content["text"])
        if "content" in content:
            return str(content["content"])
        return json.dumps(content, ensure_ascii=False)

    return str(content)


def safe_jsonable(obj: Any) -> Any:
    """Make sure the object is JSON-serializable.

    Args:
        obj: The object to sanitize.

    Returns:
        A JSON-serializable version of the object.
    """
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        try:
            return str(obj)
        except Exception:
            return "<non-serializable>"


def extract_tool_calls(
    result_messages: List[BaseMessage],
    input_message_count: int,
) -> List[Dict[str, Any]]:
    """Extract tool calls (name, args, output) from LC messages.

    We only look at messages created during this run
    (i.e. from input_message_count onwards).

    Args:
        result_messages: All messages after agent execution.
        input_message_count: Number of messages that were in the input.

    Returns:
        List of dictionaries containing sanitized tool call information.
    """
    new_messages = result_messages[input_message_count:]
    index: Dict[str, Dict[str, Any]] = {}

    # 1) collect tool_calls from AIMessage.tool_calls
    for msg in new_messages:
        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            for call in msg.tool_calls:
                # call may be a ToolCall object or a dict
                name = getattr(call, "name", None) or call.get("name")
                args = getattr(call, "args", None) or call.get("args")
                call_id = getattr(call, "id", None) or call.get("id")

                # best-effort JSON decode
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except Exception:
                        pass

                # Sanitize args to ensure JSON-serializable
                args_safe = safe_jsonable(args)

                index[call_id or f"no-id-{len(index)}"] = {
                    "id": call_id,
                    "name": name,
                    "args": args_safe,
                    "output": None,
                }

    # 2) attach ToolMessage contents as outputs (sanitized)
    for msg in new_messages:
        if isinstance(msg, ToolMessage):
            tc_id = getattr(msg, "tool_call_id", None)
            if tc_id and tc_id in index:
                index[tc_id]["output"] = safe_jsonable(msg.content)

    return list(index.values())


def get_new_lc_messages(
    result_state: dict[str, Any],
    input_message_count: int,
) -> list[BaseMessage]:
    """Return only the messages that were added by the agent run.

    Args:
        result_state: The state dictionary returned by the agent.
        input_message_count: Number of messages that were in the input.

    Returns:
        List of new BaseMessage objects added by the agent.
    """
    all_messages: list[BaseMessage] = result_state["messages"]
    return all_messages[input_message_count:]
