"""Modos clássicos — Agente Único e Time de Agentes."""

import streamlit as st

from core.config import resolve_team_mode
from core.team_builder import build_team, build_single_agent
from ui.citations import render_citations

EXAMPLES = [
    "Valores normais de FEVE pelo Simpson?",
    "Paciente com E/e' 16, LAVI 38. Disfunção diastólica?",
    "Critérios de estenose aórtica grave — ASE 2024",
    "Compare strain global: ASE 2022 vs EACVI 2024",
    "TAPSE 14mm, S' 8cm/s. Disfunção de VD?",
    "Quando pedir eco de estresse vs cintilografia?",
]


def render_classic_mode(cfg: dict, is_team: bool):
    """Renderiza modos agente único / time."""
    # Examples
    if not st.session_state.messages:
        st.markdown("#### 💡 Exemplos")
        cols = st.columns(3)
        for i, ex in enumerate(EXAMPLES):
            with cols[i % 3]:
                if st.button(ex, key=f"ex_{i}", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": ex})

    # History
    for msg in st.session_state.messages:
        avatar = "🫀" if msg["role"] == "assistant" else "👨‍⚕️"
        with st.chat_message(msg["role"], avatar=avatar):
            content = msg["content"]
            if msg["role"] == "assistant":
                content = render_citations(content)
            st.markdown(content, unsafe_allow_html=True)

    # Input
    if prompt := st.chat_input("Pergunta clínica..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👨‍⚕️"):
            st.markdown(prompt)

    # Generate
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        query = st.session_state.messages[-1]["content"]
        fonte_marker = cfg["fonte_marker"]

        if fonte_marker:
            query = f"{fonte_marker} {query}"

        team_mode = resolve_team_mode(fonte_marker)

        with st.chat_message("assistant", avatar="🫀"):
            if is_team:
                runner = build_team(
                    cfg["model_coord"], cfg["model_agents"],
                    st.session_state.session_id, team_mode,
                )
                spins = {
                    "coordinate": "🧠 Coordenador analisando...",
                    "route": "🔀 Roteando...",
                    "broadcast": "📡 Todos os agentes...",
                }
                spin = spins.get(team_mode.value, "👥 Equipe...")
            else:
                runner = build_single_agent(cfg["model_single"], st.session_state.session_id)
                spin = "🧠 Processando..."

            placeholder = st.empty()
            full = ""

            # Build conversation context from recent messages
            recent_msgs = st.session_state.messages[-6:]  # Last 3 exchanges (user+assistant)
            if len(recent_msgs) > 1:  # There's prior context
                context_parts = []
                for msg in recent_msgs[:-1]:  # All except current (already in query)
                    role = "Médico" if msg["role"] == "user" else "Assistente"
                    content = msg["content"][:300]  # Truncate long responses
                    context_parts.append(f"[{role}]: {content}")
                context = "\n".join(context_parts)
                contextualized_query = f"[CONTEXTO DA CONVERSA ANTERIOR]\n{context}\n\n[PERGUNTA ATUAL]\n{query}"
            else:
                contextualized_query = query

            try:
                with st.spinner(spin):
                    stream = runner.run(contextualized_query, stream=True)
                    for chunk in stream:
                        event = getattr(chunk, "event", "")
                        agent_name = getattr(chunk, "agent_name", "") or ""

                        if is_team:
                            is_coord = event == "TeamRunContent" or (event == "RunContent" and not agent_name)
                        else:
                            is_coord = event == "RunContent"

                        if is_coord and chunk.content:
                            full += chunk.content
                            placeholder.markdown(full + "▌", unsafe_allow_html=True)
            except Exception as e:
                full = f"⚠️ Erro ao processar: {e}"

            rendered = render_citations(full)
            placeholder.markdown(rendered, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": full})
