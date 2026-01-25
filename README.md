# LEARN-AI-AGENTS — Branch `02_adding_streamlit_ui_v2`

This branch adds **Streamlit UI** and **Discovery System** for interactive exploration of the AI agents.

**What's new in this branch:**
- ✅ **Streamlit Web UI**: Interactive chat interface with use case selection
- ✅ **Discovery System**: Complete hexagonal implementation for system introspection
  - List all components (LLMs, databases, etc.)
  - List all agents with their dependencies
  - List all use cases with routing information
- ✅ **VS Code Launch Configurations**: Debug both FastAPI and Streamlit
- ✅ **Monorepo Structure**: Workspace with multiple packages (`learn_ai_agents`, `streamlit_ui`)

> Stack: **Python 3.12** + **uv** + **FastAPI** + **LangChain** + **Groq** + **Streamlit**

---

## 🎯 What This Branch Demonstrates

### New Features

#### 1. Discovery System (Hexagonal Implementation)
Complete implementation following the architecture:
- **Domain Models**: `Component`, `Agent`, `UseCase` entities
- **Service**: `SettingsResourceDiscovery` reads configuration
- **Use Case**: `DiscoveryUseCase` orchestrates discovery operations
- **API Endpoints**: `/discover/components`, `/discover/agents`, `/discover/use-cases`, `/discover/all`
- **Purpose**: Runtime introspection of the system configuration

#### 2. Streamlit UI
Web interface for interacting with agents:
- **Home Page**: System overview with discovery information
- **Chat Page**: 
  - Dynamic use case selection from discovery API
  - Real-time agent information display
  - Invoke and Stream modes
  - Conversation management (ID tracking, clear/reset)
- **Responsive Design**: Clean, minimal interface

#### 3. Development Tools
- **Launch Configurations**: `.vscode/launch.json` for debugging
  - `Run learn_ai_agents`: Debug FastAPI application
  - `Run streamlit`: Debug Streamlit UI
- **Environment Setup**: Separate `.env` files for each package

---

## 🚀 Quick Start

```bash
# 1. Sync all workspace dependencies
uv sync

# 2. Set up environment variables
# For learn_ai_agents
cp .env.example .env
# Add GROQ_API_KEY to .env

# For streamlit_ui
cp src/streamlit_ui/.env.example src/streamlit_ui/.env
# Configure AGENTS_API_BASE_URL (default: http://127.0.0.1:8000)

# 3. Run FastAPI backend
cd src/learn_ai_agents
python -m learn_ai_agents

# 4. Run Streamlit UI (in another terminal)
cd src/streamlit_ui
streamlit run streamlit_ui/Home_Page.py
```

**Or use VS Code debugger:**
- Press F5 and select "Run learn_ai_agents" or "Run streamlit"

---

## 📁 Files Added in This Branch

### Discovery System
```
domain/models/agents/
└── discovery.py                           # Component, Agent, UseCase models

application/
├── dtos/discovery/
│   └── discovery.py                       # Discovery DTOs
└── use_cases/discovery/
    ├── __init__.py
    └── use_case.py                        # DiscoveryUseCase

domain/services/agents/
└── settings_resource_discovery.py        # SettingsResourceDiscovery service

infrastructure/inbound/controllers/discovery/
├── __init__.py
└── discovery.py                           # Discovery API router
```

### Streamlit UI
```
src/streamlit_ui/
├── .env.example                           # Environment template
├── pyproject.toml                         # Streamlit dependencies
├── README.md                              # UI-specific documentation
└── streamlit_ui/
    ├── __init__.py
    ├── Home_Page.py                       # Landing page
    ├── pages/
    │   ├── 1_Chat.py                      # Chat interface
    │   ├── 2_Conversation_History.py      # (MongoDB-based, disabled for now)
    │   └── 3_Character_Chat.py            # (MongoDB-based, disabled for now)
    └── utils/
        ├── __init__.py
        └── mongo_client.py                # MongoDB utilities (for future use)
```

### Configuration & Tools
```
.vscode/
└── launch.json                            # VS Code debug configurations

pyproject.toml                             # Updated with streamlit_ui workspace member
```

---

## 🔄 Request Flow

### Discovery Flow
```
GET /discover/use-cases 
  → DiscoveryUseCase.discover_use_cases() 
  → SettingsResourceDiscovery.list_use_cases()
  → Returns UseCasesResponseDTO
```

### Chat Flow
```
Streamlit UI → GET /discover/use-cases → Display use case selector
User selects use case + types message
Streamlit UI → POST /{use_case_path}/invoke → BasicAnswerUseCase → Agent → LLM → Response
```

---

## Hexagonal Architecture Overview

```
domain/             # Pure business logic (no frameworks)
├── models/         # Entities & value objects
└── services/       # Domain policies

application/        # Use case orchestration
├── dtos/           # Input/output data structures
├── inbound_ports/  # Interfaces exposed to controllers
├── outbound_ports/ # Interfaces for external dependencies
└── use_cases/      # Business workflows

infrastructure/     # Framework & vendor code
├── inbound/        # Controllers (FastAPI)
├── outbound/       # Adapters (LLM, DB, etc.)
└── bootstrap/      # Dependency injection
```

See [src/learn_ai_agents/README.md](src/learn_ai_agents/README.md) for detailed code documentation.

---

## Development Commands

```bash
# Install dependencies
uv sync

# Code quality
make format     # Auto-fix formatting
make lint       # Check code quality
make type-check # Run mypy
make verify     # Run all checks

# Run application (when complete)
python -m learn_ai_agents
```

---

## Full Repository Structure

```
.
├── data/                       # Sample corpora, fixtures, small test assets (NOT large datasets)
├── notebooks/                  # Exploration / spike notebooks (kept out of the src/ code)
├── src/
│   └── learn_ai_agents/
│       ├── application/        # The "use-cases" circle: ports + orchestrators (no vendor code)
│       │   ├── dtos/           # Input/Output DTOs for use cases (transport-agnostic shapes)
│       │   ├── inbound_ports/  # Interfaces the app exposes (controllers call these)
│       │   ├── outbound_ports/ # Interfaces the app needs (LLM, vector, repos, tracing, tools)
│       │   └── use_cases/      # Application services (implement inbound ports; orchestrate domain)
│       │
│       ├── domain/             # Pure business language: entities, value objects, domain services
│       │   ├── models/         # Conversation, Message, ToolCall, etc.
│       │   ├── services/       # Policies & domain services (no I/O, no framework types)
│       │   ├── exceptions.py   # Domain-specific error types
│       │   └── utils.py        # Tiny, pure helpers shared across domain code
│       │
│       ├── infrastructure/     # Adapters & glue (edge of the hexagon)
│       │   ├── inbound/        # Drivers (e.g., FastAPI routers) that CALL inbound ports
│       │   └── outbound/       # Tech adapters that IMPLEMENT outbound ports
│       │       ├── llm/        # LLM adapters (LangChain/PydanticAI/OpenAI/Groq…)
│       │       ├── persistence/# Conversation/history stores, vector DBs, caches
│       │       ├── tools/      # Concrete tool adapters (S3, HTTP APIs, calendars, etc.)
│       │       └── tracers/    # Observability/telemetry adapters (Phoenix, Opik…)
│       │
│       ├── bootstrap/          # Composition root: build adapters, inject into use cases
│       └── __init__.py
│
├── static/                     # Diagrams, sample JSONs for docs, etc. (served/read-only)
├── tests/                      # unit/, integration/, e2e/ (TDD-friendly from day one)
│
├── .env.example                # Env var template (copy to .env locally; never commit secrets)
├── .dockerignore
├── .gitignore
├── .pre-commit-config.yaml     # Linters/formatters/hooks (e.g., Ruff, mypy) wired via pre-commit
├── Dockerfile                  # Image with Python 3.12 + uv
├── docker-compose.yaml         # Local stack orchestration (API + optional backing services)
├── Makefile                    # One-liners: `make setup`, `make test`, `make run`, etc.
├── pyproject.toml              # Project metadata & deps (PEP 621); uv reads this
└── README.md                   # You’re here
```

### Layer responsibilities (at a glance)

- **application/** — Use‑case layer (a.k.a. “application services”). Contains:
  - **inbound_ports/**: *input boundaries* (interfaces) that controllers call.
  - **use_cases/**: classes that **implement inbound ports** and orchestrate domain + outbound ports.
  - **outbound_ports/**: the app’s needs (LLM, vector index, repositories, observability, tools) expressed as interfaces.
  - **dtos/**: input/output data shapes used by use cases (keeps HTTP models out of the core).
- **domain/** — Pure business concepts: entities/value objects (`models/`) and policies (`services/`). Absolutely no vendor or framework imports.
- **infrastructure/** — Adapters on the edge:
  - **inbound/**: FastAPI routers/controllers (they validate, map DTOs, then **call inbound ports**).
  - **outbound/**: concrete tech adapters that **implement outbound ports** (LLM providers, DBs, tracers, tools).
- **bootstrap/** — The **Composition Root**. Instantiate adapters and inject them into use cases (constructor injection). Only this layer knows which vendor you chose. The rest of the app stays agnostic.

---

## How a request flows (end‑to‑end)

1. **FastAPI router** (`infrastructure/inbound/`) receives HTTP, validates input models, and maps them to **application DTOs**.  
2. Router **calls an inbound port** (`application/inbound_ports/`).  
3. The **use case** (`application/use_cases/`) implements that port: loads domain state, applies policies, and calls **outbound ports** for I/O.  
4. **Outbound adapters** (`infrastructure/outbound/`) talk to real tech (LLM, DB, tracer, tools) and return domain‑friendly results.  
5. The use case returns a result DTO; the router maps it to an HTTP response model.

This keeps controllers thin and the core independent of frameworks/providers.

---

## Python 3.12 + uv quickstart

> Requires: [uv](https://docs.astral.sh/uv/) installed and available on your PATH.

```bash
# 1) Ensure Python 3.12 is installed via uv
uv python install 3.12

# 2) Create & sync the project environment from pyproject.toml
uv sync

# 3) (Later) run the API once the first route exists
uv run uvicorn learn_ai_agents.<your_api_module>:app --reload
```

**Notes**
- `pyproject.toml` follows **PEP 621** so tools (including uv) can read project metadata & dependencies.
- `uv sync` creates an isolated `.venv/` and keeps it in sync with the `pyproject.toml`.
- `Makefile` provides convenient shortcuts once targets are added.

---

## Prerequisites & External Dependencies

This project integrates with several external services and tools. Here's what you need to set up:

### 🤖 Groq (LLM Provider)

**What it is**: Cloud-based LLM inference platform providing fast access to open models like Llama 3.3.

**Setup**:
1. Create an account at [https://console.groq.com](https://console.groq.com)
2. Navigate to API Keys section
3. Generate a new API key
4. Add to your `.env` file:
   ```bash
   GROQ_API_KEY=your_groq_api_key_here
   ```

**Why we use it**: Groq provides fast, cost-effective access to state-of-the-art open-source LLMs with OpenAI-compatible API.

### 🔭 Opik (Observability & Tracing)

**What it is**: Agent observability platform for tracing LLM calls, tool executions, and conversation flows.

**Setup**:
1. Create an account at [https://www.comet.com/opik](https://www.comet.com/opik)
2. Create a new workspace for your project
3. Go to Settings → API Keys
4. Generate an API key
5. Add to your `.env` file:
   ```bash
   OPIK_API_KEY=your_opik_api_key_here
   OPIK_WORKSPACE=your_workspace_name
   ```

**Why we use it**: Opik provides deep visibility into agent execution, helping debug issues and optimize performance.

**Note**: Available from Branch 06 onwards.

### 🐳 MongoDB (Conversation Persistence)

**What it is**: NoSQL database for storing conversation history and checkpoints.

**Setup**:
1. **Install Docker**: Ensure Docker is installed on your system
   - [Docker Desktop](https://www.docker.com/products/docker-desktop) (Mac/Windows)
   - [Docker Engine](https://docs.docker.com/engine/install/) (Linux)

2. **Use docker-compose**: MongoDB is pre-configured in `docker-compose.yaml`
   ```bash
   # Start MongoDB (and other services)
   docker-compose up -d mongodb
   
   # Stop services
   docker-compose down
   ```

3. **Connection string**: Already configured in `docker-compose.yaml`
   ```yaml
   mongodb:
     image: mongo:7
     ports:
       - "27017:27017"
   ```

**Why we use it**: MongoDB provides flexible document storage for conversation history and LangGraph checkpoints.

**Note**: Available from Branch 03 onwards.

### 🔍 Qdrant (Vector Database)

**What it is**: Vector database for semantic search and RAG (Retrieval Augmented Generation).

**Setup**:
1. **Docker image**: Qdrant runs as a Docker container (included in `docker-compose.yaml`)
   ```bash
   # Start Qdrant
   docker-compose up -d qdrant
   ```

2. **Configuration** in `docker-compose.yaml`:
   ```yaml
   qdrant:
     image: qdrant/qdrant:latest
     ports:
       - "6333:6333"
     volumes:
       - qdrant_storage:/qdrant/storage
   ```

3. **Access**: 
   - API: `http://localhost:6333`
   - Dashboard: `http://localhost:6333/dashboard`

**Why we use it**: Qdrant enables semantic search over character knowledge, powering our RAG-based chat agents.

**Note**: Available from Branch 05 onwards.

### 🐳 Docker Quick Reference

**Start all services**:
```bash
docker-compose up -d
```

**Check running services**:
```bash
docker-compose ps
```

**View logs**:
```bash
docker-compose logs -f
```

**Stop all services**:
```bash
docker-compose down
```

**Clean up (remove volumes)**:
```bash
docker-compose down -v
```

---

## Configuration & environment

- Copy **`.env.example`** to **`.env`** and fill values for local dev (API keys, DB URLs, etc.).  
- Add a config loader (e.g., Pydantic `BaseSettings`) in `bootstrap/` to read `env` and/or `YAML` and construct adapters accordingly.

---

## Testing strategy (once code lands)

- **unit/**: domain models & use cases (replace outbound ports with fakes).  
- **integration/**: each adapter against a real sandbox (e.g., OpenAI test, local Qdrant).  
- **e2e/**: FastAPI routes calling real use cases with a test container stack.

---

## Conventions

- **Ports are framework‑free** (`Protocol`/ABC in `application/…_ports/`).  
- **Controllers call inbound ports.** Outbound adapters implement outbound ports.  
- **No service locator**: all wiring happens once in `bootstrap/` (constructor injection).  
- **Domain stays pure**: avoid importing infra/application from domain.

---

Happy building! Subsequent branches will add the first use case, a small FastAPI router, and a couple of outbound adapters (LLM + persistence) to demonstrate the full ports‑and‑adapters flow.


## Credits

This package was inspired by [Cookiecutter](https://github.com/audreyfeldroy/cookiecutter) and the [agent-api-cookiecutter](https://github.com/neural-maze/agent-api-cookiecutter) project template.
