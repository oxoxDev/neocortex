# General

### What is Neocortex?

Neocortex is a brain-inspired AI memory system. It's a realtime LLM with built-in memory that understands context at massive scale at low costs. It stores, organizes, and retrieves knowledge using graph-based retrieval (GraphRAG), time-decay scoring, and interaction weighting. You plug it into any AI application so your agent can remember context across sessions, forget irrelevant noise automatically, and retrieve the right information when it matters.

Neocortex MK1 is [open source on GitHub](https://github.com/tinyhumansai/neocortex).

### What is AlphaHuman?

[AlphaHuman](https://github.com/tinyhumansai/alphahuman) is an open-source (GNU) AI agent protocol that uses the Neocortex model to execute tasks and consume real-time intelligence. It's a GUI-first consumer product that connects to Notion, Gmail, Slack, Telegram, Google Sheets, and more. Think of AlphaHuman as the agent that acts on your behalf, powered by Neocortex's memory and context understanding.

### What is Tiny Humans?

[Tiny Humans](https://tinyhumans.ai/) (TinyHumans AI) is the AI lab that builds both Neocortex and AlphaHuman. It's focused on creating AI algorithms that scale with large amounts of data at low costs.

### How do Neocortex and AlphaHuman relate to each other?

**Neocortex** is the brain: the memory engine and model that understands context at scale. **AlphaHuman** is the hands: the agent protocol that uses Neocortex to take actions and execute tasks.

Developers can use Neocortex independently (via SDK/API) to add memory to their own AI applications. Or they can build on the AlphaHuman agent protocol for a full agent stack with Neocortex built in.

### How is Neocortex different from a vector database?

Vector databases retrieve by **similarity**. Neocortex retrieves by **importance**.

In a vector DB, a six-month-old message that's semantically similar to your query ranks just as high as a critical update from yesterday. There's no concept of "this information is stale" or "this was interacted with recently."

Neocortex handles this natively. Memories have retention scores that decay over time. Knowledge that gets accessed is reinforced. The system builds a knowledge graph with entities and relationships, so queries traverse structured context rather than just matching embeddings.

The benchmarks show the difference: Neocortex achieves 0.70 context precision and 0.80 context recall on organizational queries, versus 0.55 and 0.68 for Gemini + vector DB.

### How is Neocortex different from Mem0?

[Mem0](https://mem0.ai/) is the most well-known memory layer in the space ($24M Series A, 41K GitHub stars). It operates as general-purpose memory middleware for individual AI agents.

Neocortex differs in three key ways:

1. **Structure-aware compression**: Neocortex compresses graph structure directly (entities, relationships, temporal chains), not flat text. Mem0 has no explicit compression.
2. **Cross-platform data fusion**: Neocortex ingests and resolves entities across multiple platforms. Mem0 operates per-agent without cross-platform fusion.
3. **Memory decay and interaction weighting**: Unused memories lose retention over time. Mem0 stores memories without decay.

In head-to-head benchmarks, Neocortex outperforms Mem0 on faithfulness (\~0.71 vs \~0.61), answer relevancy (\~0.76 vs \~0.59), context precision (\~0.81 vs \~0.03), and context recall (\~0.68 vs \~0.08), while delivering 3.3x faster latency and 28x lower indexing costs.

#### How does Neocortex compare to other systems?

| Dimension     | Vectorize         | Zep/Graphiti       | Cognee           | Mem0              | Neocortex                                                |
| ------------- | ----------------- | ------------------ | ---------------- | ----------------- | -------------------------------------------------------- |
| Core approach | Biomimetic memory | Temporal KG        | KG with ontology | Memory middleware | Structure-aware compression + KG + cross-platform fusion |
| Compression   | No                | Implicit via graph | No               | No                | \~1,000:1                                                |
| Privacy       | Server-side       | Server-side        | Server-side      | Cloud-hosted      | Raw data never leaves source                             |

### What LLMs does Neocortex work with?

Neocortex is model-agnostic. It works with OpenAI (GPT-4o, GPT-4o-mini), Anthropic (Claude), Google (Gemini), open-source models (Llama, Mistral), or your own fine-tuned models. The `recall_with_llm` convenience method accepts an OpenAI API key, but you can also use `recall` directly to get raw memory results and pass them to whatever model you prefer.

### Can Neocortex handle large-scale data?

Yes. Neocortex is designed to process over 1 billion tokens while maintaining low latency and high retrieval quality. An 18-person team generates roughly 50,000 messages per month across platforms, or 300,000 messages over six months. Processing this raw volume with a frontier model costs $4-30 per query. Neocortex compresses this down so queries cost \~$0.001.



***

#### Getting Help

* **Discord**: [discord.com/invite/k23Kn8nK](https://discord.com/invite/k23Kn8nK)
* **Reddit**: [r/alphahuman](https://www.reddit.com/r/alphahuman/)
* **GitHub**: [github.com/tinyhumansai](https://github.com/tinyhumansai)
* **Email**: [founders@tinyhumans.ai](mailto:founders@tinyhumans.ai)
