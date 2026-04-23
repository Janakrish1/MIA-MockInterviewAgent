import { motion } from "framer-motion";
import {
  TrendingUp,
  TrendingDown,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import ScoreCard from "@/components/ScoreCard";
import { getInterviewReport, type InterviewReportResponse } from "@/lib/api";

function formatDuration(totalSeconds: number): string {
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${m}m ${s.toString().padStart(2, "0")}s`;
}

const Report = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const interviewId = searchParams.get("interviewId") ?? "";
  const elapsed = Number(searchParams.get("elapsed") ?? "0");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<InterviewReportResponse | null>(null);

  useEffect(() => {
    if (!interviewId) {
      setLoading(false);
      setError("No interview session found. Start an interview first.");
      return;
    }
    let active = true;
    setLoading(true);
    setError(null);
    getInterviewReport(interviewId)
      .then((data) => {
        if (!active) return;
        setReport(data);
      })
      .catch((err) => {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Could not load report");
      })
      .finally(() => {
        if (!active) return;
        setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [interviewId]);

  const entries = report?.feedback_entries ?? [];
  const average = report?.average_score ?? 0;
  const overallPct = Math.round((average / 5) * 100);

  const scoreCards = useMemo(() => {
    const high = entries.filter((e) => typeof e.score === "number" && e.score >= 4).length;
    const mid = entries.filter((e) => typeof e.score === "number" && e.score === 3).length;
    const low = entries.filter((e) => typeof e.score === "number" && e.score <= 2).length;
    const consistency = entries.length ? Math.round((high / entries.length) * 10) : 0;
    const progress = entries.length ? Math.round(((high + mid) / entries.length) * 10) : 0;
    const confidence = Math.min(10, entries.length * 2);
    return [
      { label: "Answer Quality", score: Math.round(average * 2), max: 10 },
      { label: "Consistency", score: consistency, max: 10 },
      { label: "Interview Progress", score: progress || confidence, max: 10 },
      { label: "Areas To Improve", score: 10 - Math.min(10, low * 2), max: 10 },
    ];
  }, [entries, average]);

  const strengths = entries
    .filter((e) => typeof e.score === "number" && e.score >= 4 && e.feedback)
    .slice(0, 3)
    .map((e) => e.feedback);

  const improvements = entries
    .filter((e) => typeof e.score === "number" && e.score <= 3 && e.feedback)
    .slice(0, 3)
    .map((e) => e.feedback);

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
            Software Engineering · {report?.total_answers_scored ?? 0} Answers · {formatDuration(elapsed)}
          </p>
        </motion.div>

        {loading && (
          <div className="mb-8 rounded-xl border border-border bg-card p-6 text-center text-muted-foreground">
            Loading report...
          </div>
        )}

        {error && (
          <div className="mb-8 rounded-xl border border-destructive/40 bg-destructive/10 p-6 text-center text-destructive">
            {error}
          </div>
        )}

        {!loading && !error && !report && (
          <div className="mb-8 rounded-xl border border-border bg-card p-6 text-center text-muted-foreground">
            No report data found for this interview.
          </div>
        )}

        {report && (
          <>

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
          {scoreCards.map((s, i) => (
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
              {(strengths.length ? strengths : ["Strong engagement shown during the interview session."]).map((s) => (
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
              {(improvements.length ? improvements : ["Add more technical depth and explicit trade-off analysis in answers."]).map((s) => (
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
            Start New Interview
            <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
          </>
        )}
      </div>
    </div>
  );
};

export default Report;
