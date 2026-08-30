import os

import requests

_SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"
_MAX_CHARS = 1500  # bulbul:v2 limit; keep a safe margin under bulbul:v3's 2500


def _get_api_key() -> str:
    api_key = os.environ.get("SARVAM_API_KEY")
    if not api_key:
        raise RuntimeError("SARVAM_API_KEY is not set")
    return api_key


def _chunk_text(text: str, max_chars: int = _MAX_CHARS) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    chunks = []
    remaining = text
    while len(remaining) > max_chars:
        split_at = remaining.rfind(". ", 0, max_chars)
        if split_at == -1:
            split_at = max_chars
        else:
            split_at += 1  # keep the period
        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks


def synthesize(text: str, language_code: str = "en-IN", speaker: str = "shubh") -> list[str]:
    """Returns a list of base64-encoded audio chunks (in order) for the given text."""
    api_key = _get_api_key()
    audios: list[str] = []
    for chunk in _chunk_text(text):
        response = requests.post(
            _SARVAM_TTS_URL,
            headers={
                "api-subscription-key": api_key,
                "Content-Type": "application/json",
            },
            json={
                "text": chunk,
                "language_code": language_code,
                "speaker": speaker,
            },
            timeout=30,
        )
        response.raise_for_status()
        audios.extend(response.json()["audios"])
    return audios
