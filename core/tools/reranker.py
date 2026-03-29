"""
FlashRank reranker singleton.
Loads once on first call, reranks (query, chunk) pairs by relevance.
Ultra-light: ~150 MB (multilingual), no torch/sentence-transformers dependency.
"""

import logging
import re
from flashrank import Ranker, RerankRequest

logger = logging.getLogger(__name__)

_ranker: Ranker | None = None

# Multilingual (100+ languages incl. PT-BR + EN), ~150 MB
MODEL_NAME = "ms-marco-MultiBERT-L-12"

# Regex to strip [CONTEXTO] preambles that waste reranker's token window
_CONTEXTO_RE = re.compile(
    r"\[CONTEXTO\].*?\[/CONTEXTO\]\s*",
    re.DOTALL | re.IGNORECASE,
)


def _strip_contexto(text: str) -> str:
    """Remove [CONTEXTO]...[/CONTEXTO] blocks so reranker sees actual content."""
    cleaned = _CONTEXTO_RE.sub("", text)
    # Also strip "Contexto:" single-line preambles from enrichment
    cleaned = re.sub(r"^Contexto:.*?\n", "", cleaned, count=1)
    return cleaned.strip()


def get_reranker() -> Ranker:
    """Return FlashRank singleton. Downloads model on first call."""
    global _ranker
    if _ranker is None:
        logger.info("Loading reranker model: %s ...", MODEL_NAME)
        _ranker = Ranker(model_name=MODEL_NAME, max_length=512)
        logger.info("Reranker ready.")
    return _ranker


def rerank(
    query: str,
    results: list[tuple[str, dict, float]],
    top_n: int = 8,
) -> list[tuple[str, dict, float]]:
    """Rerank (doc_text, metadata, distance) tuples using FlashRank.

    Args:
        query: The user query.
        results: List of (doc_text, metadata, distance) from hybrid search.
        top_n: Number of top results to return after reranking.

    Returns:
        Reranked list of (doc_text, metadata, reranker_score) tuples,
        sorted by relevance descending. The score replaces the original distance
        (higher = more relevant, range ~0-1).
    """
    if not results:
        return []

    ranker = get_reranker()

    # Build passages in FlashRank format
    # Strip [CONTEXTO] preambles so reranker scores on actual clinical content
    passages = [
        {
            "id": i,
            "text": _strip_contexto(doc.replace("passage: ", "", 1)),
            "meta": meta,
        }
        for i, (doc, meta, _) in enumerate(results)
    ]

    # Rerank
    rerank_request = RerankRequest(query=query, passages=passages)
    ranked = ranker.rerank(rerank_request)

    # Map back to (doc_text, metadata, score) format
    # Use ORIGINAL doc text (with contexto), not stripped version
    scored = []
    for item in ranked[:top_n]:
        idx = item["id"]
        original_doc = results[idx][0]
        meta = item["meta"]
        score = item["score"]
        scored.append((original_doc, meta, float(score)))

    return scored
