"""Azure Speech Service — text-to-speech (replaces Kokoro)."""
import azure.cognitiveservices.speech as speechsdk

from app.config import settings


def get_speech_config() -> speechsdk.SpeechConfig:
    if not settings.is_azure_speech_configured:
        raise RuntimeError(
            "Azure Speech is not configured (AZURE_SPEECH_KEY and AZURE_SPEECH_REGION)."
        )
    config = speechsdk.SpeechConfig(
        subscription=settings.azure_speech_key,
        region=settings.azure_speech_region,
    )
    # WAV (RIFF 16kHz 16bit mono) so frontend can play with Audio element
    config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm
    )
    return config


def synthesize_to_bytes(
    text: str,
    *,
    voice_name: str | None = None,
) -> bytes:
    """
    Synthesize text to speech and return audio as bytes (WAV).
    Uses a neural voice by default (e.g. en-US-JennyNeural).
    """
    config = get_speech_config()
    if voice_name:
        config.speech_synthesis_voice_name = voice_name
    else:
        config.speech_synthesis_voice_name = "en-US-JennyNeural"

    # Synthesize to in-memory stream
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=config, audio_config=None)
    result = synthesizer.speak_text_async(text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return result.audio_data
    if result.reason == speechsdk.ResultReason.Canceled:
        cancellation = result.cancellation_details
        raise RuntimeError(
            f"Speech synthesis canceled: {cancellation.reason}. {cancellation.error_details}"
        )
    raise RuntimeError(f"Speech synthesis failed: {result.reason}")
