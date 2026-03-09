# Choosing an SDK

Neocortex offers two SDKs depending on your needs:

| | TinyHumans SDK (`tinyhumansai`) | Neocortex GraphRAG (`neocortex`) |
| --- | --- | --- |
| **Type** | Cloud API (managed) | Local library (self-hosted) |
| **Install** | `pip install tinyhumansai` | `pip install neocortex` |
| **Infrastructure** | None — fully managed | Neo4j + OpenAI API key |
| **Best for** | Production apps, quick integration | Research, full control, custom pipelines |
| **Memory model** | Key-value with namespaces | Knowledge graph (entities + relations) |
| **Query style** | Prompt-based recall, LLM answer | Graph traversal, scored context |
| **Auth** | TinyHumans API key | OpenAI API key |

## Which should I pick?

**Choose TinyHumans SDK if you want:**
- A managed service with no infrastructure to maintain
- Simple key-value memory storage with namespaces
- Built-in LLM recall (OpenAI, Anthropic, Gemini)
- The fastest path to production

**Choose Neocortex GraphRAG if you want:**
- Full control over the knowledge graph
- To inspect extracted entities, relations, and chunks
- To run everything locally
- Custom query tuning and retrieval pipelines

## Prerequisites

- **Python 3.9+**
- **TinyHumans SDK**: A TinyHumans API key ([request access](mailto:founders@tinyhumans.ai))
- **Neocortex GraphRAG**: A running Neo4j instance and an OpenAI API key
