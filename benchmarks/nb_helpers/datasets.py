"""Dataset loaders for benchmark notebooks.

Each loader returns ``(chunks, testset)`` where:
- ``chunks``: list[Chunk] ready for adapter indexing
- ``testset``: list[dict] with at least ``question`` and ``ground_truth`` keys
"""

from __future__ import annotations

import json
import os

from .config import PROJECT_ROOT


def load_ragas_sherlock(
    chunk_size: int = 1200,
    chunk_overlap: int = 200,
    max_questions: int = 0,
    corpus_path: str | None = None,
    testset_path: str | None = None,
) -> tuple[list, list[dict]]:
    """Load the existing Sherlock Holmes RAGAS benchmark data.

    Reuses the corpus chunker and test set from the CLI pipeline.

    Returns:
        (chunks, testset) tuple.
    """
    from helpers.chunking import chunk_corpus

    corpus_file = corpus_path or str(PROJECT_ROOT / "corpus" / "adventures_of_sherlock_holmes.txt")
    ts_file = testset_path or str(PROJECT_ROOT / "testset" / "sherlock_holmes.json")

    if not os.path.exists(corpus_file):
        raise FileNotFoundError(
            f"Corpus not found: {corpus_file}\n"
            "Run: bash scripts/download_corpus.sh"
        )
    if not os.path.exists(ts_file):
        raise FileNotFoundError(
            f"Test set not found: {ts_file}\n"
            "Run: python scripts/generate_testset.py"
        )

    with open(corpus_file) as f:
        text = f.read()
    chunks = chunk_corpus(text, chunk_size, chunk_overlap, source=os.path.basename(corpus_file))

    with open(ts_file) as f:
        testset = json.load(f)

    if max_questions and max_questions > 0:
        testset = testset[:max_questions]

    print(f"Sherlock Holmes corpus: {len(text):,} chars -> {len(chunks)} chunks")
    print(f"Test set: {len(testset)} questions")
    return chunks, testset


def load_hotpotqa(
    split: str = "validation",
    max_questions: int = 50,
    subset: str = "distractor",
    chunk_size: int = 1200,
    chunk_overlap: int = 200,
) -> tuple[list, list[dict]]:
    """Load HotPotQA from HuggingFace.

    Each HotPotQA example contains supporting paragraphs as context.
    We pool all unique context paragraphs into chunks and build a
    testset with gold answers.

    Args:
        split: HuggingFace split name (``"train"`` or ``"validation"``).
        max_questions: Maximum questions to load (0 = all).
        subset: Dataset subset (``"distractor"`` or ``"fullwiki"``).
        chunk_size: Target chunk size in characters.
        chunk_overlap: Overlap between chunks.

    Returns:
        (chunks, testset) tuple.
    """
    from datasets import load_dataset

    from helpers.chunking import chunk_corpus

    print(f"Downloading HotPotQA ({subset}/{split}) from HuggingFace...")
    ds = load_dataset("hotpotqa/hotpot_qa", subset, split=split, trust_remote_code=True)

    if max_questions and max_questions > 0:
        ds = ds.select(range(min(max_questions, len(ds))))

    # Collect all context paragraphs into one big text block for chunking
    all_paragraphs: list[str] = []
    seen: set[str] = set()
    for row in ds:
        for title, sentences in zip(row["context"]["title"], row["context"]["sentences"]):
            paragraph = " ".join(sentences).strip()
            key = paragraph[:200]
            if key not in seen:
                seen.add(key)
                all_paragraphs.append(f"[{title}] {paragraph}")

    corpus_text = "\n\n".join(all_paragraphs)
    chunks = chunk_corpus(corpus_text, chunk_size, chunk_overlap, source="hotpotqa")

    # Build testset
    testset: list[dict] = []
    for row in ds:
        # Build gold contexts from supporting facts
        gold_contexts: list[str] = []
        for title, sentences in zip(row["context"]["title"], row["context"]["sentences"]):
            gold_contexts.append(f"[{title}] {' '.join(sentences).strip()}")

        testset.append({
            "question": row["question"],
            "ground_truth": row["answer"],
            "gold_contexts": gold_contexts,
            "question_type": row.get("type", ""),
            "level": row.get("level", ""),
        })

    print(f"HotPotQA: {len(all_paragraphs)} paragraphs -> {len(chunks)} chunks")
    print(f"Test set: {len(testset)} questions")
    return chunks, testset


def load_twowiki_multihop(
    split: str = "validation",
    max_questions: int = 50,
    chunk_size: int = 1200,
    chunk_overlap: int = 200,
) -> tuple[list, list[dict]]:
    """Load 2WikiMultiHopQA from HuggingFace.

    Args:
        split: HuggingFace split name.
        max_questions: Maximum questions to load (0 = all).
        chunk_size: Target chunk size in characters.
        chunk_overlap: Overlap between chunks.

    Returns:
        (chunks, testset) tuple.
    """
    from datasets import load_dataset

    from helpers.chunking import chunk_corpus

    print(f"Downloading 2WikiMultiHopQA ({split}) from HuggingFace...")
    ds = load_dataset("xanhho/2WikiMultihopQA", split=split, trust_remote_code=True)

    if max_questions and max_questions > 0:
        ds = ds.select(range(min(max_questions, len(ds))))

    # Collect context paragraphs
    all_paragraphs: list[str] = []
    seen: set[str] = set()
    for row in ds:
        context = row.get("context", "")
        # Context may be a string or structured — handle both
        if isinstance(context, str) and context.strip():
            key = context[:200]
            if key not in seen:
                seen.add(key)
                all_paragraphs.append(context.strip())
        elif isinstance(context, list):
            for item in context:
                if isinstance(item, list) and len(item) >= 2:
                    title, sentences = item[0], item[1]
                    if isinstance(sentences, list):
                        paragraph = f"[{title}] {' '.join(sentences).strip()}"
                    else:
                        paragraph = f"[{title}] {sentences}"
                    key = paragraph[:200]
                    if key not in seen:
                        seen.add(key)
                        all_paragraphs.append(paragraph)
                elif isinstance(item, str) and item.strip():
                    key = item[:200]
                    if key not in seen:
                        seen.add(key)
                        all_paragraphs.append(item.strip())

    corpus_text = "\n\n".join(all_paragraphs)
    chunks = chunk_corpus(corpus_text, chunk_size, chunk_overlap, source="2wikimultihop")

    # Build testset
    testset: list[dict] = []
    for row in ds:
        testset.append({
            "question": row["question"],
            "ground_truth": row["answer"],
            "question_type": row.get("type", ""),
        })

    print(f"2WikiMultiHopQA: {len(all_paragraphs)} paragraphs -> {len(chunks)} chunks")
    print(f"Test set: {len(testset)} questions")
    return chunks, testset


def load_locomo(
    data_path: str | None = None,
    max_questions: int = 0,
    categories: list[str] | None = None,
    chunk_size: int = 1200,
    chunk_overlap: int = 200,
) -> tuple[list, list[dict]]:
    """Load LoCoMo long-conversation memory benchmark.

    Expects a JSON file (e.g. ``corpus/locomo10.json``) with conversation
    sessions containing dialogue turns and QA pairs.

    Args:
        data_path: Path to the LoCoMo JSON file.
        max_questions: Maximum questions to load (0 = all).
        categories: Filter QA pairs by category (e.g. ``["single-hop", "multi-hop"]``).
        chunk_size: Target chunk size in characters.
        chunk_overlap: Overlap between chunks.

    Returns:
        (chunks, testset) tuple.
    """
    from helpers.chunking import chunk_corpus

    locomo_path = data_path or str(PROJECT_ROOT / "corpus" / "locomo10.json")
    if not os.path.exists(locomo_path):
        raise FileNotFoundError(
            f"LoCoMo data not found: {locomo_path}\n"
            "Download from: https://github.com/snap-research/locomo"
        )

    with open(locomo_path) as f:
        data = json.load(f)

    # LoCoMo format: list of sessions, each with "conversation" and "qa_pairs"
    sessions = data if isinstance(data, list) else [data]

    all_turns: list[str] = []
    testset: list[dict] = []

    for session in sessions:
        # Extract conversation turns as chunk-able text
        conversation = session.get("conversation", [])
        session_text_parts: list[str] = []
        for turn in conversation:
            speaker = turn.get("speaker", turn.get("role", ""))
            text = turn.get("text", turn.get("content", ""))
            if text:
                session_text_parts.append(f"{speaker}: {text}")

        if session_text_parts:
            all_turns.append("\n".join(session_text_parts))

        # Extract QA pairs
        qa_pairs = session.get("qa_pairs", session.get("questions", []))
        for qa in qa_pairs:
            cat = qa.get("category", qa.get("type", ""))
            if categories and cat not in categories:
                continue
            question = qa.get("question", "")
            answer = qa.get("answer", qa.get("ground_truth", ""))
            if question and answer:
                testset.append({
                    "question": question,
                    "ground_truth": answer,
                    "category": cat,
                })

    if max_questions and max_questions > 0:
        testset = testset[:max_questions]

    # Chunk conversation text
    corpus_text = "\n\n---\n\n".join(all_turns)
    chunks = chunk_corpus(corpus_text, chunk_size, chunk_overlap, source="locomo")

    print(f"LoCoMo: {len(sessions)} sessions, {len(corpus_text):,} chars -> {len(chunks)} chunks")
    print(f"Test set: {len(testset)} questions")
    return chunks, testset
