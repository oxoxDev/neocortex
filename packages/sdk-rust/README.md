# TinyHuman Neocortex SDK (Rust)

A persistent memory layer for AI applications. Neocortex lets your AI agents store, retrieve, and use context across conversations -- so they remember what matters.

Built on the [TinyHumans API](https://tinyhumans.ai).

## Install

Add to your `Cargo.toml`:

```toml
[dependencies]
tinyhumansai = "0.1"
```

Requires Rust 1.70+ and Tokio (async runtime).

## Running locally

From the package directory (`packages/sdk-rust`):

```bash
cargo build
cargo test
```

Unit and integration tests use mocked HTTP. For **end-to-end tests** (hits a real backend; skipped by default):

```bash
TINYHUMANS_API_KEY=your_key cargo test e2e_live_insert_query_delete -- --ignored
```

Set `TINYHUMANS_BASE_URL` if your backend URL differs from the default (`https://staging-api.tinyhumans.ai`).

## Quick start

```rust
use tinyhumansai::{
    TinyHumanConfig, TinyHumanMemoryClient, InsertMemoryParams, QueryMemoryParams, DeleteMemoryParams,
};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let client = TinyHumanMemoryClient::new(
        TinyHumanConfig::new("your-api-key")
    )?;

    // Insert a document
    let res = client.insert_memory(InsertMemoryParams {
        title: "User preference".into(),
        content: "User prefers dark mode".into(),
        namespace: "preferences".into(),
        ..Default::default()
    }).await?;
    println!("{:?}", res.data);

    // Query memory
    let query = client.query_memory(QueryMemoryParams {
        query: "What does the user prefer?".into(),
        namespace: Some("preferences".into()),
        max_chunks: Some(10),
        ..Default::default()
    }).await?;
    println!("{:?}", query.data.response);

    // Delete memory
    client.delete_memory(DeleteMemoryParams {
        namespace: Some("preferences".into()),
    }).await?;

    Ok(())
}
```

## Core concepts

**Memory items** are the basic unit of storage. Each item has `title`, `content`, `namespace`, and optional `metadata`, `priority`, and timestamps. The API supports insert, query (RAG), delete, recall (Master node), and memories/recall (Ebbinghaus bank).

**Namespaces** let you organize memories by category (e.g. `"preferences"`, `"conversation-history"`, `"user-facts"`).

**Context** is retrieved via `query_memory` or `recall_memory` and can be injected into LLM prompts as system context.

## API reference

### `TinyHumanMemoryClient`

```rust
let client = TinyHumanMemoryClient::new(
    TinyHumanConfig::new("your-api-key")
        .with_base_url("https://..."),  // optional
)?;
```

Configuration: `TinyHumanConfig::new(token)`. Optionally set base URL with `.with_base_url(url)` or the `TINYHUMANS_BASE_URL` environment variable.

### `insert_memory`

Insert (ingest) a document into memory. POST `/v1/memory/insert`.

```rust
client.insert_memory(InsertMemoryParams {
    title: "Doc title".into(),
    content: "Content".into(),
    namespace: "preferences".into(),
    ..Default::default()
}).await?;
```

### `query_memory`

Query memory via RAG. POST `/v1/memory/query`.

```rust
let res = client.query_memory(QueryMemoryParams {
    query: "What is the user's preference?".into(),
    namespace: Some("preferences".into()),
    max_chunks: Some(10),
    ..Default::default()
}).await?;
```

### `delete_memory`

Delete memory (admin). POST `/v1/memory/admin/delete`. Optional `namespace` to scope deletion.

### `recall_memory`

Recall context from Master node. POST `/v1/memory/recall`.

### `recall_memories`

Recall memories from Ebbinghaus bank. POST `/v1/memory/memories/recall`.

## Error handling

Errors are returned as `TinyHumanError`: `Validation`, `Http`, `Api { message, status, body }`, or `Decode`. Use `thiserror` / `#[error]` for display and matching.

## Tests

```bash
cargo test
```

End-to-end (real backend):

```bash
TINYHUMANS_API_KEY=your_key cargo test e2e_live_insert_query_delete -- --ignored
```
