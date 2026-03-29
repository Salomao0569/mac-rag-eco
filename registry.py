"""Backwards compatibility — imports from core.registry."""
from core.registry import *  # noqa: F401,F403
from core.registry import (
    register_tool, get_tools, get_all_tools,
    register_agent, build_registered_agents, list_agents,
    load_prompt, ToolEntry, AgentDef,
)
