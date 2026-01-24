# pages/02_📜_Conversation_History.py
"""Search and view conversation history from the database."""

import os
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from streamlit_ui.utils.mongo_client import MongoConversationStore

# --- Setup & config ----------------------------------------------------------
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("MONGO_DATABASE", "learn_ai_agents")

st.set_page_config(
    page_title="Conversation History - Learn AI Agents", 
    page_icon="📜", 
    layout="wide"
)

# Styling
st.markdown(
    """
    <style>
      .block-container { padding-top: 1.2rem; }
      .conversation-card { 
        padding: 1rem; 
        border: 1px solid rgba(0,0,0,0.1); 
        border-radius: 8px; 
        margin-bottom: 1rem;
        background-color: rgba(0,0,0,0.02);
      }
      .message-block {
        padding: 0.8rem;
        margin: 0.5rem 0;
        border-radius: 6px;
      }
      .user-message {
        background-color: rgba(59, 130, 246, 0.1);
        border-left: 3px solid rgba(59, 130, 246, 0.8);
      }
      .assistant-message {
        background-color: rgba(16, 185, 129, 0.1);
        border-left: 3px solid rgba(16, 185, 129, 0.8);
      }
      .system-message {
        background-color: rgba(107, 114, 128, 0.1);
        border-left: 3px solid rgba(107, 114, 128, 0.8);
      }
      .timestamp {
        font-size: 0.75rem;
        color: rgba(0,0,0,0.5);
        margin-top: 0.25rem;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Helper functions --------------------------------------------------------
@st.cache_data(ttl=10)
def fetch_all_conversation_ids() -> List[str]:
    """Fetch all conversation IDs from MongoDB."""
    try:
        async def _fetch():
            store = MongoConversationStore(MONGO_URI, DATABASE_NAME)
            try:
                return await store.get_all_conversation_ids()
            finally:
                store.close()
        
        return asyncio.run(_fetch())
    except Exception as e:
        st.error(f"Failed to fetch conversation IDs: {e}")
        return []


def fetch_conversation_summary(conversation_id: str) -> Optional[Dict[str, Any]]:
    """Fetch conversation summary from MongoDB."""
    try:
        async def _fetch():
            store = MongoConversationStore(MONGO_URI, DATABASE_NAME)
            try:
                return await store.get_conversation_summary(conversation_id)
            finally:
                store.close()
        
        return asyncio.run(_fetch())
    except Exception as e:
        st.error(f"Failed to fetch conversation: {e}")
        return None


def format_timestamp(timestamp: float) -> str:
    """Format timestamp to readable string."""
    if not timestamp:
        return "N/A"
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "Invalid timestamp"


def get_message_class(role: str) -> str:
    """Get CSS class for message based on role."""
    role = role.lower()
    if role in ["user", "human"]:
        return "user-message"
    elif role in ["assistant", "ai"]:
        return "assistant-message"
    elif role == "system":
        return "system-message"
    return ""


# --- Main UI -----------------------------------------------------------------
st.title("📜 Conversation History")
st.caption("Search and view conversation messages from the database")

# --- Sidebar controls --------------------------------------------------------
with st.sidebar:
    st.header("🔍 Search Options")
    
    search_mode = st.radio(
        "Search by:",
        options=["Conversation ID", "Browse All"],
        index=0
    )
    
    conversation_id_input = ""
    search_button = False
    
    if search_mode == "Conversation ID":
        conversation_id_input = st.text_input(
            "Enter Conversation ID:",
            placeholder="e.g., 550e8400-e29b-41d4-a716-446655440000",
            help="Paste the conversation ID you want to view"
        )
        
        search_button = st.button("🔎 Search", use_container_width=True, type="primary")
    else:
        st.info("Fetching all conversations from the database...")
        if st.button("🔄 Refresh List", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

# --- Main content area -------------------------------------------------------
if search_mode == "Conversation ID":
    if search_button and conversation_id_input:
        with st.spinner("Fetching conversation..."):
            summary = fetch_conversation_summary(conversation_id_input.strip())
        
        if not summary:
            st.warning(f"No conversation found with ID: `{conversation_id_input}`")
        else:
            # Display conversation summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Conversation ID", summary["conversation_id"][:8] + "...")
            with col2:
                st.metric("Total Messages", summary["message_count"])
            with col3:
                if summary["last_message_time"]:
                    st.metric("Last Activity", format_timestamp(summary["last_message_time"]))
                else:
                    st.metric("Last Activity", "N/A")
            
            st.divider()
            
            # Display messages
            if summary["messages"]:
                st.subheader("💬 Messages")
                
                for idx, msg in enumerate(summary["messages"]):
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    timestamp = msg.get("timestamp", 0.0)
                    
                    # Map role names
                    display_role = role
                    if role == "human":
                        display_role = "User"
                        emoji = "🧑‍💻"
                    elif role == "ai":
                        display_role = "Assistant"
                        emoji = "🤖"
                    elif role == "user":
                        display_role = "User"
                        emoji = "🧑‍💻"
                    elif role == "assistant":
                        display_role = "Assistant"
                        emoji = "🤖"
                    elif role == "system":
                        display_role = "System"
                        emoji = "⚙️"
                    else:
                        emoji = "💬"
                    
                    message_class = get_message_class(role)
                    
                    st.markdown(
                        f"""
                        <div class="message-block {message_class}">
                            <strong>{emoji} {display_role}</strong> 
                            <span class="timestamp">• {format_timestamp(timestamp)}</span>
                            <div style="margin-top: 0.5rem;">{content}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.info("This conversation has no messages yet.")
    elif not conversation_id_input:
        st.info("👆 Enter a conversation ID in the sidebar and click Search")

else:  # Browse All mode
    all_ids = fetch_all_conversation_ids()
    
    if not all_ids:
        st.info("No conversations found in the database.")
    else:
        st.success(f"Found {len(all_ids)} conversation(s)")
        
        # Display as expandable sections
        st.subheader("📋 All Conversations")
        
        for conv_id in all_ids:
            with st.expander(f"🗨️ Conversation: `{conv_id}`"):
                summary = fetch_conversation_summary(conv_id)
                
                if summary:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Messages:** {summary['message_count']}")
                    with col2:
                        if summary["last_message_time"]:
                            st.write(f"**Last Activity:** {format_timestamp(summary['last_message_time'])}")
                    
                    st.divider()
                    
                    # Show messages
                    for msg in summary["messages"]:
                        role = msg.get("role", "unknown")
                        content = msg.get("content", "")
                        timestamp = msg.get("timestamp", 0.0)
                        
                        # Map role
                        if role in ["human", "user"]:
                            display_role = "User 🧑‍💻"
                        elif role in ["ai", "assistant"]:
                            display_role = "Assistant 🤖"
                        elif role == "system":
                            display_role = "System ⚙️"
                        else:
                            display_role = role
                        
                        with st.chat_message(
                            "user" if role in ["human", "user"] else "assistant",
                            avatar="🧑‍💻" if role in ["human", "user"] else "🤖"
                        ):
                            st.markdown(f"**{display_role}** • *{format_timestamp(timestamp)}*")
                            st.markdown(content)
                else:
                    st.error("Failed to load conversation details")

# --- Footer ------------------------------------------------------------------
st.divider()
st.caption("💡 Tip: Use the Chat page to continue an existing conversation by pasting its ID")
