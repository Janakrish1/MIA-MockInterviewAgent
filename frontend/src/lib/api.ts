/**
 * Backend API client for MIA (Mock Interview Agent).
 * Chat = Azure OpenAI, TTS = Azure Speech Service.
 */

const getBaseUrl = () =>
  (import.meta.env.VITE_API_URL as string) || "http://localhost:8000";

export type ChatMessage = { role: "system" | "user" | "assistant"; content: string };

export async function chatCompletion(messages: ChatMessage[]): Promise<string> {
  const res = await fetch(`${getBaseUrl()}/api/chat/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      messages,
      max_completion_tokens: 1024,
      temperature: 1.0,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail?: string }).detail || `Chat failed: ${res.status}`);
  }
  const data = (await res.json()) as { content: string };
  return data.content;
}

export async function synthesizeSpeech(text: string, voiceName?: string): Promise<Blob> {
  const res = await fetch(`${getBaseUrl()}/api/speech/synthesize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, voice_name: voiceName }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail?: string }).detail || `TTS failed: ${res.status}`);
  }
  return res.blob();
}

/** Play TTS blob in the browser (WAV from Azure Speech). */
export function playAudio(blob: Blob): Promise<void> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio.onended = () => {
      URL.revokeObjectURL(url);
      resolve();
    };
    audio.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("Audio playback failed"));
    };
    audio.play().catch(reject);
  });
}

/** Get first interviewer question from backend, then optionally speak it. */
export async function getFirstQuestion(focusArea: string): Promise<string> {
  const systemPrompt = `You are MIA, a Mock Interview Agent. You conduct technical software engineering interviews. 
Ask one clear, focused interview question at a time. Be concise and professional. 
The candidate's focus area is: ${focusArea}.`;
  const content = await chatCompletion([
    { role: "system", content: systemPrompt },
    { role: "user", content: "Start the interview. Ask the first question only." },
  ]);
  return content.trim();
}

/** Get the next interviewer message (follow-up or next question) given conversation history. */
export async function getNextAgentMessage(
  focusArea: string,
  conversationHistory: ChatMessage[]
): Promise<string> {
  const systemPrompt = `You are MIA, a Mock Interview Agent. You conduct technical software engineering interviews. 
Ask one follow-up question or give brief feedback, then one new question if appropriate. Be concise. 
Focus area: ${focusArea}.`;
  const messages: ChatMessage[] = [
    { role: "system", content: systemPrompt },
    ...conversationHistory,
  ];
  const content = await chatCompletion(messages);
  return content.trim();
}
