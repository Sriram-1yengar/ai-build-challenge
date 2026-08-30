import os

import requests

_SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"


def _get_api_key() -> str:
    api_key = os.environ.get("SARVAM_API_KEY")
    if not api_key:
        raise RuntimeError("SARVAM_API_KEY is not set")
    return api_key


def transcribe(audio_bytes: bytes, filename: str = "audio.webm", content_type: str | None = None) -> str:
    """Transcribes+translates spoken audio to English text via Sarvam's
    speech-to-text endpoint (mode="translate" auto-detects the spoken language
    and returns an English transcript, matching Phase 1's transcript_en contract).
    """
    api_key = _get_api_key()
    # Sarvam requires a recognized audio content-type on the multipart file part
    # (a missing/None type is rejected outright) — fall back to webm, which is
    # what the browser's MediaRecorder sends.
    response = requests.post(
        _SARVAM_STT_URL,
        headers={"api-subscription-key": api_key},
        files={"file": (filename, audio_bytes, content_type or "audio/webm")},
        data={
            "language_code": "unknown",
            "mode": "translate",
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["transcript"]
