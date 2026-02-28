"""Notebook-optimized charts and tables.

All functions render inline in Jupyter via ``plt.show()`` and
``IPython.display.HTML``.
"""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
from IPython.display import HTML, display


# ---------------------------------------------------------------------------
# Summary table (HTML)
# ---------------------------------------------------------------------------


def summary_table(
    all_results: dict[str, dict],
    extra_metrics: list[str] | None = None,
) -> None:
    """Display an HTML summary table of benchmark results.

    Args:
        all_results: Dict mapping method_name -> result dict.
        extra_metrics: Additional metric columns to show (e.g. ``["exact_match", "f1"]``).
    """
    if not all_results:
        print("No results to display.")
        return

    headers = [
        "Method",
        "Faithfulness",
        "Relevancy",
        "Ctx Precision",
        "Ctx Recall",
        "Avg Latency",
        "Index Time",
        "Index $",
        "Query $",
    ]
    if extra_metrics:
        for m in extra_metrics:
            headers.append(m.replace("_", " ").title())

    rows: list[list[str]] = []
    for name, data in all_results.items():
        ragas = data.get("ragas_scores", {})
        indexing = data.get("indexing", {})
        querying = data.get("querying", {})
        em_f1 = data.get("em_f1_scores", {})

        row = [
            f"<b>{name}</b>",
            f"{ragas.get('faithfulness', 0):.2f}" if ragas.get("faithfulness") is not None else "-",
            f"{ragas.get('answer_relevancy', 0):.2f}" if ragas.get("answer_relevancy") is not None else "-",
            f"{ragas.get('context_precision', 0):.2f}" if ragas.get("context_precision") is not None else "-",
            f"{ragas.get('context_recall', 0):.2f}" if ragas.get("context_recall") is not None else "-",
            f"{querying.get('avg_latency_seconds', 0):.2f}s",
            f"{indexing.get('time_seconds', 0):.1f}s",
            f"${indexing.get('cost_usd', 0):.4f}",
            f"${querying.get('total_cost_usd', 0):.4f}",
        ]
        if extra_metrics:
            for m in extra_metrics:
                val = em_f1.get(m)
                row.append(f"{val:.2f}" if val is not None else "-")
        rows.append(row)

    # Build HTML table
    html = '<table style="border-collapse: collapse; font-family: monospace; font-size: 13px;">'
    html += "<tr>"
    for h in headers:
        html += f'<th style="border: 1px solid #ddd; padding: 6px 10px; background: #f5f5f5; text-align: center;">{h}</th>'
    html += "</tr>"
    for row in rows:
        html += "<tr>"
        for j, cell in enumerate(row):
            align = "left" if j == 0 else "center"
            html += f'<td style="border: 1px solid #ddd; padding: 6px 10px; text-align: {align};">{cell}</td>'
        html += "</tr>"
    html += "</table>"

    display(HTML(html))


# ---------------------------------------------------------------------------
# RAGAS bar chart
# ---------------------------------------------------------------------------


def ragas_bar_chart(
    all_results: dict[str, dict],
    title: str = "RAGAS Scores by Method",
) -> None:
    """Grouped bar chart of 4 RAGAS metrics across methods."""
    methods = list(all_results.keys())
    metrics = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    labels = ["Faithfulness", "Relevancy", "Ctx Precision", "Ctx Recall"]
    colors = ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0"]

    n_methods = len(methods)
    n_metrics = len(metrics)
    bar_width = 0.8 / n_metrics
    x = range(n_methods)

    fig, ax = plt.subplots(figsize=(max(8, n_methods * 1.5), 5))
    for i, (metric, label, color) in enumerate(zip(metrics, labels, colors)):
        values = [
            all_results[m].get("ragas_scores", {}).get(metric, 0)
            for m in methods
        ]
        positions = [xi + i * bar_width for xi in x]
        ax.bar(positions, values, bar_width, label=label, color=color, alpha=0.85)

    ax.set_xlabel("Method")
    ax.set_ylabel("Score")
    ax.set_title(title)
    ax.set_xticks([xi + bar_width * (n_metrics - 1) / 2 for xi in x])
    ax.set_xticklabels(methods, rotation=30, ha="right")
    ax.set_ylim(0, 1.05)
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.show()


# ---------------------------------------------------------------------------
# Latency chart
# ---------------------------------------------------------------------------


def latency_chart(
    all_results: dict[str, dict],
    title: str = "Average Query Latency",
) -> None:
    """Horizontal bar chart of average query latency per method."""
    methods = list(all_results.keys())
    latencies = [
        all_results[m].get("querying", {}).get("avg_latency_seconds", 0)
        for m in methods
    ]

    fig, ax = plt.subplots(figsize=(8, max(3, len(methods) * 0.5)))
    colors = ["#EF5350" if lat > 5 else "#FF9800" if lat > 2 else "#4CAF50" for lat in latencies]
    ax.barh(methods, latencies, color=colors, alpha=0.85)
    ax.set_xlabel("Seconds")
    ax.set_title(title)
    for i, v in enumerate(latencies):
        ax.text(v + 0.05, i, f"{v:.2f}s", va="center", fontsize=9)
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    plt.show()


# ---------------------------------------------------------------------------
# Cost breakdown chart
# ---------------------------------------------------------------------------


def cost_breakdown_chart(
    all_results: dict[str, dict],
    title: str = "Cost Breakdown (Index vs Query)",
) -> None:
    """Stacked horizontal bar chart of indexing vs querying cost."""
    methods = list(all_results.keys())
    index_costs = [
        all_results[m].get("indexing", {}).get("cost_usd", 0)
        for m in methods
    ]
    query_costs = [
        all_results[m].get("querying", {}).get("total_cost_usd", 0)
        for m in methods
    ]

    fig, ax = plt.subplots(figsize=(8, max(3, len(methods) * 0.5)))
    ax.barh(methods, index_costs, color="#2196F3", alpha=0.85, label="Index")
    ax.barh(methods, query_costs, left=index_costs, color="#FF9800", alpha=0.85, label="Query")
    ax.set_xlabel("Cost (USD)")
    ax.set_title(title)
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    plt.show()


# ---------------------------------------------------------------------------
# EM / F1 chart (HotPotQA / 2Wiki)
# ---------------------------------------------------------------------------


def em_f1_chart(
    all_results: dict[str, dict],
    title: str = "Exact Match & F1 Scores",
) -> None:
    """Bar chart comparing EM and F1 across methods."""
    methods = list(all_results.keys())
    em_scores = [
        all_results[m].get("em_f1_scores", {}).get("exact_match", 0)
        for m in methods
    ]
    f1_scores = [
        all_results[m].get("em_f1_scores", {}).get("f1", 0)
        for m in methods
    ]

    n_methods = len(methods)
    bar_width = 0.35
    x = range(n_methods)

    fig, ax = plt.subplots(figsize=(max(6, n_methods * 1.2), 5))
    ax.bar([xi - bar_width / 2 for xi in x], em_scores, bar_width, label="Exact Match", color="#2196F3", alpha=0.85)
    ax.bar([xi + bar_width / 2 for xi in x], f1_scores, bar_width, label="F1", color="#4CAF50", alpha=0.85)

    ax.set_xlabel("Method")
    ax.set_ylabel("Score")
    ax.set_title(title)
    ax.set_xticks(list(x))
    ax.set_xticklabels(methods, rotation=30, ha="right")
    ax.set_ylim(0, 1.05)
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.show()
