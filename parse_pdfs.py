"""
Parser de PDFs para MAC RAG Ecocardiografia.
Extrai texto dos PDFs usando PyMuPDF, chunka por parágrafos/seções,
e gera chunks_all.json no formato esperado pelo enrich.py e index.py.

Uso:
    python parse_pdfs.py                    # Processa todos os PDFs
    python parse_pdfs.py --test 3           # Teste com 3 PDFs apenas
    python parse_pdfs.py --min-chunk 50     # Tamanho mínimo de chunk
    python parse_pdfs.py --max-chunk 1500   # Tamanho máximo de chunk
"""

import argparse
import json
import logging
import os
import re
from pathlib import Path

import fitz  # PyMuPDF

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
PDF_DIR = BASE_DIR / "guidelines_pdf"
OUTPUT_PATH = BASE_DIR / "chunks_all.json"

# Chunking parameters
MAX_CHUNK = 1500
MIN_CHUNK = 50
TABLE_MAX = 4000

# ─── Metadata extraction from filename ─────────────────────────────────────

def extract_metadata_from_filename(filename: str) -> dict:
    """Extract structured metadata from PDF filename.

    Expected format: NN_Title_Words_YYYY.pdf
    Examples:
        01_Strain_Echocardiography_2025.pdf
        07b_Cardiac_Chamber_Quantification_2015_PTBR.pdf
        41_ESC_2023_Endocarditis_Guidelines.pdf
    """
    base = filename.replace(".pdf", "")

    # Extract year
    year_match = re.search(r'(\d{4})', base)
    year = year_match.group(1) if year_match else ""

    # Extract number prefix
    num_match = re.match(r'^(\d+[a-z]?)_', base)
    num = num_match.group(1) if num_match else ""

    # Extract title (everything between number and year)
    title_part = base
    if num_match:
        title_part = base[num_match.end():]
    # Remove year from title
    title_part = re.sub(r'_?\d{4}_?', ' ', title_part)
    title_part = re.sub(r'_', ' ', title_part).strip()

    # Detect society
    society = "ASE"  # default
    if "ESC" in base.upper():
        society = "ESC"
    elif "AHA" in base.upper() or "ACC" in base.upper():
        society = "AHA/ACC"
    elif "BSE" in base.upper():
        society = "BSE"
    elif "PTBR" in base.upper() or "PT" in base.upper():
        society = "DIC-SBC"

    # Detect language
    idioma = "pt" if "PTBR" in base.upper() or "PT_BR" in base.upper() else "en"

    # Detect topic
    topic = _infer_topic(title_part)

    return {
        "diretriz": title_part,
        "sociedade": society,
        "topico": topic,
        "ano": year,
        "doi": "",
        "secao": "",
        "hierarquia": "",
        "tipo": "texto",
        "parte": "0",
        "idioma": idioma,
        "arquivo": filename,
    }


def _infer_topic(title: str) -> str:
    """Infer clinical topic from title."""
    title_lower = title.lower()

    topic_map = {
        "strain": "Strain / Deformação Miocárdica",
        "diastol": "Função Diastólica",
        "chamber quantif": "Quantificação de Câmaras",
        "right heart": "Coração Direito / Hipertensão Pulmonar",
        "pulmonary hypertension": "Coração Direito / Hipertensão Pulmonar",
        "valve stenosis": "Estenose Valvar",
        "aortic stenosis": "Estenose Aórtica",
        "valvular regurg": "Regurgitação Valvar",
        "prosthetic": "Prótese Valvar",
        "tee": "Ecocardiograma Transesofágico",
        "transesophageal": "Ecocardiograma Transesofágico",
        "tte": "Ecocardiograma Transtorácico",
        "transthoracic": "Ecocardiograma Transtorácico",
        "comprehensive tte": "Ecocardiograma Transtorácico",
        "stress echo": "Ecocardiograma de Estresse",
        "pocus": "Point-of-Care Ultrasound",
        "fetal": "Ecocardiografia Fetal",
        "pediatric": "Ecocardiografia Pediátrica",
        "congenital": "Cardiopatias Congênitas",
        "endocarditis": "Endocardite Infecciosa",
        "pericardi": "Doenças do Pericárdio",
        "aorta": "Doenças da Aorta",
        "thoracic aorta": "Doenças da Aorta Torácica",
        "cardiomyop": "Cardiomiopatias",
        "hcm": "Cardiomiopatia Hipertrófica",
        "hypertension": "Hipertensão Arterial",
        "covid": "COVID-19",
        "chagas": "Doença de Chagas",
        "cancer": "Cardio-Oncologia",
        "cardio-oncology": "Cardio-Oncologia",
        "lvad": "Dispositivos de Assistência Ventricular",
        "3d echo": "Ecocardiografia 3D",
        "doppler": "Doppler",
        "contrast": "Agentes de Contraste",
        "embolism": "Fonte Cardíaca de Embolia",
        "cannulation": "Canulação Vascular Guiada por Eco",
        "resynchronization": "Terapia de Ressincronização",
        "athlete": "Atletas",
        "rheumatic": "Doença Reumática",
        "standardiz": "Padronização de Laudo",
        "reporting": "Padronização de Laudo",
        "nomenclature": "Nomenclatura",
        "neonatal": "Neonatal",
        "coronary": "Síndromes Coronárias",
        "carotid": "Carótidas",
        "asd": "Comunicação Interatrial / FOP",
        "pfo": "Comunicação Interatrial / FOP",
        "tetralogy": "Tetralogia de Fallot",
        "tga": "Transposição das Grandes Artérias",
        "valvular heart disease": "Doença Valvar",
        "cardiac mechanic": "Mecânica Cardíaca",
        "interventional": "Ecocardiografia Intervencionista",
    }

    for key, topic in topic_map.items():
        if key in title_lower:
            return topic

    return title


# ─── PDF Extraction ─────────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_path: str) -> list[dict]:
    """Extract text from PDF, page by page."""
    pages = []
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            if text and len(text.strip()) > MIN_CHUNK:
                pages.append({
                    "page": page_num + 1,
                    "text": text.strip(),
                })
        doc.close()
    except Exception as e:
        logger.error("Error extracting %s: %s", pdf_path, e)
    return pages


# ─── Chunking ───────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Clean extracted PDF text."""
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove page headers/footers (common patterns)
    text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)  # Standalone page numbers
    text = re.sub(r'^Journal of the American.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^JACC.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^Circulation.*$', '', text, flags=re.MULTILINE)
    # Clean hyphenation
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
    return text.strip()


def chunk_text(text: str, max_size: int = MAX_CHUNK) -> list[str]:
    """Split text into chunks by paragraphs, respecting max size."""
    paragraphs = text.split('\n\n')
    chunks = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current) + len(para) + 2 <= max_size:
            current = current + "\n\n" + para if current else para
        else:
            if current and len(current) >= MIN_CHUNK:
                chunks.append(current)

            if len(para) > max_size:
                # Split long paragraph by sentences
                sentences = re.split(r'(?<=[.!?])\s+', para)
                current = ""
                for sent in sentences:
                    if len(current) + len(sent) + 1 <= max_size:
                        current = current + " " + sent if current else sent
                    else:
                        if current and len(current) >= MIN_CHUNK:
                            chunks.append(current)
                        current = sent
            else:
                current = para

    if current and len(current) >= MIN_CHUNK:
        chunks.append(current)

    return chunks


def detect_section(text: str) -> str:
    """Try to detect section heading from chunk text."""
    lines = text.split('\n')
    for line in lines[:3]:
        line = line.strip()
        # Section headings are usually short, capitalized or numbered
        if len(line) < 100 and (
            re.match(r'^\d+\.', line) or
            line.isupper() or
            re.match(r'^[A-Z][A-Za-z\s:]+$', line)
        ):
            return line[:100]
    return ""


# ─── Main Pipeline ──────────────────────────────────────────────────────────

def process_pdf(pdf_path: str) -> list[dict]:
    """Process a single PDF into chunks with metadata."""
    filename = os.path.basename(pdf_path)
    base_meta = extract_metadata_from_filename(filename)

    logger.info("Processing: %s", filename)

    pages = extract_text_from_pdf(pdf_path)
    if not pages:
        logger.warning("No text extracted from %s", filename)
        return []

    all_chunks = []
    chunk_num = 0

    for page_data in pages:
        text = clean_text(page_data["text"])
        if len(text) < MIN_CHUNK:
            continue

        text_chunks = chunk_text(text)

        for chunk_text_str in text_chunks:
            section = detect_section(chunk_text_str)
            meta = base_meta.copy()
            meta["secao"] = section
            meta["hierarquia"] = f"{base_meta['topico']} > {section}" if section else base_meta['topico']
            meta["parte"] = str(chunk_num)

            all_chunks.append({
                "text": chunk_text_str,
                "metadata": meta,
            })
            chunk_num += 1

    logger.info("  → %d chunks from %s", chunk_num, filename)
    return all_chunks


def main():
    global MIN_CHUNK, MAX_CHUNK

    parser = argparse.ArgumentParser(description="Parse PDFs for MAC RAG Ecocardiografia")
    parser.add_argument("--test", type=int, default=0, help="Process only N PDFs for testing")
    parser.add_argument("--min-chunk", type=int, default=MIN_CHUNK, help="Min chunk size (chars)")
    parser.add_argument("--max-chunk", type=int, default=MAX_CHUNK, help="Max chunk size (chars)")
    parser.add_argument("--pdf-dir", type=str, default=str(PDF_DIR), help="PDF directory")
    args = parser.parse_args()

    MIN_CHUNK = args.min_chunk
    MAX_CHUNK = args.max_chunk

    pdf_dir = Path(args.pdf_dir)
    pdfs = sorted(pdf_dir.glob("*.pdf"))

    if not pdfs:
        logger.error("No PDFs found in %s", pdf_dir)
        return

    if args.test:
        pdfs = pdfs[:args.test]

    logger.info("Processing %d PDFs from %s", len(pdfs), pdf_dir)

    all_chunks = []
    for pdf_path in pdfs:
        chunks = process_pdf(str(pdf_path))
        all_chunks.extend(chunks)

    # Save
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    logger.info("=" * 60)
    logger.info("Total: %d chunks from %d PDFs", len(all_chunks), len(pdfs))
    logger.info("Output: %s (%.1f MB)", OUTPUT_PATH, OUTPUT_PATH.stat().st_size / 1e6)

    # Stats
    societies = {}
    topics = {}
    for c in all_chunks:
        soc = c["metadata"]["sociedade"]
        top = c["metadata"]["topico"]
        societies[soc] = societies.get(soc, 0) + 1
        topics[top] = topics.get(top, 0) + 1

    logger.info("\nBy society:")
    for s, n in sorted(societies.items(), key=lambda x: -x[1]):
        logger.info("  %s: %d chunks", s, n)

    logger.info("\nTop topics:")
    for t, n in sorted(topics.items(), key=lambda x: -x[1])[:15]:
        logger.info("  %s: %d chunks", t, n)


if __name__ == "__main__":
    main()
