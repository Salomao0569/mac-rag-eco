"""
Módulo 1 (unificado): Parser de diretrizes → Chunks com metadados para RAG.

Providers:
  - parse_xml_guidelines()  — JATS XML do SciELO (diretrizes SBC)
  - parse_json_guidelines() — JSON extraído via Playwright (ESC/AHA)

Uso CLI:
  python parse.py                    # Processa tudo (SBC + internacional)
  python parse.py --xml-only         # Apenas SBC (XML)
  python parse.py --json-only        # Apenas internacional (JSON)
"""

import argparse
import glob
import json
import logging
import os
import re
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAX_CHUNK_SIZE = 1500

# ─── Metadados das diretrizes internacionais ─────────────────────────────────

GUIDELINE_META = {
    'ESC_HF_2023': {
        'title': '2023 Focused Update of the 2021 ESC Guidelines for the diagnosis and treatment of acute and chronic heart failure',
        'society': 'ESC',
        'topic': 'Insuficiência Cardíaca',
        'year': '2023',
        'doi': '10.1093/eurheartj/ehad195',
    },
    'AHA_HF_2022': {
        'title': '2022 AHA/ACC/HFSA Guideline for the Management of Heart Failure',
        'society': 'AHA/ACC',
        'topic': 'Insuficiência Cardíaca',
        'year': '2022',
        'doi': '10.1161/CIR.0000000000001063',
    },
    'ESC_ACS_2023': {
        'title': '2023 ESC Guidelines for the management of acute coronary syndromes',
        'society': 'ESC',
        'topic': 'Síndromes Coronarianas Agudas',
        'year': '2023',
        'doi': '10.1093/eurheartj/ehad191',
    },
    'ESC_HF_2021': {
        'title': '2021 ESC Guidelines for the diagnosis and treatment of acute and chronic heart failure',
        'society': 'ESC',
        'topic': 'Insuficiência Cardíaca',
        'year': '2021',
        'doi': '10.1093/eurheartj/ehab368',
    },
    'ESC_VHD_2021': {
        'title': '2021 ESC/EACTS Guidelines for the management of valvular heart disease',
        'society': 'ESC/EACTS',
        'topic': 'Valvopatias',
        'year': '2021',
        'doi': '10.1093/eurheartj/ehab395',
    },
    'ESC_VASCD_2022': {
        'title': '2022 ESC Guidelines for the management of patients with ventricular arrhythmias and the prevention of sudden cardiac death',
        'society': 'ESC',
        'topic': 'Arritmias Ventriculares e Morte Súbita',
        'year': '2022',
        'doi': '10.1093/eurheartj/ehac262',
    },
    'ESC_DM_2023': {
        'title': '2023 ESC Guidelines for the management of cardiovascular disease in patients with diabetes',
        'society': 'ESC',
        'topic': 'Diabetes e Doença Cardiovascular',
        'year': '2023',
        'doi': '10.1093/eurheartj/ehad192',
    },
    'ESC_CM_2023': {
        'title': '2023 ESC Guidelines for the management of cardiomyopathies',
        'society': 'ESC',
        'topic': 'Cardiomiopatias',
        'year': '2023',
        'doi': '10.1093/eurheartj/ehad194',
    },
    'ESC_IE_2023': {
        'title': '2023 ESC Guidelines for the management of endocarditis',
        'society': 'ESC',
        'topic': 'Endocardite Infecciosa',
        'year': '2023',
        'doi': '10.1093/eurheartj/ehad193',
    },
    'ESC_PAD_2024': {
        'title': '2024 ESC Guidelines for the management of peripheral arterial and aortic diseases',
        'society': 'ESC',
        'topic': 'Doença Arterial Periférica e Aorta',
        'year': '2024',
        'doi': '10.1093/eurheartj/ehae179',
    },
    'ESC_ONCO_2022': {
        'title': '2022 ESC Guidelines on cardio-oncology',
        'society': 'ESC',
        'topic': 'Cardio-Oncologia',
        'year': '2022',
        'doi': '10.1093/eurheartj/ehac244',
    },
    'ESC_PH_2022': {
        'title': '2022 ESC/ERS Guidelines for the diagnosis and treatment of pulmonary hypertension',
        'society': 'ESC/ERS',
        'topic': 'Hipertensão Pulmonar',
        'year': '2022',
        'doi': '10.1093/eurheartj/ehac237',
    },
    'ESC_VHD_2025': {
        'title': '2025 ESC/EACTS Guidelines for the management of valvular heart disease',
        'society': 'ESC/EACTS',
        'topic': 'Valvopatias',
        'year': '2025',
        'doi': '10.1093/eurheartj/ehaf194',
    },
    'AHA_REVASC_2021': {
        'title': '2021 ACC/AHA/SCAI Guideline for Coronary Artery Revascularization',
        'society': 'AHA/ACC',
        'topic': 'Revascularização Coronária',
        'year': '2021',
        'doi': '10.1161/CIR.0000000000001038',
    },
    'AHA_CHESTPAIN_2021': {
        'title': '2021 AHA/ACC/ASE/CHEST/SAEM/SCCT/SCMR Guideline for the Evaluation and Diagnosis of Chest Pain',
        'society': 'AHA/ACC',
        'topic': 'Dor Torácica',
        'year': '2021',
        'doi': '10.1161/CIR.0000000000001029',
    },
    'AHA_VHD_2020': {
        'title': '2020 ACC/AHA Guideline for the Management of Patients With Valvular Heart Disease',
        'society': 'AHA/ACC',
        'topic': 'Valvopatias',
        'year': '2020',
        'doi': '10.1161/CIR.0000000000000923',
    },
    # ─── ESC 2024 ────────────────────────────────────────────
    'ESC_AF_2024': {
        'title': '2024 ESC Guidelines for the Management of Atrial Fibrillation',
        'society': 'ESC',
        'topic': 'Fibrilação Atrial',
        'year': '2024',
        'doi': '10.1093/eurheartj/ehae176',
    },
    'ESC_CCS_2024': {
        'title': '2024 ESC Guidelines for the Management of Chronic Coronary Syndromes',
        'society': 'ESC',
        'topic': 'Síndrome Coronariana Crônica',
        'year': '2024',
        'doi': '10.1093/eurheartj/ehae177',
    },
    'ESC_HTN_2024': {
        'title': '2024 ESC Guidelines for the Management of Elevated Blood Pressure and Hypertension',
        'society': 'ESC',
        'topic': 'Hipertensão Arterial',
        'year': '2024',
        'doi': '10.1093/eurheartj/ehae178',
    },
    # ─── ESC 2025 ────────────────────────────────────────────
    'ESC_MYOPERI_2025': {
        'title': '2025 ESC Guidelines for the Management of Myocarditis and Pericarditis',
        'society': 'ESC',
        'topic': 'Miocardite e Pericardite',
        'year': '2025',
        'doi': '10.1093/eurheartj/ehaf026',
    },
    'ESC_PREG_2025': {
        'title': '2025 ESC Guidelines for the Management of Cardiovascular Disease and Pregnancy',
        'society': 'ESC',
        'topic': 'Doença Cardiovascular na Gestação',
        'year': '2025',
        'doi': '10.1093/eurheartj/ehaf194',
    },
    'ESC_DYSLIP_2025': {
        'title': '2025 Focused Update of the 2019 ESC/EAS Guidelines for the Management of Dyslipidaemias',
        'society': 'ESC/EAS',
        'topic': 'Dislipidemias',
        'year': '2025',
        'doi': '10.1093/eurheartj/ehaf025',
    },
    # ─── AHA 2025 ────────────────────────────────────────────
    'AHA_ACS_2025': {
        'title': '2025 ACC/AHA Guideline for the Management of Patients With Acute Coronary Syndromes',
        'society': 'AHA/ACC',
        'topic': 'Síndromes Coronarianas Agudas',
        'year': '2025',
        'doi': '10.1161/CIR.0000000000001309',
    },
    'AHA_HTN_2025': {
        'title': '2025 AHA/ACC Guideline for the Prevention, Detection, Evaluation and Management of High Blood Pressure in Adults',
        'society': 'AHA/ACC',
        'topic': 'Hipertensão Arterial',
        'year': '2025',
        'doi': '10.1161/CIR.0000000000001356',
    },
    # ─── Perioperatórias ────────────────────────────────────────
    'ESC_Perioperative_2022': {
        'title': '2022 ESC Guidelines on cardiovascular assessment and management of patients undergoing non-cardiac surgery',
        'society': 'ESC',
        'topic': 'Avaliação Perioperatória',
        'year': '2022',
        'doi': '10.1093/eurheartj/ehac270',
    },
    'AHA_ACC_Perioperative_2024': {
        'title': '2024 AHA/ACC/ACS/ASNC/HRS/SCA/SCCT/SCMR/SVM Guideline for Perioperative Cardiovascular Management for Noncardiac Surgery',
        'society': 'AHA/ACC',
        'topic': 'Avaliação Perioperatória',
        'year': '2024',
        'doi': '10.1161/CIR.0000000000001285',
    },
    # ─── AHA 2023 ────────────────────────────────────────────
    'AHA_CCD_2023': {
        'title': '2023 AHA/ACC/ACCP/ASPC/NLA/PCNA Guideline for the Management of Patients With Chronic Coronary Disease',
        'society': 'AHA/ACC',
        'topic': 'Doença Coronariana Crônica',
        'year': '2023',
        'doi': '10.1161/CIR.0000000000001168',
    },
    'AHA_AF_2023': {
        'title': '2023 ACC/AHA/ACCP/HRS Guideline for the Diagnosis and Management of Atrial Fibrillation',
        'society': 'AHA/ACC',
        'topic': 'Fibrilação Atrial',
        'year': '2023',
        'doi': '10.1161/CIR.0000000000001193',
    },
    # ─── AHA 2022 ────────────────────────────────────────────
    'AHA_AORTIC_2022': {
        'title': '2022 ACC/AHA Guideline for the Diagnosis and Management of Aortic Disease',
        'society': 'AHA/ACC',
        'topic': 'Doença Aórtica',
        'year': '2022',
        'doi': '10.1161/CIR.0000000000001106',
    },
    # ─── AHA 2025 (Scientific Statement) ─────────────────────
    'AHA_INFLAMMATION_2025': {
        'title': '2025 ACC Scientific Statement: Inflammation and Cardiovascular Disease',
        'society': 'AHA/ACC',
        'topic': 'Inflamação e Doença Cardiovascular',
        'year': '2025',
        'doi': '10.1161/CIR.0000000000001380',
    },
    # ─── AHA 2020 (Focused Update Mitral) ────────────────────
    'AHA_MITRAL_2020': {
        'title': '2020 Focused Update of the 2017 ACC Expert Consensus Decision Pathway on the Management of Mitral Regurgitation',
        'society': 'AHA/ACC',
        'topic': 'Regurgitação Mitral',
        'year': '2020',
        'doi': '10.1016/j.jacc.2020.02.005',
    },
    # ─── docs/novas (já indexados anteriormente, agora no pipeline) ───
    'AHA_CHD_ADULT_2025': {
        'title': '2025 ACC/AHA/HRS/ISACHD/SCAI Guideline for the Management of Adults With Congenital Heart Disease',
        'society': 'AHA/ACC',
        'topic': 'Cardiopatia Congênita no Adulto',
        'year': '2025',
        'doi': '10.1161/CIR.0000000000001345',
    },
    'AHA_DYSLIP_2026': {
        'title': '2026 ACC/AHA Guideline on the Management of Dyslipidemia',
        'society': 'AHA/ACC',
        'topic': 'Dislipidemias',
        'year': '2026',
        'doi': '10.1161/CIR.0000000000001400',
    },
    'AHA_TEP_2026': {
        'title': '2026 AHA/ACC Guideline for the Evaluation and Management of Acute Pulmonary Embolism in Adults',
        'society': 'AHA/ACC',
        'topic': 'Tromboembolismo Pulmonar',
        'year': '2026',
        'doi': '10.1161/CIR.0000000000001401',
    },
    'AHA_REVASC_2021': {
        'title': '2021 ACC/AHA/SCAI Guideline for Coronary Artery Revascularization',
        'society': 'AHA/ACC',
        'topic': 'Revascularização Coronária',
        'year': '2021',
        'doi': '10.1161/CIR.0000000000001038',
    },
    'SBC_IC_2018': {
        'title': 'Diretriz Brasileira de Insuficiência Cardíaca Crônica e Aguda – 2018',
        'society': 'SBC',
        'topic': 'Insuficiência Cardíaca',
        'year': '2018',
        'doi': '10.5935/abc.20180190',
    },
    'SBC_IC_UPDATE_2021': {
        'title': 'Atualização de Tópicos Emergentes da Diretriz Brasileira de Insuficiência Cardíaca – 2021',
        'society': 'SBC',
        'topic': 'Insuficiência Cardíaca',
        'year': '2021',
        'doi': '10.36660/abc.20210367',
    },
    'SBC_REAB_2020': {
        'title': 'Diretriz Brasileira de Reabilitação Cardiovascular – 2020',
        'society': 'SBC',
        'topic': 'Reabilitação Cardiovascular',
        'year': '2020',
        'doi': '10.36660/abc.20200407',
    },
}

# ─── Mapeamento de PDFs para chaves de metadados ─────────────────────────────
PDF_GUIDELINE_MAP = {
    'ESC_Perioperative_2022.pdf': 'ESC_Perioperative_2022',
    'AHA_ACC_Perioperative_2024.pdf': 'AHA_ACC_Perioperative_2024',
    'AHA_CCD_2023.pdf': 'AHA_CCD_2023',
    'AHA_AF_2023.pdf': 'AHA_AF_2023',
    'AHA_AORTIC_2022.pdf': 'AHA_AORTIC_2022',
    'AHA_INFLAMMATION_2025.pdf': 'AHA_INFLAMMATION_2025',
    'AHA_MITRAL_2020.pdf': 'AHA_MITRAL_2020',
    'AHA_CHD_Adult_2025.pdf': 'AHA_CHD_ADULT_2025',
    'AHA_Dyslipidemia_2026.pdf': 'AHA_DYSLIP_2026',
    'AHA_TEP_2026.pdf': 'AHA_TEP_2026',
    'AHA_Revascularization_2021.pdf': 'AHA_REVASC_2021',
    'SBC_IC_2018.pdf': 'SBC_IC_2018',
    'SBC_IC_Update_2021.pdf': 'SBC_IC_UPDATE_2021',
    'SBC_Reabilitacao_CV_2020.pdf': 'SBC_REAB_2020',
}


# ═════════════════════════════════════════════════════════════════════════════
# Shared helpers
# ═════════════════════════════════════════════════════════════════════════════

def clean_text(text):
    """Normalize whitespace: collapse runs of whitespace into single spaces."""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def split_text(text, max_size=MAX_CHUNK_SIZE):
    """Split long text respecting paragraphs, then sentences, with force-cut fallback."""
    # Try paragraphs first
    parts = text.split('\n\n')
    if len(parts) <= 1:
        # No paragraph breaks — split by sentences (. followed by space and uppercase)
        parts = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)

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

    # Force-cut chunks that are still too large
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
    """Detect disclosure / references / acknowledgements sections."""
    skip = (
        'references', 'acknowledgement', 'disclosure', 'conflict of interest',
        'supplementary', 'author contribution', 'funding', 'data availability',
        'article contents', 'cite', 'table of contents', 'share', 'search',
        'navbar', 'skip to', 'sign in', 'related articles', 'metrics',
        'responses', 'close', 'pdf', 'permissions', 'reprints',
    )
    lower = text.lower()
    return any(m in lower for m in skip)


def add_chunks(chunks, text, section, base_metadata):
    """Create 1+ chunk dicts from text, splitting if over MAX_CHUNK_SIZE."""
    text = clean_text(text)
    if len(text) < 50:
        return

    if len(text) > MAX_CHUNK_SIZE:
        sub_chunks = split_text(text, MAX_CHUNK_SIZE)
        for j, sc in enumerate(sub_chunks):
            if len(sc.strip()) > 50:
                chunks.append({
                    'text': sc,
                    'metadata': {
                        **base_metadata,
                        'secao': section,
                        'hierarquia': section,
                        'tipo': 'texto',
                        'parte': j + 1,
                    }
                })
    else:
        chunks.append({
            'text': text,
            'metadata': {
                **base_metadata,
                'secao': section,
                'hierarquia': section,
                'tipo': 'texto',
                'parte': 0,
            }
        })


# ═════════════════════════════════════════════════════════════════════════════
# Provider: JATS XML (SBC guidelines)
# ═════════════════════════════════════════════════════════════════════════════

MAX_TABLE_CHARS = 4000  # Tabelas maiores são truncadas com aviso


def _xml_get_text(elem):
    """Extrai texto limpo recursivamente de um elemento XML."""
    if elem is None:
        return ''
    parts = []
    if elem.text:
        parts.append(elem.text)
    for child in elem:
        tag = child.tag
        if tag == 'xref':
            ref_type = child.get('ref-type', '')
            if ref_type == 'bibr':
                pass  # ignora referências bibliográficas inline
            else:
                parts.append(_xml_get_text(child))
        elif tag == 'break':
            parts.append(' ')
        elif tag == 'ext-link':
            parts.append(_xml_get_text(child))
        elif tag == 'list':
            parts.append('\n' + _xml_extract_list(child))
        elif tag in ('sup', 'sub'):
            parts.append(_xml_get_text(child))
        else:
            parts.append(_xml_get_text(child))
        if child.tail:
            parts.append(child.tail)
    return ''.join(parts)


def _xml_extract_list(list_elem):
    """Converte lista JATS em texto limpo."""
    lines = []
    for item in list_elem.findall('list-item'):
        texts = []
        for p in item.findall('p'):
            t = _xml_get_text(p).strip()
            if t:
                texts.append(t)
        if texts:
            lines.append('- ' + '; '.join(texts))
    return '\n'.join(lines)


def _xml_is_disclosure_table(caption_text, table_wrap):
    """Detecta tabelas de declaração de interesse/conflito (sem valor clínico)."""
    markers = (
        'declaraç', 'disclosure', 'conflito de interesse',
        'conflict of interest', 'potencial conflito',
    )
    text_to_check = caption_text.lower()
    table = table_wrap.find('.//table')
    if table is not None:
        first_rows = []
        for tr in list(table.iter('tr'))[:2]:
            first_rows.append(_xml_get_text(tr).lower())
        text_to_check += ' '.join(first_rows)
    return any(m in text_to_check for m in markers)


def _xml_extract_table_as_text(table_wrap):
    """Converte tabela JATS em texto legível para embedding."""
    lines = []

    # Caption
    label = table_wrap.find('label')
    caption = table_wrap.find('caption')
    caption_text = ''
    if label is not None:
        caption_text += _xml_get_text(label).strip()
    if caption is not None:
        title = caption.find('title')
        if title is not None:
            caption_text += ' ' + _xml_get_text(title).strip()
        for p in caption.findall('p'):
            caption_text += ' ' + _xml_get_text(p).strip()
    if caption_text.strip():
        lines.append(caption_text.strip())

    # Filtrar tabelas de disclosure
    if _xml_is_disclosure_table(caption_text, table_wrap):
        return ''

    # Table rows
    table = table_wrap.find('.//table')
    if table is None:
        return '\n'.join(lines)

    for section in [table.find('thead'), table.find('tbody'), table.find('tfoot')]:
        if section is None:
            continue
        for tr in section.findall('tr'):
            cells = []
            for cell in tr:
                text = _xml_get_text(cell).strip().replace('\n', ' ')
                text = re.sub(r'\s+', ' ', text)
                if text:
                    cells.append(text)
            if cells:
                lines.append(' | '.join(cells))

    # Direct tr children (tables without thead/tbody/tfoot)
    if not any(table.find(s) is not None for s in ['thead', 'tbody', 'tfoot']):
        for tr in table.findall('tr'):
            cells = []
            for cell in tr:
                text = _xml_get_text(cell).strip().replace('\n', ' ')
                if text:
                    cells.append(text)
            if cells:
                lines.append(' | '.join(cells))

    # Footer notes
    for fn in table_wrap.findall('.//table-wrap-foot//fn'):
        fn_text = _xml_get_text(fn).strip()
        if fn_text:
            lines.append(f'Nota: {fn_text}')

    result = '\n'.join(lines)

    # Truncar tabelas muito grandes
    if len(result) > MAX_TABLE_CHARS:
        result = result[:MAX_TABLE_CHARS].rsplit('\n', 1)[0] + '\n[...tabela truncada]'

    return result


def _xml_get_section_path(sec_elem, ancestors=None):
    """Retorna o caminho hierárquico da seção."""
    if ancestors is None:
        ancestors = []
    label = sec_elem.find('label')
    title = sec_elem.find('title')
    name = ''
    if label is not None and label.text:
        name += label.text.strip() + ' '
    if title is not None:
        name += _xml_get_text(title).strip()
    return ancestors + [name.strip()] if name.strip() else ancestors


def _xml_split_text(text, max_size=MAX_CHUNK_SIZE):
    """Divide texto longo respeitando parágrafos (versão XML, join com \\n\\n)."""
    paragraphs = text.split('\n\n')
    chunks = []
    current = []
    current_len = 0

    for p in paragraphs:
        if current_len + len(p) > max_size and current:
            chunks.append('\n\n'.join(current))
            current = [p]
            current_len = len(p)
        else:
            current.append(p)
            current_len += len(p)

    if current:
        chunks.append('\n\n'.join(current))
    return chunks


def _xml_extract_chunks_from_section(sec_elem, metadata, ancestors=None, chunks=None):
    """Extrai chunks recursivamente de uma seção XML."""
    if chunks is None:
        chunks = []
    if ancestors is None:
        ancestors = []

    path = _xml_get_section_path(sec_elem, ancestors)
    section_name = path[-1] if path else ''

    paragraphs = []
    tables = []
    for child in sec_elem:
        if child.tag == 'p':
            text = _xml_get_text(child).strip()
            text = re.sub(r'\s+', ' ', text)
            if text and len(text) > 30:
                paragraphs.append(text)
        elif child.tag == 'table-wrap':
            table_text = _xml_extract_table_as_text(child)
            if table_text.strip():
                tables.append(table_text)
        elif child.tag == 'fig':
            caption = child.find('caption')
            if caption is not None:
                fig_text = _xml_get_text(caption).strip()
                if fig_text:
                    paragraphs.append(f'[Figura] {fig_text}')
        elif child.tag == 'list':
            list_text = _xml_extract_list(child)
            if list_text.strip():
                paragraphs.append(list_text)
        elif child.tag == 'sec':
            _xml_extract_chunks_from_section(child, metadata, path, chunks)

    # Criar chunk de texto
    if paragraphs:
        text = '\n\n'.join(paragraphs)
        if len(text) > 2000:
            sub_chunks = _xml_split_text(text, max_size=1500)
            for i, sc in enumerate(sub_chunks):
                chunks.append({
                    'text': sc,
                    'metadata': {
                        **metadata,
                        'secao': section_name,
                        'hierarquia': ' > '.join(path),
                        'tipo': 'texto',
                        'parte': i + 1 if len(sub_chunks) > 1 else 0,
                    }
                })
        else:
            chunks.append({
                'text': text,
                'metadata': {
                    **metadata,
                    'secao': section_name,
                    'hierarquia': ' > '.join(path),
                    'tipo': 'texto',
                    'parte': 0,
                }
            })

    # Chunks separados para tabelas
    for table_text in tables:
        chunks.append({
            'text': table_text,
            'metadata': {
                **metadata,
                'secao': section_name,
                'hierarquia': ' > '.join(path),
                'tipo': 'tabela',
                'parte': 0,
            }
        })

    return chunks


def _xml_parse_guideline(xml_path):
    """Processa um XML de diretriz e retorna lista de chunks."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    meta = root.find('.//article-meta')

    # Metadados
    title_elem = meta.find('.//article-title')
    title = ''.join(title_elem.itertext()).strip() if title_elem is not None else os.path.basename(xml_path)

    doi = ''
    for aid in meta.findall('article-id'):
        if aid.get('pub-id-type') == 'doi':
            doi = aid.text or ''

    year = ''
    for pd in meta.findall('pub-date'):
        y = pd.find('year')
        if y is not None:
            year = y.text
            break

    base_metadata = {
        'diretriz': title,
        'ano': year,
        'doi': doi,
        'arquivo': os.path.basename(xml_path),
    }

    body = root.find('body')
    if body is None:
        return []

    chunks = []
    for child in body:
        if child.tag == 'sec':
            _xml_extract_chunks_from_section(child, base_metadata, chunks=chunks)
        elif child.tag == 'table-wrap':
            table_text = _xml_extract_table_as_text(child)
            if table_text.strip():
                chunks.append({
                    'text': table_text,
                    'metadata': {
                        **base_metadata,
                        'secao': 'Corpo',
                        'hierarquia': 'Corpo',
                        'tipo': 'tabela',
                        'parte': 0,
                    }
                })

    return chunks


def parse_xml_guidelines(xml_dir=None):
    """Process all SBC XML guidelines and return list of chunks."""
    if xml_dir is None:
        xml_dir = os.environ.get('SBC_XML_DIR', os.path.expanduser('~/Downloads/Diretrizes SBC - XML'))

    logger.info('MAC RAG — Parsing de diretrizes SBC (XML JATS)')

    all_chunks = []
    xml_files = sorted(glob.glob(os.path.join(xml_dir, '**', '*.xml'), recursive=True))

    logger.info(f'Encontrados {len(xml_files)} arquivos XML')

    for xml_path in xml_files:
        basename = os.path.basename(xml_path)
        chunks = _xml_parse_guideline(xml_path)
        logger.info(f'  {basename}: {len(chunks)} chunks')
        all_chunks.extend(chunks)

    logger.info(f'Total SBC: {len(all_chunks)} chunks')
    return all_chunks


# ═════════════════════════════════════════════════════════════════════════════
# Provider: JSON (international guidelines — ESC/AHA via Playwright)
# ═════════════════════════════════════════════════════════════════════════════

def _json_parse_guideline(json_path, guideline_key):
    """Parseia JSON extraído via Playwright e retorna chunks."""
    meta = GUIDELINE_META.get(guideline_key)
    if not meta:
        logger.warning(f'Metadados não encontrados para {guideline_key}')
        return []

    with open(json_path, 'r', encoding='utf-8') as f:
        raw = f.read()

    # Formatos possíveis:
    # A) MCP wrapper: [{type: "text", text: "### Result\n\"[...]\""}]
    # B) Raw Playwright: ### Result\n"[{\"s\":\"...\"}]"
    # C) Direct JSON array: [{s, c}, ...]
    try:
        if raw.startswith('### Result'):
            json_line = raw.split('\n', 1)[1]
            decoder = json.JSONDecoder()
            json_str, _ = decoder.raw_decode(json_line)
            sections_data = json.loads(json_str)
        else:
            mcp_wrapper = json.loads(raw)
            if isinstance(mcp_wrapper, list) and mcp_wrapper:
                if isinstance(mcp_wrapper[0], dict) and 'text' in mcp_wrapper[0]:
                    text_content = mcp_wrapper[0]['text']
                    if '### Result' in text_content:
                        json_line = text_content.split('\n', 1)[1]
                        decoder = json.JSONDecoder()
                        json_str, _ = decoder.raw_decode(json_line)
                        sections_data = json.loads(json_str)
                    else:
                        sections_data = json.loads(text_content)
                elif isinstance(mcp_wrapper[0], dict) and 's' in mcp_wrapper[0]:
                    sections_data = mcp_wrapper
                else:
                    sections_data = mcp_wrapper
            else:
                sections_data = mcp_wrapper
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f'Erro parsing JSON: {e}')
        return []

    if not isinstance(sections_data, list):
        logger.warning(f'Formato inesperado em {json_path}')
        return []

    base_metadata = {
        'diretriz': meta['title'],
        'sociedade': meta['society'],
        'topico': meta['topic'],
        'ano': meta['year'],
        'doi': meta['doi'],
        'idioma': 'en',
    }

    chunks = []

    for section in sections_data:
        section_name = section.get('s', section.get('section', ''))
        content = section.get('c', section.get('content', ''))

        if not section_name or not content:
            continue

        if is_non_clinical(section_name):
            continue

        content = clean_text(content)
        if len(content) < 50:
            continue

        add_chunks(chunks, content, section_name, base_metadata)

    return chunks


def parse_json_guidelines(json_dir=None):
    """Process all international JSON guidelines and return list of chunks."""
    if json_dir is None:
        json_dir = os.path.join(BASE_DIR, 'guidelines_html')

    logger.info('MAC RAG — Parsing de diretrizes internacionais (JSON)')

    all_chunks = []
    json_files = sorted(f for f in os.listdir(json_dir) if f.endswith('.json'))

    logger.info(f'Encontrados {len(json_files)} arquivos JSON')

    for filename in json_files:
        key = filename.replace('.json', '')
        filepath = os.path.join(json_dir, filename)

        if key not in GUIDELINE_META:
            logger.warning(f'{key}: sem metadados configurados, pulando')
            continue

        meta = GUIDELINE_META[key]
        logger.info(f'  Parseando {key} ({meta["society"]} {meta["year"]})...')

        chunks = _json_parse_guideline(filepath, key)
        logger.info(f'  -> {len(chunks)} chunks')

        all_chunks.extend(chunks)

    logger.info(f'Total internacional: {len(all_chunks)} chunks')
    return all_chunks


# ═════════════════════════════════════════════════════════════════════════════
# Provider: PDF (international guidelines — fallback when JSON unavailable)
# ═════════════════════════════════════════════════════════════════════════════

# Regex for ESC/AHA section headings: "4.1.1 Beta-blockers" or "Recommendations"
_PDF_HEADING_RE = re.compile(
    r'^(\d+\.[\d.]*\s+[A-Z].*|Recommendations?\b|Table\s+\d+|Figure\s+\d+)',
)

# Non-clinical page markers
_PDF_SKIP_MARKERS = (
    'references', 'acknowledgement', 'disclosure', 'conflict of interest',
    'supplementary data', 'author contribution', 'funding',
    'web addenda', 'affiliations',
)


def _pdf_is_skip_page(text):
    """Detect reference/disclosure pages to skip."""
    lower = text[:500].lower()
    return any(m in lower for m in _PDF_SKIP_MARKERS)


def _pdf_clean_page(text):
    """Remove journal headers, footers, page numbers."""
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        stripped = line.strip()
        # Skip very short lines (page numbers, headers)
        if len(stripped) < 10:
            continue
        # Skip journal header/footer patterns
        if re.match(r'^\d+\s*$', stripped):  # page numbers
            continue
        if re.match(r'^(European Heart Journal|Circulation|JACC)', stripped, re.IGNORECASE):
            continue
        if re.match(r'^\.\s*$', stripped):
            continue
        cleaned.append(stripped)
    return '\n'.join(cleaned)


def _pdf_parse_guideline(pdf_path, guideline_key):
    """Parse a PDF guideline using PyMuPDF and return chunks."""
    import fitz  # PyMuPDF

    meta = GUIDELINE_META.get(guideline_key)
    if not meta:
        logger.warning(f'Metadados não encontrados para {guideline_key}')
        return []

    base_metadata = {
        'diretriz': meta['title'],
        'sociedade': meta['society'],
        'topico': meta['topic'],
        'ano': meta['year'],
        'doi': meta['doi'],
        'idioma': 'en',
    }

    doc = fitz.open(pdf_path)
    chunks = []
    current_section = 'Introduction'
    current_text = []

    for page in doc:
        page_text = page.get_text()
        if not page_text or len(page_text.strip()) < 50:
            continue

        # Skip reference/disclosure pages
        if _pdf_is_skip_page(page_text):
            continue

        page_text = _pdf_clean_page(page_text)

        for line in page_text.split('\n'):
            line = line.strip()
            if not line:
                continue

            # Detect section heading
            heading_match = _PDF_HEADING_RE.match(line)
            if heading_match and len(line) < 200:
                # Flush current section
                if current_text:
                    section_content = ' '.join(current_text)
                    if not is_non_clinical(current_section):
                        add_chunks(chunks, section_content, current_section, base_metadata)
                    current_text = []
                current_section = line
            else:
                current_text.append(line)

    # Flush last section
    if current_text:
        section_content = ' '.join(current_text)
        if not is_non_clinical(current_section):
            add_chunks(chunks, section_content, current_section, base_metadata)

    doc.close()
    return chunks


def parse_pdf_guidelines(pdf_dir=None):
    """Process all PDF guidelines and return list of chunks."""
    if pdf_dir is None:
        pdf_dir = os.path.join(BASE_DIR, 'guidelines_html')

    logger.info('MAC RAG — Parsing de diretrizes internacionais (PDF)')

    all_chunks = []

    for filename, key in PDF_GUIDELINE_MAP.items():
        filepath = os.path.join(pdf_dir, filename)
        if not os.path.exists(filepath):
            logger.warning(f'  PDF não encontrado: {filepath}')
            continue

        meta = GUIDELINE_META[key]
        logger.info(f'  Parseando {key} ({meta["society"]} {meta["year"]})...')

        chunks = _pdf_parse_guideline(filepath, key)
        logger.info(f'  -> {len(chunks)} chunks')
        all_chunks.extend(chunks)

    logger.info(f'Total PDF: {len(all_chunks)} chunks')
    return all_chunks


# ═════════════════════════════════════════════════════════════════════════════
# Unified pipeline
# ═════════════════════════════════════════════════════════════════════════════

def _log_chunk_stats(label, chunks):
    """Log statistics about a chunk list."""
    if not chunks:
        logger.info(f'{label}: 0 chunks')
        return

    sizes = [len(c['text']) for c in chunks]
    logger.info(f'{label}: {len(chunks)} chunks | '
                f'avg {sum(sizes) // len(sizes)} chars | '
                f'min {min(sizes)} | max {max(sizes)} chars')

    # By type
    by_type = {}
    for c in chunks:
        t = c['metadata'].get('tipo', '?')
        by_type[t] = by_type.get(t, 0) + 1
    for t, count in sorted(by_type.items()):
        logger.info(f'  {t}: {count} chunks')

    # By society (international only)
    by_society = {}
    for c in chunks:
        s = c['metadata'].get('sociedade')
        if s:
            by_society[s] = by_society.get(s, 0) + 1
    if by_society:
        for s, count in sorted(by_society.items()):
            logger.info(f'  {s}: {count} chunks')

    # By topic (international only)
    by_topic = {}
    for c in chunks:
        t = c['metadata'].get('topico')
        if t:
            by_topic[t] = by_topic.get(t, 0) + 1
    if by_topic:
        for t, count in sorted(by_topic.items()):
            logger.info(f'  {t}: {count} chunks')


def process_all(xml_only=False, json_only=False):
    """Process all guidelines (SBC + international) and save output files.

    Args:
        xml_only:  If True, process only SBC XML guidelines.
        json_only: If True, process only international JSON guidelines.

    Returns:
        Combined list of all chunks processed.
    """
    sbc_chunks = []
    intl_chunks = []

    # ── SBC (XML) ────────────────────────────────────────────
    if not json_only:
        xml_dir = os.environ.get('SBC_XML_DIR', os.path.expanduser('~/Downloads/Diretrizes SBC - XML'))
        sbc_chunks = parse_xml_guidelines(xml_dir)

        output_sbc = os.path.join(BASE_DIR, 'chunks.json')
        with open(output_sbc, 'w', encoding='utf-8') as f:
            json.dump(sbc_chunks, f, ensure_ascii=False, indent=2)
        logger.info(f'Chunks SBC salvos: {output_sbc}')

    # ── International (JSON) ─────────────────────────────────
    if not xml_only:
        intl_chunks = parse_json_guidelines()

        # ── International (PDF) ──────────────────────────────────
        pdf_chunks = parse_pdf_guidelines()
        intl_chunks.extend(pdf_chunks)

        output_intl = os.path.join(BASE_DIR, 'chunks_international.json')
        with open(output_intl, 'w', encoding='utf-8') as f:
            json.dump(intl_chunks, f, ensure_ascii=False, indent=2)
        logger.info(f'Chunks internacionais salvos: {output_intl}')

    # ── Combined ─────────────────────────────────────────────
    if not xml_only and not json_only:
        combined = sbc_chunks + intl_chunks
        output_all = os.path.join(BASE_DIR, 'chunks_all.json')
        with open(output_all, 'w', encoding='utf-8') as f:
            json.dump(combined, f, ensure_ascii=False, indent=2)
        logger.info(f'Chunks combinados salvos: {output_all} ({len(combined)} total)')
    elif xml_only:
        combined = sbc_chunks
    else:
        combined = intl_chunks

    # ── Statistics ────────────────────────────────────────────
    if sbc_chunks:
        _log_chunk_stats('SBC', sbc_chunks)
    if intl_chunks:
        _log_chunk_stats('Internacional', intl_chunks)
    if sbc_chunks and intl_chunks:
        _log_chunk_stats('Total combinado', sbc_chunks + intl_chunks)

    return combined


# ═════════════════════════════════════════════════════════════════════════════
# CLI
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='MAC RAG — Parser unificado de diretrizes cardiológicas')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--xml-only', action='store_true',
                       help='Processar apenas diretrizes SBC (XML JATS)')
    group.add_argument('--json-only', action='store_true',
                       help='Processar apenas diretrizes internacionais (JSON)')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')

    chunks = process_all(xml_only=args.xml_only, json_only=args.json_only)
    logger.info(f'Concluido! {len(chunks)} chunks processados.')
