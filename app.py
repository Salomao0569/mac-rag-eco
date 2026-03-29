"""
MAC RAG Ecocardiografia — Dashboard Streamlit
Entrypoint slim: carrega .env, configura página, delega para módulos UI.
Gerado pelo RAG Factory.
"""

import os
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

from ui.styles import apply_styles
from ui.sidebar import render_sidebar
from ui.consult_mode import render_consult_mode
from ui.classic_mode import render_classic_mode
from ui.context_tab import render_context_mode

# ============================================================
# Page config
# ============================================================
st.set_page_config(
    page_title="MAC RAG Ecocardiografia",
    page_icon="💓",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_styles()

# ============================================================
# State
# ============================================================
defaults = {
    "messages": [],
    "session_id": "bio-" + os.urandom(4).hex(),
    "patient_card": None,
    "diarized_text": None,
    "consult_messages": [],
    "transcription_info": None,
    "soap_note": None,
    "clinical_alerts": [],
    "auto_scores": [],
    "patient_letter": None,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ============================================================
# Sidebar
# ============================================================
cfg = render_sidebar(is_team=False, is_consult=False)

is_team = "Time" in cfg["app_mode"]
is_consult = "Consulta" in cfg["app_mode"]

# ============================================================
# Tabs
# ============================================================
tab_chat, tab_context = st.tabs(["\U0001f4ac Chat", "\U0001f4da Referências"])

with tab_chat:
    if is_consult:
        render_consult_mode(cfg)
    else:
        render_classic_mode(cfg, is_team)

with tab_context:
    render_context_mode(cfg)
