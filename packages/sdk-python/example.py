"""
Example usage of the TinyHumans SDK.

Install with examples extra for dotenv: pip install -e ".[examples]"
Copy .env.example to .env and set TINYHUMANS_TOKEN, TINYHUMANS_MODEL_ID, OPENAI_API_KEY.
Optional: set TINYHUMANSAI_LOG_LEVEL=DEBUG to print outbound API requests.
"""

import logging
import hashlib
import os
import time

from dotenv import load_dotenv

load_dotenv()
if os.environ.get("TINYHUMANSAI_LOG_LEVEL") and not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO)

import tinyhumansai as api

client = api.TinyHumanMemoryClient(
    os.environ["TINYHUMANS_TOKEN"],
    model_id=os.environ.get("TINYHUMANS_MODEL_ID", "neocortex-mk1"),
)

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

# ---------------------------------------------------------------------------
# Documents & mirrored endpoints (aligned with the TypeScript SDK)
# ---------------------------------------------------------------------------

docs_ns = f"python-e2e-docs-{int(time.time())}"

document_id_single = f"py-doc-single-{int(time.time())}"
document_id_batch_0 = f"py-doc-batch-0-{int(time.time())}"
document_id_batch_1 = f"py-doc-batch-1-{int(time.time())}"

print("\n--- Documents endpoints (new) ---")

try:
    single_doc = client.insert_document(
        title="Python E2E Doc (single)",
        content="Content stored by the Python SDK example (single).",
        namespace=docs_ns,
        source_type="doc",
        metadata={"source": "sdk-python-example", "variant": "single"},
        document_id=document_id_single,
    )
    print("insert_document:", single_doc)
except Exception as e:
    print("insert_document failed:", e)

try:
    batch_res = client.insert_documents_batch(
        items=[
            {
                "title": "Python E2E Doc (batch 0)",
                "content": "Content stored by the Python SDK example (batch 0).",
                "namespace": docs_ns,
                "sourceType": "doc",
                "metadata": {"source": "sdk-python-example", "variant": "batch-0"},
                "documentId": document_id_batch_0,
            },
            {
                "title": "Python E2E Doc (batch 1)",
                "content": "Content stored by the Python SDK example (batch 1).",
                "namespace": docs_ns,
                "sourceType": "doc",
                "metadata": {"source": "sdk-python-example", "variant": "batch-1"},
                "documentId": document_id_batch_1,
            },
        ]
    )
    print("insert_documents_batch:", batch_res)
except Exception as e:
    print("insert_documents_batch failed:", e)

try:
    list_res = client.list_documents(namespace=docs_ns, limit=10, offset=0)
    print("list_documents:", list_res)
except Exception as e:
    print("list_documents failed:", e)

try:
    get_res = client.get_document(document_id=document_id_single, namespace=docs_ns)
    print("get_document:", get_res)
except Exception as e:
    print("get_document failed:", e)

try:
    query_ctx_res = client.query_memory_context(
        query="What content did the Python SDK example store?",
        namespace=docs_ns,
        include_references=True,
        max_chunks=5,
        document_ids=[document_id_single],
    )
    print("query_memory_context:", query_ctx_res)
except Exception as e:
    print("query_memory_context failed:", e)

try:
    chat_ctx_res = client.chat_memory_context(
        messages=[
            {
                "role": "user",
                "content": "Using the stored memory, summarize what the single document contains.",
            }
        ],
        temperature=0,
        max_tokens=256,
    )
    print("chat_memory_context:", chat_ctx_res)
except Exception as e:
    print("chat_memory_context failed:", e)

try:
    interact_res = client.record_interactions(
        namespace=docs_ns,
        entity_names=["PY-ENTITY-A", "PY-ENTITY-B"],
        description="Recorded by sdk-python example",
        interaction_level="engage",
    )
    print("record_interactions:", interact_res)
except Exception as e:
    print("record_interactions failed:", e)

try:
    thoughts_res = client.recall_thoughts(namespace=docs_ns, max_chunks=5)
    print("recall_thoughts:", thoughts_res)
except Exception as e:
    print("recall_thoughts failed:", e)

try:
    # Optional: this endpoint may be backend-specific.
    graph_snapshot = client.get_graph_snapshot(
        namespace=docs_ns,
        mode="latest_chunks",
        limit=10,
        seed_limit=3,
    )
    print("get_graph_snapshot:", graph_snapshot)
except Exception as e:
    print("get_graph_snapshot failed (optional):", e)

print("\n--- Core endpoints (new) ---")

try:
    workspace_id = os.environ.get("TINYHUMANS_WORKSPACE_ID")
    agent_id = os.environ.get("TINYHUMANS_AGENT_ID")
    if workspace_id and agent_id:
        sync_content = "File sync content from sdk-python example."
        sync_hash = hashlib.sha256(sync_content.encode("utf-8")).hexdigest()
        sync_res = client.sync_memory(
            workspace_id=workspace_id,
            agent_id=agent_id,
            source="startup",
            files=[
                {
                    "file_path": "example.txt",
                    "content": sync_content,
                    "timestamp": str(int(time.time())),
                    "hash": sync_hash,
                }
            ],
        )
        print("sync_memory:", sync_res)
    else:
        print(
            "sync_memory skipped (set TINYHUMANS_WORKSPACE_ID and TINYHUMANS_AGENT_ID)."
        )
except Exception as e:
    print("sync_memory failed (optional):", e)

try:
    chat_res = client.chat_memory(
        messages=[
            {
                "role": "user",
                "content": "Summarize the single document that was stored earlier.",
            }
        ],
        temperature=0,
        max_tokens=256,
    )
    print("chat_memory:", chat_res)
except Exception as e:
    print("chat_memory failed (optional):", e)

try:
    interact_res = client.interact_memory(
        namespace=docs_ns,
        entity_names=["PY-ENTITY-A", "PY-ENTITY-B"],
        description="Recorded by sdk-python example (interactMemory endpoint).",
        interaction_level="engage",
        timestamp=time.time(),
    )
    print("interact_memory:", interact_res)
except Exception as e:
    print("interact_memory failed (optional):", e)

try:
    master_ctx = client.recall_memory_master(namespace=docs_ns, max_chunks=5)
    print("recall_memory_master.context:", master_ctx.context)
except Exception as e:
    print("recall_memory_master failed (optional):", e)

try:
    memories_res = client.recall_memories(namespace=docs_ns, top_k=5, min_retention=0)
    print("recall_memories:", memories_res)
except Exception as e:
    print("recall_memories failed (optional):", e)

try:
    # Optional: if insert returned jobId fields.
    job_id = None
    if isinstance(single_doc, dict):
        job_id = single_doc.get("jobId")
    if not job_id and isinstance(batch_res, dict):
        job_id = batch_res.get("jobId")
    if job_id:
        ingestion_job = client.get_ingestion_job(job_id=job_id)
        print("get_ingestion_job:", ingestion_job)
    else:
        print("get_ingestion_job skipped (no jobId returned).")
except Exception as e:
    print("get_ingestion_job failed (optional):", e)

try:
    client.delete_document(document_id=document_id_single, namespace=docs_ns)
except Exception as e:
    print("delete_document (single) failed:", e)

for doc_id in [document_id_batch_0, document_id_batch_1]:
    try:
        client.delete_document(document_id=doc_id, namespace=docs_ns)
    except Exception as e:
        print(f"delete_document ({doc_id}) failed:", e)

# Cleanup: delete entire namespace (safe fallback).
try:
    client.delete_memory(namespace=docs_ns, delete_all=True)
except Exception as e:
    print("cleanup delete_memory failed:", e)
