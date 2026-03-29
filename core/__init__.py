"""MAC RAG Ecocardiografia — Core library."""
from .config import get_collection, build_model, load_coordinator_prompt, COLLECTION_NAME
from .schemas import CartaoClinico
from . import tools as _tools  # noqa: F401 — trigger tool registration via decorators
from .team_builder import build_team, build_single_agent, ask
from .consultation import process_consultation
from .patient_letter import generate_patient_letter
from .auto_scores import calculate_applicable_scores, format_scores_markdown
from .alerts import generate_alerts, format_alerts_markdown
from .exam_requests import generate_exam_requests, format_exam_requests_markdown, format_exam_requests_text
from .registry import get_all_tools, register_tool, register_agent
