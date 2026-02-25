'use client'

import { useState, useEffect } from 'react'
import clsx from 'clsx'
import { Maximize2, Volume2, VolumeX, Activity, AlertTriangle, Eye, EyeOff, RefreshCw } from 'lucide-react'
import { cameras, tickerEvents, globalStats, type CameraFeed } from '@/lib/mockData'
import { ThreatBadge } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'

// ---- Camera Feed Component ----
function CameraCard({ cam, large = false }: { cam: CameraFeed; large?: boolean }) {
  const [arVisible, setArVisible] = useState(true)

  const statusColor = {
    online:      'border-threat-low/40',
    offline:     'border-threat-high/40',
    degraded:    'border-threat-medium/40',
    maintenance: 'border-accent-blue/40',
  }[cam.status]

  const overlayFacePos = cam.personCount > 0 ? [
    { x: 38, y: 22, w: 28, emotion: 'COLÈRE', score: 88, threat: cam.threatLevel }
  ] : []

  return (
    <div className={clsx(
      'relative rounded-xl overflow-hidden border bg-bg-card camera-feed scanline group',
      statusColor,
      large ? 'aspect-video' : 'aspect-video'
    )}>
      {/* Feed background */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#050810] via-[#0a0f1a] to-[#050810]">
        {cam.status === 'online' && (
          <>
            {/* Fake scene elements */}
            <div className="absolute bottom-0 left-0 right-0 h-1/3 bg-gradient-to-t from-[#0a0d15] to-transparent" />
            <div className="absolute top-1/4 left-1/4 w-1/2 h-px bg-accent-orange/5" />
            {/* Grid lines simulating ground */}
            {[...Array(3)].map((_, i) => (
              <div key={i} className="absolute left-0 right-0" style={{ bottom: `${10 + i * 8}%`, height: '1px', background: 'rgba(255,255,255,0.02)' }} />
            ))}
          </>
        )}
        {cam.status === 'offline' && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
            <div className="w-10 h-10 rounded-full border-2 border-threat-high/30 flex items-center justify-center">
              <EyeOff className="w-5 h-5 text-threat-high/50" />
            </div>
            <p className="text-threat-high/60 text-xs font-mono">SIGNAL PERDU</p>
          </div>
        )}
        {cam.status === 'degraded' && (
          <div className="absolute top-0 left-0 right-0 h-full" style={{
            backgroundImage: 'repeating-linear-gradient(0deg, rgba(255,255,0,0.015) 0px, rgba(255,255,0,0.015) 1px, transparent 1px, transparent 4px)',
          }} />
        )}
      </div>

      {/* AR Overlay — person detection */}
      {cam.status === 'online' && arVisible && cam.personCount > 0 && (
        <div className="absolute inset-0 pointer-events-none">
          {overlayFacePos.map((face, i) => (
            <div key={i} className="absolute" style={{ left: `${face.x}%`, top: `${face.y}%`, width: `${face.w}%` }}>
              {/* Bounding box */}
              <div className={clsx(
                'border-2 rounded relative',
                face.threat === 'critical' ? 'border-red-500' : face.threat === 'high' ? 'border-threat-high' : 'border-accent-orange'
              )} style={{ paddingBottom: '120%' }}>
                {/* Corner markers */}
                <span className="absolute -top-0.5 -left-0.5 w-2 h-2 border-t-2 border-l-2 border-inherit rounded-tl" />
                <span className="absolute -top-0.5 -right-0.5 w-2 h-2 border-t-2 border-r-2 border-inherit rounded-tr" />
                <span className="absolute -bottom-0.5 -left-0.5 w-2 h-2 border-b-2 border-l-2 border-inherit rounded-bl" />
                <span className="absolute -bottom-0.5 -right-0.5 w-2 h-2 border-b-2 border-r-2 border-inherit rounded-br" />

                {/* Wireframe mesh overlay */}
                <div className="absolute inset-0 opacity-40" style={{
                  backgroundImage: 'linear-gradient(rgba(249,115,22,0.15) 1px, transparent 1px), linear-gradient(90deg, rgba(249,115,22,0.15) 1px, transparent 1px)',
                  backgroundSize: '20% 14%',
                }} />

                {/* Emotion label */}
                <div className={clsx(
                  'absolute -top-5 left-0 right-0 flex justify-center',
                )}>
                  <span className={clsx(
                    'text-[9px] font-mono font-bold px-1 rounded',
                    face.threat === 'critical' ? 'bg-red-500 text-white' : 'bg-threat-high text-white'
                  )}>
                    {face.emotion} {face.score}%
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Top overlay: camera name + status */}
      <div className="absolute top-0 left-0 right-0 p-2 flex items-start justify-between">
        <div className="flex items-center gap-1.5">
          <span className={clsx(
            'w-2 h-2 rounded-full',
            cam.status === 'online' ? 'bg-threat-low status-online' :
            cam.status === 'offline' ? 'bg-threat-high animate-pulse' :
            'bg-threat-medium'
          )} />
          <span className="text-[10px] font-mono text-text-primary/90 font-medium bg-black/50 px-1.5 py-0.5 rounded">
            {cam.id}
          </span>
        </div>
        {cam.threatLevel !== 'low' && (
          <ThreatBadge level={cam.threatLevel} size="sm" pulse={cam.threatLevel === 'critical'} />
        )}
      </div>

      {/* Bottom overlay: camera info */}
      <div className="absolute bottom-0 left-0 right-0 p-2 bg-gradient-to-t from-black/80 to-transparent">
        <p className="text-[10px] text-text-primary/90 font-medium truncate">{cam.name}</p>
        <div className="flex items-center justify-between mt-0.5">
          <span className="text-[9px] font-mono text-text-muted">{cam.location}</span>
          <div className="flex items-center gap-2">
            {cam.status === 'online' && (
              <>
                <span className="text-[9px] font-mono text-text-muted">{cam.fps}fps</span>
                {cam.personCount > 0 && (
                  <span className="text-[9px] font-mono text-accent-orange">{cam.personCount}P</span>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      {/* AR toggle + fullscreen (hover) */}
      <div className="absolute top-0 right-0 p-2 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
        <button
          onClick={() => setArVisible(!arVisible)}
          className="p-1 rounded bg-black/60 hover:bg-black/80 transition-colors"
          title="Toggle AR"
        >
          {arVisible ? <Eye className="w-3 h-3 text-accent-orange" /> : <EyeOff className="w-3 h-3 text-text-muted" />}
        </button>
        <button className="p-1 rounded bg-black/60 hover:bg-black/80 transition-colors" title="Plein écran">
          <Maximize2 className="w-3 h-3 text-text-secondary" />
        </button>
      </div>

      {/* REC indicator */}
      {cam.status === 'online' && (
        <div className="absolute top-2 right-2 flex items-center gap-1">
          <span className="w-1.5 h-1.5 bg-red-500 rounded-full animate-pulse" />
          <span className="text-[8px] font-mono text-red-400">REC</span>
        </div>
      )}
    </div>
  )
}

// ---- Threat Gauge ----
function ThreatGauge({ level }: { level: 'low' | 'medium' | 'high' | 'critical' }) {
  const levels = ['low', 'medium', 'high', 'critical']
  const idx = levels.indexOf(level)
  const pct = ((idx + 1) / 4) * 100

  const config = {
    low:      { label: 'FAIBLE',   color: '#22c55e', glow: 'rgba(34,197,94,0.4)',    arc: 25 },
    medium:   { label: 'MODÉRÉ',   color: '#f59e0b', glow: 'rgba(245,158,11,0.4)',   arc: 50 },
    high:     { label: 'ÉLEVÉ',    color: '#ef4444', glow: 'rgba(239,68,68,0.4)',    arc: 75 },
    critical: { label: 'CRITIQUE', color: '#dc2626', glow: 'rgba(220,38,38,0.6)',    arc: 100 },
  }[level]

  const r = 42
  const circ = 2 * Math.PI * r
  const dashArray = (pct / 100) * circ * 0.75
  const dashOffset = circ * 0.125

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: 110, height: 90 }}>
        <svg viewBox="0 0 100 80" className="w-full h-full">
          {/* Track */}
          <path
            d="M 14 70 A 36 36 0 0 1 86 70"
            fill="none"
            stroke="#1e2a3d"
            strokeWidth="8"
            strokeLinecap="round"
          />
          {/* Fill */}
          <path
            d="M 14 70 A 36 36 0 0 1 86 70"
            fill="none"
            stroke={config.color}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={`${(pct / 100) * 113} 113`}
            style={{ filter: `drop-shadow(0 0 6px ${config.glow})`, transition: 'all 0.5s ease' }}
          />
          {/* Tick marks */}
          {[0, 25, 50, 75, 100].map((tick) => {
            const angle = -180 + (tick / 100) * 180
            const rad = (angle * Math.PI) / 180
            const cx = 50 + 36 * Math.cos(rad)
            const cy = 70 + 36 * Math.sin(rad)
            return <circle key={tick} cx={cx} cy={cy} r={1.5} fill="#1e2a3d" />
          })}
        </svg>
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-end pb-3">
          <span className="font-mono font-bold text-base" style={{ color: config.color }}>{config.label}</span>
        </div>
      </div>
      <p className="text-[10px] text-text-muted uppercase tracking-wider">Niveau de Menace Global</p>
    </div>
  )
}

// ---- Alert Ticker ----
function AlertTicker() {
  const doubled = [...tickerEvents, ...tickerEvents]
  const levelColors = {
    critical: 'text-red-400',
    high:     'text-threat-high',
    medium:   'text-threat-medium',
    low:      'text-threat-low',
    info:     'text-text-secondary',
  }

  return (
    <div className="ticker-container relative">
      <div className="ticker-inner flex flex-col gap-0">
        {doubled.map((evt, i) => (
          <div
            key={`${evt.id}-${i}`}
            className={clsx(
              'flex items-start gap-2 py-2 px-3 border-b border-bg-border/50 hover:bg-bg-elevated/50 transition-colors',
              evt.type === 'alert' ? 'bg-threat-high/3' : ''
            )}
          >
            <span className="font-mono text-[10px] text-text-muted flex-shrink-0 pt-0.5">{evt.timestamp}</span>
            <div className="flex-1 min-w-0">
              <p className={clsx('text-[11px] font-medium leading-snug', levelColors[evt.level])}>
                {evt.type === 'alert' && <span className="mr-1">⚠</span>}
                {evt.type === 'system' && <span className="mr-1">⚙</span>}
                {evt.type === 'acknowledged' && <span className="mr-1">✓</span>}
                {evt.message}
              </p>
              <p className="text-[10px] text-text-muted font-mono">{evt.cameraName}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ---- Main Dashboard ----
export default function DashboardPage() {
  const [layout, setLayout] = useState<'2x3' | '3x3' | 'focus'>('2x3')
  const [muted, setMuted] = useState(false)
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const i = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(i)
  }, [])

  const displayCameras = cameras.slice(0, layout === '2x3' ? 6 : layout === '3x3' ? 9 : 4)
  const gridCols = layout === '2x3' ? 'grid-cols-3' : layout === '3x3' ? 'grid-cols-3' : 'grid-cols-2'

  const statItems = [
    { label: 'Alertes 24h',  value: globalStats.totalAlerts24h, color: 'text-threat-medium' },
    { label: 'En attente',   value: globalStats.pendingAlerts,  color: 'text-threat-high animate-pulse' },
    { label: 'Faux positifs', value: `${globalStats.falsePositiveRate}%`, color: 'text-text-secondary' },
    { label: 'Rép. moyen',  value: `${globalStats.avgResponseTime}s`, color: 'text-accent-orange' },
  ]

  return (
    <div className="h-full flex gap-4">
      {/* Main video wall */}
      <div className="flex-1 flex flex-col gap-3 min-w-0">
        {/* Header strip */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-bg-card border border-bg-border rounded-lg">
              <span className="w-1.5 h-1.5 bg-red-500 rounded-full animate-pulse" />
              <span className="text-[11px] font-mono text-text-secondary">LIVE</span>
              <span className="text-[11px] font-mono text-text-muted">{time.toLocaleTimeString('fr-FR')}</span>
            </div>
            <div className="flex gap-1">
              {([['2x3', '2×3'], ['3x3', '3×3']] as const).map(([val, lbl]) => (
                <button
                  key={val}
                  onClick={() => setLayout(val)}
                  className={clsx(
                    'px-2.5 py-1 text-[11px] font-mono rounded border transition-all',
                    layout === val
                      ? 'bg-accent-orange/10 border-accent-orange/30 text-accent-orange'
                      : 'bg-bg-card border-bg-border text-text-muted hover:text-text-secondary'
                  )}
                >{lbl}</button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setMuted(!muted)}
              className="p-1.5 rounded-lg bg-bg-card border border-bg-border hover:border-accent-orange/30 transition-all"
            >
              {muted ? <VolumeX className="w-3.5 h-3.5 text-text-muted" /> : <Volume2 className="w-3.5 h-3.5 text-accent-orange" />}
            </button>
            <button className="p-1.5 rounded-lg bg-bg-card border border-bg-border hover:border-accent-orange/30 transition-all">
              <RefreshCw className="w-3.5 h-3.5 text-text-secondary" />
            </button>
          </div>
        </div>

        {/* Camera grid */}
        <div className={clsx('grid gap-2 flex-1', gridCols)}>
          {displayCameras.map((cam) => (
            <CameraCard key={cam.id} cam={cam} />
          ))}
        </div>

        {/* Stats strip */}
        <div className="grid grid-cols-4 gap-2">
          {statItems.map((s) => (
            <div key={s.label} className="bg-bg-card border border-bg-border rounded-lg px-3 py-2 flex items-center justify-between">
              <span className="text-[11px] text-text-muted">{s.label}</span>
              <span className={clsx('text-sm font-mono font-bold', s.color)}>{s.value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Right panel */}
      <div className="w-56 flex flex-col gap-3 flex-shrink-0">
        {/* Threat Gauge */}
        <Card padding="sm" glow={globalStats.globalThreatLevel === 'critical' ? 'red' : globalStats.globalThreatLevel === 'high' ? 'red' : 'none'}>
          <ThreatGauge level={globalStats.globalThreatLevel} />
          <div className="mt-3 pt-3 border-t border-bg-border space-y-1.5">
            <div className="flex justify-between text-[11px]">
              <span className="text-text-muted">Caméras actives</span>
              <span className="font-mono text-text-primary">{globalStats.camerasOnline}/{globalStats.camerasTotal}</span>
            </div>
            <div className="flex justify-between text-[11px]">
              <span className="text-text-muted">Alertes en attente</span>
              <span className={clsx('font-mono font-bold', globalStats.pendingAlerts > 0 ? 'text-threat-high' : 'text-threat-low')}>
                {globalStats.pendingAlerts}
              </span>
            </div>
            <div className="flex justify-between text-[11px]">
              <span className="text-text-muted">Menaces neutralisées</span>
              <span className="font-mono text-threat-low">{globalStats.threatsNeutralized}</span>
            </div>
          </div>
        </Card>

        {/* Active alerts */}
        <Card padding="sm" className="flex-shrink-0">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-semibold text-text-primary uppercase tracking-wider">Alertes actives</span>
            {globalStats.pendingAlerts > 0 && (
              <span className="w-5 h-5 bg-threat-high text-white text-[10px] font-bold rounded-full flex items-center justify-center animate-pulse">
                {globalStats.pendingAlerts}
              </span>
            )}
          </div>
          <div className="space-y-2">
            {[
              { cam: 'CAM-03', msg: 'Colère 88% + Asymétrie', level: 'critical' as const, time: '14:32' },
              { cam: 'CAM-02', msg: 'Stress 81%', level: 'high' as const, time: '14:28' },
              { cam: 'CAM-01', msg: 'Peur 76% + Asymétrie', level: 'high' as const, time: '14:21' },
            ].map((a, i) => (
              <div key={i} className={clsx(
                'p-2 rounded-lg border text-[10px]',
                a.level === 'critical' ? 'border-red-500/30 bg-red-500/5' : 'border-threat-high/30 bg-threat-high/5'
              )}>
                <div className="flex items-center justify-between mb-0.5">
                  <span className="font-mono font-bold text-text-primary">{a.cam}</span>
                  <span className="font-mono text-text-muted">{a.time}</span>
                </div>
                <p className={clsx('font-medium', a.level === 'critical' ? 'text-red-400' : 'text-threat-high')}>
                  {a.msg}
                </p>
              </div>
            ))}
          </div>
        </Card>

        {/* Alert ticker */}
        <Card padding="none" className="flex-1 overflow-hidden">
          <div className="px-3 py-2 border-b border-bg-border flex items-center gap-2">
            <Activity className="w-3.5 h-3.5 text-accent-orange" />
            <span className="text-[11px] font-semibold text-text-primary">Fil d'événements</span>
          </div>
          <div className="overflow-hidden" style={{ height: 'calc(100% - 36px)' }}>
            <AlertTicker />
          </div>
        </Card>
      </div>
    </div>
  )
}
