import { VideoWall } from "@/components/video-wall";
import { ThreatGauge } from "@/components/threat-gauge";
import { AlertTicker } from "@/components/alert-ticker";
import { Shield } from "lucide-react";

export default function DashboardPage() {
  return (
    <div className="p-6 space-y-6 flex flex-col h-full overflow-hidden">
      <header className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Surveillance Live</h1>
          <p className="text-muted-foreground text-sm flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
            </span>
            Système opérationnel • 4 caméras en ligne
          </p>
        </div>
        <div className="flex gap-4">
          <div className="flex flex-col items-end">
             <span className="text-[10px] font-bold text-muted-foreground uppercase">Mode Actuel</span>
             <span className="text-sm font-semibold flex items-center gap-1.5">
               <Shield className="h-4 w-4 text-primary" />
               Protection Active
             </span>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-12 gap-6 flex-1 min-h-0 overflow-hidden">
        {/* Main Monitoring Area */}
        <div className="col-span-12 lg:col-span-9 flex flex-col gap-6 min-h-0">
           <div className="flex-1 min-h-0">
             <VideoWall />
           </div>
        </div>

        {/* Sidebar Info */}
        <div className="col-span-12 lg:col-span-3 flex flex-col gap-6 overflow-y-auto">
          <ThreatGauge level={42} />
          <div className="flex-1 min-h-0">
            <AlertTicker />
          </div>
        </div>
      </div>
    </div>
  );
}
