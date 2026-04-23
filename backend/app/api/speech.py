"""Speech endpoints (TTS + STT) via Azure Speech Service."""
import asyncio

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from app.config import settings
from app.services import azure_speech

router = APIRouter()


class SynthesizeRequest(BaseModel):
    text: str
    voice_name: str | None = None  # e.g. "en-US-JennyNeural"


class TranscribeResponse(BaseModel):
    text: str


@router.post("/synthesize")
async def synthesize(body: SynthesizeRequest):
    """
    Synthesize text to speech using Azure Speech Service.
    Returns WAV audio (16kHz, 16bit, mono) for playback in the browser.
    """
    if not settings.is_azure_speech_configured:
        raise HTTPException(
            status_code=503,
            detail="Azure Speech is not configured. Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION.",
        )
    try:
        audio_bytes = await asyncio.to_thread(
            azure_speech.synthesize_to_bytes,
            body.text,
            voice_name=body.voice_name,
        )
        return Response(
            content=audio_bytes,
            media_type="audio/wav",
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    audio: UploadFile = File(..., description="Short audio clip (<= ~60s)"),
    language: str | None = Form(None, description="BCP-47 tag, e.g. en-US"),
):
    """
    Transcribe a short audio clip (recorded by the candidate in the browser) to text
    using Azure Speech Service's short-audio REST API. Accepts WAV (PCM 16-bit mono),
    Ogg Opus, and WebM Opus. Returns the recognized text as plain text.
    """
    if not settings.is_azure_speech_configured:
        raise HTTPException(
            status_code=503,
            detail="Azure Speech is not configured. Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION.",
        )

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio upload.")

    # Browser's MediaRecorder usually sets a specific codec (e.g. "audio/webm;codecs=opus").
    # Fall back to webm/opus since that is the default MediaRecorder output on Chrome/Edge.
    content_type = audio.content_type or "audio/webm; codecs=opus"

    try:
        text = await asyncio.to_thread(
            azure_speech.transcribe_audio,
            audio_bytes,
            content_type,
            language=language,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    return TranscribeResponse(text=text)
