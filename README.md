# LEARN-AI-AGENTS — Branch `05_vector_database_v2`

This branch adds **RAG (Retrieval-Augmented Generation)** with **Vector Database** and **Embeddings** for knowledge-enhanced agents.

**What's new in this branch:**
- ✅ **Vector Database**: Qdrant integration for semantic search
  - QdrantVectorStoreRepository with COSINE similarity
  - 384-dimensional embeddings (all-MiniLM-L6-v2)
  - Efficient similarity search for RAG
- ✅ **Embeddings**: Sentence transformers for text vectorization
  - SentenceTransformerEmbedder adapter
  - all-MiniLM-L6-v2 model (384 dims, fast, high quality)
  - Document and query embedding support
- ✅ **Content Indexer**: Complete RAG pipeline
  - Source ingestion (Baldur's Gate 3 character data from web)
  - Document splitting (hierarchical markdown splitting)
  - Vectorization (embedding generation and storage)
  - MongoDB repositories for documents and chunks
- ✅ **Character Chat Agent**: RAG-powered conversational agent
  - Vector search tool for retrieving relevant context
  - LangGraph state management with checkpointing
  - Character-specific knowledge from ingested documents
- ✅ **Content Indexer Use Cases**: Three-step RAG workflow
  - `/05_a_source_ingestion`: Fetch and store documents
  - `/05_b_document_splitting`: Split documents into chunks
  - `/05_c_vectorization`: Generate embeddings and store in Qdrant
- **From Branch 04:**
  - ✅ **Tools System**: External tool integration (web search, math, age calculator)
  - ✅ **Adding Tools Agent**: LangGraph with tool calling
- **From Branch 03:**
  - ✅ **Memory System**: MongoDB persistence and LangGraph state management
- **From Branch 02:**
  - ✅ **Streamlit Web UI**: Interactive chat interface
  - ✅ **Discovery System**: System introspection

> Stack: **Python 3.12** + **uv** + **FastAPI** + **LangChain** + **LangGraph** + **MongoDB** + **Qdrant** + **Sentence Transformers** + **Groq** + **Streamlit**

---

## 🎯 What This Branch Demonstrates

### New Features

#### 1. Vector Database Integration
Complete Qdrant setup for semantic search:

**QdrantVectorStoreRepository** (`infrastructure/outbound/content_indexer/repositories/vector_stores/`):
- Store embeddings with metadata (chunk_id, document_id, character)
- Similarity search with configurable top_k
- COSINE distance for semantic similarity
- 384-dimensional vector space (all-MiniLM-L6-v2)

**Configuration**:
```yaml
vector_store_repository:
  qdrant:
    store:
      params:
        host: ${QDRANT_HOST}  # Default: localhost
        port: ${QDRANT_PORT}  # Default: 6333
        vector_size: 384
        distance: COSINE
```

#### 2. Embeddings System
Sentence transformers for high-quality embeddings:

**SentenceTransformerEmbedder** (`infrastructure/outbound/content_indexer/embedders/`):
- Model: all-MiniLM-L6-v2 (384 dimensions)
- Fast inference on CPU
- Batch embedding support
- Normalize vectors for COSINE similarity

**Configuration**:
```yaml
embedders:
  sentence_transformers:
    all_minilm_l6_v2:
      params:
        model_name: all-MiniLM-L6-v2
        device: cpu  # or 'cuda' for GPU
```

#### 3. Content Indexer - Complete RAG Pipeline
Three-phase document processing:

**Phase 1: Source Ingestion** (`/05_a_source_ingestion`):
- Fetch character data from web (Baldur's Gate 3 wiki)
- Store raw documents in MongoDB
- BaldursGate3CharactersAdapter with timeout configuration

**Phase 2: Document Splitting** (`/05_b_document_splitting`):
- Hierarchical markdown splitting
- Configurable chunk_size (1000) and overlap (200)
- Preserve document structure and metadata
- Store chunks in MongoDB

**Phase 3: Vectorization** (`/05_c_vectorization`):
- Generate embeddings for all chunks
- Store vectors in Qdrant with metadata
- Link chunks to documents for traceability

**Repositories**:
- MongoDocumentRepository: Full document storage
- MongoChunkRepository: Chunk storage with document references
- QdrantVectorStoreRepository: Vector embeddings with metadata

#### 4. Character Chat Agent with RAG
LangGraph agent enhanced with vector search:

**CharacterChatLangchainAgent** (`infrastructure/outbound/agents/langchain_fwk/character_chat/`):
- Vector search tool for context retrieval
- Character-specific knowledge base
- State management with conversation history
- MongoDB checkpointing for persistence

**Vector Search Tool**:
```python
# Automatically searches for relevant context
# Returns top-k most similar chunks
# Integrates context into agent responses
```

**Usage**:
```bash
curl -X POST http://localhost:8000/05_character_chat/ainvoke \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me about Shadowheart",
    "character_name": "shadowheart",
    "config": {"conversation_id": "user123"}
  }'
```

#### 5. RAG Workflow Example
Complete end-to-end RAG setup:

**Step 1: Ingest Documents**
```bash
curl -X POST http://localhost:8000/05_a_source_ingestion/execute \
  -H "Content-Type: application/json" \
  -d '{"source_name": "baldurs_gate_3_characters"}'
# Fetches BG3 character data and stores in MongoDB
```

**Step 2: Split Documents**
```bash
curl -X POST http://localhost:8000/05_b_document_splitting/execute \
  -H "Content-Type: application/json" \
  -d '{"splitter_type": "markdown"}'
# Splits documents into 1000-char chunks with 200-char overlap
```

**Step 3: Vectorize Chunks**
```bash
curl -X POST http://localhost:8000/05_c_vectorization/execute \
  -H "Content-Type: application/json" \
  -d '{"embedder_type": "sentence_transformers"}'
# Generates embeddings and stores in Qdrant
```

**Step 4: Chat with Character**
```bash
curl -X POST http://localhost:8000/05_character_chat/ainvoke \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are your abilities?",
    "character_name": "shadowheart",
    "config": {"conversation_id": "user123"}
  }'
# Agent retrieves relevant context and responds
```

### Previous Features (From Branches 02-04)

#### Tools System (Branch 04)

**LangChain Tool Adapters** (`infrastructure/outbound/tools/langchain_fwk/`):
- **LangChainAgeCalculatorToolAdapter**: Wraps age calculator for LangChain
- **LangChainMathExpressionToolAdapter**: Wraps math evaluator for LangChain  
- **LangChainWebSearchToolAdapter**: DuckDuckGo search integration
  - Uses `langchain-community` DuckDuckGoSearchResults
  - Returns JSON results from web search

**Adding Tools Agent** (`infrastructure/outbound/agents/langchain_fwk/adding_tools/`):
- LangGraph StateGraph with tool binding
- Automatic tool selection based on user queries
- Tool execution integrated into conversation flow
- Memory + Tools: Combines checkpointing with tool calls
- State management for tool results

#### 2. Memory System with MongoDB Persistence (from Branch 03)
Complete stateful conversation implementation:
- **Database Adapters**:
  - `MongoEngineAdapter`: Odmantic-based MongoDB engine
  - `PyMongoAsyncAdapter`: Motor-based async MongoDB client
- **Chat History**: 
  - `MongoChatHistoryStore`: Persistent message storage
  - `ConversationModel`: Odmantic model for conversations
- **Checkpointers**:
  - `MongoCheckpointerAdapter`: LangGraph checkpointing with MongoDB
  - `MemoryCheckpointerAdapter`: In-memory checkpointing for testing
- **Adding Memory Agent**: LangGraph StateGraph with:
  - Conversation state management
  - System prompt injection
  - Message persistence
  - Checkpointed state across requests
- **Base Repository Pattern**: `BaseMongoModelRepository` for MongoDB operations
- **Eager Database Initialization**: Databases connect during DI container creation

#### 3. Discovery System (Hexagonal Implementation from Branch 02)
Complete implementation following the architecture:
- **Domain Models**: `Component`, `Agent`, `UseCase` entities
- **Service**: `SettingsResourceDiscovery` reads configuration
- **Use Case**: `DiscoveryUseCase` orchestrates discovery operations
- **API Endpoints**: `/discover/components`, `/discover/agents`, `/discover/use-cases`, `/discover/all`
- **Purpose**: Runtime introspection of the system configuration

#### 4. Streamlit UI (from Branch 02)
Web interface for interacting with agents:
- **Home Page**: System overview with discovery information
- **Chat Page**: 
  - Dynamic use case selection from discovery API
  - Real-time agent information display
  - Invoke and Stream modes
  - Conversation management (ID tracking, clear/reset)
- **Responsive Design**: Clean, minimal interface

#### 5. Development Tools
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
# Add GROQ_API_KEY and MONGODB_URL to .env
# Example: MONGODB_URL=mongodb://localhost:27017

# For streamlit_ui
cp src/streamlit_ui/.env.example src/streamlit_ui/.env
# Configure AGENTS_API_BASE_URL (default: http://127.0.0.1:8000)

# 3. Start MongoDB (if using Docker)
docker run -d -p 27017:27017 --name mongodb mongo:latest

# 4. Run FastAPI backend
cd src/learn_ai_agents
python -m learn_ai_agents

# 5. Run Streamlit UI (in another terminal)
cd src/streamlit_ui
streamlit run streamlit_ui/Home_Page.py
```

**Or use VS Code debugger:**
- Press F5 and select "Run learn_ai_agents" or "Run streamlit"

---

## 📁 Files Added in This Branch

### Memory System
```
# Database Infrastructure
infrastructure/outbound/database/mongo/
├── mongo_engine.py                        # MongoEngineAdapter (Odmantic)
└── pymongo_async.py                       # PyMongoAsyncAdapter (Motor)

# Chat History Persistence
infrastructure/outbound/chat_history/mongo/
├── repository.py                          # MongoChatHistoryStore
└── models.py                              # ConversationModel (Odmantic)

# Checkpointers
infrastructure/outbound/checkpointers/
├── mongo.py                               # MongoCheckpointerAdapter (LangGraph)
└── memory.py                              # MemoryCheckpointerAdapter (in-memory)

# Adding Memory Agent
infrastructure/outbound/agents/langchain_fwk/adding_memory/
├── agent.py                               # AddingMemoryLangGraphAgent
├── nodes.py                               # chatbot_node
├── prompts.py                             # ADDING_MEMORY_PROMPT_TEMPLATE
└── state.py                               # State (TypedDict)

# Application Layer
application/
├── outbound_ports/
│   ├── agents/
│   │   ├── chat_history.py                # ChatHistoryStorePort
│   │   ├── tools.py                       # ToolPort
│   │   └── tracing.py                     # AgentTracingPort
│   └── database/
│       └── __init__.py                    # DatabaseClient, DatabaseEngine
└── use_cases/agents/adding_memory/
    ├── use_case.py                        # AddingMemoryUseCase
    └── mapper.py                          # Mappers for conversions

# Domain Layer
domain/
├── models/agents/
│   └── conversation.py                    # Conversation domain model
└── exceptions/
    ├── _base.py                           # BaseException hierarchy
    ├── agents.py                          # Agent-specific exceptions
    ├── components.py                      # Component exceptions
    └── domain.py                          # Domain exceptions

# Base Persistence
infrastructure/outbound/base_persistence/
└── mongo.py                               # BaseMongoModelRepository
Memory-Enabled Chat Flow
```
POST /03_adding_memory/invoke
  → AddingMemoryUseCase.ainvoke()
  → Load conversation from MongoDB (if exists)
  → AddingMemoryLangGraphAgent.ainvoke()
    → LangGraph StateGraph execution:
      1. Load checkpointed state (if exists)
      2. Add new message to state
      3. Execute chatbot_node (with LLM)
      4. Save checkpoint to MongoDB
  → Save messages to chat history
  → Return AIMessage response
```

### Discovery Flow
```
GET /discover/use-cases 
  → DiscoveryUseCase.discover_use_cases() 
  → SettingsResourceDiscovery.list_use_cases()
  → Returns UseCasesResponseDTO
```

### Basic Chat Flow (Stateless)/agents/
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

### Streamlit UI (from Branch 02)
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

### Tools-Enabled Chat Flow
```
POST /04_adding_tools/invoke
  → AddingToolsUseCase.ainvoke()
  → Load conversation from MongoDB (if exists)
  → AddingToolsLangchainAgent.ainvoke()
    → LangGraph StateGraph execution:
      1. Load checkpointed state (if exists)
    Basic Chat Flow (Stateless from Branch 01)new message to state
      3. Execute chatbot_node:
         - LLM decides if tools are needed
         - If yes: calls tools with arguments
         - Tool execution returns results
         - LLM generates final response with tool results
      4. Save checkpoint to MongoDB
  → Save messages to chat history
  → Return AIMessage response (with tool results if used)
```

**Example Tool Usage**:
- User: "What's 45 * 23?"
  - Agent calls `math_expression` tool with "45 * 23"
  - Tool returns "1035"
  - Agent responds: "The result is 1035"

- User: "How old is someone born on 1990-05-15?"
  - Agent calls `age_calculator` tool with "1990-05-15"
  - Tool returns "34 years old"
  - Agent responds: "They are 34 years old"

- User: "Search for latest AI news"
  - Agent calls `duckduckgo_results_json` tool with query
  - Tool returns web search results
  - Agent summarizes findings

### Memory-Enabled Chat Flow (from Branch 03)
```
POST /03_adding_memory/invoke
  → AddingMemoryUseCase.ainvoke()
  → Load conversation from MongoDB (if exists)
  → AddingMemoryLangGraphAgent.ainvoke()
    → LangGraph StateGraph execution:
      1. Load checkpointed state (if exists)
      2. Add new message to state
      3. Execute chatbot_node (with LLM)
      4. Save checkpoint to MongoDB
  → Save messages to chat history
  → Return AIMessage response
```

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
