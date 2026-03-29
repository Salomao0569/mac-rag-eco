"""
Standardize metadata schema across SBC and international chunks.

Adds missing fields to SBC chunks (sociedade, topico, idioma)
and missing fields to international chunks (arquivo).
Then regenerates chunks_all.json.
"""

import json
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
CHUNKS_SBC = BASE_DIR / "chunks.json"
CHUNKS_INTL = BASE_DIR / "chunks_international.json"
CHUNKS_ALL = BASE_DIR / "chunks_all.json"

TOPIC_MAP = {
    "Hipertensão Arterial": "Hipertensão Arterial",
    "Angina Instável": "Síndromes Coronarianas Agudas",
    "Infarto Agudo": "Síndromes Coronarianas Agudas",
    "Fibrilação Atrial": "Fibrilação Atrial",
    "Dislipidemias": "Dislipidemias",
    "Tromboembolismo Venoso": "Tromboembolismo Venoso",
    "Miocardites": "Miocardite e Pericardite",
    "Eletrocardiográficos": "Eletrocardiograma",
    "Chagas": "Doença de Chagas",
    "Dispositivos Cardíacos": "Dispositivos Cardíacos",
    "Ergometria": "Ergometria",
    "Tomografia": "Imagem Cardiovascular",
    "Ressonância": "Imagem Cardiovascular",
    "Perioperatória": "Avaliação Perioperatória",
    "Cardiomiopatia Hipertrófica": "Cardiomiopatia Hipertrófica",
    "Climatério": "Saúde Cardiovascular da Mulher",
    "Menopausa": "Saúde Cardiovascular da Mulher",
    "Saúde da Mulher": "Saúde Cardiovascular da Mulher",
    "Saúde Cardiometabólica": "Saúde Cardiovascular da Mulher",
    "Pressão Arterial": "Medidas de Pressão Arterial",
    "Dor Torácica": "Dor Torácica na Emergência",
    "Obesidade": "Obesidade e Prevenção CV",
    "Síndrome Coronariana Crônica": "Síndrome Coronariana Crônica",
    "Coronariana Crônica": "Síndrome Coronariana Crônica",
}


def infer_topic(diretriz: str) -> str:
    """Infer topic from diretriz title using TOPIC_MAP."""
    for key, topic in TOPIC_MAP.items():
        if key in diretriz:
            return topic
    return ""


def standardize_sbc(chunks: list[dict]) -> dict:
    """Add sociedade, topico, idioma to SBC chunks. Returns stats."""
    topic_counts: dict[str, int] = {}
    unmatched = 0

    for chunk in chunks:
        meta = chunk["metadata"]
        meta["sociedade"] = "SBC"
        meta["idioma"] = "pt"

        topico = infer_topic(meta.get("diretriz", ""))
        meta["topico"] = topico

        if topico:
            topic_counts[topico] = topic_counts.get(topico, 0) + 1
        else:
            unmatched += 1

    return {"topic_counts": topic_counts, "unmatched": unmatched}


def standardize_international(chunks: list[dict]) -> int:
    """Add arquivo field to international chunks if missing. Returns count of added."""
    added = 0
    for chunk in chunks:
        meta = chunk["metadata"]
        if "arquivo" not in meta:
            meta["arquivo"] = ""
            added += 1
    return added


def main():
    # --- SBC chunks ---
    logger.info("Reading %s", CHUNKS_SBC)
    with open(CHUNKS_SBC, "r", encoding="utf-8") as f:
        sbc_chunks = json.load(f)
    logger.info("Loaded %d SBC chunks", len(sbc_chunks))

    stats = standardize_sbc(sbc_chunks)
    logger.info("SBC topic inference results:")
    for topic, count in sorted(stats["topic_counts"].items()):
        logger.info("  %s: %d chunks", topic, count)
    if stats["unmatched"]:
        logger.warning("  Unmatched (no topic): %d chunks", stats["unmatched"])

    with open(CHUNKS_SBC, "w", encoding="utf-8") as f:
        json.dump(sbc_chunks, f, ensure_ascii=False, indent=2)
    logger.info("Wrote standardized %s", CHUNKS_SBC)

    # --- International chunks ---
    logger.info("Reading %s", CHUNKS_INTL)
    with open(CHUNKS_INTL, "r", encoding="utf-8") as f:
        intl_chunks = json.load(f)
    logger.info("Loaded %d international chunks", len(intl_chunks))

    added = standardize_international(intl_chunks)
    if added:
        logger.info("Added 'arquivo' field to %d international chunks", added)
        with open(CHUNKS_INTL, "w", encoding="utf-8") as f:
            json.dump(intl_chunks, f, ensure_ascii=False, indent=2)
        logger.info("Wrote updated %s", CHUNKS_INTL)
    else:
        logger.info("All international chunks already have 'arquivo' field")

    # --- Combine into chunks_all.json ---
    all_chunks = sbc_chunks + intl_chunks
    with open(CHUNKS_ALL, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    logger.info(
        "Wrote %s with %d total chunks (%d SBC + %d international)",
        CHUNKS_ALL,
        len(all_chunks),
        len(sbc_chunks),
        len(intl_chunks),
    )

    # --- Final metadata key check ---
    sbc_keys = set()
    for c in sbc_chunks:
        sbc_keys.update(c["metadata"].keys())
    intl_keys = set()
    for c in intl_chunks:
        intl_keys.update(c["metadata"].keys())
    logger.info("SBC metadata keys: %s", sorted(sbc_keys))
    logger.info("International metadata keys: %s", sorted(intl_keys))
    if sbc_keys == intl_keys:
        logger.info("Metadata schemas are now aligned!")
    else:
        logger.warning("Key diff — SBC only: %s | Intl only: %s", sbc_keys - intl_keys, intl_keys - sbc_keys)


if __name__ == "__main__":
    main()
