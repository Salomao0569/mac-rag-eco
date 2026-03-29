"""Tavily — busca na internet para informações regulatórias e notícias."""

import logging
import os
import requests
from agno.tools import tool
from ..registry import register_tool


@register_tool("tavily", "all")
@tool
def tavily_search(query: str, max_results: int = 5) -> str:
    """Busca na internet via Tavily: bulas, alertas ANVISA/FDA, notícias recentes.
    Use apenas como último recurso ou para informações regulatórias ao vivo.

    Args:
        query (str): Termo de busca.
        max_results (int): Máximo de resultados (padrão 5).
    """
    api_key = os.environ.get("TAVILY_API_KEY", "")
    if not api_key:
        return "ERRO: Tavily — TAVILY_API_KEY não configurada."
    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=api_key)
        results = client.search(
            query=query, search_depth="advanced", max_results=max_results
        )
        output = []
        for r in results.get("results", []):
            output.append(
                f"[{r.get('title')}]\n"
                f"{r.get('content', '')[:500]}\n"
                f"Fonte: {r.get('url')}"
            )
        return "\n\n".join(output) if output else "Tavily: sem resultado para esta query."
    except (requests.RequestException, KeyError) as e:
        return f"ERRO: Tavily — {e}"
    except Exception as e:
        logging.getLogger(__name__).exception("Unexpected error in tavily_search")
        return f"ERRO: Tavily — erro inesperado: {type(e).__name__}"
