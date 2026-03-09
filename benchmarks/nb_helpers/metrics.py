"""Evaluation metrics for benchmark notebooks.

Wraps RAGAS evaluation and provides standard EM/F1 scoring for
extractive QA benchmarks (HotPotQA, 2WikiMultiHopQA).
"""

from __future__ import annotations

import re
import string
from collections import Counter
from typing import Any


# ---------------------------------------------------------------------------
# EM / F1 answer normalization (HotPotQA standard)
# ---------------------------------------------------------------------------


def _normalize_answer(s: str) -> str:
    """Lower text, remove punctuation, articles, and extra whitespace."""
    s = s.lower()
    # Remove articles
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    # Remove punctuation
    s = s.translate(str.maketrans("", "", string.punctuation))
    # Collapse whitespace
    s = " ".join(s.split())
    return s


def exact_match_score(prediction: str, ground_truth: str) -> float:
    """Return 1.0 if normalized prediction matches ground truth, else 0.0."""
    return float(_normalize_answer(prediction) == _normalize_answer(ground_truth))


def f1_score(prediction: str, ground_truth: str) -> float:
    """Token-level F1 score between prediction and ground truth."""
    pred_tokens = _normalize_answer(prediction).split()
    gold_tokens = _normalize_answer(ground_truth).split()

    if not pred_tokens and not gold_tokens:
        return 1.0
    if not pred_tokens or not gold_tokens:
        return 0.0

    common = Counter(pred_tokens) & Counter(gold_tokens)
    num_common = sum(common.values())

    if num_common == 0:
        return 0.0

    precision = num_common / len(pred_tokens)
    recall = num_common / len(gold_tokens)
    return 2 * precision * recall / (precision + recall)


def compute_em_f1(results: list[dict]) -> dict[str, float]:
    """Compute aggregate EM and F1 over a method's per-question results.

    Args:
        results: List of per-question dicts with ``answer`` and ``ground_truth``.

    Returns:
        Dict with ``exact_match`` and ``f1`` mean scores.
    """
    valid = [r for r in results if r.get("answer") and r.get("ground_truth")]
    if not valid:
        return {"exact_match": 0.0, "f1": 0.0}

    em_scores = [exact_match_score(r["answer"], r["ground_truth"]) for r in valid]
    f1_scores = [f1_score(r["answer"], r["ground_truth"]) for r in valid]

    return {
        "exact_match": sum(em_scores) / len(em_scores),
        "f1": sum(f1_scores) / len(f1_scores),
    }


# ---------------------------------------------------------------------------
# RAGAS evaluation wrapper
# ---------------------------------------------------------------------------


async def run_ragas_evaluation(
    per_question: list[dict], config: Any
) -> tuple[dict[str, float], list[dict[str, float]]]:
    """Run RAGAS evaluation on one method's per-question results.

    Wraps ``scripts.evaluate.evaluate_method``.

    Args:
        per_question: List of per-question result dicts.
        config: BenchmarkConfig instance.

    Returns:
        Tuple of (aggregate_scores, per_question_scores).
    """
    from scripts.evaluate import evaluate_method

    return await evaluate_method(per_question, config)


# ---------------------------------------------------------------------------
# Combined evaluation
# ---------------------------------------------------------------------------


async def evaluate_all_methods(
    all_results: dict[str, dict],
    config: Any,
    use_ragas: bool = True,
    use_em_f1: bool = False,
) -> dict[str, dict]:
    """Evaluate all methods with selected metrics.

    Updates each method's result dict in-place with scores and returns
    the same dict.

    Args:
        all_results: Dict mapping method_name -> result dict (from pipeline).
        config: BenchmarkConfig.
        use_ragas: Run RAGAS metrics.
        use_em_f1: Compute EM/F1 scores.

    Returns:
        The updated ``all_results`` dict.
    """
    for method_name, method_data in all_results.items():
        per_question = method_data.get("per_question", [])
        if not per_question:
            print(f"  [{method_name}] No per-question data, skipping evaluation.")
            continue

        # RAGAS evaluation
        if use_ragas:
            print(f"  [{method_name}] Running RAGAS evaluation...")
            try:
                aggregate, per_q_scores = await run_ragas_evaluation(per_question, config)
                method_data["ragas_scores"] = aggregate

                # Attach per-question RAGAS scores
                if per_q_scores:
                    valid_idx = 0
                    for pq in per_question:
                        if pq.get("answer") and pq.get("ground_truth") and valid_idx < len(per_q_scores):
                            pq["ragas"] = per_q_scores[valid_idx]
                            valid_idx += 1

                if aggregate:
                    scores_str = ", ".join(f"{k}={v:.2f}" for k, v in aggregate.items())
                    print(f"  [{method_name}] RAGAS: {scores_str}")
                else:
                    print(f"  [{method_name}] RAGAS: no valid results")
            except Exception as e:
                print(f"  [{method_name}] RAGAS evaluation failed: {e}")

        # EM/F1 evaluation
        if use_em_f1:
            em_f1 = compute_em_f1(per_question)
            method_data["em_f1_scores"] = em_f1
            print(
                f"  [{method_name}] EM={em_f1['exact_match']:.2f}, "
                f"F1={em_f1['f1']:.2f}"
            )

    return all_results
