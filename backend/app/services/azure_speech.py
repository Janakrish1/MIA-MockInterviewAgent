"""Azure Speech Service — text-to-speech (replaces Kokoro). Uses REST API to avoid SDK codec timeout."""
import html
import urllib.request

from app.config import settings

# REST avoids the SDK's "Codec decoding is not started within 2s" timeout
TTS_OUTPUT_FORMAT = "riff-16khz-16bit-mono-pcm"  # WAV, 16kHz, 16-bit mono
DEFAULT_VOICE = "en-US-JennyNeural"


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
