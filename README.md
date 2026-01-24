# LEARN-AI-AGENTS — Branch `01_create_first_use_case_v2`

This branch implements **the first working use case**: a simple AI chat agent using Hexagonal Architecture.

**What's new in this branch:**
- ✅ Domain models for messages and conversations
- ✅ Application layer: DTOs, ports, and use case
- ✅ Infrastructure: LLM adapter (Groq), Agent engine (LangChain)
- ✅ FastAPI endpoint for chat

> Stack: **Python 3.12** + **uv** + **FastAPI** + **LangChain** + **Groq**

---

## 🎯 What This Branch Demonstrates

Complete flow of implementing a feature in Hexagonal Architecture:

### 1. Domain Layer (Pure Business Logic)
- `Message` and `Conversation` models
- `AgentConfig` value object
- Zero framework dependencies

### 2. Application Layer (Use Case Orchestration)
- **DTOs**: `BasicAnswerInputDto`, `BasicAnswerOutputDto`
- **Inbound Port**: `BasicAnswerInboundPort` protocol
- **Outbound Ports**: `LlmModelPort`, `AgentEnginePort` protocols
- **Use Case**: `BasicAnswerUseCase` orchestrates chat
- **Mapper**: Domain ↔ DTO conversion

### 3. Infrastructure Layer (Not Yet Implemented)
- LLM Adapter (Groq + LangChain)
- Agent Engine (LangChain agent)
- FastAPI controller
- Bootstrap container

---

## 🔄 Request Flow (When Complete)

```
POST /chat → Controller → BasicAnswerUseCase → AgentEngine → Groq LLM → Response
```

---

## 🚀 Quick Start

```bash
# Sync dependencies
uv sync

# Set environment variables
cp .env.example .env
# Add GROQ_API_KEY to .env

# Run (when infrastructure is implemented)
python -m learn_ai_agents
```

---

## 📁 Files Added in This Branch

```
domain/models/
├── config.py          # AgentConfig
└── messages.py        # Message, Conversation, Role

application/
├── dtos/basic_answer.py              # Input/Output DTOs
├── inbound_ports/basic_answer.py     # IBasicAnswerUseCase
├── outbound_ports/
│   ├── agent_engine.py               # IAgentEngine
│   └── llm_model.py                  # ILLMModel
└── use_cases/basic_answer/
    ├── basic_answer.py               # BasicAnswerUseCase
    └── mapper.py                     # Mapper
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
