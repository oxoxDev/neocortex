# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **RAG (Retrieval-Augmented Generation) benchmark suite** that compares the Neocortex GraphRAG implementation against other RAG methods (vector DB, LightRAG, GraphRAG, Cognee, etc.) using a Sherlock Holmes corpus. It measures faithfulness, answer relevancy, context precision/recall (via RAGAS), latency, and cost.

## Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
bash scripts/download_corpus.sh                   # Download Sherlock Holmes corpus

# Start Neo4j (required for neocortex/neocortex_v1 methods)
docker compose up -d

# Generate test questions (uses OpenAI API)
python scripts/generate_testset.py
python scripts/generate_testset.py --num-questions 50 --model gpt-4o

# Run benchmarks
python run.py                                         # All methods from config.json
python run.py --methods neocortex,vdb --max-questions 10  # Specific methods, limited questions
python run.py --skip-index                            # Reuse existing indexes
python run.py --evaluate-only                         # Re-run RAGAS without re-querying
python run.py --skip-ragas                            # Skip RAGAS evaluation
python run.py -q 3                                    # Run single question (0-indexed)

# View results
python scripts/chart.py                    # Markdown table
python scripts/chart.py --chart bar        # Bar chart (matplotlib)
python scripts/chart.py --chart questions  # Per-question breakdown
python scripts/chart.py --chart csv        # CSV export
```

## Architecture

**Pipeline flow**: `scripts/download_corpus.sh` → `scripts/generate_testset.py` → `run.py` → `scripts/evaluate.py` → `scripts/chart.py`

- **`run.py`** — Main CLI orchestrator. Loads corpus, chunks it, runs each adapter (index → query), then evaluates with RAGAS. Saves per-method JSON results to `results/`.
- **`scripts/generate_testset.py`** — Generates RAGAS-compatible test questions using OpenAI. Produces 4 question types: inference, multi-hop, cross-story, analytical. Output: `testset/sherlock_holmes.json`.
- **`scripts/evaluate.py`** — RAGAS evaluation wrapper (async, uses RAGAS 0.4.x `aevaluate` API). Returns aggregate and per-question scores.
- **`scripts/chart.py`** — Results visualization (markdown table, CSV, matplotlib charts).
- **`config.json`** — Central config: methods list, chunk params, model names, RAGAS metrics.

### Adapter System

All RAG methods are wrapped in adapters under `adapters/` implementing `MethodAdapter` (defined in `adapters/_base.py`):
- **Interface**: `create_index(chunks, working_dir, config)` → `IndexResult`, `query(question, config)` → `QueryResult`, `load_index(working_dir, config)`
- **Registry**: `adapters/__init__.py` maps method names to adapter classes via lazy imports
- **Available**: neocortex, neocortex_v1, vdb, directfeed, lightrag, fast_graphrag, nano_graphrag, graphrag, cognee, gpt52_vdb, gemini_vdb

To add a new adapter: create `adapters/my_method.py` with a class extending `MethodAdapter`, then register it in `_ADAPTER_REGISTRY` in `adapters/__init__.py`.

### Data Flow

- Corpus text → `corpus/` (gitignored, downloaded via script)
- Chunked indexes → `db/<method_name>/` (gitignored)
- Results → `results/<method>.json` (tracked)
- Test set → `testset/sherlock_holmes.json`

## Environment

- **Python 3.13+** with `.venv`
- Requires `OPENAI_API_KEY` in `.env` (for embeddings, judge model, and some adapters)
- Neo4j (via Docker Compose) needed only for `neocortex` and `neocortex_v1` methods
- The `neocortex` package itself is installed from the parent repo (`pip install -e .` from repo root)
