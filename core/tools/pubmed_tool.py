"""PubMed — busca de abstracts via Biopython Entrez."""

import logging
import os
import ssl
import urllib.error
from agno.tools import tool
from ..registry import register_tool


def _get_ssl_context():
    """Cria contexto SSL que funciona mesmo com certificados intermediários."""
    import certifi
    return ssl.create_default_context(cafile=certifi.where())


@register_tool("pubmed", "all")
@tool
def pubmed_search(query: str, max_results: int = 5) -> str:
    """Busca no PubMed: ensaios clínicos, meta-análises, revisões.
    IMPORTANTE: envie query em inglês para melhores resultados.
    Retorna abstracts com PMID para rastreabilidade.

    Args:
        query (str): Termo de busca.
        max_results (int): Máximo de artigos (padrão 5).
    """
    try:
        from Bio import Entrez
        from urllib.request import install_opener, build_opener, HTTPSHandler

        # Fix SSL: usa certificados do certifi
        ctx = _get_ssl_context()
        opener = build_opener(HTTPSHandler(context=ctx))
        install_opener(opener)

        Entrez.email = os.getenv("ENTREZ_EMAIL", "contato@biocardio.com.br")
        handle = Entrez.esearch(
            db="pubmed", term=query, retmax=max_results, sort="relevance"
        )
        record = Entrez.read(handle)
        ids = record.get("IdList", [])
        if not ids:
            return "PubMed: sem resultado para esta query."
        handle = Entrez.efetch(
            db="pubmed", id=ids, rettype="abstract", retmode="text"
        )
        abstracts = handle.read()
        return abstracts[:4000] if abstracts else "PubMed: sem abstracts disponíveis."
    except (urllib.error.URLError, IOError) as e:
        return f"ERRO: PubMed — conexão falhou: {e}"
    except Exception as e:
        logging.getLogger(__name__).exception("Unexpected error in pubmed_search")
        return f"ERRO: PubMed — erro inesperado: {type(e).__name__}"
