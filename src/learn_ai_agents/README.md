# learn_ai_agents — Code Documentation (Branch 08_llm_evaluation_v2)

> This README explains the **code structure**, **component interactions**, and **implementation patterns** for this branch.

## 🆕 What's New in This Branch

**Branch 08 adds:**
1. **RAGAS Integration**: Industry-standard RAG evaluation metrics (Context Precision, Faithfulness)
2. **Evaluation Datasets**: Structured JSON datasets for testing RAG quality
3. **Evaluation Script**: Automated workflow for batch evaluation with Groq LLM
4. **Results Tracking**: JSON output for reproducible evaluation results

**Branch 07 added:**
1. **Exception Hierarchy**: Structured error handling with domain-specific exceptions
2. **Retry Mechanisms**: Exponential backoff for resilient LLM and tool operations
3. **Robust Agent**: Production-ready agent with error recovery and retry logic
4. **Exception Handlers**: FastAPI middleware for clean HTTP error responses
5. **Unit Tests**: Comprehensive test suite for error scenarios

**Branch 06 added:**
1. **Tracing System**: Agent observability with Opik integration
2. **Agent Tracing**: Framework-agnostic tracing port and adapters
3. **Thread-Based Tracking**: Traces span entire conversation threads
4. **Middleware Utilities**: Helper functions for LangChain integration

**Branch 05 added:**
1. **Vector Database System**: Qdrant integration for semantic search
2. **Embeddings System**: Sentence transformers for text vectorization (all-MiniLM-L6-v2)
3. **Content Indexer**: Complete RAG pipeline (source ingestion, document splitting, vectorization)
4. **Character Chat Agent**: RAG-powered conversational agent with vector search tool
5. **Vector Search Tool**: LangChain adapter for Qdrant similarity search
6. **MongoDB Repositories**: Document and chunk storage for RAG pipeline
7. **Content Indexer Use Cases**: Three-step workflow (ingest, split, vectorize)

**Previous branches:**
- **Branch 04**: Tools System - External tool integration
- **Branch 03**: Memory System - MongoDB-backed conversation persistence
- **Branch 02**: Streamlit UI - Web interface

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

## 🛠️ Tools System Architecture

This branch implements a complete tool integration system following hexagonal architecture:

### Tool Port (`application/outbound_ports/agents/tools.py`)

Framework-independent interface for tools:

```python
class ToolPort(Protocol):
    """Port for exposing a tool to an agent."""
    
    name: str
    description: str
    
    def get_tool(self) -> Any:
        """Return the underlying framework-specific tool object."""
        ...
```

### Base Tools (`infrastructure/outbound/tools/base/`)

Pure Python business logic with zero framework dependencies:

**Age Calculator** (`age_calculator.py`):
```python
def calculate_age(birth_date: str) -> str:
    """Calculate age based on birth date.
    
    Args:
        birth_date: yyyy-mm-dd format (e.g., '1990-05-15')
    
    Returns:
        Age description or error message
    """
    try:
        birth = datetime.strptime(birth_date, "%Y-%m-%d")
        today = datetime.now()
        age = today.year - birth.year
        
        # Adjust if birthday hasn't occurred this year
        if (today.month, today.day) < (birth.month, birth.day):
            age -= 1
            
        return f"{age} years old."
    except ValueError:
        return "Error: Invalid date format. Use yyyy-mm-dd."
```

**Math Expression Evaluator** (`math_expressions.py`):
```python
def calculate_math_expression(math_expression: str) -> str:
    """Evaluate mathematical expressions safely using AST.
    
    Supports: +, -, *, /, **, //, %, parentheses
    Prevents arbitrary code execution.
    """
    try:
        result = eval(compile(ast.parse(math_expression, mode="eval"), "", "eval"))
        return str(result)
    except SyntaxError:
        return f"Error: Invalid expression '{math_expression}'"
```

### LangChain Tool Adapters (`infrastructure/outbound/tools/langchain_fwk/`)

Framework-specific wrappers implementing `ToolPort`:

**Age Calculator Adapter**:
```python
class LangChainAgeCalculatorToolAdapter(ToolPort):
    """LangChain adapter for age calculator tool."""
    
    name = "age_calculator"
    description = "Calculate age from birth date in yyyy-mm-dd format"
    
    def get_tool(self) -> BaseTool:
        """Return LangChain StructuredTool."""
        from learn_ai_agents.infrastructure.outbound.tools.base.age_calculator import (
            calculate_age,
        )
        
        return StructuredTool.from_function(
            func=calculate_age,
            name=self.name,
            description=self.description,
            args_schema=AgeCalculatorInput,  # Pydantic model
        )
```

**Web Search Adapter**:
```python
class LangChainWebSearchToolAdapter(ToolPort):
    """DuckDuckGo search integration."""
    
    name = "duckduckgo_results_json"
    description = "Search the web using DuckDuckGo"
    
    def get_tool(self) -> BaseTool:
        """Return DuckDuckGo search tool from langchain-community."""
        return DuckDuckGoSearchResults()
```

### Adding Tools Agent (`infrastructure/outbound/agents/langchain_fwk/adding_tools/`)

LangGraph agent with tool binding:

**State** (`state.py`):
```python
class AgentState(TypedDict):
    """State for adding tools agent."""
    messages: Annotated[list[BaseMessage], add_messages]
```

**Agent** (`agent.py`):
```python
class AddingToolsLangchainAgent(BaseLangChainAgent):
    """Agent with tool calling capabilities."""
    
    def __init__(
        self,
        *,
        config: dict,
        llms: dict[str, ChatModelProvider],
        tools: dict[str, ToolPort],  # Tools injected via DI
        chat_history_persistence: ChatHistoryStorePort | None = None,
        checkpointer: BaseCheckpointSaver | None = None,
    ):
        self.checkpointer = checkpointer
        super().__init__(
            config=config,
            llms=llms,
            tools=tools,
            chat_history_persistence=chat_history_persistence,
        )
    
    def _build_graph(self):
        """Build LangGraph with tool nodes."""
        # Bind tools to LLM
        llm_with_tools = self.llms["default"].get_model().bind_tools(
            [tool.get_tool() for tool in self.tools.values()]
        )
        
        # Build graph
        graph = StateGraph(AgentState)
        graph.add_node("chatbot", chatbot_node)  # LLM with tools
        graph.add_node("tools", ToolNode(self.tools_by_name))  # Tool execution
        
        # Routing: if LLM calls tools → execute tools, else → end
        graph.add_conditional_edges("chatbot", tools_condition)
        graph.add_edge("tools", "chatbot")  # After tools, back to LLM
        graph.add_edge(START, "chatbot")
        
        self.graph = graph.compile(checkpointer=self.checkpointer)
```

**Nodes** (`nodes.py`):
```python
async def chatbot_node(state: AgentState, config: RunnableConfig):
    """Execute LLM with tool binding."""
    llm_with_tools = config["configurable"]["llm_with_tools"]
    response = await llm_with_tools.ainvoke(state["messages"])
    return {"messages": [response]}

def tools_condition(state: AgentState) -> Literal["tools", "__end__"]:
    """Route to tools if LLM made tool calls."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "__end__"
```

### Flow: Tool-Enabled Conversation

1. **Request arrives** → `POST /04_adding_tools/invoke`
2. **Use case** loads conversation from MongoDB (if exists)
3. **Agent**:
   - Loads checkpointed state using `thread_id`
   - Adds new user message to state
   - Executes `chatbot_node` → LLM with bound tools
   - **If LLM decides to use tools**:
     - LLM returns tool calls with arguments
     - Graph routes to `tools` node
     - Tools execute and return results
     - Graph routes back to `chatbot_node`
     - LLM generates final response using tool results
   - **If no tools needed**:
     - LLM returns direct response
     - Graph ends
   - Saves checkpoint to MongoDB
4. **Use case** saves messages (including tool calls/results) to chat history
5. **Response** returned with tool-augmented answer

### Benefits

- **Separation of Concerns**: Business logic (base tools) separate from framework code
- **Testability**: Base tools are pure Python functions (easy to unit test)
- **Flexibility**: Swap LangChain for another framework by creating new adapters
- **Dependency Injection**: Tools configured in settings.yaml, injected into agent
- **Memory + Tools**: State persists across requests, tools can be used in multi-turn conversations

---

## 🧠 Memory System Architecture (from Branch 03)

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

## 🔭 Branch 06: Tracing and Observability

### Overview

Branch 06 adds production-grade observability through the Opik tracing platform, enabling full visibility into agent execution, LLM calls, and tool usage.

### Architecture

#### 1. Tracing Port (`application/outbound_ports/agents/tracing.py`)

Framework-agnostic interface for tracing:

```python
from typing import Protocol

class AgentTracingPort(Protocol):
    """Port for agent execution tracing."""
    
    def start_trace(self, *, project_name: str, trace_name: str) -> str:
        """Initialize a new trace and return trace ID."""
        ...
    
    def end_trace(self, trace_id: str, *, output: dict | None = None) -> None:
        """Finalize a trace with optional output."""
        ...
    
    def get_langchain_callback_handler(self, trace_id: str):
        """Get LangChain callback handler for this trace."""
        ...
```

**Why this design?**
- Decouples tracing logic from infrastructure
- Allows swapping Opik for other observability platforms (DataDog, LangSmith, etc.)
- Testable with mock implementations

#### 2. Opik Adapter (`infrastructure/outbound/tracing/opik.py`)

Concrete implementation using Opik SDK:

```python
from opik import track, opik_context
from opik.integrations.langchain import OpikTracer

class OpikAgentTracerAdapter(AgentTracingPort):
    """Opik-based tracing implementation."""
    
    def __init__(self, config: dict):
        self.project_name = config.get("project_name", "ai-agents")
        self._traces: dict[str, dict] = {}  # Thread-safe trace storage
    
    def start_trace(self, *, project_name: str, trace_name: str) -> str:
        """Start Opik trace and store context."""
        trace_id = Helper.generate_uuid()
        
        # Initialize Opik trace
        trace_data = opik_context.get_current_trace_data()
        
        self._traces[trace_id] = {
            "project_name": project_name,
            "trace_name": trace_name,
            "trace_data": trace_data,
        }
        
        return trace_id
    
    def get_langchain_callback_handler(self, trace_id: str):
        """Create OpikTracer with trace context."""
        trace_info = self._traces.get(trace_id)
        if not trace_info:
            raise ValueError(f"No trace found for ID: {trace_id}")
        
        return OpikTracer(
            project_name=trace_info["project_name"],
            tags=["langchain", "agent"],
        )
```

**Key features:**
- Thread-based trace management (supports concurrent requests)
- LangChain integration via `OpikTracer` callback handler
- Automatic span creation for LLM calls, tool invocations, and agent steps

#### 3. Tracing Agent (`infrastructure/outbound/agents/langchain_fwk/agent_tracing/`)

LangGraph agent with full tracing integration:

**Agent** (`agent.py`):
```python
class TracingLangchainAgent(BaseLangChainAgent):
    """Agent with Opik tracing capabilities."""
    
    def __init__(
        self,
        *,
        config: dict,
        llms: dict[str, ChatModelProvider],
        tracing: AgentTracingPort,  # Tracing port injected
        chat_history_persistence: ChatHistoryStorePort | None = None,
        checkpointer: BaseCheckpointSaver | None = None,
    ):
        self.tracing = tracing
        self.checkpointer = checkpointer
        super().__init__(
            config=config,
            llms=llms,
            chat_history_persistence=chat_history_persistence,
        )
    
    async def ainvoke(
        self,
        new_message: Message,
        config: Config,
        **kwargs,
    ) -> Message:
        """Execute agent with tracing enabled."""
        # Start trace
        trace_id = self.tracing.start_trace(
            project_name=config.tracing_project_name or "ai-agents",
            trace_name=f"agent_tracing_{config.thread_id}",
        )
        
        try:
            # Get LangChain callback handler
            opik_tracer = self.tracing.get_langchain_callback_handler(trace_id)
            
            # Add tracer to LangGraph config
            langchain_config = {
                "configurable": {
                    "thread_id": config.thread_id,
                    "llm": self.llms["default"].get_model(),
                },
                "callbacks": [opik_tracer],  # Enable tracing
            }
            
            # Execute graph
            response = await self.graph.ainvoke(
                {"messages": [lc_message]},
                config=langchain_config,
            )
            
            # End trace with success
            self.tracing.end_trace(
                trace_id,
                output={"response": response["messages"][-1].content}
            )
            
            return domain_response
            
        except Exception as e:
            # End trace with error
            self.tracing.end_trace(trace_id, output={"error": str(e)})
            raise
```

**What gets traced:**
- **Agent execution**: Complete conversation flow
- **LLM calls**: Prompts, responses, token usage
- **Graph nodes**: Entry/exit for each state transition
- **Errors**: Exception details and stack traces

#### 4. Helper Utilities (`infrastructure/outbound/agents/langchain_fwk/helpers.py`)

Reusable conversion functions:

```python
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from learn_ai_agents.domain.models.agents.messages import Message, Role

def lc_message_to_domain(lc_message: BaseMessage) -> Message:
    """Convert LangChain message to domain Message."""
    role_mapping = {
        "human": Role.USER,
        "ai": Role.ASSISTANT,
        "system": Role.SYSTEM,
    }
    
    return Message(
        role=role_mapping.get(lc_message.type, Role.USER),
        content=lc_message.content,
        timestamp=Helper.generate_timestamp(),
    )

def domain_message_to_lc(message: Message) -> BaseMessage:
    """Convert domain Message to LangChain message."""
    message_classes = {
        Role.USER: HumanMessage,
        Role.ASSISTANT: AIMessage,
        Role.SYSTEM: SystemMessage,
    }
    
    message_class = message_classes.get(message.role, HumanMessage)
    return message_class(content=message.content)

def safe_jsonable(obj: Any) -> Any:
    """Convert objects to JSON-serializable format."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    elif isinstance(obj, dict):
        return {k: safe_jsonable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [safe_jsonable(item) for item in obj]
    else:
        return obj
```

### Configuration

```yaml
# settings.yaml
components:
  tracing:
    opik:
      agent_tracer:
        constructor:
          module_class: learn_ai_agents.infrastructure.outbound.tracing.opik.OpikAgentTracerAdapter
          config:
            project_name: learn-ai-agents

agents:
  langchain:
    tracing_chat:
      constructor:
        module_class: learn_ai_agents.infrastructure.outbound.agents.langchain_fwk.agent_tracing.agent.TracingLangchainAgent
        components:
          llms:
            default: llms.langchain.groq.default
          tracing: tracing.opik.agent_tracer  # Inject tracing
          checkpointer: checkpointers.memory_checkpointer

use_cases:
  agent_tracing:
    info:
      path_prefix: /06_agent_tracing
      router_factory: learn_ai_agents.infrastructure.inbound.controllers.agents.agent_tracing:get_router
    constructor:
      module_class: learn_ai_agents.application.use_cases.agents.agent_tracing.use_case.AgentTracingUseCase
      components:
        agents:
          agent: agents.langchain.tracing_chat
```

### Observability Benefits

1. **Performance Monitoring**: Track LLM latency and token usage
2. **Debugging**: See exact prompts sent to LLMs and responses received
3. **Error Tracking**: Capture exceptions with full context
4. **Cost Analysis**: Monitor token consumption per conversation
5. **Conversation Analytics**: Understand user interaction patterns

### Opik Dashboard

Access the Opik UI to view:
- Trace timelines with nested spans
- LLM call details (model, temperature, tokens)
- Tool execution logs
- Error rates and latency metrics

---

## 🛡️ Branch 07: Robust Error Handling

### Overview

Branch 07 implements production-grade error handling with structured exceptions, retry mechanisms, and graceful degradation.

### Exception Hierarchy

#### Base Exception (`domain/exceptions/_base.py`)

```python
class BaseApplicationException(Exception):
    """Root exception for all application errors."""
    
    def __init__(
        self,
        message: str,
        *,
        error_code: str | None = None,
        details: dict | None = None,
        original_exception: Exception | None = None,
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.original_exception = original_exception
        super().__init__(message)
    
    def to_dict(self) -> dict:
        """Convert exception to JSON-serializable dict."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }
```

#### Domain Exceptions (`domain/exceptions/domain.py`)

Business rule violations:

```python
class BusinessRuleException(BaseApplicationException):
    """Raised when business rules are violated."""
    pass

class ValidationException(BusinessRuleException):
    """Invalid input data."""
    pass

class AuthorizationException(BusinessRuleException):
    """User not authorized for operation."""
    pass
```

#### Component Exceptions (`domain/exceptions/components.py`)

Infrastructure failures:

```python
class ComponentException(BaseApplicationException):
    """External component failure."""
    pass

class DatabaseException(ComponentException):
    """Database operation failed."""
    pass

class LLMException(ComponentException):
    """LLM service error."""
    pass

class VectorDatabaseException(ComponentException):
    """Vector database error."""
    pass
```

#### Agent Exceptions (`domain/exceptions/agents.py`)

Agent-specific errors:

```python
class AgentException(BaseApplicationException):
    """Agent execution error."""
    pass

class AgentExecutionException(AgentException):
    """Agent failed during execution."""
    pass

class ToolExecutionException(AgentException):
    """Tool call failed."""
    pass
```

### Retry Mechanisms

#### Configuration (`settings.yaml`)

```yaml
agents:
  langchain:
    robust:
      constructor:
        module_class: learn_ai_agents.infrastructure.outbound.agents.langchain_fwk.robust.agent.RobustLangchainAgent
        components:
          llms:
            default: llms.langchain.groq.default
          checkpointer: checkpointers.mongo_checkpointer
        config:
          system_prompt: "You are a helpful assistant."
          retry_policy:
            max_attempts: 3
            backoff_multiplier: 2.0
            initial_delay: 1.0
            max_delay: 10.0
```

#### Robust Agent (`infrastructure/outbound/agents/langchain_fwk/robust/agent.py`)

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

class RobustLangchainAgent(BaseLangChainAgent):
    """Agent with retry logic and error recovery."""
    
    def __init__(
        self,
        *,
        config: dict,
        llms: dict[str, ChatModelProvider],
        checkpointer: BaseCheckpointSaver | None = None,
        chat_history_persistence: ChatHistoryStorePort | None = None,
    ):
        self.retry_policy = config.get("retry_policy", {})
        self.checkpointer = checkpointer
        super().__init__(
            config=config,
            llms=llms,
            chat_history_persistence=chat_history_persistence,
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2.0, min=1, max=10),
        retry=retry_if_exception_type((LLMException, ComponentException)),
        reraise=True,
    )
    async def _invoke_with_retry(self, state: dict, config: RunnableConfig) -> dict:
        """Execute LLM with automatic retry on transient failures."""
        try:
            return await self.graph.ainvoke(state, config=config)
        except Exception as e:
            # Wrap in appropriate exception type
            if "rate_limit" in str(e).lower():
                raise LLMException(
                    "LLM rate limit exceeded",
                    error_code="RATE_LIMIT_ERROR",
                    original_exception=e,
                )
            elif "timeout" in str(e).lower():
                raise ComponentException(
                    "LLM request timed out",
                    error_code="TIMEOUT_ERROR",
                    original_exception=e,
                )
            else:
                raise AgentExecutionException(
                    f"Agent execution failed: {str(e)}",
                    original_exception=e,
                )
    
    async def ainvoke(
        self,
        new_message: Message,
        config: Config,
        **kwargs,
    ) -> Message:
        """Execute agent with error handling and retry logic."""
        try:
            # Prepare state
            lc_message = domain_message_to_lc(new_message)
            state = {"messages": [lc_message]}
            
            # Execute with retry
            response = await self._invoke_with_retry(state, langchain_config)
            
            # Convert response
            return lc_message_to_domain(response["messages"][-1])
            
        except LLMException as e:
            # LLM-specific error handling
            logger.error(f"LLM error after retries: {e.message}")
            raise
        except ComponentException as e:
            # Infrastructure error handling
            logger.error(f"Component error: {e.message}")
            raise
        except Exception as e:
            # Unexpected errors
            logger.exception("Unexpected error in robust agent")
            raise AgentExecutionException(
                "Unexpected error during execution",
                original_exception=e,
            )
```

**Retry behavior:**
1. **Attempt 1**: Immediate execution
2. **Attempt 2**: Wait 1 second (initial_delay)
3. **Attempt 3**: Wait 2 seconds (backoff_multiplier × previous delay)
4. **After max_attempts**: Raise exception

**Retryable errors:**
- Rate limit errors (429 status)
- Timeout errors
- Temporary connection failures
- Transient API errors

**Non-retryable errors:**
- Validation errors (400)
- Authentication errors (401, 403)
- Not found errors (404)
- Permanent failures

### Exception Handlers

#### FastAPI Exception Handlers (`infrastructure/inbound/exception_handlers.py`)

```python
from fastapi import Request, status
from fastapi.responses import JSONResponse

async def business_rule_exception_handler(
    request: Request, exc: BusinessRuleException
) -> JSONResponse:
    """Handle business rule violations."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=exc.to_dict(),
    )

async def component_exception_handler(
    request: Request, exc: ComponentException
) -> JSONResponse:
    """Handle external component failures."""
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=exc.to_dict(),
    )

async def agent_exception_handler(
    request: Request, exc: AgentException
) -> JSONResponse:
    """Handle agent execution errors."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=exc.to_dict(),
    )

# Register handlers in app_factory.py
app.add_exception_handler(BusinessRuleException, business_rule_exception_handler)
app.add_exception_handler(ComponentException, component_exception_handler)
app.add_exception_handler(AgentException, agent_exception_handler)
```

**HTTP status code mapping:**
- `BusinessRuleException` → 400 Bad Request
- `ValidationException` → 400 Bad Request
- `AuthorizationException` → 403 Forbidden
- `ComponentException` → 503 Service Unavailable
- `AgentException` → 500 Internal Server Error

### Unit Tests

#### Test Structure (`tests/unit/endpoints/test_robust_use_case/`)

```python
import pytest
from unittest.mock import AsyncMock, patch

class TestRobustUseCase:
    """Test robust agent error handling."""
    
    @pytest.mark.asyncio
    async def test_ainvoke_with_preloaded_data(self, use_case):
        """Test successful execution."""
        cmd = AnswerRequestDTO(
            message="What is the capital of France?",
            config=ConfigDTO(thread_id="test-123"),
        )
        
        result = await use_case.ainvoke(cmd)
        
        assert result.answer == "The capital of France is Paris."
        assert result.config.thread_id == "test-123"
    
    @pytest.mark.asyncio
    async def test_ainvoke_with_api_connection_error(self, use_case, agent_mock):
        """Test LLM connection failure with retry."""
        # Simulate LLM failure
        agent_mock.ainvoke.side_effect = LLMException(
            "Connection timeout",
            error_code="TIMEOUT_ERROR",
        )
        
        cmd = AnswerRequestDTO(
            message="Test message",
            config=ConfigDTO(thread_id="test-error"),
        )
        
        with pytest.raises(LLMException) as exc_info:
            await use_case.ainvoke(cmd)
        
        assert exc_info.value.error_code == "TIMEOUT_ERROR"
        # Verify retry attempts
        assert agent_mock.ainvoke.call_count == 3
    
    @pytest.mark.asyncio
    async def test_ainvoke_with_authentication_error(self, use_case, agent_mock):
        """Test authentication failure (non-retryable)."""
        agent_mock.ainvoke.side_effect = BusinessRuleException(
            "Invalid API key",
            error_code="AUTH_ERROR",
        )
        
        cmd = AnswerRequestDTO(
            message="Test",
            config=ConfigDTO(thread_id="test-auth"),
        )
        
        with pytest.raises(BusinessRuleException) as exc_info:
            await use_case.ainvoke(cmd)
        
        assert exc_info.value.error_code == "AUTH_ERROR"
        # No retry for auth errors
        assert agent_mock.ainvoke.call_count == 1
```

#### Running Tests

```bash
# Run all robust tests
pytest tests/unit/endpoints/test_robust_use_case/

# Run specific test
pytest tests/unit/endpoints/test_robust_use_case/test_use_case.py::TestRobustUseCase::test_ainvoke_with_api_connection_error

# Run with coverage
pytest --cov=learn_ai_agents.application.use_cases.agents.robust tests/unit/endpoints/test_robust_use_case/
```

### Production Benefits

1. **Resilience**: Automatic retry for transient failures
2. **Observability**: Structured error logging with context
3. **User Experience**: Clean error messages for clients
4. **Debugging**: Full exception chains with original errors
5. **Monitoring**: Error categorization for metrics and alerts

---

## 📊 Branch 08: LLM Evaluation with RAGAS

### Overview

Branch 08 adds automated RAG evaluation using RAGAS (Retrieval Augmented Generation Assessment), enabling systematic quality measurement of our character chat agents and RAG pipeline.

### Architecture

#### 1. RAGAS Metrics

Framework-agnostic metrics for RAG evaluation:

**Context Precision**:
Measures the relevance of retrieved contexts to the user's question.

```python
from ragas.metrics.collections import ContextPrecision

metric = ContextPrecision(llm=evaluator_llm)
score = await metric.ascore(
    user_input="What are your abilities?",
    reference="Expected answer with character skills...",
    retrieved_contexts=[
        "Character class and abilities context...",
        "Skills and proficiencies context..."
    ]
)
# Score: 0.0 to 1.0 (higher = better retrieval)
```

**What it evaluates**:
- Are the retrieved contexts relevant to the question?
- Does the retrieval system surface the most important information?
- Is there noise/irrelevant content in the contexts?

**Faithfulness**:
Measures whether the generated response is grounded in the retrieved contexts.

```python
from ragas.metrics.collections import Faithfulness

metric = Faithfulness(llm=evaluator_llm)
score = await metric.ascore(
    user_input="What are your abilities?",
    response="Agent's actual response...",
    retrieved_contexts=[
        "Character class and abilities context...",
        "Skills and proficiencies context..."
    ]
)
# Score: 0.0 to 1.0 (higher = less hallucination)
```

**What it evaluates**:
- Does the response contain information from the contexts?
- Is the agent hallucinating facts not in the contexts?
- Is the generated content faithful to the source material?

#### 2. Evaluation Datasets

Structured JSON format for systematic testing:

**Dataset Structure** (`data/llm_evaluation/datasets/*.json`):
```json
{
    "user_input": "User question to the agent",
    "reference": "Expected/ideal answer (ground truth)",
    "retrieved_contexts": [
        "First retrieved chunk from vector store",
        "Second retrieved chunk from vector store",
        "Additional relevant chunks..."
    ]
}
```

**Creating Datasets**:
1. **Collect real conversations**: Export actual user interactions
2. **Manual curation**: Add expected answers (ground truth)
3. **Context extraction**: Save what was retrieved from vector store
4. **Format as JSON**: Structure according to schema

**Example Datasets**:

`astarion_conversation_01.json`:
```json
{
    "user_input": "Hola, cuáles son tus habilidades",
    "reference": "Mis habilidades son bastante... variadas...",
    "retrieved_contexts": [
        "(Character: Astarion)\\n# Overview\\n\\n## Starting Class...",
        "(Character: Astarion)\\n# Overview\\n\\n## Recruitment..."
    ]
}
```

`gale_conversation_03.json`:
```json
{
    "user_input": "¿Qué sabes de magia?",
    "reference": "Ah, la magia! Mi especialidad...",
    "retrieved_contexts": [
        "(Character: Gale)\\n# Abilities\\n\\n## Spellcasting...",
        "(Character: Gale)\\n# Background\\n\\n## Wizard Training..."
    ]
}
```

#### 3. Evaluation Script

Automated batch evaluation workflow:

**Script** (`scripts/llm_evaluation/evaluate_ragas.py`):
```python
"""Simple script to evaluate RAG datasets using ragas metrics."""

import asyncio
import json
from pathlib import Path
from openai import AsyncOpenAI
from ragas.llms import llm_factory
from ragas.metrics.collections import ContextPrecision, Faithfulness


async def evaluate_dataset(dataset: dict, dataset_name: str, llm) -> dict:
    """Evaluate a single dataset with ragas metrics."""
    # Initialize metrics
    context_precision = ContextPrecision(llm=llm)
    faithfulness = Faithfulness(llm=llm)
    
    # Evaluate context precision
    precision_result = await context_precision.ascore(
        user_input=dataset["user_input"],
        reference=dataset["reference"],
        retrieved_contexts=dataset["retrieved_contexts"]
    )
    
    # Evaluate faithfulness
    faithfulness_result = await faithfulness.ascore(
        user_input=dataset["user_input"],
        response=dataset.get("response", dataset["reference"]),
        retrieved_contexts=dataset["retrieved_contexts"]
    )
    
    return {
        "dataset_name": dataset_name,
        "user_input": dataset["user_input"],
        "context_precision": precision_result.value,
        "faithfulness": faithfulness_result.value,
    }


async def main():
    """Main evaluation function."""
    # Initialize Groq LLM (OpenAI-compatible)
    client = AsyncOpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1",
    )
    
    llm = llm_factory(
        "llama-3.3-70b-versatile",
        provider="openai",
        client=client,
    )
    
    # Find all dataset files
    datasets_dir = Path(__file__).parent.parent.parent / "data" / "llm_evaluation" / "datasets"
    dataset_files = list(datasets_dir.glob("*.json"))
    
    # Evaluate each dataset
    all_results = []
    for dataset_file in dataset_files:
        dataset = await load_dataset(dataset_file)
        result = await evaluate_dataset(dataset, dataset_file.stem, llm)
        all_results.append(result)
    
    # Save results
    output_file = results_dir / "ragas_evaluation_results.json"
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    
    # Print summary
    print("\\nSummary:")
    for result in all_results:
        print(f"{result['dataset_name']:<30} {result['context_precision']:<20.4f} {result['faithfulness']:<15.4f}")
```

**Running Evaluation**:
```bash
# From project root
cd src/learn_ai_agents

# Run evaluation script
uv run python scripts/llm_evaluation/evaluate_ragas.py
```

**Output**:
```
============================================================
Evaluating: astarion_conversation_01
============================================================

Evaluating Context Precision...
Evaluating Faithfulness...

Results for astarion_conversation_01:
  Context Precision: 0.8750
  Faithfulness:      0.9200

============================================================
Evaluating: gale_conversation_03
============================================================

Evaluating Context Precision...
Evaluating Faithfulness...

Results for gale_conversation_03:
  Context Precision: 0.9100
  Faithfulness:      0.8800

============================================================
Results saved to: data/llm_evaluation/results/ragas_evaluation_results.json
============================================================

Summary:
Dataset                        Context Precision    Faithfulness
-----------------------------------------------------------------
astarion_conversation_01       0.8750              0.9200
gale_conversation_03           0.9100              0.8800
```

#### 4. Results Storage

**Results Format** (`data/llm_evaluation/results/ragas_evaluation_results.json`):
```json
[
  {
    "dataset_name": "astarion_conversation_01",
    "user_input": "Hola, cuáles son tus habilidades",
    "context_precision": 0.875,
    "faithfulness": 0.92
  },
  {
    "dataset_name": "gale_conversation_03",
    "user_input": "¿Qué sabes de magia?",
    "context_precision": 0.91,
    "faithfulness": 0.88
  }
]
```

### Configuration

**Dependencies** (`pyproject.toml`):
```toml
[project]
dependencies = [
    # ... existing dependencies ...
    "ragas>=0.4.3",  # RAG evaluation framework
]
```

**Environment Variables** (`.env`):
```bash
GROQ_API_KEY=your_groq_api_key  # Used for evaluation LLM
```

### Evaluation Workflow

1. **Prepare Datasets**: Create JSON files with user inputs, references, and retrieved contexts
2. **Run Evaluation**: Execute the RAGAS evaluation script
3. **Review Results**: Check metrics in console and JSON output
4. **Iterate**: Use results to improve:
   - Retrieval quality (chunking strategy, embedding model)
   - Context relevance (reranking, filtering)
   - Response generation (prompts, model selection)
5. **Track Over Time**: Compare results across iterations

### Interpreting Scores

**Context Precision**:
- **0.9-1.0**: Excellent retrieval - highly relevant contexts
- **0.7-0.9**: Good retrieval - mostly relevant with some noise
- **0.5-0.7**: Fair retrieval - significant irrelevant content
- **<0.5**: Poor retrieval - needs improvement

**Faithfulness**:
- **0.9-1.0**: Excellent - responses grounded in contexts
- **0.7-0.9**: Good - minor hallucinations
- **0.5-0.7**: Fair - noticeable hallucinations
- **<0.5**: Poor - significant hallucinations

### Best Practices

1. **Diverse Datasets**: Cover different question types and difficulty levels
2. **Real Conversations**: Use actual user interactions for authentic testing
3. **Ground Truth**: Invest in high-quality reference answers
4. **Regular Evaluation**: Run after each RAG pipeline change
5. **Version Control**: Track results over time to measure improvements
6. **Error Analysis**: Investigate low scores to identify root causes

### Production Benefits

1. **Quality Assurance**: Systematic measurement of RAG performance
2. **Continuous Improvement**: Data-driven optimization of retrieval and generation
3. **Regression Detection**: Catch quality degradation early
4. **Baseline Establishment**: Quantify current performance
5. **A/B Testing**: Compare different models, prompts, or configurations

---

## 🎯 Key Takeaways

1. **Domain is king**: Start here, keep it pure
2. **Ports define contracts**: Application layer specifies interfaces
3. **Adapters are swappable**: Infrastructure implements ports
4. **Bootstrap wires it all**: DI happens once at startup
5. **Test each layer**: Unit → Integration → E2E
6. **Discovery enables introspection**: Runtime visibility into system configuration
7. **Containers manage lifecycle**: Lazy loading, proper initialization, clean shutdown
8. **Tracing enables observability**: Full visibility into agent execution
9. **Exceptions enable resilience**: Structured error handling and retry logic
10. **Evaluation enables improvement**: Measure quality to guide optimization

This architecture makes the code:
- ✅ Testable (mock any dependency)
- ✅ Maintainable (clear separation)
- ✅ Flexible (swap implementations)
- ✅ Scalable (add features without breaking existing code)
- ✅ Observable (tracing and discovery provide runtime visibility)
- ✅ Resilient (retry mechanisms and error recovery)
- ✅ Production-ready (comprehensive error handling)
- ✅ User-friendly (Streamlit UI for exploration and testing)
