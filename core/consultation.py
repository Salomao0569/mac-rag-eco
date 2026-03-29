"""
Módulo de Consulta — 4 agentes que realmente raciocinam.

Agente 1 (Diarizador): transcrição bruta → identifica [MÉDICO] vs [PACIENTE]
Agente 2 (Extrator):   transcrição diarizada → cartão clínico estruturado
Agente 3 (SOAP):       transcrição + cartão → nota SOAP estruturada
Agente 4 (Consultor):  pergunta + cartão → RAG contextualizado
"""

import json
import logging
from agno.agent import Agent
from agno.db.sqlite import SqliteDb

from .config import (
    DEFAULT_COORD_MODEL,
    DEFAULT_AGENT_MODEL,
    MEMORY_DB,
    load_coordinator_prompt,
    build_model,
)
from .registry import load_prompt, get_all_tools
from .schemas import CartaoClinico
from .auto_scores import calculate_applicable_scores
from .alerts import generate_alerts


def _serialize_card(patient_card: CartaoClinico | dict) -> str:
    """Serializa CartaoClinico (Pydantic) ou dict para JSON string."""
    if isinstance(patient_card, CartaoClinico):
        return patient_card.model_dump_json(indent=2)
    return json.dumps(patient_card, ensure_ascii=False, indent=2)

logger = logging.getLogger(__name__)


# ============================================================
# Agente 1 — Diarizador
# ============================================================

def build_diarizer(model_id=DEFAULT_AGENT_MODEL):
    return Agent(
        name="Diarizador",
        model=build_model(model_id),
        instructions=load_prompt("diarizer"),
        markdown=False,
    )


# ============================================================
# Agente 2 — Extrator de Contexto Clínico
# ============================================================

def build_extractor(model_id=DEFAULT_COORD_MODEL):
    return Agent(
        name="Extrator Clínico",
        model=build_model(model_id),
        instructions=load_prompt("extractor"),
        markdown=False,
    )


# ============================================================
# Agente 3 — Nota SOAP
# ============================================================

def build_soap_agent(model_id=DEFAULT_COORD_MODEL):
    return Agent(
        name="SOAP",
        model=build_model(model_id),
        instructions=load_prompt("soap"),
        markdown=True,
    )


def generate_soap(
    diarized_text: str,
    patient_card: CartaoClinico | dict,
    model_id=DEFAULT_COORD_MODEL,
) -> str:
    """Gera nota SOAP combinando transcrição + cartão."""
    agent = build_soap_agent(model_id)

    card_json = _serialize_card(patient_card)

    prompt = (
        f"## Transcrição Diarizada:\n\n{diarized_text}\n\n"
        f"## Cartão Clínico Extraído:\n\n```json\n{card_json}\n```\n\n"
        "Gere a nota SOAP completa."
    )

    response = agent.run(prompt)
    return response.content


# ============================================================
# Agente 4 — Consultor RAG Contextual
# ============================================================

def _build_contextual_prompt(patient_card: CartaoClinico | dict) -> str:
    """Constrói prompt do consultor com o cartão do paciente injetado."""
    base = load_coordinator_prompt()

    card_json = _serialize_card(patient_card)

    context_section = f"""

## CONTEXTO DO PACIENTE (extraído da consulta em andamento)

```json
{card_json}
```

## Regras de contexto:
- SEMPRE considere os dados do paciente ao buscar nas ferramentas
- Ao buscar no RAG, ENRIQUEÇA a query com dados relevantes do paciente
  Ex: se perguntam "meta de LDL" e o paciente tem DM + DRC → busque
  "meta LDL muito alto risco cardiovascular diabetes doença renal"
- Ao calcular escores (RCRI, CHA₂DS₂-VASc), PREENCHA automaticamente
  os campos com os dados do cartão — não peça ao médico repetir
- Se o paciente tem dados que mudam a conduta (ex: alergia, gestação,
  insuficiência renal), SEMPRE mencione na resposta
- Cite explicitamente quando um dado do paciente influencia a recomendação
"""
    return base + context_section


def build_consultant(patient_card: CartaoClinico | dict, model_id=DEFAULT_COORD_MODEL, session_id="consult"):
    """Consultor RAG que conhece o paciente."""
    return Agent(
        name="Consultor Cardiológico",
        model=build_model(model_id),
        tools=get_all_tools(),
        instructions=_build_contextual_prompt(patient_card),
        db=SqliteDb(db_file=MEMORY_DB),
        enable_agentic_memory=True,
        update_memory_on_run=True,
        add_history_to_context=True,
        num_history_runs=5,
        session_id=session_id,
        user_id="biocardio",
        markdown=True,
    )


# ============================================================
# Pipeline completo
# ============================================================

def process_consultation(
    raw_transcript: str,
    already_diarized: bool = False,
    model_coord=DEFAULT_COORD_MODEL,
    model_agents=DEFAULT_AGENT_MODEL,
) -> tuple[str, CartaoClinico, str | None, list[dict], list[dict]]:
    """
    Processa transcrição → diarização → cartão clínico → scores → alertas → nota SOAP.

    Returns:
        (transcrição_diarizada, CartaoClinico validado, nota_soap ou None, auto_scores, clinical_alerts)
    """
    # Passo 1: Diarizar
    if already_diarized:
        diarized_text = raw_transcript
    else:
        logger.info("Agente 1: Diarizando...")
        diarizer = build_diarizer(model_agents)
        diarized_response = diarizer.run(raw_transcript)
        diarized_text = diarized_response.content

    # Passo 2: Extrair contexto clínico → CartaoClinico validado
    logger.info("Agente 2: Extraindo cartão clínico...")
    extractor = build_extractor(model_coord)
    card_response = extractor.run(diarized_text)
    patient_card = CartaoClinico.from_raw(card_response.content)

    # Passo 2.1: Auto-calculate applicable clinical scores
    auto_scores = calculate_applicable_scores(patient_card)
    if auto_scores:
        logger.info("Scores calculados: %s", [s['name'] for s in auto_scores])

    # Passo 2.2: Generate clinical decision support alerts
    clinical_alerts = generate_alerts(patient_card)
    if clinical_alerts:
        logger.info("Alertas clínicos gerados: %d", len(clinical_alerts))

    # Passo 3: Gerar nota SOAP
    soap_note = None
    try:
        logger.info("Agente 3: Gerando SOAP...")
        soap_note = generate_soap(diarized_text, patient_card, model_coord)
    except Exception as e:
        logger.warning("Falha ao gerar SOAP: %s", e)

    return diarized_text, patient_card, soap_note, auto_scores, clinical_alerts
