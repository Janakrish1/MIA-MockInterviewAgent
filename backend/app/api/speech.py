"""Text-to-speech via Azure Speech Service (replaces Kokoro)."""
import asyncio

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from app.config import settings
from app.services import azure_speech

router = APIRouter()


class SynthesizeRequest(BaseModel):
    text: str
    voice_name: str | None = None  # e.g. "en-US-JennyNeural"


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
