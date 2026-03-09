<div align="center">
  <h1>You need to forget to Remember</h1>
  <p><strong>Neocortex</strong> is an AI memory system that processes up to 1 billion tokens, forgets the noise, and remembers only what matters just like the human brain.</p>
  <p>
    <a href="#benchmarks">Benchmarks</a> - <a href="#getting-started">Getting Started</a>
  </p>
</div>

---

## Key Features

### Low Latency, Low Cost, High Quality

Fast, cost-efficient retrieval that doesn't sacrifice accuracy. Neocortex delivers high-quality answers with minimal latency and token spend — making it practical for production workloads at scale.

### Human Interaction Awareness

Not all memories are equal. Neocortex learns from how users interact — views, reactions, replies, and content creation all signal what matters most. Knowledge that people engage with rises to the top; ignored information fades away.

### Intelligent Compression

Just like the human brain, Neocortex forgets the noise. Memories that aren't accessed naturally decay over time, while frequently recalled knowledge becomes more durable. The result: a memory that stays lean, relevant, and focused on what actually matters.

---

## Benchmarks

Neocortex is evaluated across four benchmark suites covering retrieval quality, temporal reasoning, needle-in-haystack retrieval, and agentic decision-making. See [BENCHMARKS.md](BENCHMARKS.md) for full details.

### RAGAS (Sherlock Holmes Corpus)

Standard RAG quality metrics evaluated on a Sherlock Holmes test set using [RAGAS](https://docs.ragas.io/). Neocortex leads in **Answer Relevancy (0.97)** and **Context Precision (0.75)**, outperforming vector DB, FastGraphRAG, Mem0, and SuperMemory.

<div align="center">
<img src=".github/images/chart_ragas.png" alt="RAGAS Benchmark" width="700"/>
</div>

### TemporalBench

Temporal reasoning benchmark measuring accuracy across ordering, state-at-time, recency, interval, and sequence question types. Neocortex achieves **100% on recency questions** — correctly identifying the most recent events thanks to its time-decay memory model.

<div align="center">
<img src=".github/images/chart_temporalbench.png" alt="TemporalBench" width="700"/>
</div>

### BABILong (Needle in a Haystack)

Long-context retrieval benchmark testing whether methods can find specific facts buried in large contexts. Neocortex is the **only method to successfully retrieve needles at 4k context length** (33% accuracy), while directfeed (raw context window) scores 0% across all lengths.

<div align="center">
<img src=".github/images/heatmap_babilong.png" alt="BABILong Heatmap" width="600"/>
</div>

### Vending-Bench (Agentic)

An agentic benchmark where methods manage a simulated vending machine business over 30 days. Neocortex achieves the **highest cumulative P&L (~$295 by day 30)**, demonstrating that better memory leads to better decision-making over time.

<div align="center">
<img src=".github/images/chart_vendingbench.png" alt="Vending-Bench P&L" width="700"/>
</div>
