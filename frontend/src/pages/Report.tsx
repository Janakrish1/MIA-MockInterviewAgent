import { motion } from "framer-motion";
import {
  TrendingUp,
  TrendingDown,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import ScoreCard from "@/components/ScoreCard";

const MOCK_SCORES = [
  { label: "Problem Solving", score: 8, max: 10 },
  { label: "Conceptual Understanding", score: 6, max: 10 },
  { label: "Communication", score: 7, max: 10 },
  { label: "Code Quality", score: 5, max: 10 },
  { label: "Time Management", score: 9, max: 10 },
];

const STRENGTHS = [
  "Clear problem decomposition approach",
  "Strong grasp of tree traversal patterns",
  "Good time management across questions",
];

const IMPROVEMENTS = [
  "Edge case handling needs more rigor",
  "Space complexity analysis was incomplete",
  "Could improve code readability with better naming",
];

const Report = () => {
  const navigate = useNavigate();
  const totalScore = MOCK_SCORES.reduce((s, c) => s + c.score, 0);
  const totalMax = MOCK_SCORES.reduce((s, c) => s + c.max, 0);
  const overallPct = Math.round((totalScore / totalMax) * 100);

  return (
    <div className="min-h-screen px-6 pt-24 pb-16">
      <div className="container mx-auto max-w-4xl">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12 text-center"
        >
          <h1 className="mb-2 text-3xl font-bold text-foreground">
            Interview Report
          </h1>
          <p className="text-muted-foreground">
            Data Structures · 5 Questions · 28 min
          </p>
        </motion.div>

        {/* Overall score */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="mb-10 flex flex-col items-center rounded-2xl border border-border bg-card p-8"
        >
          <div className="relative mb-4">
            <svg className="h-32 w-32" viewBox="0 0 120 120">
              <circle
                cx="60"
                cy="60"
                r="52"
                fill="none"
                stroke="hsl(var(--muted))"
                strokeWidth="8"
              />
              <motion.circle
                cx="60"
                cy="60"
                r="52"
                fill="none"
                stroke="hsl(var(--primary))"
                strokeWidth="8"
                strokeLinecap="round"
                strokeDasharray={`${overallPct * 3.27} 327`}
                transform="rotate(-90 60 60)"
                initial={{ strokeDasharray: "0 327" }}
                animate={{
                  strokeDasharray: `${overallPct * 3.27} 327`,
                }}
                transition={{ delay: 0.3, duration: 1, ease: "easeOut" }}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="font-mono text-3xl font-bold text-foreground">
                {overallPct}%
              </span>
            </div>
          </div>
          <span className="text-sm text-muted-foreground">Overall Score</span>
        </motion.div>

        {/* Score breakdown */}
        <div className="mb-10 grid gap-4 md:grid-cols-2">
          {MOCK_SCORES.map((s, i) => (
            <ScoreCard
              key={s.label}
              label={s.label}
              score={s.score}
              maxScore={s.max}
              delay={i * 0.1}
            />
          ))}
        </div>

        {/* Strengths & Improvements */}
        <div className="mb-10 grid gap-6 md:grid-cols-2">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5 }}
            className="rounded-xl border border-border bg-card p-6"
          >
            <div className="mb-4 flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-success" />
              <h3 className="font-semibold text-foreground">Strengths</h3>
            </div>
            <ul className="space-y-3">
              {STRENGTHS.map((s) => (
                <li key={s} className="flex items-start gap-2 text-sm">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" />
                  <span className="text-muted-foreground">{s}</span>
                </li>
              ))}
            </ul>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.6 }}
            className="rounded-xl border border-border bg-card p-6"
          >
            <div className="mb-4 flex items-center gap-2">
              <TrendingDown className="h-5 w-5 text-warning" />
              <h3 className="font-semibold text-foreground">
                Areas for Improvement
              </h3>
            </div>
            <ul className="space-y-3">
              {IMPROVEMENTS.map((s) => (
                <li key={s} className="flex items-start gap-2 text-sm">
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
                  <span className="text-muted-foreground">{s}</span>
                </li>
              ))}
            </ul>
          </motion.div>
        </div>

        {/* CTA */}
        <div className="text-center">
          <Button
            size="lg"
            onClick={() => navigate("/interview")}
            className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90 glow-primary"
          >
            Try Another Interview
            <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Report;
