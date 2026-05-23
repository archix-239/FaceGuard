'use client'

import { useState } from 'react'
import clsx from 'clsx'
import {
  Save, RotateCcw, Sliders, Shield, Eye, EyeOff, Brain,
  Zap, Clock, Camera, Info, AlertTriangle, CheckCircle
} from 'lucide-react'
import { defaultAISettings, type AISettings } from '@/lib/mockData'
import { Card } from '@/components/ui/Card'

function Toggle({ checked, onChange, label, description, icon, danger = false }: {
  checked: boolean
  onChange: (v: boolean) => void
  label: string
  description?: string
  icon?: React.ReactNode
  danger?: boolean
}) {
  return (
    <div className={clsx(
      'flex items-center justify-between p-3 rounded-xl border transition-all',
      checked
        ? danger ? 'bg-threat-high/5 border-threat-high/20' : 'bg-accent-orange/5 border-accent-orange/20'
        : 'bg-bg-elevated border-bg-border'
    )}>
      <div className="flex items-center gap-3">
        {icon && (
          <div className={clsx(
            'p-1.5 rounded-lg border flex-shrink-0',
            checked
              ? danger ? 'bg-threat-high/10 border-threat-high/20 text-threat-high' : 'bg-accent-orange/10 border-accent-orange/20 text-accent-orange'
              : 'bg-bg-card border-bg-border text-text-muted'
          )}>
            {icon}
          </div>
        )}
        <div>
          <p className="text-xs font-semibold text-text-primary">{label}</p>
          {description && <p className="text-[11px] text-text-muted mt-0.5">{description}</p>}
        </div>
      </div>
      <label className="toggle-switch flex-shrink-0 ml-4">
        <input type="checkbox" checked={checked} onChange={e => onChange(e.target.checked)} />
        <span className="toggle-slider" />
      </label>
    </div>
  )
}

function SliderField({ label, value, min, max, step = 1, unit = '%', onChange, warning }: {
  label: string; value: number; min: number; max: number; step?: number; unit?: string
  onChange: (v: number) => void; warning?: string
}) {
  const pct = ((value - min) / (max - min)) * 100
  const color = value >= 85 ? '#ef4444' : value >= 70 ? '#f97316' : '#22c55e'

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-[11px] text-text-secondary font-medium">{label}</label>
        <span className="font-mono text-sm font-bold" style={{ color }}>{value}{unit}</span>
      </div>
      <div className="relative">
        <div className="absolute top-1/2 -translate-y-1/2 left-0 right-0 h-1.5 bg-bg-border rounded-full pointer-events-none">
          <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, background: color }} />
        </div>
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={e => onChange(Number(e.target.value))}
          className="relative w-full"
          style={{ background: 'transparent' }}
        />
      </div>
      <div className="flex justify-between text-[10px] text-text-muted font-mono">
        <span>{min}{unit}</span>
        <span>{Math.round((min + max) / 2)}{unit}</span>
        <span>{max}{unit}</span>
      </div>
      {warning && (
        <p className="flex items-center gap-1.5 text-[10px] text-threat-medium">
          <AlertTriangle className="w-3 h-3 flex-shrink-0" />
          {warning}
        </p>
      )}
    </div>
  )
}

// Save notification
function SaveToast({ visible }: { visible: boolean }) {
  return (
    <div className={clsx(
      'fixed bottom-6 right-6 flex items-center gap-3 px-4 py-3 bg-bg-card border border-threat-low/30 rounded-xl shadow-lg transition-all duration-300',
      visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4 pointer-events-none'
    )}>
      <CheckCircle className="w-4 h-4 text-threat-low" />
      <div>
        <p className="text-xs font-semibold text-text-primary">Configuration sauvegardée</p>
        <p className="text-[11px] text-text-muted">Les paramètres seront appliqués au prochain cycle</p>
      </div>
    </div>
  )
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<AISettings>(defaultAISettings)
  const [saved, setSaved] = useState(false)

  const update = <K extends keyof AISettings>(key: K, value: AISettings[K]) => {
    setSettings(prev => ({ ...prev, [key]: value }))
  }

  const handleSave = () => {
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  const handleReset = () => {
    if (confirm('Réinitialiser tous les paramètres aux valeurs par défaut ?')) {
      setSettings(defaultAISettings)
    }
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-4xl mx-auto space-y-5 pb-6">
        {/* Header actions */}
        <div className="flex items-center justify-between">
          <div className="p-3 bg-accent-orange/5 border border-accent-orange/20 rounded-xl flex items-start gap-3 flex-1 mr-4">
            <Info className="w-4 h-4 text-accent-orange flex-shrink-0 mt-0.5" />
            <p className="text-[11px] text-text-secondary">
              Ces paramètres contrôlent le moteur Python FaceGuard en temps réel. Les modifications prennent effet au cycle d'analyse suivant (~500ms). <strong className="text-text-primary">Aucune ligne de code à toucher.</strong>
            </p>
          </div>
          <div className="flex gap-2 flex-shrink-0">
            <button onClick={handleReset} className="flex items-center gap-2 px-4 py-2.5 text-xs font-semibold text-text-secondary border border-bg-border rounded-xl hover:border-accent-orange/20 transition-all">
              <RotateCcw className="w-3.5 h-3.5" />
              Réinitialiser
            </button>
            <button onClick={handleSave} className="flex items-center gap-2 px-4 py-2.5 text-xs font-semibold text-black bg-accent-orange rounded-xl hover:bg-accent-orange/90 transition-all">
              <Save className="w-3.5 h-3.5" />
              Sauvegarder
            </button>
          </div>
        </div>

        {/* Section 1: Thresholds */}
        <Card>
          <div className="flex items-center gap-2 mb-5">
            <div className="p-2 rounded-lg bg-threat-high/10 border border-threat-high/20">
              <Sliders className="w-4 h-4 text-threat-high" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-text-primary">Seuils de Déclenchement</h3>
              <p className="text-[11px] text-text-muted">Définissez à partir de quel pourcentage le système génère une alerte</p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-6">
            <SliderField
              label="Score de Menace Global → Alerte Rouge"
              value={settings.threatThreshold}
              min={50} max={95}
              onChange={v => update('threatThreshold', v)}
              warning={settings.threatThreshold < 65 ? 'Seuil bas : risque de nombreux faux positifs' : undefined}
            />
            <SliderField
              label="Seuil Émotion : Colère"
              value={settings.angerThreshold}
              min={50} max={95}
              onChange={v => update('angerThreshold', v)}
            />
            <SliderField
              label="Seuil Émotion : Peur"
              value={settings.fearThreshold}
              min={50} max={95}
              onChange={v => update('fearThreshold', v)}
            />
            <SliderField
              label="Seuil Émotion : Stress"
              value={settings.stressThreshold}
              min={50} max={95}
              onChange={v => update('stressThreshold', v)}
            />
            <SliderField
              label="Poids Asymétrie Faciale (bonus score)"
              value={settings.asymmetryWeight}
              min={0} max={30}
              unit="pts"
              onChange={v => update('asymmetryWeight', v)}
              warning={settings.asymmetryWeight > 20 ? 'Valeur élevée : l\'asymétrie pèse fortement dans le score' : undefined}
            />
            <SliderField
              label="Délai Anti-Doublon (cooldown alertes)"
              value={settings.alertCooldownSeconds}
              min={5} max={120}
              unit="s"
              onChange={v => update('alertCooldownSeconds', v)}
            />
          </div>
        </Card>

        {/* Section 2: Modules */}
        <Card>
          <div className="flex items-center gap-2 mb-5">
            <div className="p-2 rounded-lg bg-accent-blue/10 border border-accent-blue/20">
              <Brain className="w-4 h-4 text-accent-blue" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-text-primary">Modules du Moteur IA</h3>
              <p className="text-[11px] text-text-muted">Activez ou désactivez les composants analytiques</p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Toggle
              checked={settings.claheEnabled}
              onChange={v => update('claheEnabled', v)}
              icon={<Eye className="w-3.5 h-3.5" />}
              label="Filtre Vision Nocturne (CLAHE)"
              description="Améliore la robustesse en basse luminosité"
            />
            <Toggle
              checked={settings.asymmetryDetection}
              onChange={v => update('asymmetryDetection', v)}
              icon={<Brain className="w-3.5 h-3.5" />}
              label="Détection d'Asymétrie Faciale"
              description="Analyse la déformation musculaire du visage"
            />
            <Toggle
              checked={settings.arOverlay}
              onChange={v => update('arOverlay', v)}
              icon={<Zap className="w-3.5 h-3.5" />}
              label="Incrustation AR (Wireframe 3D)"
              description="Affiche le masque filaire sur le live"
            />
            <Toggle
              checked={settings.temporalSmoothing}
              onChange={v => update('temporalSmoothing', v)}
              icon={<Activity className="w-3.5 h-3.5" />}
              label="Lissage Temporel"
              description="Stabilise les prédictions sur une fenêtre glissante"
            />
            <Toggle
              checked={settings.snapshotOnAlert}
              onChange={v => update('snapshotOnAlert', v)}
              icon={<Camera className="w-3.5 h-3.5" />}
              label="Capture Automatique sur Alerte"
              description="Snapshot du visage au pic d'émotion"
            />
          </div>
        </Card>

        {/* Section 3: Privacy + advanced */}
        <div className="grid grid-cols-2 gap-4">
          <Card>
            <div className="flex items-center gap-2 mb-5">
              <div className="p-2 rounded-lg bg-accent-orange/10 border border-accent-orange/20">
                <Shield className="w-4 h-4 text-accent-orange" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-text-primary">Confidentialité</h3>
                <p className="text-[11px] text-text-muted">Conformité RGPD / législation locale</p>
              </div>
            </div>
            <div className="space-y-3">
              <Toggle
                checked={settings.privacyMode}
                onChange={v => update('privacyMode', v)}
                icon={settings.privacyMode ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                label="Mode Privacy (Floutage Visages)"
                description="Les visages sont floutés sur le Live Monitoring. Le calcul IA continue en arrière-plan."
                danger
              />
              {settings.privacyMode && (
                <div className="p-3 bg-threat-medium/5 border border-threat-medium/20 rounded-lg flex items-start gap-2">
                  <AlertTriangle className="w-3.5 h-3.5 text-threat-medium flex-shrink-0 mt-0.5" />
                  <p className="text-[11px] text-threat-medium">Mode Privacy actif : les visages sont floutés sur le Live. Les snapshots d'alertes seront également anonymisés.</p>
                </div>
              )}
            </div>
          </Card>

          <Card>
            <div className="flex items-center gap-2 mb-5">
              <div className="p-2 rounded-lg bg-threat-low/10 border border-threat-low/20">
                <Clock className="w-4 h-4 text-threat-low" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-text-primary">Paramètres Avancés</h3>
                <p className="text-[11px] text-text-muted">Finesse de l'analyse temporelle</p>
              </div>
            </div>
            <div className="space-y-5">
              <SliderField
                label="Fenêtre de Lissage Temporel"
                value={settings.smoothingWindow}
                min={1} max={15}
                unit=" frames"
                onChange={v => update('smoothingWindow', v)}
                warning={settings.smoothingWindow > 10 ? 'Latence accrue : prédictions plus lentes mais plus stables' : undefined}
              />
              <SliderField
                label="Buffer Replay (avant/après alerte)"
                value={settings.replayBufferSeconds}
                min={1} max={10}
                unit="s"
                onChange={v => update('replayBufferSeconds', v)}
              />
            </div>
          </Card>
        </div>

        {/* Current config summary */}
        <Card padding="sm" className="opacity-80">
          <p className="text-[11px] text-text-muted mb-2 font-mono uppercase tracking-wider">Résumé de configuration actuelle</p>
          <div className="flex flex-wrap gap-2">
            {[
              { k: 'Menace Rouge', v: `>${settings.threatThreshold}%` },
              { k: 'Colère', v: `>${settings.angerThreshold}%` },
              { k: 'Peur', v: `>${settings.fearThreshold}%` },
              { k: 'Stress', v: `>${settings.stressThreshold}%` },
              { k: 'Asymétrie', v: `+${settings.asymmetryWeight}pts` },
              { k: 'CLAHE', v: settings.claheEnabled ? 'ON' : 'OFF', warn: !settings.claheEnabled },
              { k: 'Asymétrie', v: settings.asymmetryDetection ? 'ON' : 'OFF', warn: !settings.asymmetryDetection },
              { k: 'Privacy', v: settings.privacyMode ? 'ON' : 'OFF', warn: settings.privacyMode },
              { k: 'Lissage', v: `${settings.smoothingWindow}f` },
              { k: 'Replay', v: `±${settings.replayBufferSeconds}s` },
            ].map(item => (
              <span key={item.k} className={clsx(
                'text-[10px] font-mono px-2 py-1 rounded border',
                item.warn ? 'text-threat-medium border-threat-medium/30 bg-threat-medium/5' : 'text-text-secondary border-bg-border bg-bg-elevated'
              )}>
                {item.k}: <strong>{item.v}</strong>
              </span>
            ))}
          </div>
        </Card>
      </div>

      <SaveToast visible={saved} />
    </div>
  )
}
