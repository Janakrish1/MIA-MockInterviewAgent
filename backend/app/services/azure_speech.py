"""Azure Speech Service — text-to-speech + speech-to-text. Uses REST API to avoid SDK codec timeout."""
import html
import json
import urllib.error
import urllib.request

from app.config import settings

# REST avoids the SDK's "Codec decoding is not started within 2s" timeout
TTS_OUTPUT_FORMAT = "riff-16khz-16bit-mono-pcm"  # WAV, 16kHz, 16-bit mono
DEFAULT_VOICE = "en-US-JennyNeural"
DEFAULT_STT_LANGUAGE = "en-US"


def _get_token() -> str:
    """Fetch Azure Speech token (valid 10 min)."""
    if not settings.azure_speech_key or not settings.azure_speech_region:
        raise RuntimeError("Azure Speech is not configured (AZURE_SPEECH_KEY and AZURE_SPEECH_REGION).")
    url = f"https://{settings.azure_speech_region}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
    req = urllib.request.Request(url, method="POST")
    req.add_header("Ocp-Apim-Subscription-Key", settings.azure_speech_key)
    req.add_header("Content-Length", "0")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read().decode()


def synthesize_to_bytes(
    text: str,
    *,
    voice_name: str | None = None,
) -> bytes:
    """
    Synthesize text to speech via Azure REST TTS. Returns WAV bytes.
    Uses REST instead of SDK to avoid "Codec decoding is not started within 2s" errors.
    """
    if not settings.is_azure_speech_configured:
        raise RuntimeError(
            "Azure Speech is not configured (AZURE_SPEECH_KEY and AZURE_SPEECH_REGION)."
        )
    voice = voice_name or DEFAULT_VOICE
    escaped = html.escape(text.strip())
    ssml = f"""<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
<voice name='{voice}'>{escaped}</voice>
</speak>"""

    token = _get_token()
    url = f"https://{settings.azure_speech_region}.tts.speech.microsoft.com/cognitiveservices/v1"
    req = urllib.request.Request(url, data=ssml.encode("utf-8"), method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/ssml+xml")
    req.add_header("X-Microsoft-OutputFormat", TTS_OUTPUT_FORMAT)
    req.add_header("User-Agent", "MIA-MockInterviewAgent")

    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def transcribe_audio(
    audio_bytes: bytes,
    content_type: str,
    *,
    language: str | None = None,
) -> str:
    """
    Transcribe short-form audio (under ~60s) via Azure Speech-to-Text REST API.

    Args:
        audio_bytes: raw audio payload as produced by the browser's MediaRecorder
            or an uploaded file. Supported formats include WAV (PCM 16-bit mono),
            Ogg Opus, and WebM Opus.
        content_type: MIME type of the audio (e.g. "audio/webm; codecs=opus",
            "audio/ogg; codecs=opus", "audio/wav"). Passed straight through to Azure.
        language: BCP-47 language tag. Defaults to en-US.

    Returns:
        The recognized text (empty string if nothing was recognized).
    """
    if not settings.is_azure_speech_configured:
        raise RuntimeError(
            "Azure Speech is not configured (AZURE_SPEECH_KEY and AZURE_SPEECH_REGION)."
        )
    if not audio_bytes:
        return ""

    lang = language or DEFAULT_STT_LANGUAGE
    url = (
        f"https://{settings.azure_speech_region}.stt.speech.microsoft.com"
        f"/speech/recognition/conversation/cognitiveservices/v1"
        f"?language={lang}&format=detailed"
    )
    req = urllib.request.Request(url, data=audio_bytes, method="POST")
    req.add_header("Ocp-Apim-Subscription-Key", settings.azure_speech_key)
    req.add_header("Content-Type", content_type)
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", "MIA-MockInterviewAgent")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace") if exc.fp else str(exc)
        raise RuntimeError(f"Azure STT HTTP {exc.code}: {detail}") from exc

    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Azure STT returned non-JSON response: {payload}") from exc

    status = (data.get("RecognitionStatus") or "").strip()
    print(
        f"Azure STT response: status={status!r} "
        f"content_type={content_type!r} bytes={len(audio_bytes)}"
    )
    if status and status.lower() != "success":
        # Common non-success statuses: NoMatch, InitialSilenceTimeout, BabbleTimeout.
        return ""

    # "DisplayText" is the best human-readable transcription; fall back through NBest.
    text = (data.get("DisplayText") or "").strip()
    if text:
        return text
    nbest = data.get("NBest") or []
    if nbest:
        return str(nbest[0].get("Display") or nbest[0].get("Lexical") or "").strip()
    return ""
