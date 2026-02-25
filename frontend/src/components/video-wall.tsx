"use client";

import { Maximize2, Camera } from "lucide-react";

const cameras = [
  { id: 1, name: "Pont-bascule 01", location: "Entrée Nord" },
  { id: 2, name: "Sortie Stock A", location: "Hangar 2" },
  { id: 3, name: "Zone Déchargement", location: "Quai 4" },
  { id: 4, name: "Parking Employés", location: "Zone Sud" },
];

export function VideoWall() {
  return (
    <div className="grid grid-cols-2 gap-4 h-full">
      {cameras.map((cam) => (
        <div key={cam.id} className="group relative aspect-video bg-muted rounded-xl border overflow-hidden shadow-sm">
          {/* Mock Video Content */}
          <div className="absolute inset-0 flex items-center justify-center opacity-20">
            <Camera className="h-12 w-12" />
          </div>

          {/* AR Overlay Mock (YouTube Look) */}
          <div className="absolute inset-0 p-4 flex flex-col justify-between pointer-events-none">
            <div className="flex justify-between items-start">
              <div className="bg-black/60 backdrop-blur-md px-2 py-1 rounded text-[10px] font-mono text-white flex flex-col">
                <span>REC ● 1080p</span>
                <span>CAM_{cam.id}</span>
              </div>
              <button className="pointer-events-auto p-1.5 bg-black/40 hover:bg-black/60 rounded-full text-white transition-colors">
                <Maximize2 className="h-4 w-4" />
              </button>
            </div>

            <div className="flex justify-between items-end">
              <div className="bg-black/60 backdrop-blur-md px-2 py-1 rounded text-[10px] font-mono text-white">
                {cam.name} - {cam.location}
              </div>
              {/* Fake detection box if cam.id is 1 or 2 */}
              {(cam.id === 1 || cam.id === 3) && (
                 <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-40 border border-primary/50 flex flex-col justify-start p-1">
                    <div className="bg-primary/20 text-[8px] text-primary px-1 font-bold">HUMAN DETECTED</div>
                    {/* Wireframe lines mock */}
                    <div className="flex-1 relative overflow-hidden">
                       <div className="absolute inset-0 opacity-20 bg-[radial-gradient(circle,_var(--primary)_1px,_transparent_1px)] bg-[size:4px_4px]" />
                    </div>
                 </div>
              )}
            </div>
          </div>

          {/* Hover state */}
          <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
        </div>
      ))}
    </div>
  );
}
