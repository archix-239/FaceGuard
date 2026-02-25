"use client";

import { motion, AnimatePresence } from "framer-motion";
import { AlertCircle, Clock } from "lucide-react";

const mockAlerts = [
  { id: 1, time: "14:32", camera: "Caméra 3", message: "Stress détecté", severity: "medium" },
  { id: 2, time: "14:35", camera: "Pont-bascule", message: "Colère élevée", severity: "high" },
  { id: 3, time: "14:40", camera: "Sortie Stock", message: "Comportement suspect", severity: "low" },
];

export function AlertTicker() {
  return (
    <div className="flex flex-col h-full bg-card border rounded-xl overflow-hidden shadow-sm">
      <div className="p-4 border-b bg-muted/30 flex items-center justify-between">
        <h3 className="text-sm font-semibold flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-primary" />
          Fil d&apos;actualité
        </h3>
        <span className="text-[10px] bg-primary/10 text-primary px-2 py-0.5 rounded-full font-medium">LIVE</span>
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        <AnimatePresence initial={false}>
          {mockAlerts.map((alert) => (
            <motion.div
              key={alert.id}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="p-3 rounded-lg border bg-background/50 flex flex-col gap-1"
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold text-muted-foreground flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {alert.time}
                </span>
                <div className={`h-2 w-2 rounded-full ${
                  alert.severity === 'high' ? 'bg-destructive' :
                  alert.severity === 'medium' ? 'bg-amber-500' : 'bg-emerald-500'
                }`} />
              </div>
              <div className="text-xs font-semibold">{alert.camera}</div>
              <div className="text-xs text-muted-foreground">{alert.message}</div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
