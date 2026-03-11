import { motion } from "framer-motion";

interface ScoreCardProps {
  label: string;
  score: number;
  maxScore: number;
  delay?: number;
}

const ScoreCard = ({ label, score, maxScore, delay = 0 }: ScoreCardProps) => {
  const pct = (score / maxScore) * 100;
  const color =
    pct >= 75 ? "bg-success" : pct >= 50 ? "bg-warning" : "bg-destructive";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5 }}
      className="rounded-lg border border-border bg-card p-4"
    >
      <div className="mb-2 flex items-center justify-between">
        <span className="text-sm text-muted-foreground">{label}</span>
        <span className="font-mono text-sm font-semibold text-foreground">
          {score}/{maxScore}
        </span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
        <motion.div
          className={`h-full rounded-full ${color}`}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ delay: delay + 0.3, duration: 0.8, ease: "easeOut" }}
        />
      </div>
    </motion.div>
  );
};

export default ScoreCard;
