"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Plus,
  Settings2,
  Trash2,
  Globe,
  Activity,
  Signal,
  SignalLow
} from "lucide-react";

const mockDevices = [
  { id: 1, name: "Caméra_Pont_Bascule_1", ip: "192.168.1.50", rtsp: "rtsp://admin:****@192.168.1.50:554/live", status: "online", zone: "Entrée Nord" },
  { id: 2, name: "Caméra_Sortie_A", ip: "192.168.1.51", rtsp: "rtsp://admin:****@192.168.1.51:554/live", status: "online", zone: "Hangar 2" },
  { id: 3, name: "Caméra_Quai_4", ip: "192.168.1.52", rtsp: "rtsp://admin:****@192.168.1.52:554/live", status: "offline", zone: "Déchargement" },
];

export default function DevicesPage() {
  return (
    <div className="p-6 space-y-6 flex flex-col h-full overflow-y-auto">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Gestion des Caméras</h1>
          <p className="text-muted-foreground text-sm">Administration des flux vidéo et zones de détection</p>
        </div>
        <Button className="gap-2">
          <Plus className="h-4 w-4" />
          Ajouter une Caméra
        </Button>
      </header>

      <div className="grid grid-cols-1 gap-4">
        {mockDevices.map((device) => (
          <div key={device.id} className="p-6 rounded-xl border bg-card flex items-center justify-between group">
            <div className="flex items-center gap-6">
              <div className={`h-12 w-12 rounded-full flex items-center justify-center ${device.status === 'online' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-destructive/10 text-destructive'}`}>
                {device.status === 'online' ? <Signal className="h-6 w-6" /> : <SignalLow className="h-6 w-6" />}
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-3">
                  <h3 className="font-bold">{device.name}</h3>
                  <Badge variant={device.status === 'online' ? 'success' : 'destructive'}>
                    {device.status.toUpperCase()}
                  </Badge>
                </div>
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1"><Globe className="h-3 w-3" /> {device.ip}</span>
                  <span className="flex items-center gap-1 font-mono">{device.rtsp}</span>
                  <span className="font-semibold text-primary/80 uppercase tracking-wider">{device.zone}</span>
                </div>
              </div>
            </div>

            <div className="flex gap-2">
              <Button variant="outline" size="icon" className="h-9 w-9">
                <Activity className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="icon" className="h-9 w-9">
                <Settings2 className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="icon" className="h-9 w-9 text-destructive hover:bg-destructive/10">
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        ))}
      </div>

      <div className="p-8 border-2 border-dashed rounded-xl flex flex-col items-center justify-center text-center space-y-4 opacity-60">
         <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center">
            <Plus className="h-6 w-6 text-muted-foreground" />
         </div>
         <div>
           <p className="text-sm font-semibold">Ajouter un nouveau flux RTSP</p>
           <p className="text-xs text-muted-foreground max-w-xs">FaceGuard supporte la majorité des caméras IP industrielles (H.264/H.265).</p>
         </div>
      </div>
    </div>
  );
}
