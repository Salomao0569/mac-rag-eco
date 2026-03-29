"""
Definição dos agentes especializados via Registry.
Cada agente se auto-registra — para adicionar novo agente:
1. Crie prompts/{nome}.md
2. Adicione register_agent() aqui
"""

from .config import DEFAULT_AGENT_MODEL
from .registry import register_agent, build_registered_agents

# ============================================================
# Registro — cada chamada = 1 agente no time
# ============================================================

register_agent(
    name="RAG Diretrizes",
    role="Busca trechos de diretrizes de cardiologia (SBC, ESC, AHA/ACC — 44 diretrizes, ~29.000 chunks) com metadados de fonte. Cobre: IC, FA, valvopatias, SCA, hipertensão, dislipidemias, perioperatório, arritmias, cardiomiopatias, diabetes, cardio-oncologia, hipertensão pulmonar e mais.",
    prompt_file="rag_agent",
    tool_groups=["rag"],
)

register_agent(
    name="PubMed",
    role="Busca abstracts no PubMed com PMID para rastreabilidade",
    prompt_file="pubmed_agent",
    tool_groups=["pubmed"],
)

register_agent(
    name="Tavily",
    role="Busca informações regulatórias e notícias na internet com URL de fonte",
    prompt_file="tavily_agent",
    tool_groups=["tavily"],
)


def build_agents(model_id=DEFAULT_AGENT_MODEL):
    """Cria todos os agentes registrados."""
    return build_registered_agents(model_id)
