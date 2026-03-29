"""
ECO RAG — AgentOS Entrypoint
Expõe o Team e agentes individuais no dashboard visual do Agno (os.agno.com).

Rodar:
    agno run api.py

Depois conectar em: https://os.agno.com → Add OS → Local → http://localhost:7777
"""

from agno.os import AgentOS
from agno.db.sqlite import SqliteDb

from core.config import MEMORY_DB, DEFAULT_COORD_MODEL, DEFAULT_AGENT_MODEL
from core.team_builder import build_team, build_single_agent

# --- Build agents and team ---
team = build_team(
    model_coord=DEFAULT_COORD_MODEL,
    model_agents=DEFAULT_AGENT_MODEL,
    session_id="agno-ui",
)

single_agent = build_single_agent(
    model_id=DEFAULT_COORD_MODEL,
    session_id="agno-ui-single",
)

# --- AgentOS ---
agent_os = AgentOS(
    name="ECO RAG — Ecocardiografia",
    description="Multi-Agent RAG para diretrizes de ecocardiografia (DIC-SBC, ASE, EACVI, BSE)",
    agents=[single_agent],
    teams=[team],
    tracing=True,
    db=SqliteDb(db_file=MEMORY_DB),
)

app = agent_os.get_app()
