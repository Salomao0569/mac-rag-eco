"""Backwards compatibility — imports from core.consultation."""
from core.consultation import *  # noqa: F401,F403
from core.consultation import (
    build_diarizer, build_extractor, build_soap_agent,
    generate_soap, build_consultant, process_consultation,
)
