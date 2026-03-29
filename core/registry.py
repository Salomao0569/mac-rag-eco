"""
MAC RAG Ecocardiografia — Registry de Agentes e Tools
Padrão registry: agentes e tools se auto-registram via decorators.
Adicionar novo agente/tool = 1 arquivo, 1 decorator.
"""

import os
from dataclasses import dataclass, field
from typing import Callable

from .config import build_model, DEFAULT_AGENT_MODEL, BASE_DIR

PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")


def load_prompt(name: str) -> str:
    """Carrega prompt de prompts/{name}.md"""
    path = os.path.join(PROMPTS_DIR, f"{name}.md")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ============================================================
# Tool Registry
# ============================================================

@dataclass
class ToolEntry:
    func: Callable
    groups: list[str]  # ex: ["rag", "all"] ou ["pubmed", "all"]


_tool_registry: dict[str, ToolEntry] = {}


def register_tool(*groups: str):
    """Decorator: registra uma tool em um ou mais grupos.

    Uso:
        @register_tool("rag", "all")
        @tool
        def rag_search(...): ...
    """
    def decorator(func):
        # Suporta tanto funções normais quanto objetos Agno Function (sem __name__)
        name = getattr(func, "__name__", None) or getattr(func, "name", None) or str(func)
        _tool_registry[name] = ToolEntry(func=func, groups=list(groups))
        return func
    return decorator


def _tool_name(func) -> str:
    """Extrai nome de função normal ou objeto Agno Function."""
    return getattr(func, "__name__", None) or getattr(func, "name", None) or str(func)


def get_tools(*groups: str) -> list:
    """Retorna tools que pertencem a QUALQUER dos grupos informados."""
    result = []
    seen = set()
    for entry in _tool_registry.values():
        if any(g in entry.groups for g in groups):
            name = _tool_name(entry.func)
            if name not in seen:
                result.append(entry.func)
                seen.add(name)
    return result


def get_all_tools() -> list:
    """Retorna todas as tools registradas."""
    return get_tools("all")


# ============================================================
# Agent Registry
# ============================================================

@dataclass
class AgentDef:
    name: str
    role: str
    prompt_file: str        # nome do arquivo em prompts/ (sem .md)
    tool_groups: list[str]  # grupos de tools que este agente usa
    extras: dict = field(default_factory=dict)


_agent_registry: list[AgentDef] = []


def register_agent(
    name: str,
    role: str,
    prompt_file: str,
    tool_groups: list[str],
    **extras,
):
    """Registra um agente no registry.

    Uso (em agents.py):
        register_agent(
            name="RAG Diretrizes",
            role="Busca trechos de diretrizes...",
            prompt_file="rag_agent",
            tool_groups=["rag"],
        )
    """
    _agent_registry.append(AgentDef(
        name=name,
        role=role,
        prompt_file=prompt_file,
        tool_groups=tool_groups,
        extras=extras,
    ))


def build_registered_agents(model_id: str = DEFAULT_AGENT_MODEL) -> list:
    """Instancia todos os agentes registrados."""
    from agno.agent import Agent

    model = build_model(model_id)
    agents = []
    for defn in _agent_registry:
        instructions = load_prompt(defn.prompt_file)
        tools = get_tools(*defn.tool_groups)
        agents.append(Agent(
            name=defn.name,
            role=defn.role,
            instructions=instructions,
            tools=tools,
            model=model,
            markdown=False,
        ))
    return agents


def list_agents() -> list[AgentDef]:
    """Lista definições de agentes registrados (para UI/debug)."""
    return list(_agent_registry)
