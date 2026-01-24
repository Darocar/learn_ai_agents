# learn_ai_agents — Code Documentation

> This README explains the **code structure**, **component interactions**, and **implementation patterns** for this branch.

---

## 🏗️ Hexagonal Architecture in Practice

This codebase follows **Ports and Adapters** (Hexagonal Architecture):

```
       ┌─────────────────────────────────────┐
       │     Infrastructure (Adapters)       │
       │  ┌──────────┐        ┌───────────┐  │
       │  │ FastAPI  │        │   Groq    │  │
       │  │Controller│        │  Adapter  │  │
       │  └────┬─────┘        └─────┬─────┘  │
       │       │                    │        │
       │       v                    v        │
       │  ┌──────────────────────────────┐   │
       │  │      Application Layer       │   │
       │  │  ┌──────────┐  ┌──────────┐  │   │
       │  │  │  Ports   │  │ Use Case │  │   │
       │  │  └──────────┘  └──────────┘  │   │
       │  └───────────┬──────────────────┘   │
       │              │                      │
       │              v                      │
       │  ┌──────────────────────────────┐   │
       │  │       Domain Layer           │   │
       │  │  Message, Conversation,      │   │
       │  │  AgentConfig                 │   │
       │  └──────────────────────────────┘   │
       └─────────────────────────────────────┘
```

### Key Principles

1. **Domain is Pure**: No imports from `application/` or `infrastructure/`
2. **Application Defines Interfaces**: Ports are protocols (abstract interfaces)
3. **Infrastructure Implements**: Adapters satisfy port contracts
4. **Dependencies Point Inward**: Infrastructure → Application → Domain

---

## 📦 Layer Breakdown

### Domain Layer (`domain/`)

**Purpose**: Core business concepts with zero external dependencies.

#### `domain/models/messages.py`
```python
from enum import Enum
from dataclasses import dataclass

class Role(Enum):
    """Message role in conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

@dataclass
class Message:
    """A single message in a conversation."""
    role: Role
    content: str

@dataclass
class Conversation:
    """A sequence of messages with optional system instructions."""
    messages: list[Message]
    system_instructions: str | None = None
```

**When to use:**
- Creating/validating messages
- Building conversation history
- Domain logic (e.g., "is this conversation empty?")

#### `domain/models/config.py`
```python
@dataclass
class AgentConfig:
    """Configuration for an agent's behavior."""
    model_name: str
    temperature: float = 0.7
    max_tokens: int = 1000
```

**When to use:**
- Configuring agent parameters
- Passing model settings to adapters

---

### Application Layer (`application/`)

**Purpose**: Orchestrate business workflows using ports (interfaces).

#### DTOs (`application/dtos/basic_answer.py`)

Data Transfer Objects for input/output:

```python
@dataclass
class BasicAnswerInputDto:
    """Input for basic chat interaction."""
    message: str
    conversation_id: str | None = None

@dataclass
class BasicAnswerOutputDto:
    """Output from basic chat interaction."""
    response: str
    conversation_id: str
```

**Why DTOs?**
- Decouple HTTP models from domain models
- Validation happens at the edge (controllers)
- Use cases work with simple, framework-free data

#### Inbound Ports (`application/inbound_ports/basic_answer.py`)

Interfaces that controllers call:

```python
from typing import Protocol

class BasicAnswerInboundPort(Protocol):
    """Interface for basic chat functionality."""
    
    def execute(self, input_dto: BasicAnswerInputDto) -> BasicAnswerOutputDto:
        """Execute a basic chat interaction."""
        ...
```

**Why protocols?**
- Framework-independent contracts
- Easy to mock for testing
- Type-safe interface definitions

#### Outbound Ports (`application/outbound_ports/`)

Interfaces the application needs from infrastructure:

```python
# llm_model.py
class LlmModelPort(Protocol):
    """Interface for LLM interactions."""
    
    def generate(self, prompt: str, config: AgentConfig) -> str:
        """Generate response from LLM."""
        ...

# agent_engine.py
class AgentEnginePort(Protocol):
    """Interface for agent orchestration."""
    
    def run(
        self, 
        message: str, 
        conversation: Conversation,
        config: AgentConfig
    ) -> Message:
        """Run agent with conversation context."""
        ...
```

**Why outbound ports?**
- Application doesn't know about Groq, OpenAI, or LangChain
- Swap implementations without changing use cases
- Test with fake/mock implementations

#### Use Cases (`application/use_cases/basic_answer/`)

Business logic orchestration:

```python
class BasicAnswerUseCase:
    """Orchestrates basic chat interactions."""
    
    def __init__(self, agent_engine: AgentEnginePort):
        self._agent_engine = agent_engine
    
    def execute(self, input_dto: BasicAnswerInputDto) -> BasicAnswerOutputDto:
        # 1. Map DTO to domain
        conversation = Mapper.to_domain(input_dto)
        
        # 2. Execute business logic via port
        response = self._agent_engine.run(
            message=input_dto.message,
            conversation=conversation,
            config=AgentConfig(model_name="groq-llama")
        )
        
        # 3. Map domain back to DTO
        return Mapper.to_dto(response, input_dto.conversation_id)
```

**Key points:**
- Use case receives ports via constructor injection
- Calls ports (not concrete implementations)
- Pure orchestration—no HTTP, DB, or LLM details

#### Mappers (`application/use_cases/basic_answer/mapper.py`)

Convert between DTOs and domain models:

```python
class Mapper:
    """Maps between DTOs and domain models."""
    
    @staticmethod
    def to_domain(dto: BasicAnswerInputDto) -> Conversation:
        """Convert DTO to domain Conversation."""
        return Conversation(
            messages=[Message(role=Role.USER, content=dto.message)],
            system_instructions=None
        )
    
    @staticmethod
    def to_dto(message: Message, conversation_id: str) -> BasicAnswerOutputDto:
        """Convert domain Message to DTO."""
        return BasicAnswerOutputDto(
            response=message.content,
            conversation_id=conversation_id or "new"
        )
```

---

### Infrastructure Layer (`infrastructure/`)

**Purpose**: Implement ports with actual technology (FastAPI, Groq, LangChain).

> ⚠️ **Not yet implemented in this branch.** Coming next!

#### Outbound Adapters (`infrastructure/outbound/`)

Will implement outbound ports:

```python
# llms/groq.py
class GroqAdapter:
    """Groq LLM implementation of LlmModelPort."""
    
    def __init__(self, api_key: str):
        self._client = Groq(api_key=api_key)
    
    def generate(self, prompt: str, config: AgentConfig) -> str:
        response = self._client.chat.completions.create(
            model=config.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=config.temperature
        )
        return response.choices[0].message.content
```

#### Inbound Adapters (`infrastructure/inbound/`)

Will implement FastAPI controllers:

```python
# controllers/basic_answer.py
from fastapi import APIRouter

router = APIRouter()

@router.post("/chat")
def chat(request: ChatRequest, use_case: BasicAnswerInboundPort):
    # Map HTTP model to DTO
    input_dto = BasicAnswerInputDto(
        message=request.message,
        conversation_id=request.conversation_id
    )
    
    # Call use case
    output_dto = use_case.execute(input_dto)
    
    # Map DTO to HTTP response
    return ChatResponse(
        response=output_dto.response,
        conversation_id=output_dto.conversation_id
    )
```

#### Bootstrap (`infrastructure/bootstrap/`)

Dependency injection container:

```python
# app_container.py
def create_basic_answer_use_case(settings: AppSettings) -> BasicAnswerUseCase:
    # 1. Build adapters
    llm_adapter = GroqAdapter(api_key=settings.groq_api_key)
    agent_engine = LangChainAgentEngine(llm=llm_adapter)
    
    # 2. Inject into use case
    return BasicAnswerUseCase(agent_engine=agent_engine)
```

---

## 🔄 Complete Request Flow

When a user sends a chat message:

```
1. HTTP Request arrives
   POST /chat
   {"message": "Hello", "conversation_id": "123"}

2. FastAPI Controller (infrastructure/inbound)
   - Validates HTTP request
   - Maps to BasicAnswerInputDto
   - Calls use_case.execute(dto)

3. BasicAnswerUseCase (application)
   - Maps DTO → Conversation (domain)
   - Calls agent_engine.run(message, conversation, config)

4. LangChainAgentEngine (infrastructure/outbound)
   - Formats conversation for LangChain
   - Calls llm.generate(prompt, config)

5. GroqAdapter (infrastructure/outbound)
   - Makes API call to Groq
   - Returns string response

6. Response flows back up
   - Adapter → Agent Engine → Use Case (as Message)
   - Use Case maps Message → BasicAnswerOutputDto
   - Controller maps DTO → HTTP response

7. HTTP Response returned
   {"response": "Hi there!", "conversation_id": "123"}
```

---

## 🧪 Testing Strategy

### Unit Tests (Domain & Application)

Test domain models and use cases in isolation:

```python
def test_basic_answer_use_case():
    # Arrange: Create fake port
    fake_agent = FakeAgentEngine(
        returns=Message(role=Role.ASSISTANT, content="Test response")
    )
    use_case = BasicAnswerUseCase(agent_engine=fake_agent)
    
    # Act
    input_dto = BasicAnswerInputDto(message="Test", conversation_id="123")
    result = use_case.execute(input_dto)
    
    # Assert
    assert result.response == "Test response"
    assert result.conversation_id == "123"
```

### Integration Tests (Infrastructure)

Test adapters against real services:

```python
def test_groq_adapter():
    adapter = GroqAdapter(api_key=os.getenv("GROQ_API_KEY"))
    config = AgentConfig(model_name="llama-3-70b")
    
    response = adapter.generate("Say hello", config)
    
    assert len(response) > 0
    assert isinstance(response, str)
```

### End-to-End Tests

Test full request flow:

```python
def test_chat_endpoint(client):
    response = client.post(
        "/chat",
        json={"message": "Hello", "conversation_id": "test"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["conversation_id"] == "test"
```

---

## 📋 Code Conventions

### Naming

- **Protocols**: `XxxPort` (e.g., `AgentEnginePort`)
- **DTOs**: `XxxDto` (e.g., `BasicAnswerInputDto`)
- **Use Cases**: `XxxUseCase` (e.g., `BasicAnswerUseCase`)
- **Adapters**: `XxxAdapter` (e.g., `GroqAdapter`)

### Imports

```python
# ✅ Good: Application imports domain
from learn_ai_agents.domain.models.messages import Message

# ✅ Good: Infrastructure imports application
from learn_ai_agents.application.inbound_ports.basic_answer import BasicAnswerInboundPort

# ❌ Bad: Domain imports application
from learn_ai_agents.application.dtos import SomeDto  # NO!

# ❌ Bad: Domain imports infrastructure
from learn_ai_agents.infrastructure.outbound import GroqAdapter  # NO!
```

### Type Hints

```python
# ✅ Modern Python 3.10+ syntax
def process(items: list[str]) -> dict[str, int]:
    ...

def get_user(id: str) -> User | None:
    ...

# ❌ Old syntax (avoid)
from typing import List, Dict, Optional

def process(items: List[str]) -> Dict[str, int]:  # Don't use
    ...
```

---

## 🛠️ Development Workflow

### Adding a New Feature

1. **Start with Domain**
   - Create/update domain models
   - Keep it pure (no dependencies)

2. **Define Application Layer**
   - Create DTOs for input/output
   - Define inbound port (interface)
   - Define needed outbound ports
   - Implement use case

3. **Implement Infrastructure**
   - Create adapters for outbound ports
   - Create controller for inbound port
   - Wire everything in bootstrap

4. **Test Each Layer**
   - Unit test domain & use case
   - Integration test adapters
   - E2E test controller

### Example: Adding Memory

```python
# 1. Domain
@dataclass
class ConversationHistory:
    messages: list[Message]
    created_at: datetime

# 2. Application (outbound port)
class ConversationRepositoryPort(Protocol):
    def save(self, history: ConversationHistory) -> str: ...
    def load(self, id: str) -> ConversationHistory | None: ...

# 3. Infrastructure (adapter)
class MongoConversationRepository:
    def save(self, history: ConversationHistory) -> str:
        # MongoDB implementation
        ...
```

---

## 🔍 Troubleshooting

### "Can't find module"
- Run `uv sync` to install dependencies
- Check `PYTHONPATH` includes `src/`

### "Type errors from mypy"
- Run `make type-check` to see all errors
- Ensure all ports use `Protocol` base class
- Add type hints to all function signatures

### "Use case can't call adapter directly"
- Use cases should only call **ports** (interfaces)
- Adapters are injected via constructor
- Check bootstrap wiring if adapter is None

---

## 📚 Further Reading

- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Dependency Inversion Principle](https://en.wikipedia.org/wiki/Dependency_inversion_principle)
- [Python Protocols](https://peps.python.org/pep-0544/)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)

---

## 🎯 Key Takeaways

1. **Domain is king**: Start here, keep it pure
2. **Ports define contracts**: Application layer specifies interfaces
3. **Adapters are swappable**: Infrastructure implements ports
4. **Bootstrap wires it all**: DI happens once at startup
5. **Test each layer**: Unit → Integration → E2E

This architecture makes the code:
- ✅ Testable (mock any dependency)
- ✅ Maintainable (clear separation)
- ✅ Flexible (swap implementations)
- ✅ Scalable (add features without breaking existing code)
