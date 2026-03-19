"""
Example usage of the TinyHumans SDK.

Install with examples extra for dotenv: pip install -e ".[examples]"
Copy .env.example to .env and set TINYHUMANS_TOKEN, TINYHUMANS_MODEL_ID, OPENAI_API_KEY.
Optional: set TINYHUMANSAI_LOG_LEVEL=DEBUG to print outbound API requests.
"""

import logging
import os
import time

from dotenv import load_dotenv

load_dotenv()
if os.environ.get("TINYHUMANSAI_LOG_LEVEL") and not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO)

import tinyhumansai as api

client = api.TinyHumanMemoryClient(os.environ["TINYHUMANS_TOKEN"])

# Ingest (upsert) a single memory
result = client.ingest_memory(
    item={
        "key": "user-preference-theme",
        "content": "User prefers dark mode",
        "namespace": "preferences",
        "metadata": {"source": "onboarding"},
        "created_at": time.time(),  # Optional: Unix timestamp (seconds)
        "updated_at": time.time(),  # Optional: Unix timestamp (seconds)
    }
)
print(result)  # IngestMemoryResponse(ingested=1, updated=0, errors=0)

# Or ingest multiple at once: client.ingest_memories(items=[...])

# Get LLM context (prompt fetches relevant chunks; num_chunks limits how many)
ctx = client.recall_memory(
    namespace="preferences",
    prompt="What is the user's preference for theme?",
    num_chunks=10,
)
print(ctx.context)

# (Optional) Query LLM with context (use your own API key from the provider)
# Built-in providers: "openai", "anthropic", "google"
response = client.recall_with_llm(
    prompt="What is the user's preference for theme?",
    provider="openai",
    model="gpt-4o-mini",
    api_key=os.environ["OPENAI_API_KEY"],
    context=ctx.context,
)
print(response.text)

# Custom provider (OpenAI-compatible API)
# response = client.recall_with_llm(
#     prompt="What is the user's preference for theme?",
#     provider="custom",
#     model="your-model-name",
#     api_key="your-api-key",
#     url="https://api.example.com/v1/chat/completions",
#     context=ctx.context,
# )

# Delete all memory in namespace
# The current API exposes namespace-wide delete, not key-scoped delete.
client.delete_memory(namespace="preferences", delete_all=True)
