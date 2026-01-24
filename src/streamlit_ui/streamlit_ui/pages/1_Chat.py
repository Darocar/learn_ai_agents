# pages/01_💬_Chat.py
"""Clean chat interface for interacting with AI agents."""

import os
import uuid
import json
import asyncio
from typing import Optional, List, Dict, Any

import streamlit as st
import httpx
from dotenv import load_dotenv

from streamlit_ui.utils.mongo_client import MongoConversationStore

# --- Setup & config ----------------------------------------------------------
load_dotenv()
API_BASE_URL = os.getenv("AGENTS_API_BASE_URL", "http://127.0.0.1:8000")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("MONGO_DATABASE", "learn_ai_agents")

st.set_page_config(page_title="Chat - Learn AI Agents", page_icon="💬", layout="wide")

# Minimal styling for a cleaner look
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

# --- Helpers ----------------------------------------------------------------
@st.cache_data(ttl=60)
def fetch_use_cases():
    """Fetch available use cases from the discovery endpoint."""
    try:
        async def _fetch():
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_BASE_URL}/discover/use-cases", timeout=10.0)
                response.raise_for_status()
                return response.json().get("use_cases", [])
        return asyncio.run(_fetch())
    except Exception as e:
        st.error(f"Failed to fetch use cases: {e}")
        return []

@st.cache_data(ttl=60)
def fetch_agents():
    """Fetch available agents from the discovery endpoint."""
    try:
        async def _fetch():
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_BASE_URL}/discover/agents", timeout=10.0)
                response.raise_for_status()
                return response.json().get("agents", [])
        return asyncio.run(_fetch())
    except Exception as e:
        st.error(f"Failed to fetch agents: {e}")
        return []

async def invoke_use_case_async(use_case_path: str, question: str, conversation_id: str) -> Optional[dict]:
    """Invoke use case asynchronously."""
    try:
        payload = {"message": question, "config": {"conversation_id": conversation_id}}
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{API_BASE_URL}{use_case_path}/ainvoke", json=payload, timeout=60.0)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        st.error(f"Error invoking use case: {e}")
        return None

def invoke_use_case(use_case_path: str, question: str, conversation_id: str) -> Optional[dict]:
    """Invoke use case synchronously (wrapper for async)."""
    return asyncio.run(invoke_use_case_async(use_case_path, question, conversation_id))

async def stream_use_case_async(use_case_path: str, question: str, conversation_id: str):
    """Stream use case response via SSE-like lines asynchronously."""
    try:
        payload = {"message": question, "config": {"conversation_id": conversation_id}}
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", f"{API_BASE_URL}{use_case_path}/astream", json=payload, timeout=60.0) as response:
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
                            # Skip malformed events
                            continue
    except Exception as e:
        st.error(f"Error streaming from use case: {e}")
        yield None

def stream_use_case(use_case_path: str, question: str, conversation_id: str):
    """Synchronous generator that yields SSE events from the FastAPI stream."""
    payload = {"message": question, "config": {"conversation_id": conversation_id}}
    with httpx.stream(
        "POST",
        f"{API_BASE_URL}{use_case_path}/astream",
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

def load_history(conversation_id: str) -> List[Dict[str, str]]:
    """Load history from MongoDB by conversation_id. Return list[{'role','content'}]."""
    try:
        async def _fetch():
            store = MongoConversationStore(MONGO_URI, DATABASE_NAME)
            try:
                messages = await store.get_messages(conversation_id)
                return messages
            finally:
                store.close()
        
        return asyncio.run(_fetch())
    except Exception as e:
        st.warning(f"Could not load conversation history: {e}")
        return []

# --- Session State init ------------------------------------------------------
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_input_key" not in st.session_state:
    st.session_state.chat_input_key = f"chat_input_{st.session_state.conversation_id}"
if "conversation_id_input" not in st.session_state:
    st.session_state.conversation_id_input = st.session_state.conversation_id

def _reset_conversation(new_id: Optional[str] = None):
    """Reset chat state to a fresh conversation."""
    st.session_state.conversation_id = new_id or str(uuid.uuid4())
    st.session_state.conversation_id_input = st.session_state.conversation_id
    st.session_state.messages = []
    # Change chat_input key so Streamlit forgets previous input history
    st.session_state.chat_input_key = f"chat_input_{st.session_state.conversation_id}"

def _apply_conversation_id():
    """Apply manually typed conversation_id and (later) load history."""
    st.session_state.conversation_id = st.session_state.conversation_id_input.strip()
    st.session_state.messages = load_history(st.session_state.conversation_id)
    st.session_state.chat_input_key = f"chat_input_{st.session_state.conversation_id}"

def _clear_chat_only():
    """Clear just the visible chat, keep current conversation_id."""
    st.session_state.messages = []

# --- Sidebar (all controls live here) ---------------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")

    use_cases = fetch_use_cases()
    if not use_cases:
        st.warning("No use cases available. Make sure the API is running.")
        st.stop()

    # Fetch agents for detailed information
    agents = fetch_agents()
    agents_dict = {agent["ref"]: agent for agent in agents}

    # Create dropdown with use cases
    use_case_options = {uc["ref"]: uc for uc in use_cases}
    selected_use_case_ref = st.selectbox(
        "Select a use case:",
        options=list(use_case_options.keys()),
        format_func=lambda ref: use_case_options[ref]["info"].get("name", ref),
    )

    selected_use_case = use_case_options[selected_use_case_ref]

    # Display use case and agent information
    with st.expander("📋 Use Case Details", expanded=True):
        uc_info = selected_use_case.get("info", {})
        uc_components = selected_use_case.get("components", {})
        
        st.markdown(f"**Name:** {uc_info.get('name', 'N/A')}")
        st.markdown(f"**Description:** {uc_info.get('description', 'No description available')}")
        st.markdown(f"**Reference:** `{selected_use_case.get('ref', 'N/A')}`")
        st.markdown(f"**API Path:** `{uc_info.get('path_prefix', 'N/A')}`")
        
        if uc_components:
            st.markdown("**Dependencies:**")
            st.markdown("")  # Empty line for better spacing
            
            # Show agent details if present
            if "agents" in uc_components:
                st.markdown("- **Agents:**")
                for alias, agent_ref in uc_components["agents"].items():
                    agent = agents_dict.get(agent_ref, {})
                    agent_info = agent.get("info", {})
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;- `{alias}`: {agent_ref}")
                    if agent_info:
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;*{agent_info.get('description', 'No description')}*")
                    
                    # Show agent's component dependencies
                    agent_components = agent.get("components", {})
                    if agent_components:
                        for comp_type, comp_refs in agent_components.items():
                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- **{comp_type.capitalize()}:**")
                            # comp_refs can be either a dict (aliased) or a string (direct reference)
                            if isinstance(comp_refs, dict):
                                for comp_alias, comp_ref in comp_refs.items():
                                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- `{comp_alias}`: {comp_ref}")
                            else:
                                # Direct string reference
                                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- {comp_refs}")
            
            # Show other component types
            for comp_type, comp_refs in uc_components.items():
                if comp_type != "agents":
                    st.markdown(f"- **{comp_type.capitalize()}:**")
                    # comp_refs can be either a dict (aliased) or a string (direct reference)
                    if isinstance(comp_refs, dict):
                        for alias, ref in comp_refs.items():
                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;- `{alias}`: {ref}")
                    else:
                        # Direct string reference
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;- {comp_refs}")

    mode = st.radio(
        "Response mode",
        options=["invoke", "stream"],
        index=0,
        help="Invoke returns a full answer; Stream shows tokens as they arrive.",
    )

    st.divider()
    st.text_input(
        "Conversation ID",
        key="conversation_id_input",
        help="Paste an existing ID to restore history (future).",
    )

    colA, colB = st.columns(2)
    with colA:
        st.button("Apply ID", use_container_width=True, on_click=_apply_conversation_id)
    with colB:
        st.button("New conversation", use_container_width=True, on_click=_reset_conversation)

    st.button("Clear chat", use_container_width=True, on_click=_clear_chat_only)

# Get use case path from discovery info
use_case_path = selected_use_case["info"].get("path_prefix", f"/{selected_use_case_ref}")

# --- Header chips (clean, subtle) -------------------------------------------
st.markdown(
    f"""
    <div class="muted">
      <span class="chip">Use Case: <b>{selected_use_case['info'].get('name', selected_use_case_ref)}</b></span>
      <span class="chip">Mode: <b>{mode.upper()}</b></span>
      <span class="chip">Conversation: <b>{st.session_state.conversation_id}</b></span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.title("💬 Chat with AI Agents")
st.caption("Invoke for full reply • Stream for real-time output")

# --- Render previous messages ----------------------------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "🧑‍💻"):
        st.markdown(message["content"])

# --- Chat input & handling ---------------------------------------------------
prompt = st.chat_input("Ask something…", key=st.session_state.chat_input_key)

if prompt:
    # Show user message immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)

    # Use case response
    with st.chat_message("assistant", avatar="🤖"):
        if mode == "invoke":
            with st.spinner("Thinking…"):
                result = invoke_use_case(use_case_path, prompt, st.session_state.conversation_id)
            # Extract content from the message object
            answer = (result or {}).get("message", {}).get("content", "No response")
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
        else:
            response_placeholder = st.empty()
            tool_log_placeholder = st.empty()
            full_response = ""
            tool_log: list[str] = []
            tool_calls_for_history: list[dict[str, Any]] = []

            for event in stream_use_case(use_case_path, prompt, st.session_state.conversation_id):
                if not event:
                    continue
                kind = event.get("kind")
                if kind == "tool_start":
                    tool_name = event.get("tool_name", "<unknown>")
                    tool_input = event.get("tool_input") or {}
                    tool_log.append(f"🔧 **{tool_name}** started")
                    tool_log.append(f"   Input: `{json.dumps(tool_input, ensure_ascii=False)[:100]}`")
                    with tool_log_placeholder.container():
                        st.caption("Tool Activity:")
                        for line in tool_log:
                            st.markdown(line)
                    tool_calls_for_history.append({
                        "name": tool_name,
                        "args": tool_input,
                        "output": None,
                    })
                elif kind == "tool_end":
                    tool_name = event.get("tool_name", "<unknown>")
                    tool_output = event.get("tool_output")
                    tool_log.append(f"✅ **{tool_name}** completed")
                    with tool_log_placeholder.container():
                        st.caption("Tool Activity:")
                        for line in tool_log:
                            st.markdown(line)
                    for tc in tool_calls_for_history:
                        if tc["name"] == tool_name and tc["output"] is None:
                            tc["output"] = tool_output
                            break
                elif kind == "delta" and event.get("delta"):
                    full_response += event.get("delta", "")
                    response_placeholder.markdown(full_response + "▌")
                elif kind == "done":
                    break

            response_placeholder.markdown(full_response or "_(no content)_")
            tool_log_placeholder.empty()
            # Optionally show tool calls summary (add an expander if you want)
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response or "",
                # "tool_calls": tool_calls_for_history if tool_calls_for_history else [],
            })
