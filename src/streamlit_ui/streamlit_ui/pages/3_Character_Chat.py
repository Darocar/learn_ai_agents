"""Character Chat page for interacting with BG3 characters using RAG.

This page allows users to:
1. Select a BG3 character from a dropdown menu
2. Choose a document_id (knowledge source) for that character
3. Chat with the character using their personality and knowledge base
"""

import os
import uuid
import json
import asyncio
from typing import Optional, List, Any

import streamlit as st
import httpx
from dotenv import load_dotenv

from streamlit_ui.utils.mongo_client import MongoCharacterStore

# --- Setup & config ----------------------------------------------------------
load_dotenv()
API_BASE_URL = os.getenv("AGENTS_API_BASE_URL", "http://127.0.0.1:8000")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("MONGO_DATABASE", "learn_ai_agents")

st.set_page_config(
    page_title="Character Chat - Learn AI Agents", 
    page_icon="🎭", 
    layout="wide"
)

# Minimal styling
st.markdown(
    """
    <style>
      .block-container { padding-top: 1.2rem; }
      .stChatMessage { max-width: 1000px; margin: 0 auto; }
      .chip { display:inline-block; padding: 0.2rem 0.6rem; border-radius: 999px; 
              border: 1px solid rgba(0,0,0,0.08); margin-right: 0.4rem; font-size: 0.85rem;}
      .muted { opacity: .7; }
    </style>
    """,
    unsafe_allow_html=True,
)


# --- MongoDB helpers ---------------------------------------------------------
async def get_available_characters() -> List[str]:
    """Fetch unique character names from MongoDB documents collection."""
    try:
        store = MongoCharacterStore(MONGO_URI, DATABASE_NAME)
        try:
            characters = await store.get_available_characters()
            if not characters:
                st.info(f"📊 MongoDB connected to `{DATABASE_NAME}.documents_bg3_characters` but no characters found.")
            return characters
        finally:
            store.close()
    except Exception as e:
        st.error(f"Failed to fetch characters from MongoDB: {e}")
        st.error(f"MongoDB URI: {MONGO_URI}, Database: {DATABASE_NAME}")
        return []


async def get_documents_for_character(character_name: str) -> List[str]:
    """Fetch available document_ids for a specific character."""
    try:
        store = MongoCharacterStore(MONGO_URI, DATABASE_NAME)
        try:
            return await store.get_documents_for_character(character_name)
        finally:
            store.close()
    except Exception as e:
        st.error(f"Failed to fetch documents for {character_name}: {e}")
        return []


# --- API helpers -------------------------------------------------------------
async def invoke_character_chat_async(
    message: str, 
    character_name: str, 
    document_id: str, 
    conversation_id: str
) -> Optional[dict]:
    """Invoke character chat use case asynchronously."""
    try:
        payload = {
            "config": {"conversation_id": conversation_id},
            "message": message,
            "character_name": character_name,
            "document_id": document_id
        }
        
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{API_BASE_URL}/05_character_chat/ainvoke", 
                json=payload, 
                timeout=60.0
            )
            r.raise_for_status()
            return r.json()
    except Exception as e:
        st.error(f"Error invoking character chat: {e}")
        return None


async def stream_character_chat_async(
    message: str, 
    character_name: str, 
    document_id: str, 
    conversation_id: str
):
    """Stream character chat response via SSE asynchronously."""
    try:
        payload = {
            "config": {"conversation_id": conversation_id},
            "message": message,
            "character_name": character_name,
            "document_id": document_id
        }
        
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST", 
                f"{API_BASE_URL}/05_character_chat/astream", 
                json=payload, 
                timeout=60.0
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if not data_str.strip():
                            continue
                        try:
                            yield json.loads(data_str)
                        except json.JSONDecodeError:
                            continue
    except Exception as e:
        st.error(f"Error streaming character chat: {e}")
        yield None


def invoke_character_chat(
    message: str, 
    character_name: str, 
    document_id: str, 
    conversation_id: str
) -> Optional[dict]:
    """Synchronous wrapper for character chat invocation."""
    return asyncio.run(
        invoke_character_chat_async(message, character_name, document_id, conversation_id)
    )


import httpx
def stream_character_chat(
    message: str,
    character_name: str,
    document_id: str,
    conversation_id: str,
):
    """Synchronous generator that yields SSE events from the FastAPI stream."""
    payload = {
        "config": {"conversation_id": conversation_id},
        "message": message,
        "character_name": character_name,
        "document_id": document_id,
    }
    with httpx.stream(
        "POST",
        f"{API_BASE_URL}/05_character_chat/astream",
        json=payload,
        timeout=None,
    ) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line:
                continue
            if isinstance(line, bytes):
                line = line.decode("utf-8", errors="ignore")
            if not line.startswith("data: "):
                continue
            data_str = line[6:]
            if not data_str.strip():
                continue
            try:
                event = json.loads(data_str)
            except json.JSONDecodeError:
                continue
            yield event


# --- Tool rendering helper ---------------------------------------------------
def render_tool_calls_md(tool_calls: list[dict]) -> str:
    """Render tool calls as formatted markdown.

    Args:
        tool_calls: List of tool call dictionaries.

    Returns:
        Formatted markdown string.
    """
    if not tool_calls:
        return "_No tools were used for this answer._"

    lines: list[str] = []
    for i, call in enumerate(tool_calls, 1):
        name = call.get("name", "<unknown_tool>")
        args = call.get("args") or {}
        output = call.get("output")

        lines.append(f"**{i}. `{name}`**")
        if args:
            lines.append("")
            lines.append("Arguments:")
            lines.append("```json")
            lines.append(json.dumps(args, indent=2, ensure_ascii=False))
            lines.append("```")
        if output is not None:
            # keep it short
            try:
                s = json.dumps(output, ensure_ascii=False)
                if len(s) > 400:
                    s = s[:400] + "…"
            except Exception:
                s = str(output)
                if len(s) > 400:
                    s = s[:400] + "…"
            lines.append("")
            lines.append("Output (preview):")
            lines.append("```")
            lines.append(s)
            lines.append("```")
        lines.append("---")

    return "\n".join(lines)


# --- Session State init ------------------------------------------------------
if "char_conversation_id" not in st.session_state:
    st.session_state.char_conversation_id = str(uuid.uuid4())
if "char_messages" not in st.session_state:
    st.session_state.char_messages = []
if "char_input_key" not in st.session_state:
    st.session_state.char_input_key = f"char_input_{st.session_state.char_conversation_id}"
if "selected_character" not in st.session_state:
    st.session_state.selected_character = None
if "selected_document" not in st.session_state:
    st.session_state.selected_document = None


def _reset_conversation():
    """Reset chat state to a fresh conversation."""
    st.session_state.char_conversation_id = str(uuid.uuid4())
    st.session_state.char_messages = []
    st.session_state.char_input_key = f"char_input_{st.session_state.char_conversation_id}"


def _clear_chat():
    """Clear just the visible chat."""
    st.session_state.char_messages = []


# --- Sidebar (character & document selection) --------------------------------
with st.sidebar:
    st.header("🎭 Character Configuration")
    
    # Fetch available characters
    characters = asyncio.run(get_available_characters())
    
    if not characters:
        st.warning("No characters available. Make sure documents are loaded in MongoDB.")
        st.stop()
    
    # Character selection
    selected_character = st.selectbox(
        "Select Character:",
        options=characters,
        index=0 if characters else None,
        key="character_selector"
    )
    
    # Update selected character in session state
    if selected_character != st.session_state.selected_character:
        st.session_state.selected_character = selected_character
        st.session_state.selected_document = None  # Reset document selection
    
    # Document selection for the chosen character
    if selected_character:
        documents = asyncio.run(get_documents_for_character(selected_character))
        
        if not documents:
            st.warning(f"No documents available for {selected_character}.")
            st.stop()
        
        selected_document = st.selectbox(
            "Select Knowledge Source (document_id):",
            options=documents,
            index=0 if documents else None,
            key="document_selector"
        )
        
        if selected_document:
            st.session_state.selected_document = selected_document
    else:
        st.warning("Please select a character first.")
        st.stop()
    
    st.divider()
    
    # Response mode
    mode = st.radio(
        "Response mode",
        options=["invoke", "stream"],
        index=1,
        help="Invoke returns a full answer; Stream shows tokens as they arrive.",
    )
    
    st.divider()
    
    # Conversation controls
    st.text_input(
        "Conversation ID",
        value=st.session_state.char_conversation_id,
        disabled=True,
        help="Current conversation identifier.",
    )
    
    col1, col2 = st.columns(2)
    with col1:
        st.button("New conversation", use_container_width=True, on_click=_reset_conversation)
    with col2:
        st.button("Clear chat", use_container_width=True, on_click=_clear_chat)
    
    st.divider()
    
    # Display current configuration
    st.markdown("### 📋 Current Configuration")
    st.markdown(f"**Character:** `{selected_character}`")
    st.markdown(f"**Document ID:** `{selected_document}`")
    st.markdown(f"**Mode:** `{mode.upper()}`")


# --- Main chat interface -----------------------------------------------------
st.markdown(
    f"""
    <div class="muted">
      <span class="chip">Character: <b>{selected_character}</b></span>
      <span class="chip">Source: <b>{selected_document}</b></span>
      <span class="chip">Mode: <b>{mode.upper()}</b></span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.title(f"🎭 Chat with {selected_character}")
st.caption(f"Powered by RAG using knowledge from: {selected_document}")

# Render previous messages
for message in st.session_state.char_messages:
    avatar = "🎭" if message["role"] == "assistant" else "🧑‍💻"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        # Show tool calls if this is an assistant message
        if message["role"] == "assistant":
            tc = message.get("tool_calls") or []
            if tc:
                with st.expander("🔧 Tools used in this answer", expanded=False):
                    st.markdown(render_tool_calls_md(tc))

# Chat input & handling
prompt = st.chat_input(
    f"Ask {selected_character} something...", 
    key=st.session_state.char_input_key
)

if prompt and selected_document:
    # Show user message immediately
    st.session_state.char_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)
    
    # Get character response
    with st.chat_message("assistant", avatar="🎭"):
        if mode == "invoke":
            with st.spinner(f"{selected_character} is thinking..."):
                result = invoke_character_chat(
                    prompt,
                    selected_character,
                    selected_document,
                    st.session_state.char_conversation_id
                )
            
            # Extract content from the message object
            answer = (result or {}).get("message", {}).get("content", "No response")
            
            # Get tool_calls (serialized from CharacterChatResultDTO.tool_calls)
            tool_calls = (result or {}).get("tool_calls") or []
            
            st.markdown(answer)
            
            if tool_calls:
                with st.expander("🔧 Tools used in this answer", expanded=False):
                    st.markdown(render_tool_calls_md(tool_calls))
            
            st.session_state.char_messages.append({
                "role": "assistant",
                "content": answer,
                "tool_calls": tool_calls,
            })
        else:
            # Stream mode with agent steps panel
            st.markdown(
                """
                <style>
                  .agent-steps-box {
                    font-size: 0.75rem;
                    background-color: #f5f5f5;
                    border-radius: 8px;
                    padding: 0.5rem 0.75rem;
                    margin-bottom: 0.5rem;
                    border: 1px solid rgba(0,0,0,0.06);
                  }
                  .agent-steps-title {
                    font-weight: 600;
                    font-size: 0.75rem;
                    margin-bottom: 0.25rem;
                    color: #555;
                  }
                  .agent-steps-item {
                    font-size: 0.75rem;
                    color: #666;
                    margin-left: 0.5rem;
                  }
                </style>
                """,
                unsafe_allow_html=True,
            )

            steps_placeholder = st.empty()
            response_placeholder = st.empty()
            tool_log_placeholder = st.empty()
            full_response = ""
            agent_steps: list[str] = []
            tool_calls_for_history: list[dict[str, Any]] = []

            def render_agent_steps(steps: list[str]) -> None:
                if not steps:
                    steps_placeholder.empty()
                    return
                html = ["<div class='agent-steps-box'>"]
                html.append("<div class='agent-steps-title'>Agent steps</div>")
                for s in steps:
                    html.append(f"<div class='agent-steps-item'>• {s}</div>")
                html.append("</div>")
                steps_placeholder.markdown("\n".join(html), unsafe_allow_html=True)

            for event in stream_character_chat(
                prompt,
                selected_character,
                selected_document,
                st.session_state.char_conversation_id
            ):
                if not event:
                    continue
                kind = event.get("kind")
                if kind and kind.endswith("_start"):
                    # Generic handling for any _start event
                    event_name = kind.replace("_start", "")
                    event_info = {k: v for k, v in event.items() if k != "kind"}
                    step_text = f"Event `{event_name}` started. Info: {json.dumps(event_info, ensure_ascii=False)}"
                    agent_steps.append(step_text)
                    render_agent_steps(agent_steps)
                elif kind == "delta" and event.get("delta"):
                    full_response += event["delta"]
                    response_placeholder.markdown(full_response + "▌")
                elif kind == "done":
                    break

            response_placeholder.markdown(full_response or "_(no content)_")
            tool_log_placeholder.empty()
            if tool_calls_for_history:
                with st.expander("🔧 Tools used in this answer", expanded=False):
                    st.markdown(render_tool_calls_md(tool_calls_for_history))
            st.session_state.char_messages.append({
                "role": "assistant",
                "content": full_response or "",
                "tool_calls": tool_calls_for_history if tool_calls_for_history else [],
            })

# --- Footer ------------------------------------------------------------------
st.divider()
st.markdown(
    """
    <div class="muted" style="text-align: center; font-size: 0.85rem;">
        <p>💡 <b>Tip:</b> The character's responses are based on the selected document source.</p>
        <p>Switch between different document_ids to explore different knowledge bases!</p>
    </div>
    """,
    unsafe_allow_html=True,
)
