"""Aba Referências — diretrizes indexadas + catálogo de LLMs com preços."""

import streamlit as st
from collections import defaultdict

from core.config import MODELS_INFO, DIRETRIZES, DIRETRIZES_INTERNACIONAIS


# ── Society grouping helpers ─────────────────────────────────────────

_SOCIETY_GROUP = {
    "SBC": "SBC",
    "ESC": "ESC",
    "ESC/EACTS": "ESC",
    "AHA/ACC": "AHA/ACC",
    "AHA": "AHA/ACC",
    "ACC/AHA": "AHA/ACC",
}

_GROUP_ORDER = ["SBC", "ESC", "AHA/ACC"]

_GROUP_LABEL = {
    "SBC": "\U0001f1e7\U0001f1f7 Brasileiras (SBC)",
    "ESC": "\U0001f1ea\U0001f1fa Europeias (ESC)",
    "AHA/ACC": "\U0001f1fa\U0001f1f8 Americanas (AHA/ACC)",
}


# ── ChromaDB loader (cached) ────────────────────────────────────────

@st.cache_data(ttl=600, show_spinner="Carregando diretrizes do ChromaDB...")
def _load_guidelines_from_chromadb() -> list[dict]:
    """Query ChromaDB and return a list of unique guidelines with diretriz, sociedade, ano."""
    from core.config import get_collection

    collection = get_collection()
    total = collection.count()

    if total == 0:
        return []

    batch_size = 10_000
    all_metadatas: list[dict] = []
    offset = 0

    while offset < total:
        batch = collection.get(
            limit=batch_size,
            offset=offset,
            include=["metadatas"],
        )
        all_metadatas.extend(batch["metadatas"])
        offset += len(batch["metadatas"])
        if len(batch["metadatas"]) < batch_size:
            break

    seen: set[tuple[str, str, str]] = set()
    guidelines: list[dict] = []

    for meta in all_metadatas:
        diretriz = meta.get("diretriz", "Sem nome")
        sociedade = meta.get("sociedade", "SBC")
        ano = str(meta.get("ano", ""))
        key = (diretriz, sociedade, ano)
        if key not in seen:
            seen.add(key)
            guidelines.append({
                "diretriz": diretriz,
                "sociedade": sociedade,
                "ano": ano,
                "grupo": _SOCIETY_GROUP.get(sociedade, sociedade),
            })

    guidelines.sort(key=lambda g: (
        _GROUP_ORDER.index(g["grupo"]) if g["grupo"] in _GROUP_ORDER else 99,
        g["ano"],
        g["diretriz"],
    ))

    return guidelines


# ── LLM Reference ───────────────────────────────────────────────────

_PROVIDER_GROUPS = [
    ("API Direta", lambda mid: not mid.startswith("openrouter/") and not mid.startswith("ollama:")),
    ("OpenRouter: OpenAI", lambda mid: mid.startswith("openrouter/openai")),
    ("OpenRouter: Anthropic", lambda mid: mid.startswith("openrouter/anthropic")),
    ("OpenRouter: Google", lambda mid: mid.startswith("openrouter/google")),
    ("OpenRouter: Meta", lambda mid: mid.startswith("openrouter/meta")),
    ("OpenRouter: DeepSeek", lambda mid: mid.startswith("openrouter/deepseek")),
    ("OpenRouter: Qwen (Alibaba)", lambda mid: mid.startswith("openrouter/qwen")),
    ("OpenRouter: Kimi (Moonshot)", lambda mid: mid.startswith("openrouter/moonshotai")),
    ("OpenRouter: Mistral", lambda mid: mid.startswith("openrouter/mistral")),
    ("OpenRouter: Nvidia", lambda mid: mid.startswith("openrouter/nvidia")),
    ("OpenRouter: xAI (Grok)", lambda mid: mid.startswith("openrouter/x-ai")),
    ("OpenRouter: Aion Labs (Bio)", lambda mid: mid.startswith("openrouter/aion")),
    ("Local (Ollama)", lambda mid: mid.startswith("ollama:")),
]


def _render_llm_catalog():
    """Catálogo completo de LLMs com preços e características."""
    st.markdown("### 💰 Catálogo de LLMs")
    st.caption("Preços em USD por 1M tokens · Atualizado em 2026-03-25")

    for group_name, match_fn in _PROVIDER_GROUPS:
        entries = [
            (mid, *info)
            for mid, info in MODELS_INFO.items()
            if match_fn(mid)
        ]
        if not entries:
            continue

        entries.sort(key=lambda x: x[1])  # sort by price_in

        with st.expander(f"**{group_name}** ({len(entries)})", expanded=False):
            rows = []
            for mid, p_in, p_out, ctx, notes in entries:
                # Extract short name
                if mid.startswith("ollama:"):
                    name = mid.replace("ollama:", "")
                elif "/" in mid:
                    name = mid.split("/")[-1]
                else:
                    name = mid

                ctx_str = f"{ctx // 1000}K" if ctx < 1_000_000 else f"{ctx // 1_000_000}M"
                price = "**gratis**" if p_in == 0 else f"${p_in:.3f} / ${p_out:.3f}"
                rows.append(f"| {name} | {ctx_str} | {price} | {notes} |")

            table = "| Modelo | Ctx | In / Out ($/M) | Notas |\n|---|---|---|---|\n" + "\n".join(rows)
            st.markdown(table)


# ── Diretrizes (static config lists) ────────────────────────────────

def _render_diretrizes_config():
    """Lista de diretrizes do config (SBC + internacionais)."""
    st.markdown("### 📚 Diretrizes SBC Indexadas")
    for ano, dirs in DIRETRIZES.items():
        with st.expander(f"**{ano}** ({len(dirs)})", expanded=False):
            st.markdown(" · ".join(dirs))

    st.markdown("### 🌍 Diretrizes ESC / AHA / ACC")
    for fonte, dirs in DIRETRIZES_INTERNACIONAIS.items():
        with st.expander(f"**{fonte}** ({len(dirs)})", expanded=False):
            st.markdown(" · ".join(dirs))


# ── Diretrizes from ChromaDB ────────────────────────────────────────

def _render_diretrizes_chromadb():
    """Diretrizes reais indexadas no ChromaDB."""
    st.markdown("### 🗄️ Diretrizes no ChromaDB")
    st.caption("Lidas diretamente da base vetorial")

    guidelines = _load_guidelines_from_chromadb()

    if not guidelines:
        st.warning("Nenhuma diretriz encontrada no ChromaDB. Execute `python index.py` para indexar.")
        return

    grouped: dict[str, list[dict]] = defaultdict(list)
    for g in guidelines:
        grouped[g["grupo"]].append(g)

    for group in _GROUP_ORDER:
        items = grouped.get(group)
        if not items:
            continue

        label = _GROUP_LABEL.get(group, group)
        items_sorted = sorted(items, key=lambda x: (x["ano"], x["diretriz"]), reverse=True)

        with st.expander(f"{label}  ({len(items_sorted)})", expanded=False):
            lines = []
            for item in items_sorted:
                ano_str = f" ({item['ano']})" if item["ano"] else ""
                lines.append(f"- {item['diretriz']}{ano_str}")
            st.markdown("\n".join(lines))


# ── Public entry point ───────────────────────────────────────────────

def render_context_mode(cfg: dict):
    """Renderiza a aba Referências — LLMs + diretrizes."""

    tab_llms, tab_dirs_config, tab_dirs_chroma = st.tabs([
        "🤖 Modelos LLM",
        "📚 Diretrizes (config)",
        "🗄️ Diretrizes (ChromaDB)",
    ])

    with tab_llms:
        _render_llm_catalog()

    with tab_dirs_config:
        _render_diretrizes_config()

    with tab_dirs_chroma:
        _render_diretrizes_chromadb()
