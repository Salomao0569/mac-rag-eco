"""
Contextual Retrieval enrichment for MAC RAG Ecocardiografia.
Uses gpt-4o-mini at indexing time to generate contextual summaries for each chunk.
The summary is prepended to the chunk text before embedding in ChromaDB.

Usage:
    python enrich.py                    # enrich all chunks
    python enrich.py --resume           # resume from cache (skip already processed)
    python enrich.py --test 10          # test with first 10 chunks only
    python enrich.py --no-cache         # force re-processing all chunks
"""

import argparse
import hashlib
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import openai  # noqa: E402 — must come after load_dotenv so OPENAI_API_KEY is set

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MODEL = "gpt-4o-mini"
OLLAMA_MODEL = "qwen3.5:9b"
OLLAMA_HOST = "http://192.168.18.100:11434"
TEMPERATURE = 0
MAX_TOKENS = 300
BATCH_SIZE = 50
MAX_WORKERS = 10
OLLAMA_MAX_WORKERS = 2  # Ollama handles fewer concurrent requests
TIMEOUT_SECONDS = 30
OLLAMA_TIMEOUT = 60  # Longer timeout for local model
MAX_RETRIES = 2

CACHE_PATH = Path(__file__).parent / "chunk_contexts.json"

SYSTEM_PROMPT = (
    "Você é um indexador de diretrizes de ecocardiografia. "
    "Dado um trecho de uma diretriz ou consensus statement de ecocardiografia, "
    "gere um RESUMO CONTEXTUAL curto (máx 150 palavras) que inclua:\n\n"
    "1. TEMA ECOCARDIOGRÁFICO principal (ex: avaliação da função diastólica do VE, "
    "quantificação da estenose aórtica, strain longitudinal global)\n"
    "2. MEDIDAS E PARÂMETROS mencionados (ex: FEVE, TAPSE, E/e', strain, AVA, gradiente)\n"
    "3. TÉCNICAS DE IMAGEM mencionadas (ex: Doppler tecidual, speckle tracking, 3D, TEE)\n"
    "4. VALORES DE REFERÊNCIA e classificações de gravidade presentes\n"
    "5. RECOMENDAÇÕES e classe de evidência se disponíveis\n\n"
    "IMPORTANTE:\n"
    "- Se é uma tabela de valores normais ou classificação de gravidade, liste TODOS os parâmetros e faixas\n"
    "- Se menciona uma medida ecocardiográfica, cite também o corte de anormalidade\n"
    "- Se menciona uma técnica, cite em qual janela/incidência é obtida\n"
    "- NÃO invente informação — apenas organize e conecte o que está no texto\n"
    "- Responda em português"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _chunk_hash(chunk: dict) -> str:
    """Create a stable hash key for a chunk based on text and metadata."""
    meta = chunk.get("metadata", {})
    key_parts = [
        chunk.get("text", "")[:500],
        meta.get("diretriz", ""),
        meta.get("secao", ""),
        meta.get("parte", ""),
    ]
    raw = "|".join(str(p) for p in key_parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _build_user_message(chunk: dict) -> str:
    """Build the user message for the o-mini context generation call."""
    meta = chunk.get("metadata", {})
    return (
        f"Metadados:\n"
        f"- Diretriz: {meta.get('diretriz', '')}\n"
        f"- Sociedade: {meta.get('sociedade', '')}\n"
        f"- Seção: {meta.get('secao', '')}\n"
        f"- Ano: {meta.get('ano', '')}\n\n"
        f"Texto:\n{chunk.get('text', '')}"
    )


def _load_cache() -> dict[str, str]:
    """Load the chunk context cache from disk."""
    if CACHE_PATH.exists():
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                cache = json.load(f)
            logger.info("Loaded cache with %d entries from %s", len(cache), CACHE_PATH)
            return cache
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load cache (%s), starting fresh", exc)
    return {}


def _save_cache(cache: dict[str, str]) -> None:
    """Persist the chunk context cache to disk."""
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    logger.info("Saved cache with %d entries to %s", len(cache), CACHE_PATH)


def _call_openai(client: openai.OpenAI, chunk: dict) -> str:
    """Call gpt-4o-mini to generate a contextual summary for a single chunk.

    Retries up to MAX_RETRIES times on failure. Returns empty string on
    exhausted retries (graceful degradation).
    """
    user_msg = _build_user_message(chunk)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                timeout=TIMEOUT_SECONDS,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:  # noqa: BLE001
            if attempt < MAX_RETRIES:
                logger.warning(
                    "OpenAI call failed (attempt %d/%d): %s — retrying...",
                    attempt,
                    MAX_RETRIES,
                    exc,
                )
                time.sleep(1 * attempt)  # simple linear back-off
            else:
                logger.error(
                    "OpenAI call failed after %d attempts: %s — using empty context",
                    MAX_RETRIES,
                    exc,
                )
                return ""


def _call_ollama(chunk: dict) -> str:
    """Call Ollama (Qwen 3.5 9B) to generate a contextual summary. Free, runs on GPU."""
    import requests

    user_msg = _build_user_message(chunk)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(
                f"{OLLAMA_HOST}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_msg},
                    ],
                    "stream": False,
                    "think": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": MAX_TOKENS,
                    },
                },
                timeout=OLLAMA_TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"].strip()
        except Exception as exc:
            if attempt < MAX_RETRIES:
                logger.warning(
                    "Ollama call failed (attempt %d/%d): %s — retrying...",
                    attempt, MAX_RETRIES, exc,
                )
                time.sleep(2 * attempt)
            else:
                logger.error(
                    "Ollama call failed after %d attempts: %s — using empty context",
                    MAX_RETRIES, exc,
                )
                return ""


# ---------------------------------------------------------------------------
# Core enrichment
# ---------------------------------------------------------------------------


def enrich_chunks(chunks: list[dict], *, use_cache: bool = True, use_ollama: bool = False) -> list[dict]:
    """Enrich chunks with contextual summaries.

    Uses gpt-4o-mini (API) by default, or Qwen 3.5 9B via Ollama (--ollama flag).
    For each chunk, prepends a [CONTEXTO] block to the text.
    Returns the same chunks list with modified text fields.
    """
    backend = f"Ollama ({OLLAMA_MODEL})" if use_ollama else f"OpenAI ({MODEL})"
    logger.info("Enrichment backend: %s", backend)

    # 1. Load cache
    cache: dict[str, str] = _load_cache() if use_cache else {}

    # 2. Partition chunks into cached / uncached
    chunk_hashes = [_chunk_hash(c) for c in chunks]
    to_process: list[tuple[int, dict, str]] = []  # (index, chunk, hash)
    cached_count = 0

    for idx, (chunk, h) in enumerate(zip(chunks, chunk_hashes)):
        if h in cache:
            cached_count += 1
        else:
            to_process.append((idx, chunk, h))

    total = len(chunks)
    logger.info(
        "Enrichment plan: %d total chunks, %d cached, %d to process",
        total,
        cached_count,
        len(to_process),
    )

    # 3. Process uncached chunks via ThreadPoolExecutor
    failed_count = 0

    if to_process:
        if use_ollama:
            call_fn = lambda chunk: _call_ollama(chunk)
            workers = OLLAMA_MAX_WORKERS
        else:
            client = openai.OpenAI()
            call_fn = lambda chunk: _call_openai(client, chunk)
            workers = MAX_WORKERS

        processed_count = 0
        start_time = time.time()

        def _process_one(item: tuple[int, dict, str]) -> tuple[str, str]:
            """Returns (chunk_hash, context_text)."""
            _, chunk, h = item
            context = call_fn(chunk)
            return h, context

        # Process in batches for progress logging
        for batch_start in range(0, len(to_process), BATCH_SIZE):
            batch = to_process[batch_start : batch_start + BATCH_SIZE]

            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {executor.submit(_process_one, item): item for item in batch}

                for future in as_completed(futures):
                    h, context = future.result()
                    cache[h] = context
                    if context == "":
                        failed_count += 1
                    processed_count += 1

            # Log progress
            elapsed = time.time() - start_time
            rate = processed_count / elapsed if elapsed > 0 else 0
            logger.info(
                "Processed %d/%d chunks (%d cached, %d new) — %.1f chunks/s",
                cached_count + processed_count,
                total,
                cached_count,
                processed_count,
                rate,
            )

            # Save cache after each batch (crash resilience)
            _save_cache(cache)

    # 4. Prepend context to each chunk's text
    for idx, (chunk, h) in enumerate(zip(chunks, chunk_hashes)):
        context = cache.get(h, "")
        original_text = chunk.get("text", "")

        # Avoid double-prepending if already enriched
        if original_text.startswith("[CONTEXTO]"):
            continue

        if context:
            chunk["text"] = f"[CONTEXTO] {context}\n\n[CONTEÚDO] {original_text}"
        else:
            chunk["text"] = f"[CONTEÚDO] {original_text}"

    # 5. Final save of cache
    _save_cache(cache)

    # 6. Log stats
    newly_processed = len(to_process)
    logger.info(
        "Enrichment complete: %d total, %d cached, %d newly processed, %d failed",
        total,
        cached_count,
        newly_processed,
        failed_count,
    )

    return chunks


# ---------------------------------------------------------------------------
# Standalone execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    parser = argparse.ArgumentParser(
        description="Contextual Retrieval enrichment for MAC RAG Ecocardiografia"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        default=True,
        help="Resume from cache, skipping already-processed chunks (default behavior)",
    )
    parser.add_argument(
        "--test",
        type=int,
        default=0,
        metavar="N",
        help="Only process the first N chunks (for testing)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Ignore existing cache and re-process all chunks",
    )
    parser.add_argument(
        "--ollama",
        action="store_true",
        help=f"Use Ollama ({OLLAMA_MODEL}) instead of OpenAI — free, runs on local GPU",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).parent
    input_path = base_dir / "chunks_all.json"
    output_path = base_dir / "chunks_all_enriched.json"

    if not input_path.exists():
        logger.error("Input file not found: %s", input_path)
        sys.exit(1)

    logger.info("Reading %s ...", input_path)
    with open(input_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    logger.info("Loaded %d chunks", len(chunks))

    if args.test > 0:
        chunks = chunks[: args.test]
        logger.info("Test mode: using first %d chunks only", args.test)

    use_cache = not args.no_cache
    if args.no_cache:
        logger.info("Cache disabled: all chunks will be re-processed")

    enriched = enrich_chunks(chunks, use_cache=use_cache, use_ollama=args.ollama)

    logger.info("Writing %s ...", output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)
    logger.info("Done. Output: %s (%d chunks)", output_path, len(enriched))
