# learn_ai_agents — Code Documentation (Branch 03_adding_memory_v2)

> This README explains the **code structure**, **component interactions**, and **implementation patterns** for this branch.

## 🆕 What's New in This Branch

This branch adds:
1. **Memory System**: Complete MongoDB-backed conversation persistence with LangGraph
2. **Database Infrastructure**: Async MongoDB adapters (Motor + Odmantic)
3. **Adding Memory Agent**: LangGraph StateGraph with checkpointing
4. **Enhanced Base Agent**: Support for chat history, tools, and tracing
5. **Discovery System**: Complete hexagonal implementation for system introspection (from Branch 02)
6. **Streamlit UI**: Web interface for interactive agent exploration (from Branch 02)

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

## 🧠 Memory System Architecture

This branch implements a complete conversation memory system using MongoDB and LangGraph:

### Components

#### 1. Database Adapters (`infrastructure/outbound/database/mongo/`)
Two complementary MongoDB adapters:

**MongoEngineAdapter** (Odmantic-based):
```python
class MongoEngineAdapter(DatabaseEngine):
    """MongoDB engine using Odmantic for ODM operations."""
    
    async def connect(self):
        """Initialize async MongoDB connection."""
        self.engine = AIOEngine(motor_client=..., database=...)
    
    def get_engine(self) -> AIOEngine:
        """Return Odmantic engine for model operations."""
        return self.engine
```

**PyMongoAsyncAdapter** (Motor-based):
```python
class PyMongoAsyncAdapter(DatabaseClient):
    """MongoDB client using Motor for direct async operations."""
    
    async def connect(self):
        """Initialize Motor client."""
        self.client = AsyncIOMotorClient(...)
    
    def get_client(self) -> AsyncIOMotorClient:
        """Return Motor client for LangGraph checkpointing."""
        return self.client
```

#### 2. Chat History Persistence (`infrastructure/outbound/chat_history/mongo/`)

**ConversationModel** (Odmantic):
```python
class ConversationModel(Model):
    """Odmantic model for storing conversations."""
    conversation_id: str
    messages: list[MessageModel]
    created_at: datetime
    updated_at: datetime
```

**MongoChatHistoryStore**:
```python
class MongoChatHistoryStore(ChatHistoryStorePort):
    """MongoDB implementation of chat history storage."""
    
    async def save_message(self, conversation_id: str, message: Message):
        """Save a message to conversation history."""
        
    async def load_conversation(self, conversation_id: str) -> Conversation | None:
        """Load full conversation by ID."""
```

#### 3. Checkpointers (`infrastructure/outbound/checkpointers/`)

**MongoCheckpointerAdapter**:
```python
class MongoCheckpointerAdapter:
    """LangGraph checkpointing with MongoDB persistence."""
    
    @staticmethod
    def build(**kwargs) -> BaseCheckpointSaver:
        database = kwargs["database"]  # PyMongoAsyncAdapter
        checkpointer = AsyncMongoDBSaver(
            client=database.get_client(),
            db_name=kwargs["db_name"],
            checkpoint_collection_name=kwargs["checkpoint_collection_name"]
        )
        return checkpointer
```

**MemoryCheckpointerAdapter**:
```python
class MemoryCheckpointerAdapter:
    """In-memory checkpointing for testing/development."""
    
    @staticmethod
    def build(**kwargs) -> BaseCheckpointSaver:
        return MemorySaver()
```

#### 4. Adding Memory Agent (`infrastructure/outbound/agents/langchain_fwk/adding_memory/`)

LangGraph StateGraph-based agent:

**State** (`state.py`):
```python
class State(TypedDict):
    """Graph state for adding memory agent."""
    messages: Annotated[list[BaseMessage], add_messages]
```

**Agent** (`agent.py`):
```python
class AddingMemoryLangGraphAgent(BaseLangChainAgent):
    """Conversational agent with memory using LangGraph."""
    
    def __init__(
        self,
        *,
        config: dict,
        llms: dict[str, ChatModelProvider],
        checkpointer: BaseCheckpointSaver | None = None,
        chat_history_persistence: ChatHistoryStorePort | None = None,
    ):
        self.checkpointer = checkpointer
        super().__init__(config=config, llms=llms, 
                        chat_history_persistence=chat_history_persistence)
    
    def _build_graph(self):
        """Build LangGraph StateGraph with checkpointing."""
        graph = StateGraph(State)
        graph.add_node("chatbot", chatbot_node)
        graph.add_edge(START, "chatbot")
        graph.add_edge("chatbot", END)
        
        self.graph = graph.compile(checkpointer=self.checkpointer)
```

**Node** (`nodes.py`):
```python
async def chatbot_node(state: State, config: RunnableConfig) -> dict[str, list[BaseMessage]]:
    """Execute LLM call with conversation state."""
    llm = config["configurable"]["llm"]
    response = await llm.ainvoke(state["messages"])
    return {"messages": [response]}
```

### Flow: Memory-Enabled Conversation

1. **Request arrives** → `POST /03_adding_memory/invoke`
2. **Use case** loads conversation from MongoDB (if `conversation_id` provided)
3. **Agent**:
   - Loads checkpointed state from MongoDB using `thread_id`
   - Adds system prompt (if first interaction)
   - Adds new user message to state
   - Executes graph → LLM generates response
   - Saves checkpoint back to MongoDB
4. **Use case** saves both user and AI messages to chat history
5. **Response** returned with updated `conversation_id`

### Benefits

- **Stateful conversations**: Context persists across requests
- **Dual persistence**: 
  - LangGraph checkpoints → State snapshots
  - Chat history → Full conversation logs
- **Pluggable checkpointers**: Swap MongoDB ↔ Memory for testing
- **Hexagonal design**: All MongoDB logic isolated in infrastructure

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

## 🏗️ Container-Based Dependency Injection

### Architecture Overview

The application uses a multi-layered container system for dependency injection:

```
AppContainer
├── ComponentsContainer   (LLMs, Tools, Databases)
├── AgentsContainer       (AI Agents using components)
└── UseCasesContainer     (Business logic using agents)
```

### Container Initialization Flow

```python
# app_factory.py - Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Build container asynchronously
    container = await AppContainer.build(settings=app_settings)
    app.state.container = container
    
    try:
        yield
    finally:
        # Clean up resources
        await container.shutdown()
```

### ComponentsContainer

**Purpose**: Manages infrastructure components (LLMs, databases, tools) with lazy loading and caching.

```python
# Defined in settings.yaml
components:
  llms:
    langchain:
      groq:
        constructor:
          module_class: learn_ai_agents.infrastructure.outbound.llms.langchain_fwk.groq.LangchainGroqChatModelAdapter
          api_key: ${GROQ_API_KEY}
        instances:
          default:
            params:
              temperature: 0.1
```

**Key Features**:
- Lazy instantiation (components created on first access)
- Singleton pattern (cached after creation)
- Resolves component references (e.g., `llms.langchain.groq.default`)
- Extracts `SecretStr` values automatically
- Thread-safe with `RLock`

### AgentsContainer

**Purpose**: Creates and manages AI agents that use components.

```python
# Defined in settings.yaml
agents:
  langchain:
    basic_answer:
      info:
        name: Basic Answer Agent
        description: An agent that provides basic answers
      constructor:
        module_class: learn_ai_agents.infrastructure.outbound.agents.langchain_fwk.basic_answer.agent.BasicAnswerLangChainAgent
        components:
          llms:
            default: llms.langchain.groq.default
```

**Component Resolution**:
```python
# Agent receives resolved components, not references
agent = BasicAnswerLangChainAgent(
    config={...},
    llms={
        "default": <LangchainGroqChatModelAdapter instance>
    }
)
```

### UseCasesContainer

**Purpose**: Creates use cases that orchestrate agents for business logic.

```python
# Defined in settings.yaml
use_cases:
  basic_answer:
    info:
      name: Basic Answer Use Case
      path_prefix: /01_basic_answer
      router_factory: learn_ai_agents.infrastructure.inbound.controllers.agents.basic_answer:get_router
    constructor:
      module_class: learn_ai_agents.application.use_cases.agents.basic_answer.basic_answer.BasicAnswerUseCase
      components:
        agents:
          agent: agents.langchain.basic_answer
```

**Use Case Injection**:
```python
# Use case receives resolved agents
use_case = BasicAnswerUseCase(
    agent=<BasicAnswerLangChainAgent instance>,
    mapper=Mapper()
)
```

### Accessing Dependencies in Controllers

Controllers use FastAPI's dependency injection:

```python
# infrastructure/inbound/controllers/dependencies.py
def get_basic_answer_use_case(request: Request) -> BasicAnswerUseCase:
    container = request.app.state.container
    return container.use_cases.get("basic_answer")

# Controller endpoint
@router.post("/ainvoke")
async def ainvoke(
    dto: AnswerRequestDTO,
    use_case: BasicAnswerUseCase = Depends(get_basic_answer_use_case),
):
    return await use_case.ainvoke(dto)
```

---

## 🎯 Creating New Components

### 1. Adding a New LLM Provider

**Step 1**: Create the adapter class

```python
# infrastructure/outbound/llms/langchain_fwk/openai.py
from typing import Any
from langchain_openai import ChatOpenAI
from learn_ai_agents.application.outbound_ports.agents.llm_model import ChatModelProvider

class LangchainOpenAIChatModelAdapter(ChatModelProvider):
    def __init__(self, config: dict[str, Any]) -> None:
        self._model = ChatOpenAI(
            model=config.get("model", "gpt-4"),
            temperature=config.get("temperature", 0.1),
            api_key=config["api_key"],
        )
    
    def get_model(self) -> BaseChatModel:
        return self._model
```

**Step 2**: Add to `settings.yaml`

```yaml
components:
  llms:
    langchain:
      openai:
        constructor:
          module_class: learn_ai_agents.infrastructure.outbound.llms.langchain_fwk.openai.LangchainOpenAIChatModelAdapter
          api_key: ${OPENAI_API_KEY}
        instances:
          default:
            params:
              model: gpt-4
              temperature: 0.2
```

**Step 3**: Reference in agent configuration

```yaml
agents:
  langchain:
    gpt_answer:
      constructor:
        module_class: learn_ai_agents.infrastructure.outbound.agents.langchain_fwk.basic_answer.agent.BasicAnswerLangChainAgent
        components:
          llms:
            default: llms.langchain.openai.default  # Use new LLM
```

### 2. Creating a New Agent

**Step 1**: Implement the agent class

```python
# infrastructure/outbound/agents/langchain_fwk/custom/my_agent.py
from learn_ai_agents.application.outbound_ports.agents.llm_model import ChatModelProvider
from learn_ai_agents.domain.models.agents.config import Config
from learn_ai_agents.domain.models.agents.messages import Message

class MyCustomAgent:
    def __init__(self, *, config: dict, llms: dict[str, ChatModelProvider]):
        self.llm = llms["default"]
        self.custom_setting = config.get("custom_setting", "default")
    
    async def ainvoke(self, new_message: Message, config: Config, **kwargs) -> Message:
        # Your agent logic here
        model = self.llm.get_model()
        response = await model.ainvoke([new_message])
        return Message(
            role=Role.ASSISTANT,
            content=response.content,
            timestamp=Helper.generate_timestamp()
        )
```

**Step 2**: Add to `settings.yaml`

```yaml
agents:
  langchain:
    my_custom:
      info:
        name: My Custom Agent
        description: Does something special
      constructor:
        module_class: learn_ai_agents.infrastructure.outbound.agents.langchain_fwk.custom.my_agent.MyCustomAgent
        components:
          llms:
            default: llms.langchain.groq.default
        config:
          custom_setting: special_value
```

### 3. Creating a New Use Case

**Step 1**: Define DTOs

```python
# application/dtos/agents/my_feature.py
from pydantic import BaseModel

class MyFeatureRequestDTO(BaseModel):
    input_text: str
    config: ConfigDTO

class MyFeatureResultDTO(BaseModel):
    output_text: str
```

**Step 2**: Create the use case

```python
# application/use_cases/agents/my_feature/use_case.py
from learn_ai_agents.application.outbound_ports.agents.agent_engine import AgentEngine

class MyFeatureUseCase:
    def __init__(self, *, agent: AgentEngine, mapper: Mapper):
        self._agent = agent
        self._mapper = mapper
    
    async def ainvoke(self, cmd: MyFeatureRequestDTO) -> MyFeatureResultDTO:
        message = self._mapper.dto_to_message(cmd)
        config = self._mapper.dto_to_config(cmd)
        
        response = await self._agent.ainvoke(message, config)
        
        return self._mapper.message_to_dto(response, config)
```

**Step 3**: Create controller

```python
# infrastructure/inbound/controllers/agents/my_feature.py
from fastapi import APIRouter, Depends

def get_router(use_case_config: UseCaseConfig) -> APIRouter:
    router = APIRouter(prefix=use_case_config.info.path_prefix)
    
    @router.post("/invoke")
    async def invoke(
        dto: MyFeatureRequestDTO,
        use_case: MyFeatureUseCase = Depends(get_my_feature_use_case),
    ):
        return await use_case.ainvoke(dto)
    
    return router
```

**Step 4**: Add dependency injection

```python
# infrastructure/inbound/controllers/dependencies.py
def get_my_feature_use_case(request: Request) -> MyFeatureUseCase:
    container = request.app.state.container
    return container.use_cases.get("my_feature")
```

**Step 5**: Configure in `settings.yaml`

```yaml
use_cases:
  my_feature:
    info:
      name: My Feature Use Case
      description: Implements my custom feature
      path_prefix: /my_feature
      router_factory: learn_ai_agents.infrastructure.inbound.controllers.agents.my_feature:get_router
    constructor:
      module_class: learn_ai_agents.application.use_cases.agents.my_feature.use_case.MyFeatureUseCase
      components:
        agents:
          agent: agents.langchain.my_custom
```

---

## ⚠️ Important Domain Model Changes

### Message Class with Timestamp

The `Message` domain model now requires a `timestamp` field:

```python
from datetime import datetime
from learn_ai_agents.infrastructure.helpers.generators import Helper

# ✅ Correct
message = Message(
    role=Role.USER,
    content="Hello",
    timestamp=Helper.generate_timestamp()  # Required!
)

# ❌ Wrong - will raise TypeError
message = Message(
    role=Role.USER,
    content="Hello"
)
```

**Why?**
- Tracks message creation time for conversation history
- Required for proper conversation management
- Consistent timestamping across the system

### Helper Utilities

```python
from learn_ai_agents.infrastructure.helpers.generators import Helper

# Generate timestamp
timestamp = Helper.generate_timestamp()  # Returns datetime

# Generate UUID
id = Helper.generate_uuid()  # Returns UUID string
```

---

## 🔧 Configuration Best Practices

### Environment Variables

Use environment variables for secrets in `settings.yaml`:

```yaml
components:
  llms:
    langchain:
      groq:
        constructor:
          api_key: ${GROQ_API_KEY}  # Reads from environment
```

### Component References

Use `_ref` suffix for component dependencies:

```yaml
# This won't work - wrong syntax
components:
  tools:
    my_tool:
      params:
        llm: llms.langchain.groq.default  # Wrong!

# ✅ Correct - use _ref suffix
components:
  tools:
    my_tool:
      params:
        llm_ref: llms.langchain.groq.default  # ComponentsContainer resolves this
```

The container automatically:
1. Detects `*_ref` parameters
2. Resolves the reference to the actual component instance
3. Strips the `_ref` suffix when passing to constructor

---

## 📚 Further Reading

- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Dependency Inversion Principle](https://en.wikipedia.org/wiki/Dependency_inversion_principle)
- [Python Protocols](https://peps.python.org/pep-0544/)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Streamlit Documentation](https://docs.streamlit.io/)

---

## 🎯 Key Takeaways

1. **Domain is king**: Start here, keep it pure
2. **Ports define contracts**: Application layer specifies interfaces
3. **Adapters are swappable**: Infrastructure implements ports
4. **Bootstrap wires it all**: DI happens once at startup
5. **Test each layer**: Unit → Integration → E2E
6. **Discovery enables introspection**: Runtime visibility into system configuration
7. **Containers manage lifecycle**: Lazy loading, proper initialization, clean shutdown

This architecture makes the code:
- ✅ Testable (mock any dependency)
- ✅ Maintainable (clear separation)
- ✅ Flexible (swap implementations)
- ✅ Scalable (add features without breaking existing code)
- ✅ Observable (discovery system provides runtime visibility)
- ✅ User-friendly (Streamlit UI for exploration and testing)

---

## 🚀 Next Steps (Branch 03)

The next branch will add:
- **Conversation Memory**: MongoDB-based persistence
- **Agent with Memory**: LangGraph agent using checkpointing
- **New Use Case**: `adding_memory` demonstrating stateful conversations
- **Chat History**: Database adapters and repositories
- **Checkpointers**: MongoDB and in-memory checkpointing implementations
