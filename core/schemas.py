"""
MAC RAG Ecocardiografia — Schemas Pydantic
Validação estruturada para dados clínicos do pipeline de consulta.
Gerado automaticamente pelo RAG Factory.
"""

import json
import logging
import re
from pydantic import BaseModel, Field
from typing import Optional

logger = logging.getLogger(__name__)


class DadosPaciente(BaseModel):
    idade: Optional[int] = None
    sexo: Optional[str] = None
    peso: Optional[str] = None
    altura: Optional[str] = None


class ExameFisico(BaseModel):
    pa: Optional[str] = None
    fc: Optional[str] = None
    peso: Optional[str] = None
    outros: list[str] = Field(default_factory=list)


class ExamesComplementares(BaseModel):
    laboratorio: dict = Field(default_factory=dict)
    ecg: Optional[str] = None
    ecocardiograma: Optional[str] = None
    outros: dict = Field(default_factory=dict)


class CartaoClinico(BaseModel):
    """Cartão clínico extraído da consulta — schema validado."""
    paciente: DadosPaciente = Field(default_factory=DadosPaciente)
    queixa_principal: str = ""
    hda: str = ""
    comorbidades: list[str] = Field(default_factory=list)
    medicacoes_atuais: list[str] = Field(default_factory=list)
    medicacoes_previas: list[str] = Field(default_factory=list)
    alergias: list[str] = Field(default_factory=list)
    habitos: list[str] = Field(default_factory=list)
    exame_fisico: ExameFisico = Field(default_factory=ExameFisico)
    exames_complementares: ExamesComplementares = Field(default_factory=ExamesComplementares)
    hipoteses_diagnosticas: list[str] = Field(default_factory=list)
    condutas_discutidas: list[str] = Field(default_factory=list)
    pendencias: list[str] = Field(default_factory=list)

    # === Campos críticos específicos de ecocardiografia ===
    feve: Optional[float] = None  # Fração de ejeção do VE (%)
    diametro_vdfve: Optional[str] = None  # Diâmetro diastólico/sistólico do VE (mm)
    volume_ae: Optional[float] = None  # Volume indexado do AE (mL/m²)
    e_e_prime: Optional[float] = None  # Relação E/e' médio
    tapse: Optional[float] = None  # TAPSE em mm
    psap: Optional[float] = None  # Pressão sistólica da artéria pulmonar estimada (mmHg)
    strain_global: Optional[float] = None  # Strain longitudinal global do VE (%)
    ava: Optional[float] = None  # Área valvar aórtica (cm²)
    grad_medio_ao: Optional[float] = None  # Gradiente médio transaórtico (mmHg)
    regurgitacao_mitral: Optional[str] = None  # Grau de regurgitação mitral (ausente/discreta/moderada/importante)
    regurgitacao_aortica: Optional[str] = None  # Grau de regurgitação aórtica
    derrame_pericardico: Optional[str] = None  # Derrame pericárdico (ausente/discreto/moderado/importante)


    @classmethod
    def from_raw(cls, text: str) -> "CartaoClinico":
        """Parse JSON bruto do LLM → CartaoClinico validado.
        Trata markdown code blocks, JSON malformado, campos extras.
        Nunca levanta exceção — retorna cartão vazio com warning se falhar.
        """
        if not text:
            return cls()

        clean = text.strip()
        if clean.startswith("```"):
            lines = clean.split("\n")
            start = 1 if lines[0].startswith("```") else 0
            end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
            clean = "\n".join(lines[start:end])

        try:
            data = json.loads(clean)
            data = _coerce_idade(data)
            return cls.model_validate(data)
        except json.JSONDecodeError as e:
            logger.warning("from_raw: first JSON parse failed: %s", e)
        except Exception as e:
            logger.exception("from_raw: unexpected error: %s", e)

        try:
            match = re.search(r'\{[\s\S]*\}', clean)
            if match:
                data = json.loads(match.group())
                data = _coerce_idade(data)
                return cls.model_validate(data)
        except Exception as e:
            logger.warning("from_raw: regex extraction failed: %s", e)

        logger.warning("from_raw: returning empty CartaoClinico")
        return cls()


def _coerce_idade(data: dict) -> dict:
    """Convert idade from string to int if needed."""
    paciente = data.get("paciente")
    if isinstance(paciente, dict):
        idade = paciente.get("idade")
        if isinstance(idade, str):
            match = re.search(r'\d+', idade)
            paciente["idade"] = int(match.group()) if match else None
    return data
