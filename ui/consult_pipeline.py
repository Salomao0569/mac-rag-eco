"""Modo Consulta — exibição dos resultados do pipeline (SOAP, cartão, transcrição)."""

import streamlit as st

from core.consultation import generate_soap
from core.patient_letter import generate_patient_letter
from core.schemas import CartaoClinico
from core.auto_scores import format_scores_markdown
from core.alerts import format_alerts_markdown
from core.exam_requests import generate_exam_requests, format_exam_requests_markdown, format_exam_requests_text


def get_card_field(card, field, default=None):
    """Acessa campo do cartão (suporta Pydantic e dict)."""
    if isinstance(card, CartaoClinico):
        return getattr(card, field, default)
    return card.get(field, default)


def extract_patient_header(card, include_peso=False) -> list[str]:
    """Extrai partes do header do paciente (idade, sexo, peso) de Pydantic ou dict.

    Returns:
        Lista de strings como ["65a", "Masculino", "80kg"].
    """
    is_pydantic = isinstance(card, CartaoClinico)
    if is_pydantic:
        pac = card.paciente
        parts = []
        if pac.idade:
            parts.append(f"{pac.idade}a")
        if pac.sexo:
            parts.append(pac.sexo)
        if include_peso and pac.peso:
            parts.append(f"{pac.peso}kg")
    else:
        pac = card.get("paciente", {})
        parts = []
        if pac.get("idade"):
            parts.append(f"{pac['idade']}a")
        if pac.get("sexo"):
            parts.append(pac["sexo"])
        if include_peso and pac.get("peso"):
            parts.append(f"{pac['peso']}kg")
    return parts


def render_soap_tab(card):
    """Tab da nota SOAP."""
    if st.session_state.soap_note:
        st.markdown(st.session_state.soap_note)
    else:
        st.info("Nota SOAP não foi gerada. Clique abaixo para gerar.")
        if st.button("📝 Gerar SOAP agora", type="primary"):
            with st.spinner("📝 Gerando nota SOAP..."):
                try:
                    soap = generate_soap(
                        st.session_state.diarized_text,
                        card,
                    )
                    st.session_state.soap_note = soap
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao gerar SOAP: {e}")


def render_card_tab(card):
    """Tab do cartão clínico."""
    is_pydantic = isinstance(card, CartaoClinico)
    has_error = not is_pydantic and card.get("_parse_error")

    if has_error:
        st.warning("Não foi possível parsear o cartão como JSON. Dados brutos:")
        st.code(card.get("_raw", ""), language="json")
        return

    # Dados do paciente
    header_parts = extract_patient_header(card, include_peso=True)
    st.markdown(f"### 🏥 {' · '.join(header_parts)}" if header_parts else "### 🏥 Paciente")

    col1, col2 = st.columns(2)
    with col1:
        qp = get_card_field(card, "queixa_principal")
        if qp:
            st.markdown(f"**Queixa principal:** {qp}")
        hda = get_card_field(card, "hda")
        if hda:
            st.markdown(f"**HDA:** {hda}")
        comorbs = get_card_field(card, "comorbidades", [])
        if comorbs:
            st.markdown(f"**Comorbidades:** {', '.join(comorbs)}")
        alergias = get_card_field(card, "alergias", [])
        if alergias:
            st.markdown(f"**Alergias:** {', '.join(alergias)}")
        habitos = get_card_field(card, "habitos", [])
        if habitos:
            st.markdown(f"**Hábitos:** {', '.join(habitos)}")

    with col2:
        meds = get_card_field(card, "medicacoes_atuais", [])
        if meds:
            st.markdown("**Medicações atuais:**")
            for med in meds:
                st.markdown(f"- {med}")
        meds_prev = get_card_field(card, "medicacoes_previas", [])
        if meds_prev:
            st.markdown("**Medicações prévias:**")
            for med in meds_prev:
                st.markdown(f"- {med}")

    ef = get_card_field(card, "exame_fisico")
    if ef:
        if is_pydantic:
            has_ef = getattr(ef, "pa", None) or getattr(ef, "fc", None) or getattr(ef, "peso", None) or getattr(ef, "outros", None)
        else:
            has_ef = any(ef.get(k) for k in ["pa", "fc", "peso", "outros"])

        if has_ef:
            st.markdown("---")
            st.markdown("**Exame físico:**")
            ef_parts = []
            pa = getattr(ef, "pa", None) if is_pydantic else ef.get("pa")
            fc = getattr(ef, "fc", None) if is_pydantic else ef.get("fc")
            peso = getattr(ef, "peso", None) if is_pydantic else ef.get("peso")
            outros = getattr(ef, "outros", []) if is_pydantic else ef.get("outros", [])
            if pa:
                ef_parts.append(f"PA {pa}")
            if fc:
                ef_parts.append(f"FC {fc}")
            if peso:
                ef_parts.append(f"Peso {peso}")
            st.markdown(" · ".join(ef_parts))
            if outros:
                for item in outros:
                    st.markdown(f"- {item}")

    hipoteses = get_card_field(card, "hipoteses_diagnosticas", [])
    if hipoteses:
        st.markdown(f"**Hipóteses:** {', '.join(hipoteses)}")
    condutas = get_card_field(card, "condutas_discutidas", [])
    if condutas:
        st.markdown(f"**Condutas:** {', '.join(condutas)}")
    pendencias = get_card_field(card, "pendencias", [])
    if pendencias:
        st.markdown(f"**Pendências:** {', '.join(pendencias)}")

    # Auto-calculated scores
    auto_scores = st.session_state.get("auto_scores", [])
    if auto_scores:
        st.markdown("---")
        st.markdown(format_scores_markdown(auto_scores))

    # Clinical decision support alerts
    clinical_alerts = st.session_state.get("clinical_alerts", [])
    if clinical_alerts:
        st.markdown("---")
        st.markdown(format_alerts_markdown(clinical_alerts))

    # JSON raw
    with st.expander("🔍 JSON completo"):
        if is_pydantic:
            st.json(card.model_dump())
        else:
            st.json(card)


def render_patient_letter_tab(card):
    """Tab da carta ao paciente."""
    if not st.session_state.soap_note:
        st.info("Gere a nota SOAP primeiro para criar a carta ao paciente.")
        return

    if st.session_state.patient_letter:
        st.markdown(st.session_state.patient_letter)
        st.download_button(
            label="Baixar carta",
            data=st.session_state.patient_letter,
            file_name="carta_paciente.txt",
            mime="text/plain",
        )
        if st.button("Regenerar carta"):
            st.session_state.patient_letter = None
            st.rerun()
    else:
        st.markdown("Gere uma carta em linguagem simples para entregar ao paciente.")
        if st.button("Gerar Carta ao Paciente", type="primary"):
            with st.spinner("Gerando carta ao paciente..."):
                try:
                    letter = generate_patient_letter(
                        st.session_state.soap_note,
                        card,
                    )
                    st.session_state.patient_letter = letter
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao gerar carta: {e}")


def render_exam_requests_tab(card):
    """Tab de requisição de exames baseada nas diretrizes."""
    soap_plan = st.session_state.get("soap_note", "") or ""
    requests = generate_exam_requests(card=card, soap_plan=soap_plan)

    if requests:
        st.markdown(format_exam_requests_markdown(requests))

        st.markdown("---")
        plain_text = format_exam_requests_text(requests)
        st.markdown("**Copiar para o sistema:**")
        st.code(plain_text, language=None)
    else:
        st.info("Nenhum exame sugerido automaticamente. Verifique se as hipóteses diagnósticas foram extraídas no cartão clínico.")


def render_transcript_tab():
    """Tab da transcrição diarizada."""
    if st.session_state.transcription_info:
        info = st.session_state.transcription_info
        st.caption(f"🎤 {info['method']} · {info.get('details', '')}")

    if st.session_state.diarized_text:
        st.markdown("#### Transcrição Diarizada")
        lines = st.session_state.diarized_text.split("\n")
        for line in lines:
            if line.strip().startswith("[MÉDICO"):
                st.markdown(f"🩺 **{line.strip()}**")
            elif line.strip().startswith("[PACIENTE"):
                st.markdown(f"🗣️ {line.strip()}")
            elif line.strip():
                st.markdown(line.strip())
