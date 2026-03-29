"""
Montagem do Team e do agente único.
Ponto de entrada programático via ask().
"""

import logging
from agno.agent import Agent
from agno.team import Team, TeamMode
from agno.db.sqlite import SqliteDb

from .config import (
    MEMORY_DB,
    FONTE_MARKER,
    DEFAULT_COORD_MODEL,
    DEFAULT_AGENT_MODEL,
    load_coordinator_prompt,
    load_single_agent_prompt,
    build_model,
    resolve_team_mode,
)
from .agents import build_agents
from .registry import get_all_tools
from observe import observe
import cache


def build_team(
    model_coord=DEFAULT_COORD_MODEL,
    model_agents=DEFAULT_AGENT_MODEL,
    session_id="default",
    mode=TeamMode.coordinate,
):
    return Team(
        name="Coordenador Cardiológico",
        mode=mode,
        model=build_model(model_coord),
        members=build_agents(model_agents),
        instructions=load_coordinator_prompt(model_coord),
        db=SqliteDb(db_file=MEMORY_DB),
        session_id=session_id,
        user_id="biocardio",
        markdown=True,
        share_member_interactions=True,
        store_member_responses=True,
        show_members_responses=False,
        resolve_in_context=True,
        max_iterations=3,
        add_history_to_context=True,
        num_history_runs=5,
    )


def build_single_agent(model_id=DEFAULT_COORD_MODEL, session_id="default"):
    return Agent(
        name="Cardiologista Digital",
        model=build_model(model_id),
        tools=get_all_tools(),
        instructions=load_single_agent_prompt(model_id),
        db=SqliteDb(db_file=MEMORY_DB),
        update_memory_on_run=True,
        enable_agentic_memory=True,
        add_history_to_context=True,
        num_history_runs=5,
        session_id=session_id,
        user_id="biocardio",
        markdown=True,
    )


@observe
def ask(
    question,
    fonte="auto",
    mode="coordinate",
    model_coord=DEFAULT_COORD_MODEL,
    model_agents=DEFAULT_AGENT_MODEL,
    session_id="cli",
):
    """Interface programática — usada pelo CLI e testes."""
    if fonte in FONTE_MARKER:
        query = f"{FONTE_MARKER[fonte]} {question}"
    else:
        query = question

    # Check cache
    cache_filters = f"{fonte}|{mode}"
    cached = cache.get(query, model=model_coord, filters=cache_filters)
    if cached is not None:
        return cached

    fonte_marker = FONTE_MARKER.get(fonte, "")
    team_mode = resolve_team_mode(fonte_marker) if fonte_marker else TeamMode(mode)

    try:
        team = build_team(model_coord, model_agents, session_id, team_mode)
        response = team.run(query)
        result = response.content

        # Cache the result
        cache.put(query, result, model=model_coord, filters=cache_filters)

        return result
    except (ConnectionError, TimeoutError) as e:
        return f"⚠️ Erro de conexão: {e}"
    except ValueError as e:
        return f"⚠️ Erro de configuração: {e}"
    except Exception as e:
        logging.getLogger(__name__).exception("Unexpected error in ask()")
        return f"⚠️ Erro ao processar pergunta: {type(e).__name__}: {e}"
