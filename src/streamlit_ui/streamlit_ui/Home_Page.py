"""Main landing page for the Learn AI Agents Streamlit UI."""

import os
import streamlit as st
import httpx
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure the Streamlit page
st.set_page_config(
    page_title="Learn AI Agents",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# API configuration
API_BASE_URL = os.getenv("AGENTS_API_BASE_URL", "http://127.0.0.1:8000")


@st.cache_data(ttl=60)
def fetch_use_cases():
    """Fetch available use cases from the discovery endpoint."""
    try:
        response = httpx.get(f"{API_BASE_URL}/discover/use-cases", timeout=10.0)
        response.raise_for_status()
        return response.json().get("use_cases", [])
    except Exception as e:
        st.error(f"Failed to fetch use cases: {e}")
        return []


# Main page content
st.title("🤖 Learn AI Agents")
st.subheader("A Hexagonal Architecture Approach to Building AI Agents")

st.markdown(
    """
---

## 📚 About This Project

**Learn AI Agents** is a didactic repository designed to teach you how to create AI agents 
following **hexagonal architecture** (ports and adapters pattern). This project demonstrates 
clean architecture principles applied to AI/LLM-based systems.

### 🎯 Purpose

This UI provides an interactive interface to explore and interact with AI agents built using:
- **FastAPI** backend with hexagonal architecture
- **LangChain** and **LangGraph** for agent orchestration
- **Groq** LLM integration
- **Streamlit** for an accessible web interface

### 🏗️ Architecture Highlights

The backend follows hexagonal architecture principles:

- **Inbound Ports**: Define what the application does (e.g., `AgentAnswerPort`)
- **Outbound Ports**: Define what the application needs (e.g., `AgentEngine`, `LLMModel`)
- **Use Cases**: Business logic implementation
- **Infrastructure**: Framework-specific implementations (FastAPI controllers, LangChain adapters)

---
"""
)

# Display available use cases dynamically
st.markdown("## 🚀 Available Use Cases")

use_cases = fetch_use_cases()

if use_cases:
    for uc in use_cases:
        info = uc.get("info", {})
        components = uc.get("components", {})
        
        with st.expander(f"**{info.get('name', 'Unknown')}**", expanded=False):
            st.markdown(f"**Description:** {info.get('description', 'No description available')}")
            st.markdown(f"**API Path:** `{info.get('path_prefix', 'N/A')}`")
            st.markdown(f"**Reference:** `{uc.get('ref', 'N/A')}`")
            
            if components:
                st.markdown("**Dependencies:**")
                for comp_type, comp_refs in components.items():
                    st.markdown(f"- **{comp_type.capitalize()}:**")
                    for alias, ref in comp_refs.items():
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;- `{alias}`: {ref}")
else:
    st.warning("No use cases available. Make sure the API is running.")

st.markdown(
    f"""
---

## 🔧 Technical Stack

**Backend:**
- FastAPI
- LangChain & LangGraph
- Groq LLM
- Python 3.12+

**Frontend:**
- Streamlit
- httpx for API calls

**API Base URL:** `{API_BASE_URL}`

---

## 📖 Learn More

This project demonstrates:
- ✅ Dependency injection with containers
- ✅ Protocol-based interfaces (structural subtyping)
- ✅ Clean separation of concerns
- ✅ Framework-agnostic core business logic
- ✅ Testable architecture
- ✅ Dynamic resource discovery

---

*Ready to explore? Head to the **💬 Chat** page to interact with the agents!*
"""
)
