"""Patient Letter Generator — translates SOAP notes to plain language."""

import logging
import os

from .config import build_model, DEFAULT_COORD_MODEL, BASE_DIR

logger = logging.getLogger(__name__)


def generate_patient_letter(soap_note: str, card=None, model_id: str = DEFAULT_COORD_MODEL) -> str:
    """Generate a patient-friendly letter from SOAP note and CartaoClinico.

    Args:
        soap_note: The SOAP note text
        card: Optional CartaoClinico for patient name/demographics
        model_id: LLM model to use

    Returns:
        Patient letter in plain Portuguese
    """
    # Load prompt
    prompt_path = os.path.join(BASE_DIR, 'prompts', 'patient_letter.md')
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            system_prompt = f.read()
    except FileNotFoundError:
        system_prompt = "Traduza a nota SOAP para linguagem simples para o paciente. Máximo 200 palavras. Português brasileiro."

    # Build patient context
    patient_info = ""
    if card:
        try:
            if hasattr(card, 'paciente') and card.paciente:
                pac = card.paciente
                parts = []
                if pac.idade: parts.append(f"Idade: {pac.idade}")
                if pac.sexo: parts.append(f"Sexo: {pac.sexo}")
                patient_info = f"\nDados do paciente: {', '.join(parts)}"
            elif isinstance(card, dict):
                pac = card.get('paciente', {})
                parts = []
                if pac.get('idade'): parts.append(f"Idade: {pac['idade']}")
                if pac.get('sexo'): parts.append(f"Sexo: {pac['sexo']}")
                patient_info = f"\nDados do paciente: {', '.join(parts)}"
        except Exception:
            pass

    # Build the message
    user_message = f"Nota SOAP:\n{soap_note}{patient_info}\n\nGere a carta para o paciente."

    try:
        from agno.agent import Agent

        agent = Agent(
            name="Gerador de Carta",
            model=build_model(model_id),
            instructions=system_prompt,
            markdown=True,
        )
        response = agent.run(user_message)
        letter = response.content if response.content else "Erro ao gerar carta."
        logger.info(f"Patient letter generated ({len(letter)} chars)")
        return letter
    except Exception as e:
        logger.error(f"Error generating patient letter: {e}")
        return f"Erro ao gerar carta: {e}"
