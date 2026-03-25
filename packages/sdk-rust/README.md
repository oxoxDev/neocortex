# tinyhumansai (Rust SDK)

Rust SDK for TinyHumans Neocortex memory APIs.

## Requirements

- Rust 1.70+
- Tokio runtime for async usage

## Install

Add to `Cargo.toml`:

```toml
[dependencies]
tinyhumansai = "0.1"
tokio = { version = "1", features = ["macros", "rt-multi-thread"] }
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

```rust
use tinyhumansai::{
    InsertMemoryParams, QueryMemoryParams, TinyHumanConfig, TinyHumansMemoryClient,
};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let token = std::env::var("TINYHUMANS_TOKEN")?;
    let client = TinyHumansMemoryClient::new(TinyHumanConfig::new(token))?;

    client.insert_memory(InsertMemoryParams {
        title: "User preference".into(),
        content: "User prefers dark mode".into(),
        namespace: "preferences".into(),
        ..Default::default()
    }).await?;

    let query = client.query_memory(QueryMemoryParams {
        query: "What does the user prefer?".into(),
        namespace: Some("preferences".into()),
        max_chunks: Some(10.0),
        ..Default::default()
    }).await?;

    println!("{:?}", query.data.response);
    Ok(())
}
```

## Full route example

`examples/test_routes.rs` is the comprehensive example and exercises all currently implemented methods.

```bash
cd packages/sdk-rust
cargo run --example test_routes
# optional env file override:
ENV_FILE=../sdk-python/.env cargo run --example test_routes
```

## Client configuration

`TinyHumanConfig::new(token)` supports optional `.with_base_url(url)`.

Base URL resolution: explicit config -> `TINYHUMANS_BASE_URL` -> `NEOCORTEX_BASE_URL` -> `https://api.tinyhumans.ai`.

## Implemented methods

Core memory routes:
- `insert_memory`
- `query_memory`
- `delete_memory`
- `recall_memory`
- `recall_memories`

Memories/context/chat routes:
- `recall_memories_context`
- `recall_thoughts`
- `interact_memory`
- `record_interactions`
- `query_memory_context`
- `chat_memory_context`
- `chat_memory`

Documents and admin routes:
- `insert_document`
- `insert_documents_batch`
- `list_documents`
- `get_document`
- `delete_document`
- `get_ingestion_job`
- `wait_for_ingestion_job`
- `get_graph_snapshot`
- `memory_health`
- `sync_memory`

## Tests

```bash
cargo test
```
