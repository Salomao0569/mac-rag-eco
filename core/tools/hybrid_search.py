"""
Hybrid Search: BM25 keyword search + RRF fusion with ChromaDB semantic search.
BM25 index is built once at startup from chunks JSON and kept in memory as singleton.
"""

import json
import logging
import os
import bm25s

logger = logging.getLogger(__name__)

# Singleton state
_bm25_model = None
_bm25_chunks = None  # list of dicts with 'text' and 'metadata'

# Path to chunks file
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _get_chunks_path() -> str:
    """Return path to the best available chunks file."""
    enriched = os.path.join(_BASE_DIR, "chunks_all_enriched.json")
    if os.path.exists(enriched):
        return enriched
    return os.path.join(_BASE_DIR, "chunks_all.json")


def get_bm25():
    """Return (bm25_model, chunks_list) singleton. Builds index on first call."""
    global _bm25_model, _bm25_chunks

    if _bm25_model is not None:
        return _bm25_model, _bm25_chunks

    chunks_path = _get_chunks_path()
    logger.info("Building BM25 index from %s ...", os.path.basename(chunks_path))

    with open(chunks_path, "r", encoding="utf-8") as f:
        _bm25_chunks = json.load(f)

    # Extract text for BM25 indexing
    corpus = [c.get("text", "") for c in _bm25_chunks]

    # Tokenize using bm25s built-in tokenizer
    corpus_tokens = bm25s.tokenize(corpus, stopwords="en")

    # Build BM25 index
    _bm25_model = bm25s.BM25()
    _bm25_model.index(corpus_tokens)

    logger.info("BM25 index ready: %d documents", len(_bm25_chunks))
    return _bm25_model, _bm25_chunks


def bm25_search(query: str, n_results: int = 20) -> list[tuple[dict, float]]:
    """Search BM25 index. Returns list of (chunk_dict, bm25_score) tuples."""
    model, chunks = get_bm25()

    query_tokens = bm25s.tokenize([query], stopwords="en")
    results, scores = model.retrieve(query_tokens, k=min(n_results, len(chunks)))

    # results shape: (1, k) — indices into chunks
    # scores shape: (1, k) — BM25 scores
    output = []
    for idx, score in zip(results[0], scores[0]):
        if score > 0:
            output.append((chunks[int(idx)], float(score)))

    return output


def reciprocal_rank_fusion(
    semantic_results: list[tuple[str, dict, float]],  # (doc_text, metadata, distance)
    bm25_results: list[tuple[dict, float]],            # (chunk_dict, bm25_score)
    k: int = 60,
    n_results: int = 15,
) -> list[tuple[str, dict, float]]:
    """Fuse semantic and BM25 results using Reciprocal Rank Fusion.

    RRF score = sum(1 / (k + rank)) across all result lists.
    Returns list of (doc_text, metadata, rrf_score) sorted by score descending.
    """
    # Build a unified scoring dict keyed by first 200 chars of text (dedup key)
    scores: dict[str, dict] = {}  # key -> {doc, meta, score}

    # Score semantic results
    for rank, (doc, meta, dist) in enumerate(semantic_results):
        key = doc[:200]
        if key not in scores:
            scores[key] = {"doc": doc, "meta": meta, "score": 0.0, "dist": dist}
        scores[key]["score"] += 1.0 / (k + rank + 1)

    # Score BM25 results
    for rank, (chunk, bm25_score) in enumerate(bm25_results):
        text = chunk.get("text", "")
        doc_text = f"passage: {text}"  # match ChromaDB format
        key = doc_text[:200]
        if key not in scores:
            scores[key] = {"doc": doc_text, "meta": chunk.get("metadata", {}), "score": 0.0, "dist": 0.30}
        scores[key]["score"] += 1.0 / (k + rank + 1)

    # Sort by RRF score descending
    ranked = sorted(scores.values(), key=lambda x: x["score"], reverse=True)

    # Return top n_results as (doc, meta, dist) tuples
    # For RRF results, we use a synthetic distance based on rank
    results = []
    for item in ranked[:n_results]:
        results.append((item["doc"], item["meta"], item["dist"]))

    return results
