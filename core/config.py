"""
MAC RAG Ecocardiografia — Configuração centralizada
Constantes, paths, singletons e mapeamentos usados por todo o sistema.
Gerado automaticamente pelo RAG Factory.
"""

import os
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction


def _resolve_device() -> str:
    """Auto-detect best available device: cuda → mps → cpu."""
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        if torch.backends.mps.is_available():
            return "mps"
    except ImportError:
        pass
    return "cpu"


DEVICE = _resolve_device()

# === Paths ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "chroma_db")
MEMORY_DB = os.path.join(BASE_DIR, "agent_memory.db")

# === Collection ===
COLLECTION_NAME = 'diretrizes_eco'

# === Modelos ===
DEFAULT_COORD_MODEL = "gpt-4o"
DEFAULT_AGENT_MODEL = "gpt-4o-mini"

MODELS_COORD = {
    "GPT-4o (recomendado)": "gpt-4o",
    "GPT-4o mini (econômico)": "gpt-4o-mini",
    "Sonnet 4": "claude-sonnet-4-20250514",
    "Opus 4 (máxima qualidade)": "claude-opus-4-20250514",
    "Haiku 4.5": "claude-haiku-4-5-20251001",
    "Qwen 3.5 9B (local GPU)": "ollama:qwen3.5:9b",
    "── OpenRouter: Frontier ──": None,
    "OR: GPT-5.4 (1M ctx)": "openrouter/openai/gpt-5.4",
    "OR: GPT-5": "openrouter/openai/gpt-5",
    "OR: GPT-4.1 (1M ctx)": "openrouter/openai/gpt-4.1",
    "OR: o4-mini (reasoning)": "openrouter/openai/o4-mini",
    "OR: o3 (reasoning)": "openrouter/openai/o3",
    "OR: Sonnet 4.6 (1M ctx)": "openrouter/anthropic/claude-sonnet-4.6",
    "OR: Opus 4.6 (1M ctx)": "openrouter/anthropic/claude-opus-4.6",
    "OR: Gemini 3.1 Pro (1M ctx)": "openrouter/google/gemini-3.1-pro-preview",
    "OR: Grok 4.20 (2M ctx)": "openrouter/x-ai/grok-4.20-beta",
    "OR: Aion 1.0 (biomedicina)": "openrouter/aion-labs/aion-1.0",
    "── Qwen DashScope (API direta) ──": None,
    "QW: Qwen-Max (flagship)": "dashscope/qwen-max",
    "QW: Qwen-Plus (equilibrado)": "dashscope/qwen-plus",
    "QW: Qwen-Turbo (rápido)": "dashscope/qwen-turbo",
    "QW: Qwen-Long (1M ctx)": "dashscope/qwen-long",
    "QW: QwQ-Plus (reasoning)": "dashscope/qwq-plus",
    "QW: Qwen3-235B MoE": "dashscope/qwen3-235b-a22b",
    "── OpenRouter: Custo-beneficio ──": None,
    "OR: Sonnet 4": "openrouter/anthropic/claude-sonnet-4",
    "OR: GPT-4o": "openrouter/openai/gpt-4o",
    "OR: GPT-5 Nano": "openrouter/openai/gpt-5-nano",
    "OR: Gemini 2.5 Pro": "openrouter/google/gemini-2.5-pro-preview-06-05",
    "OR: Llama 4 Maverick": "openrouter/meta-llama/llama-4-maverick",
    "OR: DeepSeek R1 0528": "openrouter/deepseek/deepseek-r1-0528",
    "OR: DeepSeek V3.2": "openrouter/deepseek/deepseek-v3.2",
    "OR: Qwen3 235B": "openrouter/qwen/qwen3-235b-a22b-2507",
}
MODELS_AGENTS = {
    "GPT-4o mini (recomendado)": "gpt-4o-mini",
    "GPT-4o": "gpt-4o",
    "Haiku 4.5": "claude-haiku-4-5-20251001",
    "Sonnet 4": "claude-sonnet-4-20250514",
    "Qwen 3.5 9B (local GPU)": "ollama:qwen3.5:9b",
    "── Qwen DashScope ──": None,
    "QW: Qwen-Turbo (rápido)": "dashscope/qwen-turbo",
    "QW: Qwen-Plus (equilibrado)": "dashscope/qwen-plus",
    "── OpenRouter ──": None,
    "OR: Haiku 4.5": "openrouter/anthropic/claude-haiku-4-5",
    "OR: GPT-4o mini": "openrouter/openai/gpt-4o-mini",
    "OR: GPT-5 Nano": "openrouter/openai/gpt-5-nano",
    "OR: DeepSeek V3.2": "openrouter/deepseek/deepseek-v3.2",
    "OR: Qwen3 235B": "openrouter/qwen/qwen3-235b-a22b-2507",
    "OR: Aion 1.0 (biomedicina)": "openrouter/aion-labs/aion-1.0",
}

# === Referência de preços (USD/1M tokens) ===
MODELS_INFO = {
    "gpt-4o":                          (2.50, 10.00, 128_000, "OpenAI flagship"),
    "gpt-4o-mini":                     (0.15,  0.60, 128_000, "OpenAI econômico"),
    "claude-sonnet-4-20250514":        (3.00, 15.00, 200_000, "Anthropic, excelente raciocínio"),
    "claude-opus-4-20250514":          (15.0, 75.00, 200_000, "Máxima qualidade"),
    "claude-haiku-4-5-20251001":       (0.80,  4.00, 200_000, "Anthropic rápido e barato"),
    "dashscope/qwen-max":              (2.80, 8.40, 128_000, "Flagship Qwen"),
    "dashscope/qwen-plus":             (0.11, 0.28, 128_000, "Equilibrado"),
    "dashscope/qwen-turbo":            (0.04, 0.08, 128_000, "Ultra rápido"),
    "ollama:qwen3.5:9b":              (0.00, 0.00, 32_768, "Local GPU, sem custo"),
}


def is_openai_model(model_id: str) -> bool:
    return model_id.startswith("gpt-")


OLLAMA_HOST = "http://192.168.18.100:11434"


def is_openrouter_model(model_id: str) -> bool:
    return model_id.startswith("openrouter/")


DASHSCOPE_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"


def build_model(model_id: str):
    """Factory: retorna instância conforme model_id."""
    if model_id.startswith("dashscope/"):
        from agno.models.openai import OpenAIChat
        ds_model = model_id.removeprefix("dashscope/")
        return OpenAIChat(
            id=ds_model,
            api_key=os.environ.get("DASHSCOPE_API_KEY", ""),
            base_url=DASHSCOPE_BASE_URL,
            role_map={"system": "system", "user": "user", "assistant": "assistant"},
        )
    elif model_id.startswith("openrouter/"):
        from agno.models.openrouter import OpenRouter
        or_model_id = model_id.removeprefix("openrouter/")
        return OpenRouter(id=or_model_id)
    elif model_id.startswith("ollama:"):
        from agno.models.ollama import Ollama
        ollama_model = model_id.replace("ollama:", "")
        return Ollama(id=ollama_model, host=OLLAMA_HOST)
    elif is_openai_model(model_id):
        from agno.models.openai import OpenAIChat
        return OpenAIChat(id=model_id)
    else:
        from agno.models.anthropic import Claude
        return Claude(id=model_id)


# === Fontes ===
FONTE_MARKER = {
    "rag": "[FONTE: RAG]",
    "pubmed": "[FONTE: PUBMED]",
    "internet": "[FONTE: INTERNET]",
    "todas": "[FONTE: TODAS]",
}
FONTES_UI = {
    "Auto (coordenador decide)": "",
    "📗 RAG Diretrizes": "[FONTE: RAG]",
    "📙 PubMed": "[FONTE: PUBMED]",
    "📘 Internet": "[FONTE: INTERNET]",
    "📡 Todas (broadcast)": "[FONTE: TODAS]",
}

# Hierarquia: DIC-SBC > ASE > EACVI > BSE

# === Diretrizes indexadas ===
DIRETRIZES = {
    "2024": ['Eco Transtorácico', 'Eco de Estresse', 'Strain/Speckle Tracking'],
    "2023": ['Cardiopatias Congênitas', 'Eco Fetal'],
    "2022": ['Valvopatias', 'Cardiomiopatias'],
    "2021": ['Eco Transesofágico'],
}

DIRETRIZES_INTERNACIONAIS = {
    "ASE 2025": ['Diastolic Function Update', '3D Echocardiography'],
    "ASE 2024": ['Aortic Stenosis Grading', 'Right Heart'],
    "ASE 2023": ['Chamber Quantification Update', 'Oncology'],
    "ASE 2022": ['Strain Imaging', 'Valvular Regurgitation'],
    "ASE 2021": ['Multimodality Imaging', 'Native Valve Endocarditis'],
    "EACVI 2024": ['Myocardial Work', 'Exercise Echocardiography'],
    "EACVI 2023": ['Echocardiography in Heart Failure', 'Cardiac Masses'],
    "EACVI 2022": ['Prosthetic Valves'],
    "BSE 2024": ['Minimum Dataset for Standard Echo'],
}


# === ChromaDB (singleton) ===
_collection = None


def get_collection():
    global _collection
    if _collection is None:
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        client = chromadb.PersistentClient(path=DB_PATH)
        # Use CPU for query-time embeddings (fast enough for single queries).
        # GPU is only needed for bulk indexing (index.py).
        embed_fn = SentenceTransformerEmbeddingFunction(
            model_name="intfloat/multilingual-e5-base",
            device="cpu",
            trust_remote_code=True,
        )
        try:
            _collection = client.get_collection(
                name=COLLECTION_NAME, embedding_function=embed_fn
            )
        except (ValueError, Exception):
            import logging
            logging.getLogger(__name__).warning(
                f"Collection '{COLLECTION_NAME}' not found. Creating empty. Run 'python index.py' to populate."
            )
            _collection = client.get_or_create_collection(
                name=COLLECTION_NAME,
                embedding_function=embed_fn,
                metadata={
                    "hnsw:space": "cosine",
                    "hnsw:search_ef": 100,
                    "hnsw:construction_ef": 200,
                },
            )
    return _collection


# === Word limits ===
_LIMITS_API = "Perguntas simples: 150-250 palavras. Perguntas complexas (multi-diretriz, caso clínico): 300-500 palavras. Sem limite para tabelas e citações [[...]]"
_LIMITS_LOCAL = "Sem limite rígido — responda com a profundidade que a evidência permitir (até 1000 palavras)."


def _apply_word_limits(prompt: str, model_id: str) -> str:
    if model_id.startswith("ollama:"):
        return prompt.replace(_LIMITS_API, _LIMITS_LOCAL)
    return prompt


def load_coordinator_prompt(model_id: str = ""):
    path = os.path.join(BASE_DIR, "coordinator_prompt.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            prompt = f.read()
        return _apply_word_limits(prompt, model_id) if model_id else prompt
    return "Você é um coordenador de ecocardiografia. Sintetize em 150 palavras. PT-BR."


def load_single_agent_prompt(model_id: str = ""):
    path = os.path.join(BASE_DIR, "prompts", "single_agent.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            prompt = f.read()
        return _apply_word_limits(prompt, model_id) if model_id else prompt
    return "Você é um assistente clínico em ecocardiografia baseado em evidências. PT-BR."


def resolve_team_mode(fonte_marker: str):
    from agno.team import TeamMode
    if fonte_marker == "[FONTE: TODAS]":
        return TeamMode.broadcast
    if fonte_marker in ("[FONTE: RAG]", "[FONTE: PUBMED]", "[FONTE: INTERNET]"):
        return TeamMode.route
    return TeamMode.coordinate
