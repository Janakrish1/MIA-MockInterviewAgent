/**
 * Browser-side audio helpers.
 *
 * Azure Speech short-audio REST only reliably decodes `audio/wav` (PCM 16-bit)
 * and `audio/ogg; codecs=opus`. Browsers' MediaRecorder, however, produces
 * `audio/webm; codecs=opus` on Chrome/Edge and `audio/mp4` on Safari. To make
 * STT work across browsers we decode whatever the MediaRecorder gave us with
 * the Web Audio API, downmix to mono, resample to 16 kHz, and re-encode as
 * a WAV PCM 16-bit blob before uploading.
 */

const TARGET_SAMPLE_RATE = 16000;

/** Decode an encoded audio blob (webm, mp4, ogg, etc.) to an AudioBuffer. */
async function decodeToAudioBuffer(blob: Blob): Promise<AudioBuffer> {
  const AudioCtx: typeof AudioContext =
    window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
  if (!AudioCtx) {
    throw new Error("Web Audio API is not available in this browser.");
  }
  const ctx = new AudioCtx();
  try {
    const arrayBuffer = await blob.arrayBuffer();
    return await ctx.decodeAudioData(arrayBuffer.slice(0));
  } finally {
    await ctx.close();
  }
}

/** Downmix multi-channel audio to mono by averaging channels. */
function toMono(buffer: AudioBuffer): Float32Array {
  const length = buffer.length;
  if (buffer.numberOfChannels === 1) {
    return buffer.getChannelData(0).slice();
  }
  const out = new Float32Array(length);
  for (let ch = 0; ch < buffer.numberOfChannels; ch++) {
    const data = buffer.getChannelData(ch);
    for (let i = 0; i < length; i++) out[i] += data[i];
  }
  const inv = 1 / buffer.numberOfChannels;
  for (let i = 0; i < length; i++) out[i] *= inv;
  return out;
}

/** Linear resample a mono Float32 buffer from inputRate to outputRate. */
function resampleLinear(input: Float32Array, inputRate: number, outputRate: number): Float32Array {
  if (inputRate === outputRate) return input;
  const ratio = inputRate / outputRate;
  const outputLength = Math.round(input.length / ratio);
  const output = new Float32Array(outputLength);
  for (let i = 0; i < outputLength; i++) {
    const srcIdx = i * ratio;
    const lower = Math.floor(srcIdx);
    const upper = Math.min(input.length - 1, lower + 1);
    const weight = srcIdx - lower;
    output[i] = input[lower] * (1 - weight) + input[upper] * weight;
  }
  return output;
}

/** Encode a mono Float32 PCM buffer (at sampleRate) as a 16-bit WAV blob. */
function encodeWav16Mono(samples: Float32Array, sampleRate: number): Blob {
  const bytesPerSample = 2;
  const dataSize = samples.length * bytesPerSample;
  const buffer = new ArrayBuffer(44 + dataSize);
  const view = new DataView(buffer);

  const writeString = (offset: number, str: string) => {
    for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i));
  };

  // RIFF header.
  writeString(0, "RIFF");
  view.setUint32(4, 36 + dataSize, true);
  writeString(8, "WAVE");
  // fmt chunk.
  writeString(12, "fmt ");
  view.setUint32(16, 16, true); // PCM fmt chunk size
  view.setUint16(20, 1, true); // PCM format
  view.setUint16(22, 1, true); // mono
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * bytesPerSample, true); // byte rate
  view.setUint16(32, bytesPerSample, true); // block align
  view.setUint16(34, 16, true); // bits per sample
  // data chunk.
  writeString(36, "data");
  view.setUint32(40, dataSize, true);

  // PCM samples (clip to [-1, 1] and convert to int16).
  let offset = 44;
  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    offset += 2;
  }

  return new Blob([buffer], { type: "audio/wav" });
}

/**
 * Convert any browser-recorded audio blob (webm/opus, mp4/aac, ogg, etc.)
 * into a WAV PCM 16-bit mono blob at 16 kHz, suitable for Azure STT.
 */
export async function convertRecordingToWav16kMono(blob: Blob): Promise<Blob> {
  const audioBuffer = await decodeToAudioBuffer(blob);
  const mono = toMono(audioBuffer);
  const resampled = resampleLinear(mono, audioBuffer.sampleRate, TARGET_SAMPLE_RATE);
  return encodeWav16Mono(resampled, TARGET_SAMPLE_RATE);
}
