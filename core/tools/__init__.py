"""
Registro central de tools — auto-registro via decorator.
Adicionar nova tool: crie arquivo, decore com @register_tool("grupo", "all").
"""

from ..registry import register_tool, get_tools, get_all_tools

# Importar módulos para que os decorators executem
from . import rag_tool    # noqa: F401
from . import scores      # noqa: F401
from . import pubmed_tool  # noqa: F401
from . import tavily_tool  # noqa: F401

# Atalhos de conveniência (retrocompatibilidade)
ALL_TOOLS = get_all_tools()
RAG_TOOLS = get_tools("rag")
PUBMED_TOOLS = get_tools("pubmed")
TAVILY_TOOLS = get_tools("tavily")
