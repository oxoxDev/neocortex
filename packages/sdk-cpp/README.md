# tinyhumans-sdk-cpp

C++ SDK for TinyHumans/TinyHuman Neocortex memory APIs.

## Requirements

- C++17+
- CMake 3.14+
- libcurl

## Build

```bash
cd packages/sdk-cpp
make build
```

## Get an API key

1. Sign in to your TinyHumans account.
2. Create a server API key in the TinyHumans dashboard.
3. Export it before running examples:

```bash
export TINYHUMANS_TOKEN="your_api_key"
# optional custom API URL
export TINYHUMANS_BASE_URL="https://api.tinyhumans.ai"
```

## Quick start

```cpp
#include "tinyhumans/tinyhumans.hpp"
using namespace tinyhumans;

TinyHumansMemoryClient client(token);

// Insert
InsertMemoryParams params;
params.set_title("title").set_content("content").set_namespace("ns");
client.insert_memory(params);

// Query
QueryMemoryParams qparams;
qparams.set_query("search query").set_namespace("ns");
auto resp = client.query_memory(qparams);
```

## Custom Model ID

```cpp
TinyHumansMemoryClient client(token, "custom-model-id", base_url);
```

All requests include `X-Model-Id` header (default: `neocortex-mk1`).

## API Reference

### Core Memory

| Method | Endpoint | Description |
|--------|----------|-------------|
| `insert_memory(params)` | POST `/memory/insert` | Ingest a document into memory |
| `query_memory(params)` | POST `/memory/query` | Query memory via RAG |
| `recall_memory(params)` | POST `/memory/recall` | Recall context from master node |
| `recall_memories(params)` | POST `/memory/memories/recall` | Recall from Ebbinghaus bank |
| `delete_memory(params)` | POST `/memory/admin/delete` | Delete memory by namespace |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| `chat_memory(params)` | POST `/memory/chat` | Chat with DeltaNet memory cache |
| `chat_memory_context(params)` | POST `/memory/conversations` | Chat with memory context |

### Interactions

| Method | Endpoint | Description |
|--------|----------|-------------|
| `interact_memory(params)` | POST `/memory/interact` | Record entity interactions |
| `record_interactions(params)` | POST `/memory/interactions` | Record interaction signals |

### Advanced Recall

| Method | Endpoint | Description |
|--------|----------|-------------|
| `recall_thoughts(params)` | POST `/memory/memories/thoughts` | Generate reflective thoughts |
| `query_memory_context(params)` | POST `/memory/queries` | Query memory context |

### Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| `insert_document(params)` | POST `/memory/documents` | Insert a document |
| `insert_documents_batch(params)` | POST `/memory/documents/batch` | Batch insert documents |
| `list_documents(params)` | GET `/memory/documents` | List documents |
| `get_document(params)` | GET `/memory/documents/{id}` | Get document by ID |
| `delete_document(id, ns)` | DELETE `/memory/documents/{id}` | Delete a document |

### Admin & Utility

| Method | Endpoint | Description |
|--------|----------|-------------|
| `get_graph_snapshot(params)` | GET `/memory/admin/graph-snapshot` | Get graph snapshot |
| `get_ingestion_job(jobId)` | GET `/memory/ingestion/jobs/{id}` | Get ingestion job status |
| `wait_for_ingestion_job(jobId, opts)` | -- | Poll until job completes |

## Example

`example/example_usage.cpp` exercises every method exposed by this SDK.

```bash
cd packages/sdk-cpp
make build
./build/example_usage
```

## Tests

```bash
make test                # unit tests
make integration-test    # requires TINYHUMANS_TOKEN
```
