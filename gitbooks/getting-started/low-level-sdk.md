# Neocortex GraphRAG (Local)

The Neocortex GraphRAG SDK gives you full control over a local knowledge graph. You manage your own Neo4j instance, extract entities and relations from documents, and query the graph directly.

## Prerequisites

- **Neo4j** running locally (start with `docker compose up -d` from the repo root)
- **OpenAI API key** set in a `.env` file
- Python 3.9+

```bash
pip install neocortex python-dotenv
```

## Initialize GraphRAG

Create a `GraphRAG` instance with domain-specific configuration:

```python
from neocortex import GraphRAG, QueryParam

rag = GraphRAG(
    working_dir="./db/my_project",
    domain="information about a robotics company, its people, products, investors, and clients",
    example_queries=(
        "Who founded the company?\n"
        "What products does the company make?\n"
        "Who are the major investors?"
    ),
    entity_types=["person", "company", "product", "location", "organization"],
)
```

| Parameter | Description |
| --- | --- |
| `working_dir` | Directory where workspace state is stored |
| `domain` | Guides the LLM on what kind of entities to extract |
| `example_queries` | Helps the extraction model understand expected questions |
| `entity_types` | Categories of entities to look for |

## Insert Documents

The `insert()` method chunks text, extracts entities and relationships via an LLM, and stores everything in the knowledge graph.

```python
num_entities, num_relations, num_chunks = rag.insert(document_text)

print(f"Entities:  {num_entities}")
print(f"Relations: {num_relations}")
print(f"Chunks:    {num_chunks}")
```

## Query the Graph

Ask natural-language questions. Neocortex retrieves relevant entities, relations, and text chunks, then generates an answer.

```python
response = rag.query(
    "Who founded the company and what are their backgrounds?",
    params=QueryParam.balanced(),
)
print(response.response)
```

## Inspect Retrieved Context

Every query response includes the scored context used to generate the answer — entities, relations, and text chunks sorted by relevance.

```python
# Entities
for entity, score in response.context.entities:
    print(f"[{entity.type}] {entity.name} (score: {score:.4f})")
    print(f"  {entity.description}")

# Relations
for relation, score in response.context.relations:
    print(f"{relation.source} --[{relation.rel_type}]--> {relation.target} (score: {score:.4f})")

# Text chunks
for chunk, score in response.context.chunks:
    print(f"Score: {score:.4f}")
    print(f"  {chunk.content[:200]}...")
```

## Next Steps

- [Query Modes](query-modes.md) — Explore presets and advanced retrieval options
- [Example notebooks](https://github.com/tinyhumans/neocortex-docs/tree/main/examples/notebooks) — Full working examples
