"""CSS e header do dashboard."""

import streamlit as st

MAIN_CSS = """
<style>
    /* Layout */
    .main .block-container { padding-top: 1.5rem; max-width: 1200px; }

    /* Header */
    .hdr { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
           padding: 1.2rem 1.8rem; border-radius: 12px; margin-bottom: 1rem; color: white; }
    .hdr h1 { color: white !important; margin: 0 !important; font-size: 1.7rem !important; }
    .hdr p  { color: #a0aec0 !important; margin: 0.2rem 0 0 0 !important; font-size: 0.85rem !important; }

    /* Sidebar badges */
    .badge  { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 10px; font-size: 0.72rem; margin: 0.08rem; }
    .b-rag  { background: #dcfce7; color: #166534; }
    .b-pm   { background: #fef3c7; color: #92400e; }
    .b-web  { background: #dbeafe; color: #1e40af; }
    .b-tool { background: #f1f5f9; color: #475569; }
    .b-consult { background: #ede9fe; color: #5b21b6; }

    /* Sidebar stats */
    .stat    { background: #f8fafc; border-radius: 8px; padding: 0.5rem; text-align: center; }
    .stat .n { font-size: 1.2rem; font-weight: 700; color: #1e40af; }
    .stat .l { font-size: 0.6rem; color: #94a3b8; text-transform: uppercase; }

    /* Patient card */
    .patient-card {
        background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
        border: 1px solid #bbf7d0;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin: 0.5rem 0;
    }
    .patient-card h4 { margin: 0 0 0.5rem 0; color: #166534; }
    .patient-card .field { font-size: 0.85rem; margin: 0.2rem 0; }
    .patient-card .label { font-weight: 600; color: #15803d; }

    /* Citation badges — estilo OpenEvidence */
    .cite-badge {
        display: inline-flex;
        align-items: center;
        gap: 3px;
        background: rgba(228, 100, 61, 0.10);
        color: #c2410c;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 2px 10px;
        border-radius: 9999px;
        cursor: pointer;
        position: relative;
        margin: 0 3px;
        vertical-align: middle;
        line-height: 1.5;
        transition: background-color 0.15s ease;
        white-space: nowrap;
        border: 1px solid rgba(228, 100, 61, 0.18);
    }
    .cite-badge:hover {
        background: rgba(228, 100, 61, 0.22);
    }
    .cite-tooltip {
        display: none !important;
        position: absolute;
        bottom: calc(100% + 10px);
        left: 50%;
        transform: translateX(-50%);
        background: #1e1e2e;
        color: #e2e8f0;
        padding: 12px 16px;
        border-radius: 10px;
        font-size: 0.78rem;
        font-weight: 400;
        line-height: 1.6;
        min-width: 300px;
        max-width: 420px;
        z-index: 9999;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
        white-space: normal;
        pointer-events: none;
    }
    .cite-badge:hover > .cite-tooltip {
        display: block !important;
    }
    .cite-tooltip::after {
        content: '';
        position: absolute;
        top: 100%;
        left: 50%;
        transform: translateX(-50%);
        border: 7px solid transparent;
        border-top-color: #1e1e2e;
    }
    .cite-line {
        display: block;
        padding: 4px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        color: #cbd5e1;
    }
    .cite-line:last-child {
        border-bottom: none;
    }
</style>
"""


def apply_styles():
    """Aplica CSS + header do dashboard."""
    st.markdown(MAIN_CSS, unsafe_allow_html=True)
    st.markdown(
        '<div class="hdr">'
        "<h1>💓 ECO RAG — Ecocardiografia</h1>"
        "<p>Multi-Agent · Diretrizes DIC-SBC + ASE + EACVI + BSE · PubMed + Internet · Consulta Contextual</p>"
        "</div>",
        unsafe_allow_html=True,
    )
