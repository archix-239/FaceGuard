"use client";

import { useState } from "react";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import {
  ShieldCheck,
  Eye,
  Zap,
  BrainCircuit,
  Save,
  RotateCcw
} from "lucide-react";

export default function IASettingsPage() {
  const [threatThreshold, setThreatThreshold] = useState([75]);
  const [nightVision, setNightVision] = useState(true);
  const [asymmetry, setAsymmetry] = useState(true);
  const [privacy, setPrivacy] = useState(false);

  return (
    <div className="p-6 space-y-6 flex flex-col h-full overflow-y-auto">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Configuration IA (FaceGuard)</h1>
          <p className="text-muted-foreground text-sm">Réglage fin du moteur de détection et des filtres de vision</p>
        </div>
        <div className="flex gap-2">
           <Button variant="outline" className="gap-2">
             <RotateCcw className="h-4 w-4" />
             Réinitialiser
           </Button>
           <Button className="gap-2">
             <Save className="h-4 w-4" />
             Sauvegarder
           </Button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Detection Engine */}
        <div className="space-y-6">
          <div className="flex items-center gap-2 mb-4 text-primary">
            <BrainCircuit className="h-5 w-5" />
            <h2 className="text-lg font-bold">Moteur de Détection</h2>
          </div>

          <div className="p-6 rounded-xl border bg-card space-y-8">
            <div className="space-y-4">
               <div className="flex justify-between items-center">
                 <Label className="text-sm font-semibold">Seuil d&apos;alerte critique (%)</Label>
                 <span className="text-xs font-mono bg-primary/10 text-primary px-2 py-0.5 rounded font-bold">{threatThreshold}%</span>
               </div>
               <Slider
                 value={threatThreshold}
                 onValueChange={setThreatThreshold}
                 max={100}
                 step={1}
               />
               <p className="text-[10px] text-muted-foreground">
                 Définit le score de menace minimal pour déclencher une &quot;Alerte Rouge&quot;. Un seuil plus bas augmente la sensibilité mais peut générer plus de faux positifs.
               </p>
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <Label className="text-sm font-semibold">Détection d&apos;Asymétrie Faciale</Label>
                <p className="text-[10px] text-muted-foreground">Analyse les micro-mouvements faciaux non coordonnés.</p>
              </div>
              <Switch checked={asymmetry} onCheckedChange={setAsymmetry} />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <Label className="text-sm font-semibold">Analyse de Micro-expressions</Label>
                <p className="text-[10px] text-muted-foreground">Capture les émotions fugaces (peur, colère, mépris).</p>
              </div>
              <Switch defaultChecked />
            </div>
          </div>
        </div>

        {/* Vision & Privacy */}
        <div className="space-y-6">
          <div className="flex items-center gap-2 mb-4 text-primary">
            <Eye className="h-5 w-5" />
            <h2 className="text-lg font-bold">Vision & Confidentialité</h2>
          </div>

          <div className="p-6 rounded-xl border bg-card space-y-8">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <Label className="text-sm font-semibold text-foreground flex items-center gap-2">
                  Filtre Vision Nocturne (CLAHE)
                  <Zap className="h-3 w-3 text-amber-500 fill-amber-500" />
                </Label>
                <p className="text-[10px] text-muted-foreground">Améliore le contraste en basse luminosité (recommandé 24h/24).</p>
              </div>
              <Switch checked={nightVision} onCheckedChange={setNightVision} />
            </div>

            <div className="flex items-center justify-between border-t pt-8">
              <div className="space-y-1">
                <Label className="text-sm font-semibold flex items-center gap-2">
                  Mode &quot;Privacy&quot; (Floutage)
                  <ShieldCheck className="h-3 w-3 text-blue-500" />
                </Label>
                <p className="text-[10px] text-muted-foreground">Floute les visages sur le Live Monitoring (l&apos;IA continue l&apos;analyse en arrière-plan).</p>
              </div>
              <Switch checked={privacy} onCheckedChange={setPrivacy} />
            </div>

            <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
               <div className="flex gap-3">
                 <BrainCircuit className="h-5 w-5 text-primary shrink-0" />
                 <div className="space-y-1">
                   <p className="text-xs font-bold uppercase tracking-wider text-primary">Info Modèle</p>
                   <p className="text-xs text-muted-foreground italic">
                     &quot;ConvNeXt-Base entraîné sur 450k images. Dernière mise à jour: 12/05/2024. Latence actuelle: 18ms.&quot;
                   </p>
                 </div>
               </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
