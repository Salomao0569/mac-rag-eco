"""Shared helpers for extracting data from CartaoClinico (Pydantic or dict)."""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def get_list(card, field: str) -> list:
    """Extract a list field from CartaoClinico (Pydantic or dict)."""
    if hasattr(card, field):
        return getattr(card, field) or []
    if isinstance(card, dict):
        return card.get(field, []) or []
    return []


def get_idade(card) -> Optional[int]:
    """Extract numeric age from CartaoClinico."""
    try:
        raw = None
        if hasattr(card, 'paciente') and card.paciente:
            raw = card.paciente.idade
        elif isinstance(card, dict):
            raw = card.get('paciente', {}).get('idade')

        if raw is None:
            return None
        if isinstance(raw, int):
            return raw
        if isinstance(raw, str):
            match = re.search(r'\d+', raw)
            return int(match.group()) if match else None
    except Exception:
        pass
    return None


def get_sexo(card) -> Optional[str]:
    """Extract sex (M/F) from CartaoClinico."""
    try:
        if hasattr(card, 'paciente') and card.paciente:
            return card.paciente.sexo
        if isinstance(card, dict):
            return card.get('paciente', {}).get('sexo')
    except Exception:
        pass
    return None


def get_comorbidades(card) -> list[str]:
    """Extract comorbidities as lowercase list."""
    return [c.lower() for c in get_list(card, 'comorbidades')]


def has_condition(items: list[str], keywords: list[str]) -> bool:
    """Check if any keyword matches any item using word boundaries.

    For short keywords (<=3 chars), uses word-boundary regex to avoid
    false positives (e.g. 'ic' matching 'medICina').
    For longer keywords, uses simple substring matching.
    """
    for item in items:
        for k in keywords:
            if len(k) <= 3:
                if re.search(rf'\b{re.escape(k)}\b', item, re.IGNORECASE):
                    return True
            else:
                if k.lower() in item.lower():
                    return True
    return False


def _get_field(card, field: str):
    """Generic field getter supporting Pydantic model or dict."""
    if hasattr(card, field):
        return getattr(card, field)
    if isinstance(card, dict):
        return card.get(field)
    return None


def get_feve(card) -> Optional[float]:
    """Extract FEVE (%) from CartaoClinico."""
    val = _get_field(card, 'feve')
    if val is not None:
        try:
            return float(val)
        except (ValueError, TypeError):
            pass
    return None


def get_creatinina(card) -> Optional[float]:
    """Extract creatinina (mg/dL) from CartaoClinico."""
    val = _get_field(card, 'creatinina')
    if val is not None:
        try:
            return float(val)
        except (ValueError, TypeError):
            pass
    return None


def get_potassio(card) -> Optional[float]:
    """Extract potássio (mEq/L) from CartaoClinico."""
    val = _get_field(card, 'potassio')
    if val is not None:
        try:
            return float(val)
        except (ValueError, TypeError):
            pass
    return None


def get_egfr(card) -> Optional[float]:
    """Extract eGFR (mL/min/1.73m²) from CartaoClinico."""
    val = _get_field(card, 'egfr')
    if val is not None:
        try:
            return float(val)
        except (ValueError, TypeError):
            pass
    return None


def get_ritmo(card) -> Optional[str]:
    """Extract ritmo cardíaco from CartaoClinico."""
    val = _get_field(card, 'ritmo')
    return str(val) if val is not None else None


def get_nyha(card) -> Optional[int]:
    """Extract NYHA class (1-4) from CartaoClinico."""
    val = _get_field(card, 'nyha_class')
    if val is not None:
        try:
            return int(val)
        except (ValueError, TypeError):
            pass
    return None


def is_gestante(card) -> bool:
    """Check if patient is pregnant."""
    val = _get_field(card, 'gestante')
    return bool(val)
