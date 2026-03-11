import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Mic,
  MicOff,
  Send,
  Clock,
  ChevronRight,
  Upload,
  Code,
  Brain,
  Settings2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import VoiceVisualizer from "@/components/VoiceVisualizer";

type Message = {
  role: "agent" | "user";
  content: string;
  timestamp: string;
};

const MOCK_QUESTION =
  "Given a binary tree, write a function to check if it is a valid binary search tree (BST). Explain your approach and analyze the time and space complexity.";

const TOPICS = [
  { label: "Data Structures", icon: Code },
  { label: "Algorithms", icon: Brain },
  { label: "System Design", icon: Settings2 },
];

const Interview = () => {
  const [phase, setPhase] = useState<"setup" | "active">("setup");
  const [isRecording, setIsRecording] = useState(false);
  const [textInput, setTextInput] = useState("");
  const [selectedTopic, setSelectedTopic] = useState("Data Structures");
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "agent",
      content: MOCK_QUESTION,
      timestamp: "00:00",
    },
  ]);
  const [elapsed, setElapsed] = useState("05:32");

  const handleSend = () => {
    if (!textInput.trim()) return;
    setMessages((prev) => [
      ...prev,
      { role: "user", content: textInput, timestamp: elapsed },
    ]);
    setTextInput("");
    // Mock follow-up
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          role: "agent",
          content:
            "Good approach! Can you walk me through how you'd handle the case where the tree has duplicate values? Also, could you optimize the space complexity?",
          timestamp: elapsed,
        },
      ]);
    }, 1500);
  };

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

          {/* Resume Upload */}
          <div className="mb-6">
            <label className="mb-2 block text-sm font-medium text-foreground">
              Resume (optional)
            </label>
            <div className="flex cursor-pointer items-center justify-center rounded-xl border-2 border-dashed border-border bg-card px-6 py-10 transition-colors hover:border-primary/30">
              <div className="text-center">
                <Upload className="mx-auto mb-2 h-8 w-8 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">
                  Drop your resume or click to upload
                </span>
              </div>
            </div>
          </div>

          {/* Topic */}
          <div className="mb-8">
            <label className="mb-2 block text-sm font-medium text-foreground">
              Focus Area
            </label>
            <div className="grid grid-cols-3 gap-3">
              {TOPICS.map(({ label, icon: Icon }) => (
                <button
                  key={label}
                  onClick={() => setSelectedTopic(label)}
                  className={`flex flex-col items-center gap-2 rounded-xl border p-4 transition-all ${
                    selectedTopic === label
                      ? "border-primary/50 bg-primary/10 glow-primary"
                      : "border-border bg-card hover:border-primary/20"
                  }`}
                >
                  <Icon
                    className={`h-5 w-5 ${
                      selectedTopic === label
                        ? "text-primary"
                        : "text-muted-foreground"
                    }`}
                  />
                  <span className="text-xs font-medium text-foreground">
                    {label}
                  </span>
                </button>
              ))}
            </div>
          </div>

          <Button
            size="lg"
            className="w-full gap-2 bg-primary text-primary-foreground hover:bg-primary/90 glow-primary"
            onClick={() => setPhase("active")}
          >
            Begin Interview
            <ChevronRight className="h-4 w-4" />
          </Button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col pt-16">
      {/* Top bar */}
      <div className="border-b border-border bg-card/50 px-6 py-3">
        <div className="container mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="rounded-md bg-primary/10 px-2 py-1 font-mono text-xs text-primary">
              {selectedTopic}
            </span>
            <span className="text-xs text-muted-foreground">
              Question 1 of 5
            </span>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Clock className="h-4 w-4" />
            <span className="font-mono text-sm">{elapsed}</span>
          </div>
        </div>
      </div>

      {/* Main area */}
      <div className="flex flex-1 flex-col container mx-auto max-w-4xl px-6 py-6">
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
                  <div className="mb-1 flex items-center gap-2">
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                      {msg.role === "agent" ? "MIA" : "You"}
                    </span>
                    <span className="font-mono text-[10px] text-muted-foreground">
                      {msg.timestamp}
                    </span>
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
        {isRecording && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-4 flex items-center justify-center rounded-xl border border-primary/20 bg-primary/5 py-4"
          >
            <VoiceVisualizer isActive={true} size="sm" />
            <span className="ml-4 text-xs text-primary">Listening...</span>
          </motion.div>
        )}

        {/* Input area */}
        <div className="rounded-xl border border-border bg-card p-3">
          <Textarea
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            placeholder="Type your answer or use voice..."
            className="min-h-[60px] resize-none border-0 bg-transparent text-sm text-foreground placeholder:text-muted-foreground focus-visible:ring-0"
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
              onClick={() => setIsRecording(!isRecording)}
              className={isRecording ? "text-primary" : "text-muted-foreground"}
            >
              {isRecording ? (
                <MicOff className="h-4 w-4" />
              ) : (
                <Mic className="h-4 w-4" />
              )}
            </Button>
            <Button
              size="sm"
              onClick={handleSend}
              disabled={!textInput.trim()}
              className="gap-1 bg-primary text-primary-foreground hover:bg-primary/90"
            >
              Send
              <Send className="h-3 w-3" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Interview;
