"""Notebook-friendly async adapter execution.

Provides ``run_single_method`` and ``run_all_methods`` that mirror the
logic in ``run.py`` but are designed for interactive Jupyter use with
inline progress output.
"""

from __future__ import annotations

import os
import time
from typing import Any

from .config import PROJECT_ROOT


async def run_single_method(
    method_name: str,
    chunks: list,
    testset: list[dict],
    config: Any,
    skip_index: bool = False,
    working_dir: str | None = None,
) -> dict[str, Any]:
    """Run a single adapter method: index + query loop.

    Args:
        method_name: Registered adapter name (e.g. ``"vdb"``).
        chunks: List of Chunk objects from a dataset loader.
        testset: List of question dicts with ``question`` and ``ground_truth``.
        config: BenchmarkConfig (or dict-like) instance.
        skip_index: If True, load an existing index instead of creating one.
        working_dir: Override the working directory for this method's index.

    Returns:
        Dict with ``indexing``, ``querying``, ``ragas_scores``, ``per_question`` keys.
    """
    from adapters import get_adapter

    adapter = get_adapter(method_name)

    if working_dir is None:
        working_dir = str(PROJECT_ROOT / "db" / f"nb_{method_name}")

    # --- Indexing ---
    indexing_result = {"time_seconds": 0, "cost_usd": 0, "tokens_input": 0, "tokens_output": 0}
    if skip_index:
        print(f"  [{method_name}] Loading existing index from {working_dir}...")
        await adapter.load_index(working_dir, config)
        print(f"  [{method_name}] Index loaded.")
    else:
        print(f"  [{method_name}] Indexing {len(chunks)} chunks...")
        os.makedirs(working_dir, exist_ok=True)
        idx = await adapter.create_index(chunks, working_dir, config)
        indexing_result = {
            "time_seconds": idx.time_seconds,
            "cost_usd": idx.cost_usd,
            "tokens_input": idx.tokens_input,
            "tokens_output": idx.tokens_output,
        }
        print(
            f"  [{method_name}] Indexed in {idx.time_seconds:.1f}s "
            f"(${idx.cost_usd:.4f})"
        )

    # --- Querying ---
    print(f"  [{method_name}] Querying {len(testset)} questions...")
    per_question: list[dict] = []
    total_start = time.perf_counter()
    total_tokens_in = 0
    total_tokens_out = 0
    total_cost = 0.0

    for i, item in enumerate(testset):
        question = item["question"]
        ground_truth = item.get("ground_truth", "")

        try:
            result = await adapter.query(question, config)
        except Exception as e:
            print(f"  [{method_name}] Q{i+1} ERROR: {e}")
            result = None

        if result:
            per_question.append({
                "question": question,
                "answer": result.answer,
                "contexts": result.contexts,
                "ground_truth": ground_truth,
                "latency_seconds": result.latency_seconds,
                "tokens_input": result.tokens_input,
                "tokens_output": result.tokens_output,
                "cost_usd": result.cost_usd,
            })
            total_tokens_in += result.tokens_input
            total_tokens_out += result.tokens_output
            total_cost += result.cost_usd
        else:
            per_question.append({
                "question": question,
                "answer": "",
                "contexts": [],
                "ground_truth": ground_truth,
                "latency_seconds": 0,
                "tokens_input": 0,
                "tokens_output": 0,
                "cost_usd": 0,
            })

        # Progress indicator every 5 questions
        if (i + 1) % 5 == 0 or (i + 1) == len(testset):
            print(f"  [{method_name}] {i+1}/{len(testset)} questions done")

    total_query_time = time.perf_counter() - total_start
    num_answered = sum(1 for q in per_question if q["answer"])
    latencies = [q["latency_seconds"] for q in per_question if q["latency_seconds"] > 0]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    print(
        f"  [{method_name}] Done: {num_answered}/{len(testset)} answered, "
        f"avg latency {avg_latency:.2f}s, total ${total_cost:.4f}"
    )

    return {
        "indexing": indexing_result,
        "querying": {
            "total_time_seconds": total_query_time,
            "total_cost_usd": total_cost,
            "total_tokens_input": total_tokens_in,
            "total_tokens_output": total_tokens_out,
            "avg_latency_seconds": avg_latency,
            "avg_cost_per_query_usd": total_cost / len(testset) if testset else 0,
        },
        "ragas_scores": {},
        "per_question": per_question,
    }


async def run_all_methods(
    methods: list[str],
    chunks: list,
    testset: list[dict],
    config: Any,
    skip_index: bool = False,
) -> dict[str, dict]:
    """Run all methods sequentially with progress output.

    Args:
        methods: List of method names to run.
        chunks: Chunk objects from dataset loader.
        testset: Question dicts.
        config: BenchmarkConfig.
        skip_index: If True, load existing indexes.

    Returns:
        Dict mapping method_name -> result dict.
    """
    all_results: dict[str, dict] = {}

    print(f"Running {len(methods)} methods: {', '.join(methods)}\n")
    for i, method_name in enumerate(methods, 1):
        print(f"--- {method_name} ({i}/{len(methods)}) ---")
        try:
            result = await run_single_method(
                method_name=method_name,
                chunks=chunks,
                testset=testset,
                config=config,
                skip_index=skip_index,
            )
            all_results[method_name] = result
        except Exception as e:
            print(f"  [{method_name}] FAILED: {e}")
            all_results[method_name] = {
                "indexing": {"time_seconds": 0, "cost_usd": 0, "tokens_input": 0, "tokens_output": 0},
                "querying": {
                    "total_time_seconds": 0,
                    "total_cost_usd": 0,
                    "total_tokens_input": 0,
                    "total_tokens_output": 0,
                    "avg_latency_seconds": 0,
                    "avg_cost_per_query_usd": 0,
                },
                "ragas_scores": {},
                "per_question": [],
                "error": str(e),
            }
        print()

    return all_results
