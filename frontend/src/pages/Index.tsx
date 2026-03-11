import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import {
  Brain,
  Mic,
  BarChart3,
  Zap,
  Target,
  MessageSquare,
  ArrowRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import FeatureCard from "@/components/FeatureCard";
import VoiceVisualizer from "@/components/VoiceVisualizer";

const Index = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen">
      {/* Hero */}
      <section className="relative flex min-h-screen items-center justify-center overflow-hidden bg-grid bg-gradient-radial px-6">
        {/* Floating glow orbs */}
        <div className="pointer-events-none absolute left-1/4 top-1/4 h-72 w-72 rounded-full bg-primary/5 blur-[100px]" />
        <div className="pointer-events-none absolute bottom-1/4 right-1/4 h-72 w-72 rounded-full bg-accent/5 blur-[100px]" />

        <div className="relative z-10 mx-auto max-w-4xl text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2"
          >
            <span className="h-2 w-2 rounded-full bg-success animate-pulse" />
            <span className="text-xs font-medium text-muted-foreground">
              AI-Powered Mock Interviews
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.7 }}
            className="mb-6 text-5xl font-bold leading-tight tracking-tight text-foreground md:text-7xl"
          >
            Meet{" "}
            <span className="text-gradient-primary">MIA</span>
            <br />
            <span className="text-3xl font-medium text-muted-foreground md:text-4xl">
              Mock Interview Agent
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25, duration: 0.6 }}
            className="mx-auto mb-10 max-w-2xl text-lg leading-relaxed text-muted-foreground"
          >
            Adaptive AI technical interviews with real-time voice interaction,
            dynamic difficulty scaling, and rubric-based feedback to prepare you
            for software engineering roles.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.6 }}
            className="mb-12 flex flex-col items-center gap-4 sm:flex-row sm:justify-center"
          >
            <Button
              size="lg"
              onClick={() => navigate("/interview")}
              className="gap-2 bg-primary px-8 text-primary-foreground hover:bg-primary/90 glow-primary"
            >
              Start Interview
              <ArrowRight className="h-4 w-4" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              onClick={() => navigate("/report")}
              className="border-border text-foreground hover:bg-secondary"
            >
              View Sample Report
            </Button>
          </motion.div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6, duration: 0.8 }}
          >
            <VoiceVisualizer isActive={true} size="lg" />
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section className="border-t border-border py-24 px-6">
        <div className="container mx-auto max-w-6xl">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="mb-16 text-center"
          >
            <h2 className="mb-4 text-3xl font-bold text-foreground">
              How MIA Works
            </h2>
            <p className="text-muted-foreground">
              An agentic pipeline that simulates real technical interviews
            </p>
          </motion.div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            <FeatureCard
              icon={Brain}
              title="Finetuned Question Generation"
              description="A finetuned Gemma model generates contextual software engineering questions based on your resume and conversation history."
              delay={0}
            />
            <FeatureCard
              icon={Target}
              title="Adaptive Difficulty"
              description="The scoring agent continuously evaluates your responses and dynamically adjusts question complexity to match your skill level."
              delay={0.1}
            />
            <FeatureCard
              icon={Mic}
              title="Voice Interaction"
              description="Kokoro open-source TTS converts questions to natural speech, creating a realistic interview experience."
              delay={0.2}
            />
            <FeatureCard
              icon={MessageSquare}
              title="Multi-Turn Conversations"
              description="The MIA agent orchestrates coherent multi-turn interview flows covering data structures, algorithms, ML, and system design."
              delay={0.3}
            />
            <FeatureCard
              icon={BarChart3}
              title="Rubric-Based Scoring"
              description="Structured feedback across problem-solving, conceptual understanding, communication, and code quality dimensions."
              delay={0.4}
            />
            <FeatureCard
              icon={Zap}
              title="Feedback Loop"
              description="Retry mechanisms with max retries ensure quality question generation and accurate scoring with self-correction."
              delay={0.5}
            />
          </div>
        </div>
      </section>

      {/* Architecture */}
      <section className="border-t border-border py-24 px-6">
        <div className="container mx-auto max-w-4xl text-center">
          <h2 className="mb-4 text-3xl font-bold text-foreground">
            System Architecture
          </h2>
          <p className="mb-12 text-muted-foreground">
            Multi-agent pipeline with feedback loops
          </p>

          <div className="grid gap-4 md:grid-cols-3">
            {[
              { label: "Gemma Model", sub: "Question Generation", color: "border-primary/40" },
              { label: "MIA Agent", sub: "Orchestrator", color: "border-accent/40" },
              { label: "Scoring Agent", sub: "Adaptive Learning", color: "border-success/40" },
            ].map((item, i) => (
              <motion.div
                key={item.label}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15 }}
                className={`rounded-xl border ${item.color} bg-card p-6`}
              >
                <div className="font-mono text-sm font-semibold text-foreground">
                  {item.label}
                </div>
                <div className="mt-1 text-xs text-muted-foreground">{item.sub}</div>
              </motion.div>
            ))}
          </div>

          <div className="mt-6 flex items-center justify-center gap-2 text-xs text-muted-foreground">
            <span className="h-px w-8 bg-border" />
            Feedback Loops with Max Retries
            <span className="h-px w-8 bg-border" />
          </div>

          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="mt-6 inline-flex items-center gap-3 rounded-xl border border-border bg-card px-6 py-4"
          >
            <span className="font-mono text-sm text-foreground">
              TTS (Kokoro)
            </span>
            <span className="text-xs text-muted-foreground">→ Voice Output</span>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-8 px-6">
        <div className="container mx-auto flex items-center justify-between text-xs text-muted-foreground">
          <span>MIA — Mock Interview Agent | University of Pittsburgh</span>
          <span>Raina · Janarthanan · Janani</span>
        </div>
      </footer>
    </div>
  );
};

export default Index;
