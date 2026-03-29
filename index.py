"""
Módulo 2: Indexação dos chunks no ChromaDB com embeddings locais.
Suporta chunks SBC e internacionais (chunks_all.json ou chunks.json).
"""

import argparse
import json
import logging
import os
from itertools import groupby

import chromadb
from enrich import enrich_chunks
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EMBEDDING_MODEL = 'intfloat/multilingual-e5-base'

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

OVERLAP_RATIO = 0.15  # 15% overlap


def create_overlap_chunks(chunks):
    """Create additional overlap chunks for boundary context.

    For each pair of consecutive chunks within the same guideline+section,
    generates an overlap chunk containing the last ~15% of chunk N and the
    first ~15% of chunk N+1. This recovers context lost at chunk boundaries.
    """
    overlap_chunks = []

    # Sort by guideline + section + part
    sorted_chunks = sorted(chunks, key=lambda c: (
        c['metadata'].get('diretriz', ''),
        c['metadata'].get('secao', ''),
        str(c['metadata'].get('parte', 0)),
    ))

    for _key, group in groupby(sorted_chunks, key=lambda c: (
        c['metadata'].get('diretriz', ''),
        c['metadata'].get('secao', ''),
    )):
        section_chunks = list(group)
        if len(section_chunks) < 2:
            continue

        for i in range(len(section_chunks) - 1):
            text_a = section_chunks[i]['text']
            text_b = section_chunks[i + 1]['text']

            # Take last 15% of A + first 15% of B
            overlap_start = max(0, len(text_a) - int(len(text_a) * OVERLAP_RATIO))
            overlap_end = int(len(text_b) * OVERLAP_RATIO)

            # Find word boundary (search within +-50 chars of target position)
            start_pos = text_a.rfind(' ', max(0, overlap_start - 50), min(len(text_a), overlap_start + 50))
            if start_pos < 0:
                start_pos = overlap_start
            end_pos = text_b.find(' ', max(0, overlap_end - 50), min(len(text_b), overlap_end + 50))
            if end_pos < 0:
                end_pos = overlap_end

            overlap_text = text_a[start_pos:].strip() + ' ' + text_b[:end_pos].strip()

            if len(overlap_text) > 100:  # Only add if meaningful
                overlap_chunks.append({
                    'text': overlap_text,
                    'metadata': {
                        **section_chunks[i]['metadata'],
                        'tipo': 'overlap',
                        'parte': f"{section_chunks[i]['metadata'].get('parte', 0)}-{section_chunks[i + 1]['metadata'].get('parte', 0)}",
                    }
                })

    return overlap_chunks


def _default_chunks_file():
    """Retorna chunks_all.json se existir, senão chunks.json."""
    all_path = os.path.join(BASE_DIR, 'chunks_all.json')
    if os.path.exists(all_path):
        return all_path
    return os.path.join(BASE_DIR, 'chunks.json')


def create_index(chunks_file: str, collection_name: str, skip_enrich: bool = False):
    # Use a local tmp path for indexing, then copy to project dir
    db_path = os.environ.get('CHROMA_DB_PATH', os.path.join(BASE_DIR, 'chroma_db'))

    with open(chunks_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    logger.info('Carregados %d chunks de %s', len(chunks), os.path.basename(chunks_file))

    # Enriquecer metadados (pular se chunks já enriquecidos)
    if skip_enrich:
        logger.info('Enrichment pulado (--skip-enrich)')
    else:
        chunks = enrich_chunks(chunks)
        logger.info('Após enrichment: %d chunks (inclui compostos)', len(chunks))

    # Gerar chunks de overlap para contexto nas fronteiras
    overlap = create_overlap_chunks(chunks)
    logger.info('Criados %d chunks de overlap (%.0f%% ratio)', len(overlap), OVERLAP_RATIO * 100)
    chunks.extend(overlap)
    logger.info('Total após overlap: %d chunks', len(chunks))

    # Estatísticas por sociedade
    societies: dict[str, int] = {}
    for c in chunks:
        s = c['metadata'].get('sociedade', 'SBC')
        societies[s] = societies.get(s, 0) + 1
    for s, count in sorted(societies.items()):
        logger.info('  %s: %d chunks', s, count)

    client = chromadb.PersistentClient(path=db_path)

    # Use env override or auto-detect (cuda/mps/cpu)
    from core.config import DEVICE
    index_device = os.environ.get('INDEX_DEVICE', DEVICE)
    embed_fn = SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL,
        device=index_device,
        trust_remote_code=True,
    )

    # Deletar coleção existente se houver
    try:
        client.delete_collection(collection_name)
        logger.info('Coleção anterior removida.')
    except Exception:
        pass

    collection = client.create_collection(
        name=collection_name,
        embedding_function=embed_fn,
        metadata={'hnsw:space': 'cosine'},
    )

    # Indexar em lotes de 100
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        ids = [f'chunk_{i + j}' for j in range(len(batch))]

        # Preparar textos com prefixo para e5 (melhora qualidade)
        documents = [f"passage: {c['text']}" for c in batch]

        # Metadados (ChromaDB aceita apenas str, int, float, bool)
        metadatas = []
        for c in batch:
            m = c['metadata']
            metadatas.append({
                'diretriz': str(m.get('diretriz', '')),
                'sociedade': str(m.get('sociedade', 'SBC')),
                'topico': str(m.get('topico', '')),
                'ano': str(m.get('ano', '')),
                'doi': str(m.get('doi', '')),
                'secao': str(m.get('secao', '')),
                'hierarquia': str(m.get('hierarquia', '')),
                'tipo': str(m.get('tipo', '')),
                'idioma': str(m.get('idioma', 'pt')),
            })

        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

        logger.info('  Indexados %d/%d', min(i + batch_size, len(chunks)), len(chunks))

    logger.info('Indexação completa! %d documentos no ChromaDB', collection.count())
    logger.info('DB salvo em: %s', db_path)

    # Invalidate query cache after re-indexing
    try:
        import cache
        cache.invalidate_all()
    except ImportError:
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Indexa chunks no ChromaDB')
    parser.add_argument('--file', default=None, help='Caminho do arquivo de chunks JSON')
    parser.add_argument('--collection', default='diretrizes_eco', help='Nome da coleção (default: diretrizes_eco)')
    parser.add_argument('--skip-enrich', action='store_true', help='Pular enrichment (usar quando chunks já estão enriquecidos)')
    args = parser.parse_args()

    chunks_file = args.file or _default_chunks_file()
    create_index(chunks_file, args.collection, skip_enrich=args.skip_enrich)
