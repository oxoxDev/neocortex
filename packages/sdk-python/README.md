# TinyHuman Neocortex SDK

A persistent memory layer for AI applications. Neocortex lets your AI agents store, retrieve, and use context across conversations -- so they remember what matters.

Built on the [TinyHumans API](https://tinyhumans.ai).

## Install

```bash
pip install tinyhumansai
```

Requires Python 3.9+. The only runtime dependency is [httpx](https://www.python-httpx.org/).

## Running locally

From the package directory (`packages/sdk-python`), install the project and optional dependency groups with [uv](https://docs.astral.sh/uv/):

```bash
uv sync --group dev --group examples
```

- **`--group dev`** — test and lint tools (pytest, pytest-asyncio, mypy, ruff).
- **`--group examples`** — `python-dotenv` for running the example script.

Then run the example:

```bash
# Copy .env.example to .env and set TINYHUMANS_TOKEN, TINYHUMANS_MODEL_ID, OPENAI_API_KEY (for recall_with_llm).
uv run python example.py

# Optional: print outbound SDK requests for debugging
TINYHUMANSAI_LOG_LEVEL=DEBUG uv run python example.py
```

To install only the package and examples (no dev tools): `uv sync --group examples`.

## Quick start

```python
import tinyhumansai as api

client = api.TinyHumanMemoryClient("YOUR_APIKEY_HERE")

# Store a single memory
client.ingest_memory(
    item={
        "key": "user-preference-theme",
        "content": "User prefers dark mode",
        "namespace": "preferences",
        "metadata": {"source": "onboarding"},
    }
)

# Fetch relevant memory context, then ask a LLM something from it
ctx = client.recall_memory(
    namespace="preferences",
    prompt="What is the user's preference for theme?",
)

response = client.recall_with_llm(
    prompt="What is the user's preference for theme?",
    api_key="OPENAI_API_KEY",
    context=ctx.context,
)
print(response.text) # The user prefers dark mode
```

## Core concepts

**Memory items** are the basic unit of storage. Each item has:

| Field        | Required | Description                                                  |
| ------------ | -------- | ------------------------------------------------------------ |
| `key`        | yes      | Unique identifier within a namespace (used for upsert/dedup) |
| `content`    | yes      | The memory text                                              |
| `namespace`  | yes      | Scope for organizing items                                   |
| `metadata`   | no       | Arbitrary dict for tagging/filtering                         |
| `created_at` | no       | Unix timestamp in seconds                                    |
| `updated_at` | no       | Unix timestamp in seconds                                    |

**Namespaces** let you organize memories by category (e.g. `"preferences"`, `"conversation-history"`, `"user-facts"`).

**Context** is a pre-formatted string built from your stored memories, ready to inject into any LLM prompt as system context.

## API reference

### `TinyHumanMemoryClient`

```python
client = api.TinyHumanMemoryClient(
    token="your-api-key",       # Required. TinyHumans API key.
    model_id="neocortex-mk1",   # Required. Model identifier.
    base_url="https://...",     # Optional. Override API base URL.
)
```

The client supports the context-manager protocol for automatic cleanup:

```python
with api.TinyHumanMemoryClient(token="...", model_id="...") as client:
    ctx = client.recall_memory(namespace="preferences", prompt="User preferences", num_chunks=10)
```

### `ingest_memory`

Upsert a single memory item. The item is deduped by `(namespace, key)` -- if a match exists, it is updated; otherwise a new item is created.

```python
result = client.ingest_memory(
    item={
        "key": "fav-color",
        "content": "User's favorite color is blue",
        "namespace": "preferences",
    }
)
print(result.ingested, result.updated, result.errors)
```

With the `MemoryItem` dataclass:

```python
from tinyhumansai import MemoryItem

result = client.ingest_memory(
    item=MemoryItem(key="fav-color", content="Blue", namespace="preferences")
)
```

### `ingest_memories`

Upsert multiple memory items in one call. Items are deduped by `(namespace, key)`.

```python
result = client.ingest_memories(
    items=[
        {"key": "fav-color", "content": "Blue", "namespace": "preferences"},
        {"key": "fav-food", "content": "Pizza", "namespace": "preferences"},
    ]
)
print(result.ingested, result.updated, result.errors)
```

### `recall_memory`

Fetch relevant memory chunks using a prompt and return them as an LLM-friendly context string. The API uses the prompt to retrieve the most relevant chunks from the namespace.

```python
# Fetch up to 10 chunks relevant to the prompt
ctx = client.recall_memory(
    namespace="preferences",
    prompt="What is the user's favorite color?",
    num_chunks=10,
)
print(ctx.context)  # Formatted string
print(ctx.items)    # List of ReadMemoryItem objects
print(ctx.count)    # Number of items

# Optional: fetch more or fewer chunks
ctx = client.recall_memory(namespace="preferences", prompt="User preferences", num_chunks=5)

# Optional: filter by specific key(s) instead of prompt-based retrieval
ctx = client.recall_memory(namespace="preferences", prompt="", key="fav-color", num_chunks=10)
```

### `delete_memory`

Delete all memories in a namespace. The current API does not expose key-scoped deletes.

```python
# Delete all memories in a namespace
client.delete_memory(namespace="preferences", delete_all=True)
```

### `recall_with_llm` (optional)

Query an LLM provider with your stored context injected -- no extra SDK dependencies needed. Supports OpenAI, Anthropic, and Google Gemini out of the box, plus any OpenAI-compatible endpoint.

```python
ctx = client.recall_memory(namespace="preferences", prompt="User preferences", num_chunks=10)

# OpenAI
response = client.recall_with_llm(
    prompt="What is the user's favorite color?",
    provider="openai",
    model="gpt-4o-mini",
    api_key="your-openai-key",
    context=ctx.context,
)
print(response.text)
```

### `insert_document`

Ingest a single memory document. Sends `POST /v1/memory/documents`.

```python
client.insert_document(
    title="Doc title",
    content="Doc content",
    namespace="documents",
    source_type="doc",  # optional
    metadata={"source": "example"},  # optional
    document_id="optional-document-id",  # optional
)
```

### `insert_documents_batch`

Ingest multiple documents in one call. Sends `POST /v1/memory/documents/batch`.

```python
client.insert_documents_batch(
    items=[
        {
            "title": "Doc A",
            "content": "Content A",
            "namespace": "documents",
            "documentId": "doc-a-id",  # optional
        },
        {
            "title": "Doc B",
            "content": "Content B",
            "namespace": "documents",
            "documentId": "doc-b-id",  # optional
        },
    ]
)
```

### `list_documents`

List ingested documents. Sends `GET /v1/memory/documents`.

```python
client.list_documents(namespace="documents", limit=10, offset=0)
```

### `get_document`

Get document details. Sends `GET /v1/memory/documents/:documentId`.

```python
client.get_document(document_id="doc-a-id", namespace="documents")
```

### `delete_document`

Delete a document. Sends `DELETE /v1/memory/documents/:documentId`.

```python
client.delete_document(document_id="doc-a-id", namespace="documents")
```

### `query_memory_context`

Query memory context via the mirrored endpoint. Sends `POST /v1/memory/queries`.

```python
client.query_memory_context(
    query="What did we store?",
    namespace="documents",
    include_references=True,
    max_chunks=5,
    document_ids=["doc-a-id"],  # optional
)
```

### `chat_memory_context`

Chat with memory context. Sends `POST /v1/memory/conversations`.

```python
client.chat_memory_context(
    messages=[{"role": "user", "content": "Summarize the stored docs"}],
    temperature=0,
    max_tokens=256,
)
```

### `record_interactions`

Record interaction signals. Sends `POST /v1/memory/interactions`.

```python
client.record_interactions(
    namespace="documents",
    entity_names=["ENTITY-A", "ENTITY-B"],
    description="Recorded via sdk-python example",
    interaction_level="engage",
)
```

### `recall_thoughts`

Generate reflective thoughts. Sends `POST /v1/memory/memories/thoughts`.

```python
client.recall_thoughts(namespace="documents", max_chunks=5)
```

### `sync_memory` (optional / backend-specific)

Sync OpenClaw memory files. Sends `POST /v1/memory/sync`.

```python
client.sync_memory(
    workspace_id="workspace-id",
    agent_id="agent-id",
    source="startup",  # optional
    files=[
        {
            "file_path": "example.txt",
            "content": "file contents",
            "timestamp": "1700000000",
            "hash": "sha256-hex",
        }
    ],
)
```

### `chat_memory`

Chat with DeltaNet memory cache. Sends `POST /v1/memory/chat`.

```python
client.chat_memory(
    messages=[{"role": "user", "content": "Hello"}],
    temperature=0.2,
    max_tokens=256,
)
```

### `interact_memory`

Record entity interactions in the core backend. Sends `POST /v1/memory/interact`.

```python
client.interact_memory(
    namespace="documents",
    entity_names=["ENTITY-A", "ENTITY-B"],
    description="Recorded by sdk-python example",
    interaction_level="engage",
)
```

### `recall_memory_master`

Recall context from the Master node. Sends `POST /v1/memory/recall`.

Note: this is different from `recall_memory(...)` which uses the RAG query endpoint (`POST /v1/memory/query`).

```python
ctx = client.recall_memory_master(namespace="documents", max_chunks=5)
print(ctx.context)
```

### `recall_memories`

Recall memories from the Ebbinghaus bank. Sends `POST /v1/memory/memories/recall`.

```python
client.recall_memories(
    namespace="documents",
    top_k=5,
    min_retention=0,
)
```

### `get_graph_snapshot` (optional / backend-specific)

Fetch graph topology snapshot. Sends `GET /v1/memory/admin/graph-snapshot`.

```python
client.get_graph_snapshot(namespace="documents", mode="latest_chunks", limit=10, seed_limit=3)
```

### `get_ingestion_job` (optional)

Get ingestion job status. Sends `GET /v1/memory/ingestion/jobs/:jobId`.

```python
client.get_ingestion_job(job_id="some-job-id")
```
