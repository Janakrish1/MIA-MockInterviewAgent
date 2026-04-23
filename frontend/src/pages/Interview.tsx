import { useState, useCallback, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Mic,
  MicOff,
  Send,
  Clock,
  ChevronRight,
  Volume2,
  Loader2,
  AlertCircle,
  Upload,
  FileText,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import VoiceVisualizer from "@/components/VoiceVisualizer";
import {
  getFirstQuestionFromInterview,
  getNextAgentMessageFromInterview,
  uploadResume,
  synthesizeSpeech,
  playAudio,
  transcribeSpeech,
  type ChatMessage,
} from "@/lib/api";
import { convertRecordingToWav16kMono } from "@/lib/audio";
import { useToast } from "@/hooks/use-toast";
import { useNavigate } from "react-router-dom";

type Message = {
  role: "agent" | "user";
  content: string;
  timestamp: string;
  /** Difficulty of this question (easy/medium/hard) — from LangGraph adapt_difficulty; only set on agent messages. */
  difficulty?: string | null;
};

const INTRO_PROMPT =
  "Hi, I am MIA, your interviewer today. To get started, could you please introduce yourself and briefly highlight your recent software engineering experience?";

function formatElapsed(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

const Interview = () => {
  const [phase, setPhase] = useState<"setup" | "active">("setup");
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [textInput, setTextInput] = useState("");
  const interviewDomain = "Software Engineering";
  const [resumeSummary, setResumeSummary] = useState("");
  const [resumeFileName, setResumeFileName] = useState<string | null>(null);
  const [resumeUploading, setResumeUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [agentThinking, setAgentThinking] = useState(false);
  const [backendError, setBackendError] = useState<string | null>(null);
  const [speakingIndex, setSpeakingIndex] = useState<number | null>(null);
  const [currentDifficulty, setCurrentDifficulty] = useState<string | null>(null);
  const { toast } = useToast();
  const navigate = useNavigate();
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const interviewIdRef = useRef<string>(crypto.randomUUID());
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    if (phase !== "active") return;
    timerRef.current = setInterval(() => setElapsedSeconds((s) => s + 1), 1000);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [phase]);

  const speakAgentMessage = useCallback(async (text: string, msgIndex: number) => {
    if (!text.trim()) return;
    setSpeakingIndex(msgIndex);
    try {
      const blob = await synthesizeSpeech(text);
      await playAudio(blob);
    } catch (e) {
      toast({
        title: "Speech playback failed",
        description: e instanceof Error ? e.message : "Could not play audio",
        variant: "destructive",
      });
    } finally {
      setSpeakingIndex(null);
    }
  }, [toast]);

  const startInterview = useCallback(async () => {
    setPhase("active");
    setBackendError(null);
    setCurrentDifficulty(null);
    setMessages([{ role: "agent", content: INTRO_PROMPT, timestamp: "00:00" }]);
    await speakAgentMessage(INTRO_PROMPT, 0);
  }, [resumeSummary, speakAgentMessage, toast]);

  const handleSend = useCallback(async () => {
    const content = textInput.trim();
    if (!content) return;

    const timestamp = formatElapsed(elapsedSeconds);
    const userMsg: Message = { role: "user", content, timestamp };
    setMessages((prev) => [...prev, userMsg]);
    setTextInput("");
    setBackendError(null);
    setAgentThinking(true);

    const currentQuestion = messages.filter((m) => m.role === "agent").pop()?.content ?? "";
    const conversationHistory: ChatMessage[] = messages.map((m) => ({
      role: m.role === "agent" ? "assistant" : "user",
      content: m.content,
    }));
    conversationHistory.push({ role: "user", content });

    try {
      const firstTechnicalTurn =
        messages.length === 1 &&
        messages[0]?.role === "agent" &&
        messages[0]?.content === INTRO_PROMPT;
      const { question, difficulty } = firstTechnicalTurn
        ? await getFirstQuestionFromInterview(
            interviewIdRef.current,
            resumeSummary,
            conversationHistory
          )
        : await getNextAgentMessageFromInterview(
            interviewIdRef.current,
            resumeSummary,
            conversationHistory,
            content,
            currentQuestion
          );
      const nextTimestamp = formatElapsed(elapsedSeconds);
      const agentMsg: Message = {
        role: "agent",
        content: question,
        timestamp: nextTimestamp,
        difficulty: difficulty ?? undefined,
      };
      if (difficulty) setCurrentDifficulty(difficulty);
      setMessages((prev) => [...prev, agentMsg]);
      const newIndex = messages.length + 2;
      await speakAgentMessage(question, newIndex);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Request failed";
      setBackendError(msg);
      toast({
        title: "Could not get next question",
        description: msg,
        variant: "destructive",
      });
    } finally {
      setAgentThinking(false);
    }
  }, [textInput, elapsedSeconds, messages, resumeSummary, speakAgentMessage, toast]);

  const endInterviewAndViewReport = useCallback(() => {
    const interviewId = encodeURIComponent(interviewIdRef.current);
    navigate(`/report?interviewId=${interviewId}&elapsed=${elapsedSeconds}`);
  }, [elapsedSeconds, navigate]);

  const stopRecording = useCallback(() => {
    const rec = mediaRecorderRef.current;
    if (rec && rec.state !== "inactive") {
      rec.stop();
    }
    const stream = mediaStreamRef.current;
    if (stream) {
      stream.getTracks().forEach((t) => t.stop());
      mediaStreamRef.current = null;
    }
    setIsRecording(false);
  }, []);

  const startRecording = useCallback(async () => {
    if (typeof navigator === "undefined" || !navigator.mediaDevices?.getUserMedia) {
      toast({
        title: "Microphone not supported",
        description: "Your browser does not expose getUserMedia. Please use a recent Chrome, Edge, or Safari build.",
        variant: "destructive",
      });
      return;
    }
    if (typeof MediaRecorder === "undefined") {
      toast({
        title: "Recording not supported",
        description: "Your browser does not support MediaRecorder. Please use Chrome, Edge, or Safari.",
        variant: "destructive",
      });
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;

      // Prefer Opus codecs that Azure STT accepts directly.
      const preferredMimeTypes = [
        "audio/webm;codecs=opus",
        "audio/ogg;codecs=opus",
        "audio/webm",
      ];
      const mimeType =
        preferredMimeTypes.find((t) => MediaRecorder.isTypeSupported?.(t)) || "";

      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];

      recorder.ondataavailable = (e: BlobEvent) => {
        if (e.data && e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        const chunks = audioChunksRef.current;
        audioChunksRef.current = [];
        if (!chunks.length) return;
        const type = recorder.mimeType || mimeType || "audio/webm";
        const recordedBlob = new Blob(chunks, { type });
        setIsTranscribing(true);
        try {
          // Azure STT short-audio REST only reliably accepts WAV PCM or Ogg/Opus,
          // so we always transcode the browser's recording (usually webm/opus or mp4)
          // to 16kHz mono WAV before upload.
          const wavBlob = await convertRecordingToWav16kMono(recordedBlob);
          const transcript = await transcribeSpeech(wavBlob);
          if (!transcript) {
            toast({
              title: "Couldn't catch that",
              description: "No speech was recognized. Please speak a bit longer or closer to the mic.",
            });
            return;
          }
          setTextInput((prev) => (prev ? `${prev} ${transcript}`.trim() : transcript));
        } catch (e) {
          toast({
            title: "Transcription failed",
            description: e instanceof Error ? e.message : "Unknown error",
            variant: "destructive",
          });
        } finally {
          setIsTranscribing(false);
        }
      };

      recorder.start();
      setIsRecording(true);
    } catch (e) {
      toast({
        title: "Microphone access denied",
        description: e instanceof Error ? e.message : "Please allow microphone access and try again.",
        variant: "destructive",
      });
      setIsRecording(false);
    }
  }, [toast]);

  const toggleRecording = useCallback(() => {
    if (isRecording) {
      stopRecording();
    } else {
      void startRecording();
    }
  }, [isRecording, startRecording, stopRecording]);

  useEffect(() => {
    return () => {
      // Cleanup on unmount: stop any active recording + release the mic.
      const rec = mediaRecorderRef.current;
      if (rec && rec.state !== "inactive") {
        try { rec.stop(); } catch { /* ignore */ }
      }
      const stream = mediaStreamRef.current;
      if (stream) stream.getTracks().forEach((t) => t.stop());
    };
  }, []);

  if (phase === "setup") {
    return (
      <div className="flex min-h-screen items-center justify-center px-6 pt-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-lg"
        >
          <h1 className="mb-2 text-3xl font-bold text-foreground">
            Setup Interview
          </h1>
          <p className="mb-8 text-muted-foreground">
            Configure your mock interview session
          </p>

          {/* Resume: upload PDF or paste */}
          <div className="mb-6">
            <label className="mb-2 block text-sm font-medium text-foreground">
              Resume (optional)
            </label>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,application/pdf"
              className="hidden"
              onChange={async (e) => {
                const f = e.target.files?.[0];
                if (!f) return;
                setResumeUploading(true);
                try {
                  const { resume_text } = await uploadResume(f);
                  setResumeSummary(resume_text);
                  setResumeFileName(f.name);
                  toast({ title: "Resume uploaded", description: "Text extracted. You can edit below if needed." });
                } catch (err) {
                  toast({
                    title: "Upload failed",
                    description: err instanceof Error ? err.message : "Could not upload PDF",
                    variant: "destructive",
                  });
                } finally {
                  setResumeUploading(false);
                  e.target.value = "";
                }
              }}
            />
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="gap-2 border-border"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={resumeUploading}
                >
                  {resumeUploading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Upload className="h-4 w-4" />
                  )}
                  {resumeUploading ? "Uploading…" : "Upload PDF"}
                </Button>
                {resumeFileName && (
                  <span className="flex items-center gap-1 text-xs text-muted-foreground">
                    <FileText className="h-3 w-3" />
                    {resumeFileName}
                    <button
                      type="button"
                      className="rounded p-0.5 hover:bg-muted"
                      onClick={() => {
                        setResumeFileName(null);
                        setResumeSummary("");
                      }}
                      aria-label="Clear resume"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                )}
              </div>
              <Textarea
                value={resumeSummary}
                onChange={(e) => setResumeSummary(e.target.value)}
                placeholder="Or paste a short summary of your background so MIA can tailor questions (skills, experience, role)."
                className="min-h-[80px] resize-none border-border bg-card text-sm"
              />
            </div>
          </div>

          {/* Interview domain */}
          <div className="mb-8">
            <label className="mb-2 block text-sm font-medium text-foreground">
              Interview Domain
            </label>
            <div className="rounded-xl border border-primary/30 bg-primary/10 px-4 py-3 text-sm text-foreground">
              {interviewDomain}
            </div>
          </div>

          <Button
            size="lg"
            className="w-full gap-2 bg-primary text-primary-foreground hover:bg-primary/90 glow-primary"
            onClick={startInterview}
            disabled={agentThinking}
          >
            {agentThinking ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Connecting to MIA...
              </>
            ) : (
              <>
                Begin Interview
                <ChevronRight className="h-4 w-4" />
              </>
            )}
          </Button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col overflow-hidden pt-16">
      {/* Top bar */}
      <div className="shrink-0 border-b border-border bg-card/50 px-6 py-3">
        <div className="container mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="rounded-md bg-primary/10 px-2 py-1 font-mono text-xs text-primary">
              {interviewDomain}
            </span>
            {currentDifficulty && (
              <span className="rounded-md bg-muted px-2 py-1 text-xs text-muted-foreground">
                {currentDifficulty}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Clock className="h-4 w-4" />
            <span className="font-mono text-sm">{formatElapsed(elapsedSeconds)}</span>
            <Button
              variant="outline"
              size="sm"
              className="ml-3"
              onClick={endInterviewAndViewReport}
            >
              End Interview & View Report
            </Button>
          </div>
        </div>
      </div>

      {/* Main area */}
      <div className="flex-1 overflow-hidden">
        <div className="container mx-auto flex h-full max-w-4xl flex-col px-6 py-6">
          {/* Backend error banner */}
          {backendError && (
            <div className="mb-4 shrink-0 flex items-center gap-2 rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-2 text-sm text-destructive">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{backendError}</span>
            </div>
          )}

          {/* Agent thinking indicator */}
          {agentThinking && (
            <div className="mb-4 shrink-0 flex items-center gap-2 rounded-xl border border-primary/20 bg-primary/5 px-4 py-3 text-sm text-primary">
              <Loader2 className="h-4 w-4 animate-spin shrink-0" />
              <span>MIA is thinking...</span>
            </div>
          )}

          {/* Messages */}
          <div className="flex-1 space-y-4 overflow-y-auto pb-4">
            <AnimatePresence>
              {messages.map((msg, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                  className={`flex ${
                    msg.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl px-5 py-4 ${
                      msg.role === "user"
                        ? "bg-primary/10 border border-primary/20"
                        : "bg-card border border-border"
                    }`}
                  >
                    <div className="mb-1 flex items-center gap-2 flex-wrap">
                      <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                        {msg.role === "agent" ? "MIA" : "You"}
                      </span>
                      {msg.role === "agent" && msg.difficulty && (
                        <span
                          className={`rounded px-1.5 py-0.5 font-mono text-[10px] font-medium ${
                            msg.difficulty === "easy"
                              ? "bg-green-500/20 text-green-600 dark:text-green-400"
                              : msg.difficulty === "hard"
                                ? "bg-amber-500/20 text-amber-600 dark:text-amber-400"
                                : "bg-blue-500/20 text-blue-600 dark:text-blue-400"
                          }`}
                        >
                          {msg.difficulty}
                        </span>
                      )}
                      <span className="font-mono text-[10px] text-muted-foreground">
                        {msg.timestamp}
                      </span>
                      {msg.role === "agent" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 shrink-0 p-0 text-muted-foreground hover:text-foreground"
                          onClick={() => speakAgentMessage(msg.content, i)}
                          disabled={speakingIndex === i}
                          title="Play question aloud"
                        >
                          {speakingIndex === i ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : (
                            <Volume2 className="h-3 w-3" />
                          )}
                        </Button>
                      )}
                    </div>
                    <p className="text-sm leading-relaxed text-foreground">
                      {msg.content}
                    </p>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>

          {/* Voice visualizer */}
          {(isRecording || isTranscribing) && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-4 shrink-0 flex items-center justify-center rounded-xl border border-primary/20 bg-primary/5 py-4"
            >
              <VoiceVisualizer isActive={isRecording} size="sm" />
              <span className="ml-4 text-xs text-primary">
                {isRecording ? "Listening... click mic to stop" : "Transcribing..."}
              </span>
            </motion.div>
          )}

          {/* Input area */}
          <div className="shrink-0 rounded-xl border border-border bg-card p-3">
            <Textarea
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder={
                isRecording
                  ? "Recording... speak your answer"
                  : isTranscribing
                    ? "Transcribing your voice..."
                    : "Type your answer or click the mic to speak..."
              }
              className="min-h-[60px] resize-none border-0 bg-transparent text-sm text-foreground placeholder:text-muted-foreground focus-visible:ring-0"
              disabled={isRecording || isTranscribing}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
            />
            <div className="mt-2 flex items-center justify-between">
              <Button
                variant="ghost"
                size="sm"
                onClick={toggleRecording}
                disabled={isTranscribing || agentThinking}
                className={isRecording ? "text-primary" : "text-muted-foreground"}
                title={isRecording ? "Stop recording" : "Record your answer"}
              >
                {isTranscribing ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : isRecording ? (
                  <MicOff className="h-4 w-4" />
                ) : (
                  <Mic className="h-4 w-4" />
                )}
              </Button>
              <Button
                size="sm"
                onClick={handleSend}
                disabled={!textInput.trim() || agentThinking || isRecording || isTranscribing}
                className="gap-1 bg-primary text-primary-foreground hover:bg-primary/90"
              >
                {agentThinking ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <>
                    Send
                    <Send className="h-3 w-3" />
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Interview;
