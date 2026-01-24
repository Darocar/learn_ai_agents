# Streamlit UI for learn-ai-agents

This package provides a web-based user interface for the learn-ai-agents API using Streamlit.

## Features

- **Home Page**: Overview of the project architecture and API endpoints
- **Chat Interface**: Interactive chat with AI agents
  - Agent selection from available use cases
  - Invoke mode (synchronous responses)
  - Stream mode (real-time streaming responses)
  - Conversation history management
  - **Load existing conversations**: Enter a conversation ID and click "Apply ID" to restore chat history from MongoDB
- **Conversation History Viewer**: Search and browse conversation messages
  - Search by specific conversation ID
  - Browse all conversations in the database
  - View message timestamps and full conversation flow
  - List all available conversation IDs

## Why No client.py?

The previous `client.py` was removed because it was **unnecessary over-engineering**:

- ✅ Streamlit can use `httpx` directly for simple API calls
- ✅ Only 2 endpoints needed (`/agents` and `/{agent_id}/invoke` or `/stream`)
- ✅ Simpler code is easier to understand and maintain
- ✅ Pydantic models can be defined inline when needed

For a production app with many endpoints, a client class might make sense. For this educational project, direct HTTP calls are clearer.

## Setup

1. Copy the `.env.example` file to `.env` in this directory:
   ```bash
   cp .env.example .env
   ```

2. Update the `.env` file with your configuration:
   ```bash
   AGENTS_API_BASE_URL=http://127.0.0.1:8000
   MONGO_URI=mongodb://localhost:27017
   MONGO_DATABASE=learn_ai_agents
   ```

## Usage

### Start the FastAPI backend

From the repository root:

```bash
# Make sure you have GROQ_API_KEY set in your environment or .env
uv run --package learn-ai-agents \
  python -m uvicorn learn_ai_agents.__main__:app --reload --port 8000
```

### Start the Streamlit UI

From the repository root:

```bash
uv run --package learn-ai-agents-ui \
  streamlit run src/streamlit_ui/streamlit_ui/app.py
```

The Streamlit app will open in your browser at `http://localhost:8501`.

## Project Structure

```
streamlit_ui/
├── pyproject.toml          # Package configuration
├── README.md               # This file
├── .env.example            # Environment variables template
└── streamlit_ui/
    ├── __init__.py
    ├── app.py              # Main landing page (home)
    └── pages/
        └── 1_💬_Chat.py    # Chat interface page
```

## Pages

### Home (app.py)
- Project overview in Markdown
- Architecture explanation
- API endpoints documentation
- Getting started guide

### Chat (pages/1_💬_Chat.py)
- Agent selection dropdown (populated from `/agents` endpoint)
- Mode selection: **invoke** or **stream**
- Chat interface with message history
- Conversation ID management
- Real-time streaming support

## How It Works

1. **Agent Discovery**: The UI calls `GET /agents` to fetch all use cases implementing `AgentAnswerPort`
2. **User Selection**: User selects an agent and chooses invoke/stream mode
3. **API Interaction**:
   - **Invoke mode**: `POST /{agent_id}/invoke` - Returns complete response
   - **Stream mode**: `POST /{agent_id}/stream` - Returns SSE stream
4. **Display**: Messages are shown in chat format with conversation history

## Future Enhancements

- Add more pages for different features
- Enhanced conversation management (save/load)
- Agent comparison view
- Performance metrics display
- Multi-turn conversation visualization

