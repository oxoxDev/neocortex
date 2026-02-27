"""Main benchmark runner.

Loads config, chunks corpus, runs adapters, evaluates with RAGAS,
and writes per-method result JSONs.

Usage:
    python run.py                                          # Full run (all methods)
    python run.py --methods neocortex,vdb --max-questions 10  # Quick test
    python run.py --skip-index                             # Reuse existing DBs
    python run.py --evaluate-only                          # Re-evaluate, no re-query
    python run.py --openai-model gpt-5.2                   # Override model
    python scripts/chart.py                                  # View results
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv

log = logging.getLogger("benchmark")

# Methods that require a Neo4j connection
_NEO4J_METHODS = {"neocortex", "neocortex_v1"}

# ---------------------------------------------------------------------------
# ANSI colours
# ---------------------------------------------------------------------------
_BOLD = "\033[1m"
_DIM = "\033[2m"
_RESET = "\033[0m"
_CYAN = "\033[36m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_MAGENTA = "\033[35m"
_BLUE = "\033[34m"


def check_neo4j() -> bool:
  """Check if Neo4j is reachable. Returns True if healthy, False otherwise."""
  uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
  user = os.environ.get("NEO4J_USER", "neo4j")
  password = os.environ.get("NEO4J_PASSWORD", "password")

  try:
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    driver.close()
    print(f"  Neo4j OK ({uri})")
    return True
  except Exception as e:
    print(f"  Neo4j UNAVAILABLE at {uri}: {e}")
    print("  Start it with: docker compose up -d")
    return False


def load_config() -> dict:
  """Load optional benchmark configuration from benchmark_simple/config.json."""
  config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
  if os.path.exists(config_path):
    with open(config_path) as f:
      return json.load(f)
  return {}


def chunk_corpus(text: str, chunk_size: int = 1200, chunk_overlap: int = 200) -> list[str]:
  """Split text into overlapping chunks."""
  chunks = []
  start = 0
  while start < len(text):
    end = start + chunk_size
    chunks.append(text[start:end])
    start += chunk_size - chunk_overlap
  return [c.strip() for c in chunks if c.strip()]


def load_testset(path: str) -> list[dict]:
  """Load test set from JSON file."""
  with open(path) as f:
    return json.load(f)


def _results_dir() -> str:
  return os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


def _method_result_path(method_name: str) -> str:
  return os.path.join(_results_dir(), f"{method_name}.json")


def save_method_result(method_name: str, run_config: dict, method_data: dict) -> str:
  """Save a single method's results to results/<method>.json."""
  results_dir = _results_dir()
  os.makedirs(results_dir, exist_ok=True)
  filepath = _method_result_path(method_name)
  payload = {
    "run_config": run_config,
    "method": method_name,
    **method_data,
  }
  with open(filepath, "w") as f:
    json.dump(payload, f, indent=2)
  return filepath


def load_all_method_results() -> dict:
  """Load all per-method JSON files from results/ and merge into a unified dict.

  Returns the same shape as the old unified format:
      {"run_config": {...}, "methods": {"neocortex": {...}, "vdb": {...}, ...}}
  """
  results_dir = _results_dir()
  if not os.path.isdir(results_dir):
    return {"run_config": {}, "methods": {}}

  merged_config: dict = {}
  methods: dict[str, Any] = {}

  for filename in sorted(os.listdir(results_dir)):
    if not filename.endswith(".json"):
      continue
    filepath = os.path.join(results_dir, filename)
    try:
      with open(filepath) as f:
        data = json.load(f)
    except (json.JSONDecodeError, OSError):
      continue

    # Must have a "method" key to be a per-method result file
    method_name = data.get("method")
    if not method_name:
      continue

    # Use the most recent run_config
    if data.get("run_config"):
      merged_config = data["run_config"]

    # Extract method data (everything except run_config and method key)
    method_data = {k: v for k, v in data.items() if k not in ("run_config", "method")}
    methods[method_name] = method_data

  return {"run_config": merged_config, "methods": methods}


def print_summary_table(results: dict) -> None:
  """Print a quick summary table to stdout."""
  methods = results.get("methods", {})
  if not methods:
    print("No results to display.")
    return

  headers = ["Method", "Faith.", "Relev.", "Avg Latency", "Index Time", "Index $", "Query $"]
  rows = []
  for name, m in methods.items():
    ragas = m.get("ragas_scores", {})
    indexing = m.get("indexing", {})
    querying = m.get("querying", {})
    rows.append(
      [
        name,
        f"{ragas.get('faithfulness', 0):.2f}" if ragas.get("faithfulness") is not None else "-",
        f"{ragas.get('answer_relevancy', 0):.2f}" if ragas.get("answer_relevancy") is not None else "-",
        f"{querying.get('avg_latency_seconds', 0):.1f}s",
        f"{indexing.get('time_seconds', 0):.0f}s",
        f"${indexing.get('cost_usd', 0):.4f}",
        f"${querying.get('total_cost_usd', 0):.4f}",
      ]
    )

  col_widths = [max(len(headers[i]), max((len(r[i]) for r in rows), default=0)) for i in range(len(headers))]
  header_line = "| " + " | ".join(h.ljust(w) for h, w in zip(headers, col_widths)) + " |"
  sep_line = "|" + "|".join("-" * (w + 2) for w in col_widths) + "|"
  print("\n" + header_line)
  print(sep_line)
  for row in rows:
    print("| " + " | ".join(c.ljust(w) for c, w in zip(row, col_widths)) + " |")
  print()


async def run_method(
  method_name: str,
  chunks: list[str],
  testset: list[dict],
  config: dict,
  skip_index: bool = False,
) -> dict[str, Any]:
  """Run a single method: index, query, collect results."""
  from adapters import get_adapter

  adapter = get_adapter(method_name)
  ws_name = method_name
  suffix = config.get("workspace_suffix")
  if suffix:
    ws_name = f"{method_name}_{suffix}"
  working_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "db",
    ws_name,
  )

  tag = f"[{method_name}]"
  ctag = f"{_CYAN}{tag}{_RESET}"

  # --- Indexing ---
  indexing_result = {"time_seconds": 0, "cost_usd": 0, "tokens_input": 0, "tokens_output": 0}
  if skip_index:
    log.info("%s %sSkipping indexing%s (--skip-index), loading existing index...", ctag, _YELLOW, _RESET)
    # Preserve indexing data from previous run.
    result_name = f"{method_name}_{config['workspace_suffix']}" if config.get("workspace_suffix") else method_name
    prev_path = _method_result_path(result_name)
    if os.path.exists(prev_path):
      try:
        with open(prev_path) as f:
          prev_data = json.load(f)
        prev_idx = prev_data.get("indexing", {})
        if prev_idx.get("time_seconds", 0) > 0:
          indexing_result = prev_idx
          log.info(
            "%s Preserved indexing data from previous run (%.1fs, $%.4f)",
            ctag,
            prev_idx["time_seconds"],
            prev_idx.get("cost_usd", 0),
          )
      except (json.JSONDecodeError, KeyError):
        pass
    log.info("%s load_index  dir=%s", ctag, working_dir)
    await adapter.load_index(working_dir, config)
    log.info("%s %sload_index done%s", ctag, _GREEN, _RESET)
  else:
    log.info("%s %sIndexing%s %d chunks  dir=%s", ctag, _YELLOW, _RESET, len(chunks), working_dir)
    os.makedirs(working_dir, exist_ok=True)
    idx = await adapter.create_index(chunks, working_dir, config)
    indexing_result = {
      "time_seconds": idx.time_seconds,
      "cost_usd": idx.cost_usd,
      "tokens_input": idx.tokens_input,
      "tokens_output": idx.tokens_output,
    }
    log.info(
      "%s %sIndexed%s in %.1fs  cost=%s$%.4f%s  tokens_in=%d  tokens_out=%d",
      ctag,
      _GREEN,
      _RESET,
      idx.time_seconds,
      _YELLOW,
      idx.cost_usd,
      _RESET,
      idx.tokens_input,
      idx.tokens_output,
    )

  # --- Querying ---
  log.info("%s %sQuerying%s %d questions...", ctag, _YELLOW, _RESET, len(testset))
  per_question = []
  total_start = time.perf_counter()
  total_tokens_in = 0
  total_tokens_out = 0
  total_cost = 0.0

  for i, item in enumerate(testset):
    question = item["question"]
    ground_truth = item.get("ground_truth", "")

    log.info(
      "%s %sQ%d/%d%s  %s%s%s",
      ctag,
      _BOLD,
      i + 1,
      len(testset),
      _RESET,
      _CYAN,
      question,
      _RESET,
    )
    try:
      result = await adapter.query(question, config)
    except Exception as e:
      log.info("%s   %sERROR%s: %s", ctag, _RED, _RESET, e)
      result = None

    if result:
      log.info(
        "%s   %s%.2fs%s  %s$%.4f%s  in=%d out=%d  ctx=%d",
        ctag,
        _GREEN,
        result.latency_seconds,
        _RESET,
        _YELLOW,
        result.cost_usd,
        _RESET,
        result.tokens_input,
        result.tokens_output,
        len(result.contexts),
      )
      # Log full answer
      answer_lines = result.answer.strip().replace("\n", "\n" + " " * 16)
      log.info(
        "%s   %sanswer%s:  %s",
        ctag,
        _MAGENTA,
        _RESET,
        answer_lines,
      )
      # Log ground truth for comparison
      log.info(
        "%s   %sexpect%s:  %s",
        ctag,
        _BLUE,
        _RESET,
        ground_truth,
      )
      per_question.append(
        {
          "question": question,
          "answer": result.answer,
          "contexts": result.contexts,
          "ground_truth": ground_truth,
          "latency_seconds": result.latency_seconds,
          "tokens_input": result.tokens_input,
          "tokens_output": result.tokens_output,
          "cost_usd": result.cost_usd,
        }
      )
      total_tokens_in += result.tokens_input
      total_tokens_out += result.tokens_output
      total_cost += result.cost_usd
    else:
      log.info("%s   %sno result%s", ctag, _RED, _RESET)
      per_question.append(
        {
          "question": question,
          "answer": "",
          "contexts": [],
          "ground_truth": ground_truth,
          "latency_seconds": 0,
          "tokens_input": 0,
          "tokens_output": 0,
          "cost_usd": 0,
        }
      )

  total_query_time = time.perf_counter() - total_start
  num_answered = sum(1 for q in per_question if q["answer"])
  latencies = [q["latency_seconds"] for q in per_question if q["latency_seconds"] > 0]
  avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

  log.info(
    "%s %sDone%s: %d/%d answered, avg latency %s%.2fs%s, total %s$%.4f%s",
    ctag,
    _GREEN,
    _RESET,
    num_answered,
    len(testset),
    _GREEN,
    avg_latency,
    _RESET,
    _YELLOW,
    total_cost,
    _RESET,
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


async def evaluate_single_method(method_name: str, config: dict) -> None:
  """Run RAGAS evaluation on a single method's saved result file."""
  from scripts.evaluate import evaluate_method

  filepath = _method_result_path(method_name)
  if not os.path.exists(filepath):
    print(f"  [{method_name}] No result file found, skipping.")
    return

  with open(filepath) as f:
    data = json.load(f)

  per_question = data.get("per_question", [])
  if not per_question:
    print(f"  [{method_name}] No per-question data, skipping.")
    return

  print(f"  [{method_name}] Running RAGAS evaluation on {len(per_question)} questions...")
  try:
    aggregate, per_q_scores = await evaluate_method(per_question, config)
    data["ragas_scores"] = aggregate
    if per_q_scores:
      valid_idx = 0
      for pq in per_question:
        if pq.get("answer") and pq.get("ground_truth") and valid_idx < len(per_q_scores):
          pq["ragas"] = per_q_scores[valid_idx]
          valid_idx += 1
    with open(filepath, "w") as f:
      json.dump(data, f, indent=2)
    if aggregate:
      print(f"  [{method_name}] RAGAS: " + ", ".join(f"{k}={v:.2f}" for k, v in aggregate.items()))
    else:
      print(f"  [{method_name}] RAGAS: no valid results for evaluation")
  except Exception as e:
    print(f"  [{method_name}] RAGAS evaluation failed: {e}")


async def main():
  """Entry point for the simplified book-based RAG benchmark CLI."""
  load_dotenv()
  config = load_config()

  parser = argparse.ArgumentParser(description="Simplified Book-Based RAG Benchmark")
  parser.add_argument("--methods", default=None, help="Comma-separated method names (default: all from config)")
  parser.add_argument("--max-questions", type=int, default=None, help="Limit number of questions (0 = all)")
  parser.add_argument("--top-k", type=int, default=None, help="Number of chunks to retrieve")
  parser.add_argument("--chunk-size", type=int, default=None, help="Chunk size in chars")
  parser.add_argument("--chunk-overlap", type=int, default=None, help="Chunk overlap in chars")
  parser.add_argument("--openai-model", default=None, help="Override OpenAI model")
  parser.add_argument("--skip-index", action="store_true", help="Skip indexing, reuse existing DBs")
  parser.add_argument("--evaluate-only", action="store_true", help="Re-evaluate without re-querying")
  parser.add_argument("--skip-ragas", action="store_true", help="Skip RAGAS evaluation")
  parser.add_argument("--corpus-path", default=None, help="Override corpus file path")
  parser.add_argument("--testset-path", default=None, help="Override test set file path")
  parser.add_argument("-q", "--question", type=int, default=None, help="Run only this question index (0-based)")
  parser.add_argument(
    "--compression",
    default=None,
    choices=["none", "attention", "gpt-2"],
    help="Compression backend for neocortex (none, attention, gpt-2)",
  )
  parser.add_argument(
    "--workspace-suffix",
    default=None,
    help="Suffix appended to workspace dir name (e.g. 'compressed' -> db/neocortex_compressed/)",
  )
  parser.add_argument(
    "--debug", action="store_true", help="Enable debug logging (shows each question, answer previews, timings)"
  )
  parser.add_argument(
    "--max-corpus-chars", type=int, default=None, help="Truncate corpus to N chars (for quick testing)"
  )
  args = parser.parse_args()

  # --- Logging setup ---
  level = logging.DEBUG if args.debug else logging.INFO
  logging.basicConfig(
    level=level,
    format="%(asctime)s %(name)s %(message)s",
    datefmt="%H:%M:%S",
  )

  # Apply CLI overrides to config
  if args.methods:
    config["methods"] = [m.strip() for m in args.methods.split(",")]
  if args.max_questions is not None:
    config["max_questions"] = args.max_questions
  if args.top_k is not None:
    config["top_k"] = args.top_k
  if args.chunk_size is not None:
    config["chunk_size"] = args.chunk_size
  if args.chunk_overlap is not None:
    config["chunk_overlap"] = args.chunk_overlap
  if args.openai_model:
    config["openai_model"] = args.openai_model
  if args.corpus_path:
    config["corpus_path"] = args.corpus_path
  if args.testset_path:
    config["testset_path"] = args.testset_path
  if args.compression:
    config["compression_backend"] = args.compression
  if args.workspace_suffix:
    config["workspace_suffix"] = args.workspace_suffix
  if args.max_corpus_chars is not None:
    config["max_corpus_chars"] = args.max_corpus_chars

  script_dir = os.path.dirname(os.path.abspath(__file__))
  methods = config.get("methods", [])

  if not methods:
    print("No methods configured. Check config.json or use --methods.")
    sys.exit(1)

  # --- Evaluate-only mode ---
  if args.evaluate_only:
    print("Re-evaluating existing results with RAGAS...\n")
    for method_name in methods:
      await evaluate_single_method(method_name, config)
    print()
    all_results = load_all_method_results()
    print_summary_table(all_results)
    return

  # --- Load corpus ---
  corpus_path = config.get("corpus_path", "./corpus/adventures_of_sherlock_holmes.txt")
  if not os.path.isabs(corpus_path):
    corpus_path = os.path.join(script_dir, corpus_path)

  if not os.path.exists(corpus_path):
    print(f"Corpus not found: {corpus_path}")
    print("Run: bash scripts/download_corpus.sh")
    sys.exit(1)

  log.info("Loading corpus from %s", corpus_path)
  print(f"Loading corpus from {corpus_path}...")
  with open(corpus_path) as f:
    text = f.read()

  # Pass corpus file extension and full text to adapters for section-aware chunking
  corpus_ext = os.path.splitext(corpus_path)[1]  # e.g. ".txt"
  if corpus_ext:
    config.setdefault("corpus_file_ext", corpus_ext)
  config["_corpus_full_text"] = text

  chunk_size = config.get("chunk_size", 1200)
  chunk_overlap = config.get("chunk_overlap", 200)
  chunks = chunk_corpus(text, chunk_size, chunk_overlap)
  print(f"Corpus: {len(text)} chars -> {len(chunks)} chunks (size={chunk_size}, overlap={chunk_overlap})")
  log.info("Corpus loaded: %d chars, %d chunks", len(text), len(chunks))

  # --- Load test set ---
  testset_path = config.get("testset_path", "./testset/sherlock_holmes.json")
  if not os.path.isabs(testset_path):
    testset_path = os.path.join(script_dir, testset_path)

  if not os.path.exists(testset_path):
    print(f"Test set not found: {testset_path}")
    print("Run: python scripts/generate_testset.py")
    sys.exit(1)

  testset = load_testset(testset_path)
  if args.question is not None:
    if args.question < 0 or args.question >= len(testset):
      print(f"Error: question index {args.question} out of range (0-{len(testset) - 1})")
      sys.exit(1)
    testset = [testset[args.question]]
    print(f"Running single question [{args.question}]: {testset[0]['question']}")
  else:
    max_q = config.get("max_questions", 0)
    if max_q and max_q > 0:
      testset = testset[:max_q]
  print(f"Test set: {len(testset)} questions")
  log.info("Test set: %d questions from %s", len(testset), testset_path)

  run_config = {
    "corpus": config.get("corpus", "sherlock_holmes"),
    "num_questions": len(testset),
    "top_k": config.get("top_k", 8),
    "chunk_size": chunk_size,
    "chunk_overlap": chunk_overlap,
    "openai_model": config.get("openai_model", "gpt-4o-mini"),
    "timestamp": datetime.now(timezone.utc).isoformat(),
  }

  # --- Pre-flight: check Neo4j if any method needs it ---
  neo4j_needed = _NEO4J_METHODS.intersection(methods)
  if neo4j_needed and not args.skip_index:
    print("Checking Neo4j connectivity (needed by: " + ", ".join(neo4j_needed) + ")...")
    if not check_neo4j():
      print("\nSkipping Neo4j-dependent methods. Fix the connection or use --skip-index.\n")
      methods = [m for m in methods if m not in _NEO4J_METHODS]
      if not methods:
        print("No methods left to run.")
        sys.exit(1)

  # --- Run each method ---
  print(f"\nRunning {len(methods)} methods: {', '.join(methods)}\n")
  # Log config without large/internal keys (e.g. _corpus_full_text) to avoid dumping the entire corpus
  _skip_keys = {"methods", "_corpus_full_text"}
  log.info("Config: %s", {k: v for k, v in config.items() if k not in _skip_keys})
  for method_idx, method_name in enumerate(methods, 1):
    log.info(
      "%s━━━ %s%s%s (%d/%d) ━━━%s",
      _BOLD,
      _CYAN,
      method_name,
      _RESET + _BOLD,
      method_idx,
      len(methods),
      _RESET,
    )
    method_start = time.perf_counter()
    try:
      method_data = await run_method(
        method_name=method_name,
        chunks=chunks,
        testset=testset,
        config=config,
        skip_index=args.skip_index,
      )
    except Exception as e:
      print(f"  [{method_name}] FAILED: {e}")
      method_data = {
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

    # --- RAGAS evaluation (per method, immediately after querying) ---
    ctag_main = f"{_CYAN}[{method_name}]{_RESET}"
    if not args.skip_ragas and method_data.get("per_question"):
      from scripts.evaluate import evaluate_method

      log.info("%s %sRunning RAGAS evaluation%s...", ctag_main, _YELLOW, _RESET)
      ragas_start = time.perf_counter()
      try:
        aggregate, per_q_scores = await evaluate_method(method_data["per_question"], config)
        method_data["ragas_scores"] = aggregate
        ragas_elapsed = time.perf_counter() - ragas_start

        # Attach per-question RAGAS scores to the result data
        if per_q_scores:
          valid_idx = 0
          for pq in method_data["per_question"]:
            if pq.get("answer") and pq.get("ground_truth") and valid_idx < len(per_q_scores):
              pq["ragas"] = per_q_scores[valid_idx]
              valid_idx += 1

          # Log per-question RAGAS scores
          for j, pq in enumerate(method_data["per_question"]):
            if "ragas" in pq:
              q_short = pq["question"][:60] + ("..." if len(pq["question"]) > 60 else "")
              scores_str = "  ".join(
                f"{k}={_GREEN}{v:.2f}{_RESET}"
                if v >= 0.7
                else f"{k}={_YELLOW}{v:.2f}{_RESET}"
                if v >= 0.4
                else f"{k}={_RED}{v:.2f}{_RESET}"
                for k, v in pq["ragas"].items()
              )
              log.info(
                "%s   %sQ%d%s  %s  %s",
                ctag_main,
                _DIM,
                j + 1,
                _RESET,
                scores_str,
                f"{_DIM}{q_short}{_RESET}",
              )

        if aggregate:
          agg_str = "  ".join(f"{k}={_BOLD}{v:.2f}{_RESET}" for k, v in aggregate.items())
          log.info(
            "%s %sRAGAS%s (%.1fs):  %s",
            ctag_main,
            _GREEN,
            _RESET,
            ragas_elapsed,
            agg_str,
          )
        else:
          log.info("%s %sRAGAS%s: no valid results for evaluation", ctag_main, _YELLOW, _RESET)
      except Exception as e:
        log.info("%s %sRAGAS error%s: %s", ctag_main, _RED, _RESET, e, exc_info=True)

    # Save this method's result to its own file
    result_name = f"{method_name}_{config['workspace_suffix']}" if config.get("workspace_suffix") else method_name
    path = save_method_result(result_name, run_config, method_data)
    method_elapsed = time.perf_counter() - method_start
    log.info(
      "%s %sSaved%s to %s  |  total time %s%.1fs%s",
      ctag_main,
      _GREEN,
      _RESET,
      path,
      _GREEN,
      method_elapsed,
      _RESET,
    )
    log.info("")

  # --- Display combined summary ---
  all_results = load_all_method_results()
  print_summary_table(all_results)


if __name__ == "__main__":
  asyncio.run(main())
