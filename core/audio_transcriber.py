"""
Módulo de Transcrição de Áudio — 3 métodos OpenAI.

1. Whisper API:      $0.006/min — batch, manda áudio inteiro, recebe texto
2. GPT-4o Audio:     $0.04/min  — LLM processa áudio nativo, entende contexto
3. Realtime API:     $0.06/min  — streaming WebSocket, transcrição ao vivo

Cada método retorna a transcrição em texto.
A diarização continua sendo feita pelo Agente 1 (LLM).
"""

import os
import base64
import json
import logging
import tempfile

logger = logging.getLogger(__name__)


def _get_openai_client():
    """Retorna cliente OpenAI com API key do ambiente."""
    from openai import OpenAI
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY não configurada. Adicione ao ~/.zshrc ou .env")
    return OpenAI(api_key=api_key)


# ============================================================
# Método 1: Whisper API (batch)
# ============================================================
# O mais barato e testado. Manda o áudio inteiro, recebe texto.
# Sem diarização nativa — o Agente Diarizador cuida disso.
# Suporta: mp3, mp4, mpeg, mpga, m4a, wav, webm
# Limite: 25MB por arquivo

def transcribe_whisper(audio_bytes: bytes, filename: str = "audio.webm") -> dict:
    """
    Transcreve áudio via Whisper API.

    Args:
        audio_bytes: Conteúdo do arquivo de áudio em bytes.
        filename: Nome do arquivo (extensão define o formato).

    Returns:
        dict com {text, method, cost_estimate, details}
    """
    client = _get_openai_client()

    # Whisper precisa de um file-like object com nome
    with tempfile.NamedTemporaryFile(suffix=os.path.splitext(filename)[1], delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="pt",
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )

        # Estimar duração e custo
        segments = response.segments or []
        duration_sec = segments[-1].end if segments else 0
        duration_min = duration_sec / 60
        cost = duration_min * 0.006

        return {
            "text": response.text,
            "method": "Whisper API",
            "cost_estimate": f"${cost:.3f}",
            "duration_min": round(duration_min, 1),
            "segments": [
                {"start": s.start, "end": s.end, "text": s.text}
                for s in segments
            ],
            "details": f"whisper-1 · {round(duration_min, 1)} min · ${cost:.3f}",
        }
    finally:
        os.unlink(tmp_path)


# ============================================================
# Método 2: GPT-4o Audio (nativo)
# ============================================================
# Manda o áudio direto como input do chat. O LLM "ouve" o áudio
# e pode entender entonação, hesitação, quem pergunta vs responde.
# Mais caro que Whisper, mas potencialmente melhor para diarização
# porque o LLM já pode marcar [MÉDICO] vs [PACIENTE] direto.

def transcribe_gpt4o_audio(audio_bytes: bytes, filename: str = "audio.wav") -> dict:
    """
    Transcreve e diariza via GPT-4o Audio input.
    O LLM ouve o áudio e já retorna transcrição com marcadores de speaker.

    Args:
        audio_bytes: Conteúdo do arquivo de áudio em bytes.
        filename: Nome do arquivo.

    Returns:
        dict com {text, method, cost_estimate, details, already_diarized}
    """
    client = _get_openai_client()

    # Detectar formato pelo nome do arquivo
    ext = os.path.splitext(filename)[1].lower().strip(".")
    format_map = {"wav": "wav", "mp3": "mp3", "webm": "webm", "m4a": "m4a", "ogg": "ogg"}
    audio_format = format_map.get(ext, "wav")

    # Encode áudio em base64
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    response = client.chat.completions.create(
        model="gpt-4o-audio-preview",
        messages=[
            {
                "role": "system",
                "content": (
                    "Você é um transcritor médico especializado. "
                    "Transcreva o áudio da consulta cardiológica fielmente. "
                    "Identifique quem fala: [MÉDICO] para o profissional de saúde "
                    "e [PACIENTE] para o paciente. "
                    "Mantenha o texto original sem correções. "
                    "Formato:\n"
                    "[MÉDICO] texto...\n"
                    "[PACIENTE] texto...\n"
                    "Se ambíguo, use [MÉDICO?] ou [PACIENTE?]."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": audio_b64,
                            "format": audio_format,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Transcreva esta consulta médica identificando quem fala.",
                    },
                ],
            },
        ],
    )

    text = response.choices[0].message.content
    usage = response.usage
    # GPT-4o audio input: ~$0.04/min estimado via tokens
    input_tokens = usage.prompt_tokens if usage else 0
    output_tokens = usage.completion_tokens if usage else 0
    cost = (input_tokens * 0.0025 / 1000) + (output_tokens * 0.01 / 1000)

    return {
        "text": text,
        "method": "GPT-4o Audio",
        "cost_estimate": f"${cost:.3f}",
        "duration_min": None,  # Não temos duração direta
        "already_diarized": True,  # GPT-4o já diariza no output
        "details": f"gpt-4o-audio-preview · {input_tokens} in + {output_tokens} out tokens · ${cost:.3f}",
    }


# ============================================================
# Método 3: Realtime API (streaming)
# ============================================================
# WebSocket bidirecional. Transcrição em tempo real, frase a frase.
# O mais caro, mas o único que mostra texto DURANTE a consulta.
# Implementação simplificada para sandbox — processa áudio batch
# via WebSocket para demonstrar o conceito.

def transcribe_realtime(audio_bytes: bytes, filename: str = "audio.wav", on_partial=None) -> dict:
    """
    Transcreve via Realtime API (WebSocket).
    Para sandbox: envia áudio pré-gravado e processa os eventos.
    Em produção: seria conectado ao microfone ao vivo.

    Args:
        audio_bytes: Conteúdo do áudio.
        filename: Nome do arquivo.
        on_partial: Callback chamado a cada frase parcial (para streaming UI).

    Returns:
        dict com {text, method, cost_estimate, details, partial_transcripts}
    """
    import websocket  # pip install websocket-client

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY não configurada.")

    url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview"
    headers = [
        f"Authorization: Bearer {api_key}",
        "OpenAI-Beta: realtime=v1",
    ]

    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    partials = []
    full_text = ""

    ws = websocket.create_connection(url, header=headers, timeout=60)

    try:
        # Configurar sessão
        ws.send(json.dumps({
            "type": "session.update",
            "session": {
                "input_audio_transcription": {
                    "model": "whisper-1",
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                },
            },
        }))

        # Enviar áudio em chunks de 32KB
        chunk_size = 32 * 1024
        for i in range(0, len(audio_b64), chunk_size):
            chunk = audio_b64[i:i + chunk_size]
            ws.send(json.dumps({
                "type": "input_audio_buffer.append",
                "audio": chunk,
            }))

        # Sinalizar fim do áudio
        ws.send(json.dumps({"type": "input_audio_buffer.commit"}))

        # Coletar transcrições
        done = False
        timed_out = False
        while not done:
            try:
                msg = ws.recv()
                event = json.loads(msg)
                event_type = event.get("type", "")

                if event_type == "conversation.item.input_audio_transcription.completed":
                    transcript = event.get("transcript", "")
                    if transcript.strip():
                        partials.append(transcript.strip())
                        full_text += transcript.strip() + "\n"
                        if on_partial:
                            on_partial(transcript.strip())

                elif event_type == "error":
                    error_msg = event.get("error", {}).get("message", "Erro desconhecido")
                    raise RuntimeError(f"Realtime API error: {error_msg}")

                elif event_type in ("response.done", "session.closed"):
                    done = True

            except websocket.WebSocketTimeoutException:
                logger.warning("WebSocket timeout — transcription may be incomplete")
                done = True
                timed_out = True

    finally:
        ws.close()

    # Custo estimado: $0.06/min input audio
    # Sem duração exata, estimamos pelo tamanho do áudio
    estimated_min = len(audio_bytes) / (16000 * 2 * 60)  # assumindo 16kHz 16bit mono
    cost = estimated_min * 0.06

    result = {
        "text": full_text.strip(),
        "method": "Realtime API",
        "cost_estimate": f"${cost:.3f}",
        "duration_min": round(estimated_min, 1),
        "partial_transcripts": partials,
        "details": f"gpt-4o-realtime-preview · ~{round(estimated_min, 1)} min · ${cost:.3f}",
    }

    if timed_out:
        result["incomplete"] = True
        result["text"] += "\n\n[AVISO: Transcrição possivelmente incompleta — conexão WebSocket expirou por timeout]"

    return result


# ============================================================
# Dispatch — chamado pelo app.py
# ============================================================

METHODS = {
    "🎙️ Whisper ($0.006/min)": "whisper",
    "🧠 GPT-4o Audio ($0.04/min)": "gpt4o_audio",
    "⚡ Realtime ($0.06/min)": "realtime",
}


def transcribe(audio_bytes: bytes, method: str, filename: str = "audio.webm", on_partial=None) -> dict:
    """
    Dispatch para o método escolhido.

    Args:
        audio_bytes: Conteúdo do áudio.
        method: "whisper", "gpt4o_audio" ou "realtime".
        filename: Nome do arquivo.
        on_partial: Callback para streaming (só Realtime).

    Returns:
        dict com {text, method, cost_estimate, details, ...}
    """
    if method == "whisper":
        return transcribe_whisper(audio_bytes, filename)
    elif method == "gpt4o_audio":
        return transcribe_gpt4o_audio(audio_bytes, filename)
    elif method == "realtime":
        return transcribe_realtime(audio_bytes, filename, on_partial)
    else:
        raise ValueError(f"Método desconhecido: {method}")
