import { motion } from "framer-motion";

interface VoiceVisualizerProps {
  isActive: boolean;
  size?: "sm" | "lg";
}

const VoiceVisualizer = ({ isActive, size = "lg" }: VoiceVisualizerProps) => {
  const barCount = size === "lg" ? 24 : 12;
  const barHeight = size === "lg" ? 48 : 24;
  // Fixed-height container so bar animation doesn't affect page layout
  const containerHeight = barHeight + 4;

  return (
    <div
      className="flex items-end justify-center gap-[3px]"
      style={{ height: containerHeight }}
    >
      {Array.from({ length: barCount }).map((_, i) => (
        <motion.div
          key={i}
          className="rounded-full bg-primary shrink-0"
          style={{ width: size === "lg" ? 3 : 2 }}
          animate={
            isActive
              ? {
                  height: [4, barHeight * (0.3 + Math.random() * 0.7), 4],
                }
              : { height: 4 }
          }
          transition={
            isActive
              ? {
                  duration: 0.6 + Math.random() * 0.6,
                  repeat: Infinity,
                  repeatType: "reverse",
                  delay: i * 0.05,
                  ease: "easeInOut",
                }
              : { duration: 0.3 }
          }
        />
      ))}
    </div>
  );
};

export default VoiceVisualizer;
