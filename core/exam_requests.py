"""Exam Request Generator — maps clinical hypotheses to guideline-recommended exams."""

import logging

from .card_helpers import get_list

logger = logging.getLogger(__name__)

# Mapping: clinical hypothesis/condition → recommended exams (from guidelines)
EXAM_MAP = {
    # Heart Failure investigation
    'insuficiência cardíaca': [
        'Ecocardiograma transtorácico',
        'BNP ou NT-proBNP',
        'Hemograma completo',
        'Função renal (ureia, creatinina, TFGe)',
        'Eletrólitos (Na+, K+, Mg2+)',
        'Função hepática (TGO, TGP, bilirrubinas)',
        'Função tireoidiana (TSH, T4L)',
        'Glicemia de jejum / HbA1c',
        'Perfil lipídico',
        'ECG de 12 derivações',
        'Radiografia de tórax PA e perfil',
    ],
    'ic': [
        'Ecocardiograma transtorácico',
        'BNP ou NT-proBNP',
        'Hemograma completo',
        'Função renal',
        'Eletrólitos',
        'ECG de 12 derivações',
    ],
    # Coronary artery disease
    'doença coronariana': [
        'ECG de 12 derivações',
        'Teste ergométrico ou cintilografia miocárdica',
        'Perfil lipídico completo',
        'Glicemia de jejum / HbA1c',
        'Função renal',
        'Hemograma',
    ],
    'síndrome coronariana': [
        'ECG de 12 derivações (seriado)',
        'Troponina ultrassensível (0h e 3h)',
        'Hemograma completo',
        'Função renal',
        'Eletrólitos',
        'Perfil lipídico',
        'Radiografia de tórax',
    ],
    # Atrial fibrillation
    'fibrilação atrial': [
        'ECG de 12 derivações',
        'Ecocardiograma transtorácico',
        'Função tireoidiana (TSH, T4L)',
        'Hemograma completo',
        'Função renal',
        'Função hepática',
        'Coagulograma (se anticoagulação)',
    ],
    # Hypertension workup
    'hipertensão': [
        'ECG de 12 derivações',
        'Função renal (ureia, creatinina, TFGe)',
        'Eletrólitos (Na+, K+)',
        'Glicemia de jejum',
        'Perfil lipídico',
        'Ácido úrico',
        'Urina tipo 1 (EAS)',
        'Microalbuminúria',
    ],
    # Valvular disease
    'valvopatia': [
        'Ecocardiograma transtorácico',
        'ECG de 12 derivações',
        'Radiografia de tórax',
    ],
    'estenose aórtica': [
        'Ecocardiograma transtorácico',
        'ECG de 12 derivações',
        'Angiotomografia de aorta e coronárias (se TAVI)',
    ],
    # Dyslipidemia
    'dislipidemia': [
        'Perfil lipídico completo (CT, LDL, HDL, TG)',
        'Glicemia de jejum',
        'Função hepática (TGO, TGP)',
        'TSH',
        'CPK (se mialgia com estatina)',
    ],
    # Pericarditis
    'pericardite': [
        'ECG de 12 derivações',
        'Ecocardiograma transtorácico',
        'Marcadores inflamatórios (PCR, VHS)',
        'Troponina',
        'Hemograma completo',
        'Radiografia de tórax',
    ],
    # Myocarditis
    'miocardite': [
        'ECG de 12 derivações',
        'Troponina ultrassensível',
        'BNP ou NT-proBNP',
        'Marcadores inflamatórios (PCR, VHS)',
        'Ecocardiograma transtorácico',
        'Ressonância magnética cardíaca (se disponível)',
    ],
    # Pulmonary embolism
    'tromboembolismo': [
        'D-dímero',
        'Angiotomografia de tórax',
        'ECG de 12 derivações',
        'Gasometria arterial',
        'Ecocardiograma transtorácico',
        'Troponina',
        'BNP',
    ],
    # Perioperative
    'perioperatório': [
        'ECG de 12 derivações',
        'Hemograma completo',
        'Coagulograma (TP, TTPA, INR)',
        'Função renal',
        'Eletrólitos',
        'Glicemia de jejum',
        'Radiografia de tórax (se indicado)',
    ],
}


def generate_exam_requests(card=None, soap_plan: str = "") -> list[dict]:
    """Generate exam requests from CartaoClinico and/or SOAP Plan.

    Returns list of dicts: [{'condition': '...', 'exams': ['...']}]
    """
    conditions_found = set()

    # Extract from CartaoClinico
    if card:
        hipoteses = get_list(card, 'hipoteses_diagnosticas')
        condutas = get_list(card, 'condutas_discutidas')
        comorbidades = get_list(card, 'comorbidades')

        all_texts = hipoteses + condutas + comorbidades
        for text in all_texts:
            text_lower = text.lower()
            for condition in EXAM_MAP:
                if condition in text_lower:
                    conditions_found.add(condition)

    # Extract from SOAP Plan text
    if soap_plan:
        plan_lower = soap_plan.lower()
        for condition in EXAM_MAP:
            if condition in plan_lower:
                conditions_found.add(condition)

    # Deduplicate exams across conditions
    results = []
    all_exams_seen = set()

    for condition in sorted(conditions_found):
        exams = EXAM_MAP[condition]
        unique_exams = [e for e in exams if e not in all_exams_seen]
        if unique_exams:
            results.append({
                'condition': condition.title(),
                'exams': unique_exams,
            })
            all_exams_seen.update(unique_exams)

    logger.info(f"Generated exam requests for {len(conditions_found)} conditions, {len(all_exams_seen)} unique exams")
    return results


def format_exam_requests_text(requests: list[dict]) -> str:
    """Format exam requests as plain text for printing/pasting."""
    if not requests:
        return "Nenhum exame sugerido automaticamente."

    lines = ["REQUISIÇÃO DE EXAMES", "=" * 40, ""]

    seen = set()
    all_exams = []
    for req in requests:
        for exam in req['exams']:
            if exam not in seen:
                seen.add(exam)
                all_exams.append(exam)

    # Deduplicated flat list
    for i, exam in enumerate(all_exams, 1):
        lines.append(f"{i}. {exam}")

    lines.append("")
    lines.append(f"Indicação: {', '.join(r['condition'] for r in requests)}")
    lines.append("Caráter: Eletivo")

    return '\n'.join(lines)


def format_exam_requests_markdown(requests: list[dict]) -> str:
    """Format exam requests as markdown for display."""
    if not requests:
        return "### Nenhum exame sugerido automaticamente\n"

    lines = ["### Exames Recomendados\n"]

    for req in requests:
        lines.append(f"**{req['condition']}:**")
        for exam in req['exams']:
            lines.append(f"- {exam}")
        lines.append("")

    return '\n'.join(lines)


