> ## Documentation Index
> Fetch the complete documentation index at: https://docs.mem0.ai/llms.txt
> Use this file to discover all available pages before exploring further.

# Pipecat Neocortex Integration

Integrate **Neocortex** with [Pipecat](https://pipecat.ai) to add long‑term conversational memory to your voice and chat agents.

This package provides a `NeocortexMemoryService` that plugs into the Pipecat pipeline in the same way as `Mem0MemoryService`, but stores and retrieves memories from Neocortex instead.

## Installation

Install from your workspace (or virtualenv) that runs Pipecat:

```bash
pip install neocortex-pipecat
```

You will also need to set your Neocortex API key as an environment variable:

```bash
export ALPHAHUMAN_API_KEY=your_neocortex_api_key
```

Optionally, configure a custom Neocortex base URL:

```bash
export ALPHAHUMAN_BASE_URL=https://api.your-backend.com
```

## Configuration

Neocortex integration is provided through the `NeocortexMemoryService` class.

```python
from neocortex_pipecat.memory import NeocortexMemoryService

memory = NeocortexMemoryService(
    api_key=os.getenv("ALPHAHUMAN_API_KEY"),  # Your Neocortex token/JWT
    user_id="unique_user_id",                 # Unique identifier for the end user
    agent_id="my_agent",                      # Identifier for the agent using the memory
    run_id="session_123",                     # Optional: specific conversation session ID
    search_limit=10,                          # Max Neocortex memory chunks per query
    system_prompt="Here are your past memories:",  # Prefix for injected memories
    add_as_system_message=True,              # Add memories as system (True) or user (False) message
)
```

- At least one of `user_id`, `agent_id`, or `run_id` must be provided.
- `search_limit` is passed to Neocortex as `maxChunks`.

## Pipeline Integration

Place `NeocortexMemoryService` between your context aggregator and LLM in the Pipecat pipeline:

```python
from pipecat.pipeline.pipeline import Pipeline

pipeline = Pipeline([
    transport.input(),
    stt,                # Speech-to-text for audio input
    user_context,       # User context aggregator
    memory,             # Neocortex memory service enhances context here
    llm,                # LLM for response generation
    tts,                # Optional: Text-to-speech
    transport.output(),
    assistant_context   # Assistant context aggregator
])
``]

## Example: Voice Agent with Neocortex Memory

See `examples/voice_demo.py` for a complete FastAPI + WebSocket voice agent that uses Neocortex memory. It mirrors the standard Pipecat Mem0 example but swaps in `NeocortexMemoryService`.

Run it with:

```bash
export ALPHAHUMAN_API_KEY=your_neocortex_api_key
export OPENAI_API_KEY=your_openai_key
uvicorn examples.voice_demo:app --reload --host 0.0.0.0 --port 8000
```

Then connect to `/chat` from your Pipecat-compatible client UI and speak; the agent will remember and reuse past conversation details via Neocortex.

