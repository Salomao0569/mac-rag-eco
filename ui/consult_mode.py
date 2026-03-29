"""Modo Consulta — entry-point fino que delega para sub-módulos.

Sub-módulos:
  - consult_transcription: input de texto/áudio e processamento inicial
  - consult_pipeline: exibição de resultados (SOAP, cartão clínico, transcrição)
  - consult_chat: chat contextual pós-pipeline (RAG com contexto do paciente)
"""

import streamlit as st

from ui.consult_transcription import render_input_phase
from ui.consult_pipeline import render_soap_tab, render_card_tab, render_transcript_tab, render_patient_letter_tab, render_exam_requests_tab
from ui.consult_chat import render_chat_tab


def render_consult_mode(cfg: dict):
    """Renderiza todo o modo consulta."""
    if st.session_state.patient_card is None:
        render_input_phase(cfg)
    else:
        _render_consult_phase()


def _render_consult_phase():
    """Fase 2: Consulta processada — tabs SOAP/Cartão/Chat."""
    card = st.session_state.patient_card

    tab_chat, tab_soap, tab_card, tab_exams, tab_letter, tab_transcript = st.tabs(
        ["💬 Perguntar", "📝 SOAP", "📋 Cartão do Paciente", "🔬 Exames", "✉️ Carta ao Paciente", "🎙️ Transcrição"]
    )

    with tab_soap:
        render_soap_tab(card)

    with tab_card:
        render_card_tab(card)

    with tab_exams:
        render_exam_requests_tab(card)

    with tab_letter:
        render_patient_letter_tab(card)

    with tab_transcript:
        render_transcript_tab()

    with tab_chat:
        render_chat_tab(card)
