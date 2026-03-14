"""Azure Speech Service — text-to-speech (replaces Kokoro)."""
import struct

import azure.cognitiveservices.speech as speechsdk

from app.config import settings


def _wav_header_for_pcm(num_samples: int, sample_rate: int = 16000, channels: int = 1) -> bytes:
    """Build a minimal WAV header for 16-bit mono PCM (so browsers can play it)."""
    byte_rate = sample_rate * channels * 2  # 16-bit = 2 bytes per sample
    block_align = channels * 2
    data_size = num_samples * 2
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,  # fmt chunk size (PCM)
        1,   # audio format (PCM)
        channels,
        sample_rate,
        byte_rate,
        block_align,
        16,  # bits per sample
        b"data",
        data_size,
    )
    return header


def get_speech_config() -> speechsdk.SpeechConfig:
    if not settings.is_azure_speech_configured:
        raise RuntimeError(
            "Azure Speech is not configured (AZURE_SPEECH_KEY and AZURE_SPEECH_REGION)."
        )
    config = speechsdk.SpeechConfig(
        subscription=settings.azure_speech_key,
        region=settings.azure_speech_region,
    )
    # Raw PCM avoids the RIFF codec path that can timeout ("Codec decoding is not started within 2s")
    config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Raw16Khz16BitMonoPcm
    )
    return config


def synthesize_to_bytes(
    text: str,
    *,
    voice_name: str | None = None,
) -> bytes:
    """
    Synthesize text to speech and return audio as bytes (WAV).
    Uses raw PCM from SDK then prepends WAV header for browser playback.
    """
    config = get_speech_config()
    if voice_name:
        config.speech_synthesis_voice_name = voice_name
    else:
        config.speech_synthesis_voice_name = "en-US-JennyNeural"

    synthesizer = speechsdk.SpeechSynthesizer(speech_config=config, audio_config=None)
    result = synthesizer.speak_text_async(text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        pcm_data = result.audio_data
        if not pcm_data:
            raise RuntimeError("Speech synthesis returned no audio data")
        # 16kHz, 16-bit mono: 2 bytes per sample
        num_samples = len(pcm_data) // 2
        header = _wav_header_for_pcm(num_samples, sample_rate=16000, channels=1)
        return header + pcm_data
    if result.reason == speechsdk.ResultReason.Canceled:
        cancellation = result.cancellation_details
        raise RuntimeError(
            f"Speech synthesis canceled: {cancellation.reason}. {cancellation.error_details}"
        )
    raise RuntimeError(f"Speech synthesis failed: {result.reason}")
