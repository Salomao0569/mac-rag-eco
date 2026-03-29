"""Auto-calculate clinical scores for Ecocardiografia.
Gerado pelo RAG Factory.
"""

import logging
from .card_helpers import get_comorbidades, get_idade, get_sexo, has_condition

logger = logging.getLogger(__name__)


def compute_disfuncao_diastolica(e_prime_septal_baixo: bool = False, e_prime_lateral_baixo: bool = False, e_E_elevado: bool = False, tr_velocity_elevada: bool = False, lai_volume_elevado: bool = False) -> dict:
    """Classificação da função diastólica do VE (ASE/EACVI)"""
    items = [
        ("e_prime_septal_baixo", e_prime_septal_baixo, 1),
        ("e_prime_lateral_baixo", e_prime_lateral_baixo, 1),
        ("e_E_elevado", e_E_elevado, 1),
        ("tr_velocity_elevada", tr_velocity_elevada, 1),
        ("lai_volume_elevado", lai_volume_elevado, 1),
    ]
    score = sum(p for _, v, p in items if v)
    details = [f"{n}(+{p})" for n, v, p in items if v]

    if 0 <= score <= 1:
        risk, rec = "Normal / Grau I (indeterminado se 1)", "Função diastólica normal ou indeterminada. Correlacionar com clínica."
    if 2 <= score <= 2:
        risk, rec = "Grau I (Relaxamento anormal)", "Disfunção diastólica grau I — pressões de enchimento normais."
    if 3 <= score <= 3:
        risk, rec = "Grau II (Pseudonormal)", "Disfunção diastólica grau II — pressões de enchimento elevadas."
    if 4 <= score <= 5:
        risk, rec = "Grau III (Restritivo)", "Disfunção diastólica grau III — pressões de enchimento significativamente elevadas."

    return {
        "name": "Disfunção Diastólica",
        "score": score,
        "details": ", ".join(details) if details else "Sem fatores identificados",
        "risk": risk,
        "recommendation": rec,
        "reference": "ASE/EACVI Diastolic Function 2016 + Update 2024",
    }

def compute_tapse_classificacao(tapse_reduzido: bool = False) -> dict:
    """Excursão sistólica do plano do anel tricúspide"""
    items = [
        ("tapse_reduzido", tapse_reduzido, 1),
    ]
    score = sum(p for _, v, p in items if v)
    details = [f"{n}(+{p})" for n, v, p in items if v]

    if 0 <= score <= 0:
        risk, rec = "Normal", "Função sistólica longitudinal do VD preservada (TAPSE >= 17 mm)"
    if 1 <= score <= 1:
        risk, rec = "Disfunção sistólica do VD", "TAPSE < 17 mm — disfunção sistólica do VD. Complementar com FAC, S' do DTI, strain do VD."

    return {
        "name": "TAPSE",
        "score": score,
        "details": ", ".join(details) if details else "Sem fatores identificados",
        "risk": risk,
        "recommendation": rec,
        "reference": "ASE Right Heart 2024",
    }

def compute_gravidade_ea(ava_menor_1: bool = False, grad_medio_maior_40: bool = False, vmax_maior_4: bool = False) -> dict:
    """Classificação de gravidade da estenose aórtica por parâmetros ecocardiográficos"""
    items = [
        ("ava_menor_1", ava_menor_1, 1),
        ("grad_medio_maior_40", grad_medio_maior_40, 1),
        ("vmax_maior_4", vmax_maior_4, 1),
    ]
    score = sum(p for _, v, p in items if v)
    details = [f"{n}(+{p})" for n, v, p in items if v]

    if 0 <= score <= 0:
        risk, rec = "Leve a Moderada", "EA leve a moderada. Seguimento ecocardiográfico conforme diretrizes."
    if 1 <= score <= 1:
        risk, rec = "Moderada a Importante", "Parâmetros discordantes — considerar EA moderada a importante. Investigar baixo fluxo."
    if 2 <= score <= 3:
        risk, rec = "Importante (Grave)", "EA importante. Avaliar sintomas e indicação de intervenção (TAVI/SAVR)."

    return {
        "name": "Gravidade da Estenose Aórtica",
        "score": score,
        "details": ", ".join(details) if details else "Sem fatores identificados",
        "risk": risk,
        "recommendation": rec,
        "reference": "ASE/EACVI Aortic Stenosis Grading 2024",
    }


def calculate_applicable_scores(card) -> list[dict]:
    """Given a CartaoClinico, calculate all applicable scores."""
    results = []
    if card is None:
        return results

    comorbidades = get_comorbidades(card)
    idade = get_idade(card)
    sexo = get_sexo(card)

    # Disfunção Diastólica
    if has_condition(comorbidades, ['disfunção diastólica', 'diastole', 'relaxamento', 'pressão de enchimento']):
        results.append(compute_disfuncao_diastolica())  # TODO: extrair parâmetros do card

    # TAPSE
    if has_condition(comorbidades, ['tapse', 'função vd', 'ventrículo direito']):
        results.append(compute_tapse_classificacao())  # TODO: extrair parâmetros do card

    # Gravidade da Estenose Aórtica
    if has_condition(comorbidades, ['estenose aórtica', 'estenose aortica', 'ea', 'aortic stenosis']):
        results.append(compute_gravidade_ea())  # TODO: extrair parâmetros do card


    return results


def format_scores_markdown(scores: list[dict]) -> str:
    if not scores:
        return ""
    lines = ["### Scores Calculados Automaticamente\n"]
    for s in scores:
        lines.append(f"**{s['name']}: {s['score']}** — {s['risk']}")
        lines.append(f"  {s['details']}")
        lines.append(f"  *{s['recommendation']}*")
        lines.append(f"  📚 *{s.get('reference', '')}*\n")
    return '\n'.join(lines)
