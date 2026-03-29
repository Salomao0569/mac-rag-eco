"""Clinical Decision Support Alerts for Ecocardiografia.
Gerado pelo RAG Factory.
"""

import logging
from .card_helpers import get_list, get_idade, has_condition

logger = logging.getLogger(__name__)


def generate_alerts(card, condutas_discutidas: list[str] = None) -> list[dict]:
    """Cross-reference CartaoClinico against clinical rules.
    Returns list of alerts.
    """
    if card is None:
        return []

    alerts = []
    comorbidades = get_list(card, 'comorbidades')
    medicacoes = get_list(card, 'medicacoes_atuais')
    condutas = condutas_discutidas or get_list(card, 'condutas_discutidas')
    idade = get_idade(card)

    comorbidades_lower = [c.lower() for c in comorbidades]
    medicacoes_lower = [m.lower() for m in medicacoes]
    condutas_lower = [c.lower() for c in condutas]

    # ── Rule 1: FEVE reduzida — IC com FE reduzida ──
    if feve is not None and feve < 40:
        alerts.append({
            'level': 'warning',
            'title': 'FEVE reduzida — IC com FE reduzida',
            'message': 'FEVE < 40%. Avaliar IC com FE reduzida. Considerar strain global, avaliação da sincronia e viabilidade miocárdica.',
            'reference': 'ASE/EACVI Chamber Quantification 2023'
        })

    # ── Rule 2: FEVE levemente reduzida (40-49%) ──
    if feve is not None and feve <= 49:
        alerts.append({
            'level': 'info',
            'title': 'FEVE levemente reduzida (40-49%)',
            'message': 'FEVE na faixa de IC com FE levemente reduzida (ICFElr). Considerar strain global para detecção de disfunção subclínica.',
            'reference': 'ESC IC 2023'
        })

    # ── Rule 3: Disfunção sistólica do VD ──
    if tapse is not None and tapse < 17:
        alerts.append({
            'level': 'warning',
            'title': 'Disfunção sistólica do VD',
            'message': 'TAPSE < 17 mm. Complementar avaliação com FAC, S\' do DTI, strain do VD e RIMP.',
            'reference': 'ASE Right Heart 2024'
        })

    # ── Rule 4: Hipertensão pulmonar estimada ──
    if psap is not None and psap > 40:
        alerts.append({
            'level': 'warning',
            'title': 'Hipertensão pulmonar estimada',
            'message': 'PSAP > 40 mmHg estimada ao eco. Correlacionar com contexto clínico. Considerar cateterismo direito para confirmação.',
            'reference': 'ESC Pulmonary Hypertension 2022'
        })

    # ── Rule 5: Átrio esquerdo dilatado ──
    if volume_ae is not None and volume_ae > 34:
        alerts.append({
            'level': 'info',
            'title': 'Átrio esquerdo dilatado',
            'message': 'Volume indexado do AE > 34 mL/m². Marcador de disfunção diastólica crônica e risco de FA. Correlacionar com E/e\' e velocidade de RT.',
            'reference': 'ASE/EACVI Chamber Quantification 2023'
        })

    # ── Rule 6: Pressões de enchimento do VE elevadas ──
    if e_e_prime is not None and e_e_prime > 14:
        alerts.append({
            'level': 'warning',
            'title': 'Pressões de enchimento do VE elevadas',
            'message': 'E/e\' médio > 14. Sugestivo de pressões de enchimento do VE elevadas. Correlacionar com volume do AE, velocidade de RT e strain do AE.',
            'reference': 'ASE/EACVI Diastolic Function 2016'
        })

    # ── Rule 7: Strain longitudinal global reduzido ──
    if strain_global is not None and strain_global > -16:
        alerts.append({
            'level': 'info',
            'title': 'Strain longitudinal global reduzido',
            'message': 'GLS menos negativo que -16%. Disfunção sistólica subclínica do VE, mesmo com FEVE preservada. Considerar contexto (cardiotoxicidade, HVE, miocardiopatia).',
            'reference': 'ASE Strain Imaging 2022'
        })


    logger.info(f"Generated {len(alerts)} clinical alerts")
    return alerts


def format_alerts_markdown(alerts: list[dict]) -> str:
    if not alerts:
        return ""
    lines = [f"### ⚠️ {len(alerts)} Alerta(s) Clínico(s)\n"]
    for a in alerts:
        level = a.get('level', 'info')
        icon = {'critical': '🔴', 'warning': '🟡'}.get(level, '🔵')
        lines.append(f"{icon} **{a['title']}**")
        lines.append(f"  {a['message']}")
        lines.append(f"  📚 *{a['reference']}*\n")
    return '\n'.join(lines)
