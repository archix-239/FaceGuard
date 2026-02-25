"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  CheckCircle2,
  AlertCircle,
  ChevronRight,
  UserPlus,
  MessageSquare,
  Play
} from "lucide-react";
import { motion } from "framer-motion";

const initialAlerts = [
  {
    id: "AL-8291",
    time: "14:35:22",
    camera: "Pont-bascule",
    severity: "high",
    reason: "Colère 85% + Asymétrie",
    status: "new",
    image: "/placeholder-face-1.jpg"
  },
  {
    id: "AL-8292",
    time: "14:32:10",
    camera: "Caméra 3",
    severity: "medium",
    reason: "Stress détecté (72%)",
    status: "new",
    image: "/placeholder-face-2.jpg"
  },
  {
    id: "AL-8290",
    time: "14:15:00",
    camera: "Sortie Stock",
    severity: "low",
    reason: "Peur détectée (45%)",
    status: "resolved",
    image: "/placeholder-face-3.jpg"
  },
];

export default function AlertManagement() {
  const [selectedAlert, setSelectedAlert] = useState(initialAlerts[0]);

  return (
    <div className="p-6 h-full flex flex-col gap-6 overflow-hidden">
      <header>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Gestion des Alertes</h1>
        <p className="text-muted-foreground text-sm">Centre de triage et d&apos;aide à la décision IA</p>
      </header>

      <div className="grid grid-cols-12 gap-6 flex-1 min-h-0 overflow-hidden">
        {/* List of alerts */}
        <div className="col-span-12 lg:col-span-5 flex flex-col border rounded-xl bg-card overflow-hidden">
          <div className="p-4 border-b flex items-center justify-between bg-muted/20">
            <span className="text-sm font-semibold">Alertes non traitées</span>
            <Badge variant="destructive">{initialAlerts.filter(a => a.status === 'new').length}</Badge>
          </div>
          <div className="flex-1 overflow-y-auto">
            {initialAlerts.map((alert) => (
              <button
                key={alert.id}
                onClick={() => setSelectedAlert(alert)}
                className={`w-full text-left p-4 border-b last:border-0 transition-colors flex items-center gap-4 ${
                  selectedAlert.id === alert.id ? "bg-primary/5 border-r-4 border-r-primary" : "hover:bg-muted/30"
                }`}
              >
                <div className={`h-10 w-10 rounded-lg flex items-center justify-center shrink-0 ${
                  alert.severity === 'high' ? 'bg-destructive/10 text-destructive' :
                  alert.severity === 'medium' ? 'bg-amber-500/10 text-amber-500' : 'bg-emerald-500/10 text-emerald-500'
                }`}>
                  <AlertCircle className="h-5 w-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold font-mono text-muted-foreground">{alert.id}</span>
                    <span className="text-[10px] text-muted-foreground font-medium">{alert.time}</span>
                  </div>
                  <div className="text-sm font-semibold truncate">{alert.camera}</div>
                  <div className="text-xs text-muted-foreground truncate">{alert.reason}</div>
                </div>
                <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
              </button>
            ))}
          </div>
        </div>

        {/* Alert Details */}
        <div className="col-span-12 lg:col-span-7 flex flex-col border rounded-xl bg-card overflow-hidden">
          {selectedAlert ? (
            <motion.div
              key={selectedAlert.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col h-full"
            >
              <div className="p-6 border-b flex items-center justify-between">
                <div className="flex items-center gap-4">
                   <div className={`h-12 w-12 rounded-xl flex items-center justify-center ${
                     selectedAlert.severity === 'high' ? 'bg-destructive/10 text-destructive' :
                     selectedAlert.severity === 'medium' ? 'bg-amber-500/10 text-amber-500' : 'bg-emerald-500/10 text-emerald-500'
                   }`}>
                     <AlertCircle className="h-6 w-6" />
                   </div>
                   <div>
                     <h2 className="text-lg font-bold">Détails de l&apos;incident {selectedAlert.id}</h2>
                     <p className="text-xs text-muted-foreground">{selectedAlert.camera} • Détecté à {selectedAlert.time}</p>
                   </div>
                </div>
                <Badge variant={selectedAlert.severity === 'high' ? 'destructive' : selectedAlert.severity === 'medium' ? 'warning' : 'success'}>
                  {selectedAlert.severity.toUpperCase()}
                </Badge>
              </div>

              <div className="flex-1 overflow-y-auto p-6 space-y-8">
                <div className="grid grid-cols-2 gap-6">
                  {/* Snapshot */}
                  <div className="space-y-3">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Capture Snapshot</h3>
                    <div className="aspect-square rounded-xl bg-muted border overflow-hidden relative group">
                       <div className="absolute inset-0 flex items-center justify-center opacity-30">
                         <span className="text-[10px] font-mono">IMAGE_SNAPSHOT_DATA</span>
                       </div>
                       {/* Mock AR overlay on snapshot */}
                       <div className="absolute top-4 left-4 border-t-2 border-l-2 border-primary w-8 h-8 opacity-50" />
                       <div className="absolute top-4 right-4 border-t-2 border-r-2 border-primary w-8 h-8 opacity-50" />
                       <div className="absolute bottom-4 left-4 border-b-2 border-l-2 border-primary w-8 h-8 opacity-50" />
                       <div className="absolute bottom-4 right-4 border-b-2 border-r-2 border-primary w-8 h-8 opacity-50" />
                    </div>
                  </div>

                  {/* Video Replay */}
                  <div className="space-y-3">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Replay (±3s)</h3>
                    <div className="aspect-square rounded-xl bg-black border overflow-hidden relative group cursor-pointer flex items-center justify-center">
                       <Play className="h-10 w-10 text-white opacity-50 group-hover:opacity-100 transition-opacity" />
                       <div className="absolute bottom-3 left-3 right-3 h-1 bg-white/20 rounded-full overflow-hidden">
                          <div className="h-full w-1/3 bg-primary" />
                       </div>
                       <div className="absolute top-2 right-2 bg-red-600 text-[8px] font-bold text-white px-1.5 py-0.5 rounded uppercase">Replay</div>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                   <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Analyse IA</h3>
                   <div className="p-4 rounded-xl border bg-muted/20 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Raison principale</span>
                        <span className="text-sm font-semibold">{selectedAlert.reason}</span>
                      </div>
                      <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                         <div className="h-full bg-destructive w-[85%]" />
                      </div>
                      <p className="text-xs text-muted-foreground italic">
                        &quot;L&apos;IA a détecté une micro-expression de colère prolongée couplée à un évitement du regard lors du passage au point de contrôle.&quot;
                      </p>
                   </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="p-6 border-t bg-muted/10 grid grid-cols-3 gap-4">
                <Button variant="outline" className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4" />
                  Fausse alerte
                </Button>
                <Button variant="secondary" className="flex items-center gap-2">
                  <UserPlus className="h-4 w-4" />
                  Intervention
                </Button>
                <Button className="flex items-center gap-2">
                  <MessageSquare className="h-4 w-4" />
                  Signaler Direction
                </Button>
              </div>
            </motion.div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground p-6 text-center">
              <AlertCircle className="h-12 w-12 mb-4 opacity-20" />
              <p>Sélectionnez une alerte pour voir les détails et agir.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
