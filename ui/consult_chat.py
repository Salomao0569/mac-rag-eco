"""Modo Consulta — chat contextual pos-pipeline (RAG com contexto do paciente)."""

import streamlit as st

from core.consultation import build_consultant
from ui.citations import render_citations
from ui.consult_pipeline import get_card_field


def render_chat_tab(card):
    """Tab de chat contextual com o consultor."""
    st.caption("Pergunte qualquer coisa — o consultor já conhece o paciente.")

    # Sugestões contextuais
    if not st.session_state.consult_messages:
        suggestions = []
        comorbs = get_card_field(card, "comorbidades", [])
        if comorbs:
            suggestions.append(f"Metas terapêuticas para {', '.join(comorbs[:3])}?")
        hipoteses = get_card_field(card, "hipoteses_diagnosticas", [])
        if hipoteses:
            suggestions.append(f"Tratamento de {hipoteses[0]} segundo SBC?")
        meds = get_card_field(card, "medicacoes_atuais", [])
        if meds:
            suggestions.append("Alguma interação medicamentosa?")
        suggestions.append("Quais exames solicitar?")

        cols = st.columns(2)
        for i, sug in enumerate(suggestions[:4]):
            with cols[i % 2]:
                if st.button(sug, key=f"sug_{i}", use_container_width=True):
                    st.session_state.consult_messages.append({"role": "user", "content": sug})

    # Chat history
    for msg in st.session_state.consult_messages:
        avatar = "🫀" if msg["role"] == "assistant" else "👨‍⚕️"
        with st.chat_message(msg["role"], avatar=avatar):
            content = msg["content"]
            if msg["role"] == "assistant":
                content = render_citations(content)
            st.markdown(content, unsafe_allow_html=True)

    # Input
    if consult_prompt := st.chat_input("Pergunta sobre este paciente..."):
        st.session_state.consult_messages.append({"role": "user", "content": consult_prompt})
        with st.chat_message("user", avatar="👨‍⚕️"):
            st.markdown(consult_prompt)

    # Generate response
    if st.session_state.consult_messages and st.session_state.consult_messages[-1]["role"] == "user":
        query = st.session_state.consult_messages[-1]["content"]

        with st.chat_message("assistant", avatar="🫀"):
            consultant = build_consultant(
                patient_card=card,
                session_id=st.session_state.session_id,
            )
            placeholder = st.empty()
            full = ""

            try:
                with st.spinner("🧠 Consultor RAG analisando com contexto do paciente..."):
                    stream = consultant.run(query, stream=True)
                    for chunk in stream:
                        event = getattr(chunk, "event", "")
                        if event == "RunContent" and chunk.content:
                            full += chunk.content
                            placeholder.markdown(full + "▌", unsafe_allow_html=True)
            except Exception as e:
                full = f"⚠️ Erro: {e}"

            rendered = render_citations(full)
            placeholder.markdown(rendered, unsafe_allow_html=True)
            st.session_state.consult_messages.append({"role": "assistant", "content": full})
