"""RAG — busca semântica nas diretrizes de cardiologia via ChromaDB."""

import logging
from agno.tools import tool
from ..config import get_collection
from ..registry import register_tool
from .hybrid_search import bm25_search, reciprocal_rank_fusion
from .reranker import rerank

# Similarity threshold: cosine distance > this means low relevance
_MAX_DISTANCE = 0.50  # similarity < 0.50 → discard


@register_tool("rag", "all")
@tool
def rag_search(query: str, ano: str = "", sociedade: str = "", diretriz: str = "", n_resultados: int = 15) -> str:
    """Consulta diretrizes de cardiologia indexadas localmente.
    Fontes: SBC (20), ESC (19), AHA (5). Total: 44 diretrizes, ~29.000 chunks.
    Retorna trechos relevantes com metadados de fonte.

    Args:
        query (str): Pergunta ou tema a buscar.
        ano (str): Filtrar por ano (ex: '2024'). Vazio = todos.
        sociedade (str): Filtrar por sociedade (ex: 'SBC', 'ESC', 'ESC/EACTS', 'AHA/ACC'). Vazio = todas.
        diretriz (str): Filtrar por nome parcial da diretriz (ex: 'valvular heart disease'). Vazio = todas.
        n_resultados (int): Trechos a retornar (padrão 8).
    """
    try:
        collection = get_collection()
        filters = []
        if ano:
            filters.append({"ano": ano})
        if sociedade:
            filters.append({"sociedade": sociedade})

        where = None
        if len(filters) == 1:
            where = filters[0]
        elif len(filters) > 1:
            where = {"$and": filters}

        # --- Hybrid Search: Semantic + BM25 + RRF ---
        fetch_n = 20  # fetch more for fusion headroom

        # 1. Semantic search (ChromaDB)
        results = collection.query(
            query_texts=[f"query: {query}"],
            n_results=fetch_n,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        semantic_results = list(zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ))

        # 2. BM25 keyword search
        try:
            bm25_results = bm25_search(query, n_results=fetch_n)
        except Exception as exc:
            logging.getLogger(__name__).warning("BM25 search failed: %s — using semantic only", exc)
            bm25_results = []

        # 3. RRF fusion
        if bm25_results:
            fused = reciprocal_rank_fusion(semantic_results, bm25_results, n_results=fetch_n)
            docs = [r[0] for r in fused]
            metas = [r[1] for r in fused]
            dists = [r[2] for r in fused]
        else:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            dists = results["distances"][0]

        # --- Recency boost: ensure recent guidelines are represented ---
        # If results are dominated by older guidelines, inject recent ones
        if not ano:  # only when no year filter is explicitly set
            years = [m.get('ano', '') for m in metas]
            max_year = max((y for y in years if y.isdigit()), default='')
            if max_year:
                recent_count = sum(1 for y in years[:n_resultados] if y == max_year)
                if recent_count < 3:
                    # Fetch top-5 from the most recent year
                    try:
                        recent_results = collection.query(
                            query_texts=[f"query: {query}"],
                            n_results=5,
                            where={"ano": max_year},
                            include=["documents", "metadatas", "distances"],
                        )
                        for rd, rm, rdist in zip(
                            recent_results["documents"][0],
                            recent_results["metadatas"][0],
                            recent_results["distances"][0],
                        ):
                            if rd[:200] not in {d[:200] for d in docs}:
                                docs.append(rd)
                                metas.append(rm)
                                dists.append(rdist)
                    except Exception:
                        pass  # graceful degradation

        # Filtrar por nome de diretriz (substring match) se solicitado
        if diretriz:
            diretriz_lower = diretriz.lower()
            filtered = [(d, m, dist) for d, m, dist in zip(docs, metas, dists)
                        if diretriz_lower in m.get('diretriz', '').lower()]
            if filtered:
                docs, metas, dists = zip(*filtered)
                docs, metas, dists = list(docs), list(metas), list(dists)
            else:
                return f"RAG: diretriz '{diretriz}' não encontrada no índice."

        # Similarity threshold — discard low-relevance chunks (pre-reranking filter)
        qualified = [(d, m, dist) for d, m, dist in zip(docs, metas, dists)
                     if dist <= _MAX_DISTANCE]
        if not qualified:
            best_score = 1 - min(dists) if dists else 0
            return (
                f"RAG: evidência insuficiente para esta query. "
                f"Similaridade máxima: {best_score:.2f} (threshold: {1 - _MAX_DISTANCE:.2f})."
            )

        # --- Cross-encoder reranking ---
        try:
            reranked = rerank(query, qualified, top_n=n_resultados)
            docs = [r[0] for r in reranked]
            metas = [r[1] for r in reranked]
            dists = [r[2] for r in reranked]  # now reranker scores (higher = better)
            _reranked = True
        except Exception as exc:
            logging.getLogger(__name__).warning("Reranker failed: %s — using RRF order", exc)
            docs, metas, dists = zip(*qualified)
            _reranked = False

        # Deduplication by first 200 chars of chunk text
        seen = set()
        deduped = []
        for d, m, dist in zip(docs, metas, dists):
            key = d[:200]
            if key not in seen:
                seen.add(key)
                deduped.append((d, m, dist))
        # Truncate to requested count
        deduped = deduped[:n_resultados]

        output = []
        for i, (doc, meta, dist) in enumerate(deduped):
            text = doc.replace("passage: ", "", 1)
            soc = meta.get('sociedade', 'SBC')
            idioma = meta.get('idioma', 'pt')
            topico = meta.get('topico', '')
            topico_line = f"Tópico: {topico}\n" if topico else ""
            if _reranked:
                score_label = f"Relevância: {dist:.2f}"
            else:
                score_label = f"Similaridade: {1-dist:.2f}"
            output.append(
                f"[Trecho {i+1}] {score_label} | {soc} | {idioma}\n"
                f"Diretriz: {meta.get('diretriz', '')} ({meta.get('ano', '')})\n"
                f"{topico_line}"
                f"Seção: {meta.get('secao', '')}\n"
                f"Hierarquia: {meta.get('hierarquia', '')} | Tipo: {meta.get('tipo', '')}\n"
                f"---\n{text}"
            )
        return "\n\n".join(output) if output else "RAG: sem resultado para esta query."
    except (ValueError, RuntimeError) as e:
        return f"ERRO: RAG — {e}"
    except Exception as e:
        logging.getLogger(__name__).exception("Unexpected error in rag_search")
        return f"ERRO: RAG — erro inesperado: {type(e).__name__}: {e}"
