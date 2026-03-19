# NeoCortex: A Surprise-Weighted, Forgetting-Aware Long-Term Memory Pipeline for Retrieval-Augmented Language Systems

**Author:** Steven Enamakel
**Affiliation:** Vezures Ltd.
**Email:** enamakel@mahadao.com

## Abstract

Large language models remain fundamentally limited by bounded context windows and weak persistence across interactions. While retrieval-augmented generation improves factual access to external corpora, most systems still lack a unified account of how memory should be written, retained, reinforced, and forgotten over time. We present **NeoCortex**, a high-level memory pipeline for long-term AI systems that combines four complementary memory mechanisms: (1) **coherence memory** over chunks, entities, and relations, (2) an append-only **state event ledger** for deterministic state reconstruction, (3) **interaction memory** that reinforces content through user and workspace engagement, and (4) **forgetting and surprise dynamics** that decay stale memory while boosting informative novelty. The proposed architecture is inspired by cognitive theories of memory retention and prediction error, as well as recent work on long-term memory for language models. NeoCortex separates write-time structuring from recall-time routing, enabling both open-ended semantic retrieval and deterministic resolution of state-style queries such as location, ownership, and transitions. We argue that this design improves retrieval efficiency, personalization, interpretability, and token economy by prioritizing memory that is recent, reinforced, and behavior-changing rather than merely semantically similar.

## 1. Introduction

Contemporary language systems are highly capable within a bounded context window, yet they remain weak at persistent memory. Standard retrieval-augmented generation (RAG) addresses this limitation by retrieving passages from external stores, but naive retrieval often treats memory as a flat collection of text chunks. This makes it difficult to distinguish between broad semantic context, explicit state transitions, user-specific salience, and stale or redundant facts.

Human memory offers a useful conceptual alternative. Memory is not merely stored and retrieved; it is reinforced through use, decays over time, and is selectively updated when new experiences are surprising or contradictory. Recent work in long-term memory for language models has begun to move in this direction, including forgetting-aware memory updates, episodic segmentation, graph-based retrieval, and persistent neural memory modules. However, these ideas are often studied separately.

This paper introduces **NeoCortex**, a product-level memory architecture that unifies these strands into a single operational pipeline. NeoCortex continuously ingests new experience into structured memory and recalls context through a blend of semantic relevance, recency, interaction history, and surprise-weighted salience. At write time, the system parses documents into chunks, extracts entities and relations, persists them in graph/vector memory, and appends explicit state transitions to an event ledger. At recall time, the system routes queries either to broad semantic retrieval or to a deterministic state resolver when the question targets ordered state transitions. Memory is further modulated by reinforcement through access patterns and by Ebbinghaus-style forgetting dynamics.

Our main claim is that long-term AI memory should be treated as a **multi-store adaptive system** rather than a passive retrieval index. In particular, efficient token use requires not only better retrieval, but also mechanisms for forgetting noise, amplifying informative novelty, and separating semantic context from ordered state.

## 2. Related Work

### 2.1 Long-term memory for language models

Several recent systems address persistent memory in LLMs. MemoryBank augments conversational agents with a long-term memory store and a forgetting-aware update mechanism inspired by the Ebbinghaus forgetting curve. Its core contribution is the explicit treatment of memory retention as a dynamic process rather than static storage.

Titans introduces a neural long-term memory module that complements short-term attention, framing attention as short-term memory and persistent neural memory as a longer-lived store. The later MIRAS framework generalizes this view by casting sequence models as associative memory systems with explicit retention and attentional bias mechanisms.

These approaches motivate the idea that memory should not be identified with the context window alone. Instead, memory should be structured, persistent, and updated through principled retention mechanisms.

### 2.2 Episodic segmentation and surprise

EM-LLM shows that long-context performance benefits from segmenting experience into events using Bayesian surprise and graph-theoretic boundary refinement. This is highly relevant to systems that must distinguish routine background information from important shifts in world state.

In cognitive science and neuroscience, prediction error has long been linked to memory updating, event segmentation, and adaptive learning. Unexpected events can either strengthen encoding or trigger the formation of a new memory boundary. This motivates the use of surprise as a write-time salience signal in memory systems.

### 2.3 Graph-based memory and retrieval

GraphRAG and HippoRAG demonstrate that graph structure can improve retrieval beyond flat vector similarity. GraphRAG builds entity-centric knowledge graphs and supports more global, query-focused reasoning over corpora. HippoRAG combines graph structure with personalized PageRank to mimic aspects of long-term associative recall.

These systems support the NeoCortex design choice to maintain a coherence graph over entities, relations, mentions, and chunks, rather than relying only on chunk embeddings.

### 2.4 Forgetting and retention

The Ebbinghaus forgetting curve remains a foundational model for memory decay, though later work suggests that the precise functional form of forgetting can vary. For AI systems, the key principle is operational: memory strength should decrease with age unless reinforced, while repeated retrieval or interaction should slow future decay.

## 3. Problem Formulation

We consider a language system that must answer user queries over an evolving corpus of documents and interactions. Let the memory store at time $t$ be

$$
\mathcal{M}_t = \{ \mathcal{C}_t, \mathcal{G}_t, \mathcal{L}_t, \mathcal{I}_t \},
$$

where:

- $\mathcal{C}_t$ is a chunk store with text and embeddings,
- $\mathcal{G}_t$ is a coherence graph over entities, relations, and mentions,
- $\mathcal{L}_t$ is an append-only state event ledger,
- $\mathcal{I}_t$ is an interaction history over users, workspaces, and entities.

The system must support two broad classes of queries:

1. **Semantic recall queries**, which benefit from retrieving relevant chunks, entities, and relations.
2. **Deterministic state queries**, which require reconstruction of ordered facts such as current holder, prior holder, location, movement, or transfer history.

The challenge is to retrieve a compact, high-value context under a token budget while preserving correctness and supporting continual updates.

## 4. NeoCortex Architecture

### 4.1 End-to-end design

NeoCortex continuously performs two processes:

1. **Ingestion** of new experience into structured memory.
2. **Recall** of context for downstream response generation.

The architecture separates write-time structuring from recall-time retrieval. This separation is important because many retrieval failures originate upstream: if memory is not encoded with entity links, state events, or salience metadata, it cannot later be selectively recalled.

### 4.2 Memory layers

NeoCortex contains four complementary memory layers.

#### Coherence memory

Coherence memory stores semantic and relational context over documents, chunks, entities, and relations. It supports open-ended retrieval where the answer may require broad contextual grounding rather than a single explicit state fact.

#### State ledger memory

The state ledger is an append-only event stream derived from chunk text and relation extraction. It records explicit transitions such as movement, possession, handoff, and spatial relations. This layer is used for deterministic state reconstruction.

#### Interaction memory

Interaction memory captures user or workspace engagement with entities and documents. Interaction strength is encoded through actions such as `view`, `read`, `react`, `engage`, and `create`. Retrieved items are reinforced through access count and last-accessed metadata.

#### Forgetting and surprise dynamics

A retention model reduces the salience of stale, unreinforced memory. A surprise model boosts non-redundant, behavior-changing content relative to routine or repeated facts.

## 5. Ingestion Pipeline

### 5.1 Parse and chunk

Incoming documents are first normalized and partitioned into bounded chunks. Chunking is necessary for embedding, retrieval, citation, and provenance tracking. Each chunk preserves local order and source metadata.

### 5.2 Entity and relation extraction

From each chunk, NeoCortex extracts entities and relations. These are linked into a coherence graph with mention-level metadata such as frequency, position, and source support. Embeddings are stored for chunks, entities, and possibly relations.

### 5.3 Graph persistence

The system upserts graph structure and chunk metadata into graph/vector storage. This enables retrieval paths that use both semantic similarity and graph connectivity.

### 5.4 State event ledger construction

In parallel with graph persistence, the system appends state events to a ledger. Each event contains:

- source document and chunk identifiers,
- sentence order and optional timestamps,
- normalized event type,
- involved entities,
- qualifiers and confidence,
- summary text for inspection.

This makes state-style queries auditable and order-sensitive.

### 5.5 Surprise scoring

Optionally, each new chunk is compared against a baseline neighborhood in memory. If the mismatch is high, the system assigns a larger `prediction_error`; if the new information contradicts prior memory, the associated reward can be negative. This value is stored as `reward_weight` and later used to modulate salience during retrieval.

## 6. Recall and Routing

### 6.1 Query routing

Given a query $q$, NeoCortex first decides whether the question is best handled by:

- a **semantic retrieval path**, or
- a **state resolver path**.

Queries that ask for current location, previous location, holder, transfer history, or spatial status are routed to the state resolver. Queries asking for themes, context, explanations, or broader summaries are routed to semantic retrieval.

### 6.2 Semantic recall

Semantic recall retrieves chunks, entities, and relations using a blended score:

$$
\text{Score}(m \mid q) =
\text{Rel}(m, q)
\cdot
\text{Retention}(m)
\cdot
\text{InteractionBias}(m)
\cdot
\text{SurpriseWeight}(m),
$$

where $\text{Rel}(m, q)$ is semantic relevance, $\text{Retention}(m)$ captures recency and reinforcement, $\text{InteractionBias}(m)$ captures user or workspace importance, and $\text{SurpriseWeight}(m)$ prioritizes informative deltas.

### 6.3 Deterministic state resolution

For state-style questions, the resolver reconstructs answers from ordered events in the ledger. This can bypass free-form generation when a deterministic answer exists, reducing hallucination risk and token usage.

## 7. Forgetting and Reinforcement

NeoCortex models retention using an Ebbinghaus-style decay process. Let $a_m$ denote the age in days of memory item $m$, and let $n_m$ denote its reinforcement count. Stability is defined as

$$
S_m = S_0 \left( 1 + \gamma \ln(1 + n_m) \right),
$$

where $S_0$ is the base stability and $\gamma$ is a growth factor. Retention is then

$$
R_m = \exp(-a_m / S_m).
$$

A configurable floor can clamp very low values to zero.

This formalism captures two desired behaviors:

1. recently accessed memory decays more slowly;
2. stale, unreinforced memory contributes less unless reactivated.

Each successful retrieval can update `last_accessed_at` and increment `access_count`, creating a closed loop:

$$
\text{interact} \rightarrow \text{recall} \rightarrow \text{reinforce}.
$$

## 8. Surprise-Weighted Memory

Pure recency and frequency are insufficient because they overvalue repeated background facts. NeoCortex therefore incorporates a surprise-weighted factor derived from prediction error.

Let $m$ be a newly ingested chunk and $\mathcal{N}(m)$ its nearest prior memory neighborhood. A prediction-error proxy can be defined as the mismatch between the new chunk and its expected baseline:

$$
\delta_m = 1 - \text{sim}(m, \mathcal{N}(m)),
$$

optionally augmented with graph-overlap disagreement or contradiction penalties. The stored salience factor can then be written as

$$
W_m = f(\delta_m, c_m),
$$

where $c_m$ captures contradiction or reward sign. High-surprise content receives a larger weight during future retrieval, while contradictory information can either suppress older beliefs or trigger state updates in the ledger.

Conceptually, this mechanism promotes memory that changes the system's world model rather than memory that merely repeats what is already known.

## 9. Why a State Ledger Matters

Many practical questions are poorly served by flat retrieval. Consider queries such as:

- Who currently holds asset $x$?
- Where was object $y$ before it moved to room $z$?
- Which entity interacted most recently with node $u$?

These are not just retrieval tasks. They require ordered state reconstruction over transitions. By maintaining an append-only ledger, NeoCortex supports deterministic resolution, provenance inspection, and conflict handling.

This design also separates two forms of truth:

- **coherence truth**, which emerges from broad supporting context;
- **state truth**, which is reconstructed from ordered transitions.

That distinction improves interpretability and reduces over-reliance on free-form synthesis.

## 10. Token Efficiency and Product Implications

The core product claim of NeoCortex is that better memory is also better token economy. Systems consume too many tokens not only because context windows are small, but because they lack mechanisms to suppress noise and preserve only what remains behaviorally useful.

NeoCortex improves token efficiency in three ways:

1. **Structured write-time compression** through chunking, entity extraction, and event normalization.
2. **Selective recall** through retention-aware, interaction-aware, and surprise-aware retrieval.
3. **Deterministic bypass** for state-style questions that do not require broad generative reasoning.

This reframes memory from a storage problem into a **salience allocation problem**.

## 11. Limitations and Open Questions

NeoCortex is a systems architecture rather than a single end-to-end trained model, and several issues remain open.

First, surprise estimation is only as good as the baseline against which novelty is measured. Poor nearest-neighbor memory can misestimate importance.

Second, event extraction for the state ledger may introduce schema errors or miss implicit transitions.

Third, retention parameters such as the base stability and growth factor are application-dependent and may require calibration.

Fourth, user interaction is an imperfect signal of importance. Frequently accessed information is not always the most correct or most valuable.

These challenges suggest future work on learned routing, contradiction management, uncertainty estimation, and offline memory consolidation.

## 12. Conclusion

We presented NeoCortex, a high-level memory pipeline for long-term AI systems that integrates coherence memory, state-ledger memory, interaction reinforcement, and forgetting plus surprise dynamics. The architecture is motivated by both recent memory-augmented language-model research and cognitive theories of retention and prediction error. The central idea is that memory should be written in structured form, recalled through routed mechanisms, strengthened through use, and allowed to forget when it no longer matters. We argue that such systems are better aligned with both practical retrieval needs and efficient token use, because they prioritize what is recent, reinforced, and informative rather than treating all stored text as equally valuable.

## References

[1] Wanjun Zhong, Lianghong Guo, Qiqi Gao, He Ye, and Yanlin Wang. _MemoryBank: Enhancing Large Language Models with Long-Term Memory_. arXiv:2305.10250, 2023.

[2] Ali Behrouz, Peilin Zhong, and Vahab Mirrokni. _Titans: Learning to Memorize at Test Time_. arXiv:2501.00663, 2025.

[3] Ali Behrouz, Meisam Razaviyayn, Peilin Zhong, and Vahab Mirrokni. _It’s All Connected: A Journey Through Test-Time Memorization, Attentional Bias, Retention, and Online Optimization_. arXiv:2504.13173, 2025.

[4] Zafeirios Fountas, Martin A. Benfeghoul, Adnan Oomerjee, Fenia Christopoulou, Gerasimos Lampouras, Haitham Bou-Ammar, and Jun Wang. _Human-like Episodic Memory for Infinite Context LLMs_. arXiv:2407.09450, 2024.

[5] Bernal Jiménez Gutiérrez, Yiheng Shu, Yu Gu, Michihiro Yasunaga, and Yu Su. _HippoRAG: Neurobiologically Inspired Long-Term Memory for Large Language Models_. arXiv:2405.14831, 2024.

[6] Darren Edge, Ha Trinh, Newman Cheng, Joshua Bradley, Alex Chao, Apurva Mody, Steven Truitt, and Jonathan Larson. _From Local to Global: A Graph RAG Approach to Query-Focused Summarization_. arXiv:2404.16130, 2024.

[7] Yaxiong Wu, Xinyue Wang, Yue Zhang, and others. _From Human Memory to AI Memory: A Survey on Memory Mechanisms in the Era of LLMs_. arXiv:2504.15965, 2025.

[8] Stephan Lewandowsky, Sergio E. Hartwig, and colleagues. _Replication and Analysis of Ebbinghaus’ Forgetting Curve_. PLOS ONE, 2015.

[9] Anne Clewett and colleagues. _Predictions Transform Memories: How Expected Versus Unexpected Events Shape Memory_. Neuroscience and Biobehavioral Reviews, 2024.

[10] Kim and colleagues. _Prediction Error Determines How Memories Are Organized in the Brain_. eLife, 2024.
