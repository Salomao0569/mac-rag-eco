"""Sidebar do dashboard — configurações e badges."""

import os
import streamlit as st

from core.config import MODELS_COORD, MODELS_AGENTS, MODELS_INFO, FONTES_UI, DIRETRIZES, DIRETRIZES_INTERNACIONAIS
from ui.consult_pipeline import extract_patient_header, get_card_field


def render_sidebar(is_team: bool, is_consult: bool) -> dict:
    """Renderiza sidebar e retorna configurações selecionadas.

    Returns:
        dict com keys: fonte_marker, model_coord, model_agents, model_single,
                       selected_method, is_text_input
    """
    cfg = {
        "fonte_marker": "",
        "model_coord": None,
        "model_agents": None,
        "model_single": None,
        "selected_method": None,
        "is_text_input": True,
    }

    with st.sidebar:
        st.markdown("### ⚙️ Configurações")
        app_mode = st.radio(
            "Modo",
            ["🧑‍⚕️ Agente Único", "👥 Time de Agentes", "🩺 Consulta"],
            index=0,
        )
        cfg["app_mode"] = app_mode

        # Derive flags from the NEW radio selection, not from stale params
        is_team = "Time" in app_mode
        is_consult = "Consulta" in app_mode

        st.markdown("---")

        if is_consult:
            _render_consult_sidebar(cfg)
        else:
            _render_classic_sidebar(cfg, is_team)

        _render_api_warnings(is_consult, cfg)
        _render_stats(is_consult, is_team)
        _render_clear_button(is_consult)

    return cfg


def _render_consult_sidebar(cfg: dict):
    """Sidebar específica do modo consulta."""
    from core.audio_transcriber import METHODS as AUDIO_METHODS

    st.markdown("### 🩺 Modo Consulta")
    st.caption("Envie áudio ou cole a transcrição. "
               "Os agentes identificam médico/paciente, extraem o contexto "
               "clínico, e respondem perguntas sabendo quem é o paciente.")

    st.markdown("### 🎤 Transcrição")
    selected_method = st.radio(
        "Método de entrada",
        ["📝 Texto (colar transcrição)"] + list(AUDIO_METHODS.keys()),
        index=0,
    )
    cfg["is_text_input"] = "Texto" in selected_method
    cfg["selected_method"] = selected_method

    if not cfg["is_text_input"]:
        audio_method = AUDIO_METHODS[selected_method]
        if audio_method == "gpt4o_audio":
            st.caption("🧠 GPT-4o ouve o áudio e já diariza — pula o Agente 1")
        elif audio_method == "realtime":
            st.caption("⚡ Streaming — mais caro, transcrição ao vivo")
        else:
            st.caption("🎙️ Batch — barato, transcreve no final")

    st.markdown("---")
    st.markdown("### 🤖 Pipeline")
    st.markdown(
        '<span class="badge b-consult">🎙️ Diarizador</span> '
        '<span class="badge b-consult">📋 Extrator</span> '
        '<span class="badge b-consult">📝 SOAP</span> '
        '<span class="badge b-rag">🧠 Consultor RAG</span>',
        unsafe_allow_html=True,
    )

    if st.session_state.get("patient_card"):
        st.markdown("---")
        st.markdown("### ✅ Paciente carregado")
        card = st.session_state.patient_card
        info = extract_patient_header(card)
        st.caption(" · ".join(info) if info else "Dados extraídos")
        comorbs = get_card_field(card, "comorbidades", [])
        if comorbs:
            st.caption(f"Comorbidades: {', '.join(comorbs)}")
        meds = get_card_field(card, "medicacoes_atuais", [])
        if meds:
            st.caption(f"Medicações: {', '.join(meds)}")


def _render_classic_sidebar(cfg: dict, is_team: bool):
    """Sidebar dos modos agente único / time."""
    st.markdown("### 🎯 Fonte")
    selected_fonte = st.radio("Selecione antes de perguntar", list(FONTES_UI.keys()), index=0)
    cfg["fonte_marker"] = FONTES_UI[selected_fonte]

    st.markdown("---")
    # Filter out separator entries (value=None) from model dicts
    coord_options = {k: v for k, v in MODELS_COORD.items() if v is not None}
    agent_options = {k: v for k, v in MODELS_AGENTS.items() if v is not None}

    if is_team:
        st.markdown("### 🤖 Modelos")
        coord_label = st.selectbox("Coordenador", list(coord_options.keys()), index=0)
        agents_label = st.selectbox("Agentes", list(agent_options.keys()), index=0)
        cfg["model_coord"] = coord_options[coord_label]
        cfg["model_agents"] = agent_options[agents_label]
        cfg["coord_label"] = coord_label
        cfg["agents_label"] = agents_label
        st.markdown("---")
        st.markdown("### 👥 Equipe")
        st.markdown(
            '<span class="badge b-rag">📗 RAG Diretrizes</span> '
            '<span class="badge b-pm">📙 PubMed</span> '
            '<span class="badge b-web">📘 Internet</span>',
            unsafe_allow_html=True,
        )
        st.caption(f"Coord: {coord_label.split(' (')[0]} → Agentes: {agents_label.split(' (')[0]}")
        _render_model_info(coord_options[coord_label], agents_label=agent_options[agents_label])
    else:
        st.markdown("### 🤖 Modelo")
        single_label = st.selectbox("Modelo", list(coord_options.keys()), index=0)
        cfg["model_single"] = coord_options[single_label]
        cfg["single_label"] = single_label
        _render_model_info(coord_options[single_label])
        st.markdown("---")
        st.markdown(
            '<span class="badge b-rag">rag</span> '
            '<span class="badge b-pm">pubmed</span> '
            '<span class="badge b-web">tavily</span> '
            '<span class="badge b-tool">Disfunção Diastólica</span> '
            '<span class="badge b-tool">Gravidade EA</span>',
            unsafe_allow_html=True,
        )


def _render_model_info(model_id: str, agents_label: str | None = None):
    """Mostra card discreto com info do modelo selecionado."""
    def _card(mid, label=""):
        info = MODELS_INFO.get(mid)
        if not info:
            return None
        price_in, price_out, ctx, notes = info
        ctx_str = f"{ctx // 1000}K" if ctx < 1_000_000 else f"{ctx // 1_000_000}M"
        if price_in == 0:
            price_html = '<span style="color:#4ade80">gratuito (local)</span>'
        else:
            price_html = (
                f'<span style="color:#94a3b8">in</span> ${price_in:.2f} · '
                f'<span style="color:#94a3b8">out</span> ${price_out:.2f}'
                f'<span style="color:#64748b"> /1M tk</span>'
            )
        prefix = f'<span style="color:#94a3b8">{label}</span>' if label else ""
        return (
            f'<div style="font-size:12px; line-height:1.6; color:#cbd5e1; '
            f'padding:4px 8px; background:#1e293b; border-radius:6px; '
            f'border-left:3px solid #334155; margin:4px 0">'
            f'{prefix}'
            f'<span style="color:#64748b">ctx</span> {ctx_str} · {price_html}<br>'
            f'<span style="color:#94a3b8">{notes}</span>'
            f'</div>'
        )

    main = _card(model_id)
    if main:
        st.markdown(main, unsafe_allow_html=True)
    if agents_label:
        agent = _card(agents_label, label="Agentes: ")
        if agent:
            st.markdown(agent, unsafe_allow_html=True)


def _render_api_warnings(is_consult: bool, cfg: dict):
    """Avisos de API keys ausentes."""
    if not os.environ.get("TAVILY_API_KEY"):
        st.warning("⚠️ TAVILY_API_KEY não configurada")

    # OpenRouter key warning
    selected_models = [cfg.get("model_coord", ""), cfg.get("model_agents", ""), cfg.get("model_single", "")]
    if any(m and m.startswith("openrouter/") for m in selected_models) and not os.environ.get("OPENROUTER_API_KEY"):
        st.error("🔑 OPENROUTER_API_KEY necessária. Adicione ao .env")

    # DashScope key warning
    if any(m and m.startswith("dashscope/") for m in selected_models) and not os.environ.get("DASHSCOPE_API_KEY"):
        st.error("🔑 DASHSCOPE_API_KEY necessária. Adicione ao .env")

    if not os.environ.get("OPENAI_API_KEY"):
        openai_needed = False
        if is_consult and not cfg["is_text_input"]:
            openai_needed = True
        elif not is_consult:
            label = cfg.get("coord_label", "") or cfg.get("agents_label", "") or cfg.get("single_label", "")
            if "OpenAI" in label:
                openai_needed = True
        if openai_needed:
            st.error('🔑 OPENAI_API_KEY necessária. Adicione ao .env')
    elif is_consult and not cfg["is_text_input"]:
        st.success("🔑 OpenAI API key configurada")


def _render_stats(is_consult: bool, is_team: bool):
    """Stats cards na sidebar."""
    st.markdown("---")
    total_dirs = sum(len(v) for v in DIRETRIZES.values()) + sum(len(v) for v in DIRETRIZES_INTERNACIONAIS.values())
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="stat"><div class="n">{total_dirs}</div><div class="l">Diretrizes</div></div>', unsafe_allow_html=True)
    with c2:
        try:
            from core.config import get_collection
            chunk_count = f"{get_collection().count():,}".replace(",", ".")
        except Exception:
            chunk_count = "—"
        st.markdown(f'<div class="stat"><div class="n">{chunk_count}</div><div class="l">Chunks</div></div>', unsafe_allow_html=True)
    with c3:
        if is_consult:
            n, label = "4", "Agentes"
        elif is_team:
            n, label = "3+1", "Agentes"
        else:
            n, label = "1", "Agente"
        st.markdown(f'<div class="stat"><div class="n">{n}</div><div class="l">{label}</div></div>', unsafe_allow_html=True)


def _render_clear_button(is_consult: bool):
    """Botão limpar conversa/consulta."""
    st.markdown("---")
    clear_label = "🗑️ Limpar consulta" if is_consult else "🗑️ Limpar conversa"
    if st.button(clear_label, use_container_width=True):
        st.session_state.messages = []
        st.session_state.consult_messages = []
        st.session_state.patient_card = None
        st.session_state.diarized_text = None
        st.session_state.soap_note = None
        st.session_state.auto_scores = []
        st.session_state.clinical_alerts = []
        st.session_state.transcription_info = None
        st.session_state.session_id = "bio-" + os.urandom(4).hex()
        st.rerun()
