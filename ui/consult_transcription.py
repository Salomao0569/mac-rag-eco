"""Modo Consulta — fase de input: texto colado ou audio (gravacao/upload)."""

import os
import streamlit as st

from core.consultation import process_consultation


def render_input_phase(cfg: dict):
    """Fase 1: Input da transcrição."""
    st.markdown("#### 🩺 Entrada da Consulta")

    if cfg["is_text_input"]:
        _render_text_input()
    else:
        _render_audio_input(cfg)


def _render_text_input():
    """Input via texto colado."""
    st.caption("Cole a transcrição abaixo. Os agentes vão identificar médico/paciente e extrair o contexto clínico.")

    col_ex, col_spacer = st.columns([1, 3])
    with col_ex:
        load_example = st.button("📄 Carregar exemplo", use_container_width=True)

    example_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "example_consultation.txt")
    default_text = ""
    if load_example and os.path.exists(example_path):
        with open(example_path, "r", encoding="utf-8") as f:
            default_text = f.read()

    transcript = st.text_area(
        "Transcrição bruta",
        value=default_text,
        height=300,
        placeholder="Cole aqui a transcrição da consulta (texto corrido, sem marcação de quem fala)...",
    )

    if st.button("🚀 Processar Consulta", type="primary", use_container_width=True):
        if not transcript.strip():
            st.warning("Cole uma transcrição primeiro.")
        else:
            with st.spinner("🎙️ Diarizando → 📋 Extraindo → 📝 Gerando SOAP..."):
                try:
                    diarized, card, soap, auto_scores, clinical_alerts = process_consultation(transcript.strip())
                    st.session_state.diarized_text = diarized
                    st.session_state.patient_card = card
                    st.session_state.soap_note = soap
                    st.session_state.auto_scores = auto_scores
                    st.session_state.clinical_alerts = clinical_alerts
                    st.session_state.consult_messages = []
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao processar consulta: {e}")


def _render_audio_input(cfg: dict):
    """Input via áudio (gravação ou upload)."""
    from core.audio_transcriber import METHODS as AUDIO_METHODS, transcribe

    selected_method = cfg["selected_method"]
    audio_method = AUDIO_METHODS[selected_method]
    st.caption(f"Método: **{selected_method}**")

    tab_record, tab_upload = st.tabs(["🔴 Gravar", "📁 Upload"])

    audio_bytes = None
    filename = "recording.wav"

    with tab_record:
        st.caption("Clique para gravar a consulta pelo microfone.")
        recorded = st.audio_input("Gravar consulta")
        if recorded:
            audio_bytes = recorded.read()
            filename = "recording.wav"
            st.audio(recorded)
            st.caption(f"📊 {len(audio_bytes) / 1024:.0f} KB capturados")

    with tab_upload:
        uploaded_audio = st.file_uploader(
            "Arquivo de áudio",
            type=["mp3", "wav", "m4a", "webm", "mp4", "ogg", "mpeg", "mpga"],
            help="Formatos: mp3, wav, m4a, webm, ogg. Máximo 25MB para Whisper.",
        )
        if uploaded_audio:
            audio_bytes = uploaded_audio.read()
            filename = uploaded_audio.name
            st.audio(uploaded_audio)

    if audio_bytes and st.button("🚀 Transcrever e Processar", type="primary", use_container_width=True):
        # Passo 1: Transcrever
        with st.spinner(f"🎤 Transcrevendo via {selected_method.split('(')[0].strip()}..."):
            try:
                result = transcribe(audio_bytes, audio_method, filename)
                raw_text = result["text"]
                already_diarized = result.get("already_diarized", False)
                st.success(f"✅ Transcrição completa · {result['details']}")
            except Exception as e:
                st.error(f"Erro na transcrição: {e}")
                raw_text = None

        # Passo 2: Diarizar + Extrair + SOAP
        if raw_text:
            if already_diarized:
                spinner_msg = "📋 Agente 2: Extraindo contexto clínico (diarização já feita pelo GPT-4o)..."
            else:
                spinner_msg = "🎙️ Agente 1: Diarizando + 📋 Agente 2: Extraindo contexto..."

            with st.spinner(spinner_msg):
                try:
                    diarized, card, soap, auto_scores, clinical_alerts = process_consultation(
                        raw_text,
                        already_diarized=already_diarized,
                    )
                    st.session_state.diarized_text = diarized
                    st.session_state.patient_card = card
                    st.session_state.soap_note = soap
                    st.session_state.auto_scores = auto_scores
                    st.session_state.clinical_alerts = clinical_alerts
                    st.session_state.consult_messages = []
                    st.session_state.transcription_info = result
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao processar consulta: {e}")
