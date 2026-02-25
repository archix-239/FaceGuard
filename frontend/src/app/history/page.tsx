"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Search,
  Filter,
  Download,
  Calendar as CalendarIcon,
  Video,
  ExternalLink
} from "lucide-react";

const mockLogs = [
  { id: "LOG-001", date: "2024-05-20", time: "02:15:22", cam: "Porte Sud", event: "Peur", score: 88, status: "Vérifié" },
  { id: "LOG-002", date: "2024-05-20", time: "03:42:10", cam: "Porte Sud", event: "Peur", score: 92, status: "Vérifié" },
  { id: "LOG-003", date: "2024-05-19", time: "22:15:00", cam: "Sortie Stock", event: "Colère", score: 75, status: "Archivé" },
  { id: "LOG-004", date: "2024-05-19", time: "18:30:45", cam: "Pont-bascule", event: "Tristesse", score: 45, status: "Ignoré" },
  { id: "LOG-005", date: "2024-05-19", time: "14:20:12", cam: "Hangar A", event: "Surprise", score: 62, status: "Archivé" },
];

export default function HistoryPage() {
  return (
    <div className="p-6 space-y-6 flex flex-col h-full overflow-hidden">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Historique & Logs</h1>
          <p className="text-muted-foreground text-sm">Recherche avancée et exportations d&apos;incidents</p>
        </div>
        <Button className="gap-2">
          <Download className="h-4 w-4" />
          Exporter Rapport
        </Button>
      </header>

      <div className="flex gap-4 items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            placeholder="Rechercher par caméra, émotion ou ID..."
            className="w-full bg-card border rounded-md pl-10 pr-4 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>
        <Button variant="outline" className="gap-2">
          <CalendarIcon className="h-4 w-4" />
          Date
        </Button>
        <Button variant="outline" className="gap-2">
          <Filter className="h-4 w-4" />
          Filtres
        </Button>
      </div>

      <div className="border rounded-xl bg-card overflow-hidden flex-1 flex flex-col min-h-0">
        <div className="overflow-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-muted/50 text-muted-foreground uppercase text-[10px] font-bold sticky top-0">
              <tr>
                <th className="px-6 py-3">ID Log</th>
                <th className="px-6 py-3">Date & Heure</th>
                <th className="px-6 py-3">Caméra</th>
                <th className="px-6 py-3">Émotion Détectée</th>
                <th className="px-6 py-3">Score IA</th>
                <th className="px-6 py-3">Statut</th>
                <th className="px-6 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {mockLogs.map((log) => (
                <tr key={log.id} className="hover:bg-muted/30 transition-colors">
                  <td className="px-6 py-4 font-mono text-xs">{log.id}</td>
                  <td className="px-6 py-4">
                    <div className="flex flex-col">
                      <span>{log.date}</span>
                      <span className="text-xs text-muted-foreground">{log.time}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 font-medium">{log.cam}</td>
                  <td className="px-6 py-4">
                    <Badge variant="secondary">{log.event}</Badge>
                  </td>
                  <td className="px-6 py-4">
                     <div className="flex items-center gap-2">
                       <div className="flex-1 w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                          <div
                            className={`h-full ${log.score > 80 ? 'bg-destructive' : 'bg-primary'}`}
                            style={{ width: `${log.score}%` }}
                          />
                       </div>
                       <span className="text-[10px] font-bold">{log.score}%</span>
                     </div>
                  </td>
                  <td className="px-6 py-4 text-xs font-medium">{log.status}</td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex justify-end gap-2">
                      <Button size="icon" variant="ghost" className="h-8 w-8">
                        <Video className="h-4 w-4" />
                      </Button>
                      <Button size="icon" variant="ghost" className="h-8 w-8">
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="p-4 border-t bg-muted/20 text-xs text-muted-foreground flex justify-between items-center">
          <span>Affichage de 5 incidents sur 128 trouvés</span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled>Précédent</Button>
            <Button variant="outline" size="sm">Suivant</Button>
          </div>
        </div>
      </div>
    </div>
  );
}
