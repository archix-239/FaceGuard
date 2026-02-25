"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface ThreatGaugeProps {
  level: number; // 0 to 100
  className?: string;
}

export function ThreatGauge({ level, className }: ThreatGaugeProps) {
  // Determine color based on level
  const getColor = (val: number) => {
    if (val < 33) return "text-emerald-500";
    if (val < 66) return "text-amber-500";
    return "text-destructive";
  };

  const getBgColor = (val: number) => {
    if (val < 33) return "bg-emerald-500";
    if (val < 66) return "bg-amber-500";
    return "bg-destructive";
  };

  const getLabel = (val: number) => {
    if (val < 33) return "SÉCURISÉ";
    if (val < 66) return "VIGILANCE";
    return "CRITIQUE";
  };

  return (
    <div className={cn("flex flex-col items-center justify-center p-4 bg-card rounded-xl border shadow-sm", className)}>
      <div className="relative h-32 w-32 flex items-center justify-center">
        {/* Background Circle */}
        <svg className="h-full w-full -rotate-90">
          <circle
            cx="64"
            cy="64"
            r="58"
            fill="transparent"
            stroke="currentColor"
            strokeWidth="8"
            className="text-muted/20"
          />
          {/* Progress Circle */}
          <motion.circle
            cx="64"
            cy="64"
            r="58"
            fill="transparent"
            stroke="currentColor"
            strokeWidth="8"
            strokeDasharray="364.42"
            initial={{ strokeDashoffset: 364.42 }}
            animate={{ strokeDashoffset: 364.42 - (364.42 * level) / 100 }}
            transition={{ duration: 1, ease: "easeOut" }}
            className={getColor(level)}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span
            key={level}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className={cn("text-3xl font-bold tabular-nums", getColor(level))}
          >
            {level}%
          </motion.span>
        </div>
      </div>
      <div className="mt-4 flex flex-col items-center">
        <span className="text-[10px] font-bold tracking-widest text-muted-foreground uppercase">Niveau de Menace</span>
        <div className={cn("mt-1 px-3 py-0.5 rounded-full text-[10px] font-bold text-white", getBgColor(level))}>
          {getLabel(level)}
        </div>
      </div>
    </div>
  );
}
