"""
Parser dedicado para diretrizes DIC-SBC (PDFs em português).
Gera chunks e adiciona ao chunks_all_enriched.json existente.

Uso:
    python parse_dic_sbc.py                    # Parse only
    python parse_dic_sbc.py --enrich           # Parse + enrich via GPT-4o-mini
    python parse_dic_sbc.py --enrich --index   # Parse + enrich + re-index ChromaDB
"""

import argparse
import json
import logging
import os
import re
import sys

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIC_PDF_DIR = os.path.join(BASE_DIR, 'guidelines_dic_sbc')
MAX_CHUNK_SIZE = 1500

# === Metadados das diretrizes DIC-SBC ===
DIC_GUIDELINES = {
    '01_Indicacoes_Eco_Adultos_2019.pdf': {
        'title': 'Posicionamento sobre Indicações da Ecocardiografia em Adultos – 2019',
        'society': 'DIC-SBC',
        'topic': 'Indicações de Ecocardiografia em Adultos',
        'year': '2019',
        'doi': '10.5935/abc.20190029',
    },
    '02_Eco_Fetal_Pediatrica_CC_2020.pdf': {
        'title': 'Posicionamento sobre Indicações da Ecocardiografia em Cardiologia Fetal, Pediátrica e Cardiopatias Congênitas do Adulto – 2020',
        'society': 'DIC-SBC',
        'topic': 'Ecocardiografia Fetal Pediátrica e Congênitas',
        'year': '2020',
        'doi': '10.36660/abc.20200266',
    },
    '03_Strain_Miocardico_2023.pdf': {
        'title': 'Posicionamento sobre o Uso do Strain Miocárdico na Rotina do Cardiologista – DIC/SBC 2023',
        'society': 'DIC-SBC',
        'topic': 'Strain Miocárdico',
        'year': '2023',
        'doi': '10.36660/abc.20230646',
    },
    '04_US_Vascular_2019.pdf': {
        'title': 'Posicionamento de Ultrassonografia Vascular do DIC/SBC – 2019',
        'society': 'DIC-SBC',
        'topic': 'Ultrassonografia Vascular',
        'year': '2019',
        'doi': '10.5935/abc.20190095',
    },
    '05_US_Carotidas_Vertebrais_2023.pdf': {
        'title': 'Atualização de Recomendações para Avaliação por US Vascular de Doença Carotídea e Vertebral – DIC/CBR/SABCV 2023',
        'society': 'DIC-SBC',
        'topic': 'Ultrassonografia Carotídeas e Vertebrais',
        'year': '2023',
        'doi': '10.36660/abc.20230695',
    },
    '06_Cardio_Oncologia_2021.pdf': {
        'title': 'Posicionamento Brasileiro sobre o Uso da Multimodalidade de Imagens na Cardio-Oncologia – DIC/SBC 2021',
        'society': 'DIC-SBC',
        'topic': 'Cardio-Oncologia Multimodalidade',
        'year': '2021',
        'doi': '10.36660/abc.20210006',
    },
    '07_COVID19_Imagem_2021.pdf': {
        'title': 'Posicionamento sobre Indicações e Reintrodução dos Métodos de Imagem CV no Cenário da COVID-19 – DIC/SBC 2021',
        'society': 'DIC-SBC',
        'topic': 'COVID-19 e Imagem Cardiovascular',
        'year': '2021',
        'doi': '10.36660/abc.20200266',
    },
    '08_Cardiologia_Nuclear_2020.pdf': {
        'title': 'Atualização da Diretriz Brasileira de Cardiologia Nuclear – 2020',
        'society': 'DIC-SBC',
        'topic': 'Cardiologia Nuclear',
        'year': '2020',
        'doi': '10.36660/abc.20200087',
    },
    '09_ESC_ACHD_2020.pdf': {
        'title': '2020 ESC Guidelines for the Management of Adult Congenital Heart Disease',
        'society': 'ESC',
        'topic': 'Cardiopatias Congênitas do Adulto',
        'year': '2020',
        'doi': '10.1093/eurheartj/ehaa554',
    },
    '10_AHA_ACC_ACHD_2018_full.txt': {
        'title': '2018 AHA/ACC Guideline for the Management of Adults With Congenital Heart Disease',
        'society': 'AHA/ACC',
        'topic': 'Cardiopatias Congênitas do Adulto',
        'year': '2018',
        'doi': '10.1161/CIR.0000000000000603',
    },
}

# === Heading detection ===
_HEADING_RE = re.compile(
    r'^(\d+\.?\s+[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ]|[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇ\s]{5,})',
    re.UNICODE
)


def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()


def split_text(text, max_size=MAX_CHUNK_SIZE):
    parts = text.split('\n\n')
    if len(parts) <= 1:
        parts = re.split(r'(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚ])', text)

    chunks = []
    current = []
    current_len = 0

    for p in parts:
        if current_len + len(p) > max_size and current:
            chunks.append(' '.join(current))
            current = [p]
            current_len = len(p)
        else:
            current.append(p)
            current_len += len(p)

    if current:
        chunks.append(' '.join(current))

    final = []
    for chunk in chunks:
        while len(chunk) > max_size * 2:
            cut = chunk[:max_size].rfind(' ')
            if cut < max_size // 2:
                cut = max_size
            final.append(chunk[:cut])
            chunk = chunk[cut:].strip()
        final.append(chunk)

    return [c for c in final if len(c.strip()) > 50]


def is_non_clinical(text):
    skip = (
        'references', 'referências', 'agradecimentos', 'acknowledgement',
        'disclosure', 'conflito de interesse', 'conflict of interest',
        'contribuição dos autores', 'author contribution', 'fontes de financiamento',
        'funding', 'data availability', 'suplementar',
    )
    lower = text.lower()
    return any(m in lower for m in skip)


def is_skip_page(text):
    lower = text.lower()
    skip_patterns = [
        'all rights reserved', 'todos os direitos reservados',
        'this is an open access', 'creative commons',
    ]
    if any(p in lower for p in skip_patterns) and len(text) < 500:
        return True
    return False


def clean_page(text):
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if len(stripped) < 10:
            continue
        if re.match(r'^\d+\s*$', stripped):
            continue
        if re.match(r'^Arq\.?\s*Bras\.?\s*Cardiol', stripped, re.IGNORECASE):
            continue
        if re.match(r'^(www\.|http)', stripped, re.IGNORECASE):
            continue
        if re.match(r'^(European Heart Journal|Circulation|JACC|Downloaded from)', stripped, re.IGNORECASE):
            continue
        cleaned.append(stripped)
    return '\n'.join(cleaned)


def parse_single_txt(txt_path, meta):
    """Parse a plain text or JSON/markdown guideline file (.txt)."""
    idioma = 'pt' if meta['society'] == 'DIC-SBC' else 'en'
    base_metadata = {
        'diretriz': meta['title'],
        'sociedade': meta['society'],
        'topico': meta['topic'],
        'ano': meta['year'],
        'doi': meta['doi'],
        'idioma': idioma,
    }

    with open(txt_path, 'r', encoding='utf-8') as f:
        raw = f.read()

    # Check if file is JSON with markdown field (e.g., from web scraper)
    if raw.strip().startswith('{'):
        try:
            data = json.loads(raw)
            content = data.get('markdown', raw)
        except json.JSONDecodeError:
            content = raw
    else:
        content = raw

    chunks = []
    current_section = 'Introduction'
    current_text = []

    # Split by lines and detect headings
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue

        # Skip non-clinical sections
        if is_non_clinical(line):
            continue

        # Detect headings: numbered sections or ALL CAPS lines
        heading_match = _HEADING_RE.match(line)
        is_heading = heading_match and len(line) < 200

        if is_heading:
            # Flush previous section
            if current_text:
                section_content = clean_text(' '.join(current_text))
                if not is_non_clinical(current_section) and len(section_content) > 50:
                    if len(section_content) > MAX_CHUNK_SIZE:
                        for j, sc in enumerate(split_text(section_content)):
                            chunks.append({
                                'text': sc,
                                'metadata': {**base_metadata, 'secao': current_section, 'hierarquia': current_section, 'tipo': 'texto', 'parte': j + 1}
                            })
                    else:
                        chunks.append({
                            'text': section_content,
                            'metadata': {**base_metadata, 'secao': current_section, 'hierarquia': current_section, 'tipo': 'texto', 'parte': 0}
                        })
                current_text = []
            current_section = line
        else:
            current_text.append(line)

    # Flush last section
    if current_text:
        section_content = clean_text(' '.join(current_text))
        if not is_non_clinical(current_section) and len(section_content) > 50:
            if len(section_content) > MAX_CHUNK_SIZE:
                for j, sc in enumerate(split_text(section_content)):
                    chunks.append({
                        'text': sc,
                        'metadata': {**base_metadata, 'secao': current_section, 'hierarquia': current_section, 'tipo': 'texto', 'parte': j + 1}
                    })
            else:
                chunks.append({
                    'text': section_content,
                    'metadata': {**base_metadata, 'secao': current_section, 'hierarquia': current_section, 'tipo': 'texto', 'parte': 0}
                })

    return chunks


def parse_single_pdf(pdf_path, meta):
    import fitz

    idioma = 'pt' if meta['society'] == 'DIC-SBC' else 'en'
    base_metadata = {
        'diretriz': meta['title'],
        'sociedade': meta['society'],
        'topico': meta['topic'],
        'ano': meta['year'],
        'doi': meta['doi'],
        'idioma': idioma,
    }

    doc = fitz.open(pdf_path)
    chunks = []
    current_section = 'Introdução'
    current_text = []

    for page in doc:
        page_text = page.get_text()
        if not page_text or len(page_text.strip()) < 50:
            continue
        if is_skip_page(page_text):
            continue

        page_text = clean_page(page_text)

        for line in page_text.split('\n'):
            line = line.strip()
            if not line:
                continue

            heading_match = _HEADING_RE.match(line)
            if heading_match and len(line) < 200:
                if current_text:
                    section_content = ' '.join(current_text)
                    if not is_non_clinical(current_section):
                        text = clean_text(section_content)
                        if len(text) > 50:
                            if len(text) > MAX_CHUNK_SIZE:
                                for j, sc in enumerate(split_text(text)):
                                    chunks.append({
                                        'text': sc,
                                        'metadata': {**base_metadata, 'secao': current_section, 'hierarquia': current_section, 'tipo': 'texto', 'parte': j + 1}
                                    })
                            else:
                                chunks.append({
                                    'text': text,
                                    'metadata': {**base_metadata, 'secao': current_section, 'hierarquia': current_section, 'tipo': 'texto', 'parte': 0}
                                })
                    current_text = []
                current_section = line
            else:
                current_text.append(line)

    # Flush last
    if current_text:
        section_content = clean_text(' '.join(current_text))
        if not is_non_clinical(current_section) and len(section_content) > 50:
            if len(section_content) > MAX_CHUNK_SIZE:
                for j, sc in enumerate(split_text(section_content)):
                    chunks.append({
                        'text': sc,
                        'metadata': {**base_metadata, 'secao': current_section, 'hierarquia': current_section, 'tipo': 'texto', 'parte': j + 1}
                    })
            else:
                chunks.append({
                    'text': section_content,
                    'metadata': {**base_metadata, 'secao': current_section, 'hierarquia': current_section, 'tipo': 'texto', 'parte': 0}
                })

    doc.close()
    return chunks


def parse_all():
    all_chunks = []
    for filename, meta in DIC_GUIDELINES.items():
        filepath = os.path.join(DIC_PDF_DIR, filename)
        if not os.path.exists(filepath):
            logger.warning(f'  Arquivo não encontrado: {filepath}')
            continue

        logger.info(f'Parseando {filename} ({meta["society"]} {meta["year"]})...')

        # Choose parser based on file extension
        if filename.endswith('.txt'):
            chunks = parse_single_txt(filepath, meta)
        else:
            chunks = parse_single_pdf(filepath, meta)

        logger.info(f'  -> {len(chunks)} chunks')
        all_chunks.extend(chunks)

    logger.info(f'Total DIC-SBC: {len(all_chunks)} chunks')
    return all_chunks


def main():
    parser = argparse.ArgumentParser(description='Parse DIC-SBC guidelines')
    parser.add_argument('--enrich', action='store_true', help='Enrich chunks with GPT-4o-mini')
    parser.add_argument('--index', action='store_true', help='Re-index ChromaDB after enrichment')
    args = parser.parse_args()

    # 1. Parse
    dic_chunks = parse_all()

    # Save standalone
    dic_output = os.path.join(BASE_DIR, 'chunks_dic_sbc.json')
    with open(dic_output, 'w', encoding='utf-8') as f:
        json.dump(dic_chunks, f, ensure_ascii=False, indent=2)
    logger.info(f'Salvos em {dic_output}')

    # 2. Merge with existing enriched chunks
    enriched_path = os.path.join(BASE_DIR, 'chunks_all_enriched.json')
    if os.path.exists(enriched_path):
        with open(enriched_path, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        logger.info(f'Chunks existentes: {len(existing)}')
    else:
        existing = []

    # Remove old DIC-SBC/ESC/AHA chunks from this parser (if re-running)
    dic_titles = {meta['title'] for meta in DIC_GUIDELINES.values()}
    existing = [c for c in existing if c.get('metadata', {}).get('diretriz') not in dic_titles]
    logger.info(f'Após remover chunks antigos deste parser: {len(existing)}')

    # 3. Enrich if requested
    if args.enrich:
        logger.info('Enriquecendo chunks DIC-SBC com GPT-4o-mini...')
        from enrich import enrich_chunks
        dic_chunks = enrich_chunks(dic_chunks)
        logger.info(f'Após enrichment: {len(dic_chunks)} chunks')

    # 4. Merge and save
    combined = existing + dic_chunks
    with open(enriched_path, 'w', encoding='utf-8') as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)
    logger.info(f'Combinados salvos: {len(combined)} chunks em {enriched_path}')

    # 5. Re-index if requested
    if args.index:
        logger.info('Re-indexando ChromaDB...')
        from index import create_index
        create_index(enriched_path, 'diretrizes_eco', skip_enrich=True)

    logger.info('Concluído!')


if __name__ == '__main__':
    main()
