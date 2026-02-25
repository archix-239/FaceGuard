'use client'

import { useState } from 'react'
import clsx from 'clsx'
import {
  CheckCircle, AlertOctagon, Send, Filter, ChevronDown,
  Camera, Clock, Brain, Zap, Play, Download, X
} from 'lucide-react'
import { alerts, type Alert, type AlertStatus } from '@/lib/mockData'
import { ThreatBadge } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'

const emotionLabels: Record<string, string> = {
  colere: 'Colère', peur: 'Peur', stress: 'Stress',
  fatigue: 'Fatigue', degoût: 'Dégoût', tristesse: 'Tristesse', neutral: 'Neutre'
}

const emotionColors: Record<string, string> = {
  colere:   'text-red-400 bg-red-500/10 border-red-500/30',
  peur:     'text-threat-medium bg-threat-medium/10 border-threat-medium/30',
  stress:   'text-orange-400 bg-orange-500/10 border-orange-500/30',
  fatigue:  'text-accent-blue bg-accent-blue/10 border-accent-blue/30',
  degoût:   'text-purple-400 bg-purple-500/10 border-purple-500/30',
  tristesse:'text-sky-400 bg-sky-500/10 border-sky-500/30',
  neutral:  'text-text-secondary bg-bg-elevated border-bg-border',
}

// Fake snapshot generator
function SnapshotPlaceholder({ emotion, score, threatLevel }: { emotion: string; score: number; threatLevel: string }) {
  const color = emotion === 'colere' ? '#ef4444' : emotion === 'peur' ? '#f59e0b' : '#f97316'
  return (
    <div className="relative rounded-lg overflow-hidden bg-[#050810] border border-bg-border" style={{ aspectRatio: '4/3' }}>
      {/* Background scene */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#05080f] to-[#0a0d16]" />
      {/* Grid */}
      <div className="absolute inset-0" style={{
        backgroundImage: `linear-gradient(${color}08 1px, transparent 1px), linear-gradient(90deg, ${color}08 1px, transparent 1px)`,
        backgroundSize: '15% 12%'
      }} />
      {/* Face bounding box */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="relative" style={{ width: '42%', height: '56%' }}>
          <div className="absolute inset-0 border-2 rounded" style={{ borderColor: color }}>
            {/* Face wireframe */}
            <div className="absolute inset-2" style={{
              backgroundImage: `linear-gradient(${color}25 1px, transparent 1px), linear-gradient(90deg, ${color}25 1px, transparent 1px)`,
              backgroundSize: '25% 16.6%'
            }} />
            {/* Eyes */}
            <div className="absolute flex gap-3 justify-center" style={{ top: '25%', left: '15%', right: '15%' }}>
              <div className="w-2 h-1.5 rounded-full border" style={{ borderColor: color, background: `${color}30` }} />
              <div className="w-2 h-1.5 rounded-full border" style={{ borderColor: color, background: `${color}30` }} />
            </div>
            {/* Nose */}
            <div className="absolute w-1 h-2 border-b border-l rounded-bl" style={{ borderColor: color, left: '45%', top: '42%' }} />
            {/* Mouth — angry */}
            <div className="absolute h-px" style={{ background: color, bottom: '25%', left: '25%', right: '25%', transform: emotion === 'colere' ? 'rotate(-3deg) scaleX(1.1)' : 'none' }} />
          </div>
          {/* Corner markers */}
          {[['top-0 left-0', 'border-t-2 border-l-2 rounded-tl'], ['top-0 right-0', 'border-t-2 border-r-2 rounded-tr'], ['bottom-0 left-0', 'border-b-2 border-l-2 rounded-bl'], ['bottom-0 right-0', 'border-b-2 border-r-2 rounded-br']].map(([pos, cls], i) => (
            <span key={i} className={clsx('absolute w-3 h-3', pos, cls)} style={{ borderColor: color }} />
          ))}
        </div>
      </div>
      {/* Overlay labels */}
      <div className="absolute top-2 left-2">
        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded font-bold" style={{ background: color, color: '#000' }}>
          {emotionLabels[emotion]?.toUpperCase()} {score}%
        </span>
      </div>
      <div className="absolute bottom-2 right-2">
        <span className="text-[9px] font-mono text-text-muted">SNAPSHOT</span>
      </div>
      {/* Scan line */}
      <div className="absolute inset-0 pointer-events-none" style={{
        backgroundImage: 'repeating-linear-gradient(0deg, rgba(0,0,0,0), rgba(0,0,0,0) 2px, rgba(0,0,0,0.08) 2px, rgba(0,0,0,0.08) 4px)'
      }} />
    </div>
  )
}

// Mini replay bar
function ReplayBar() {
  const [playing, setPlaying] = useState(false)
  return (
    <div className="flex items-center gap-2 p-2 bg-bg-elevated rounded-lg border border-bg-border">
      <button
        onClick={() => setPlaying(!playing)}
        className="w-6 h-6 rounded bg-accent-orange/15 border border-accent-orange/30 flex items-center justify-center"
      >
        <Play className="w-3 h-3 text-accent-orange" />
      </button>
      <div className="flex-1 relative h-1 bg-bg-border rounded">
        <div className="absolute left-0 top-0 h-full bg-accent-orange rounded" style={{ width: '40%' }} />
        <div className="absolute top-1/2 -translate-y-1/2 w-2.5 h-2.5 rounded-full bg-accent-orange border-2 border-bg-elevated cursor-pointer" style={{ left: '38%' }} />
      </div>
      <span className="text-[10px] font-mono text-text-muted">-3s / +3s</span>
    </div>
  )
}

// Alert card
function AlertCard({ alert: a, onAction }: { alert: Alert; onAction: (id: string, action: AlertStatus) => void }) {
  const [expanded, setExpanded] = useState(false)

  const statusConfig: Record<AlertStatus, { label: string; color: string }> = {
    pending:      { label: 'EN ATTENTE',       color: 'text-threat-high border-threat-high/30 bg-threat-high/5' },
    acknowledged: { label: 'ACQUITTÉ',         color: 'text-threat-low border-threat-low/30 bg-threat-low/5' },
    intervention: { label: 'INTERVENTION',     color: 'text-threat-medium border-threat-medium/30 bg-threat-medium/5' },
    escalated:    { label: 'SIGNALÉ DIRECTION', color: 'text-accent-orange border-accent-orange/30 bg-accent-orange/5' },
  }

  const sc = statusConfig[a.status]

  return (
    <Card
      className={clsx(
        'transition-all duration-200',
        a.status === 'pending' && a.threatLevel === 'critical' ? 'border-red-500/30' :
        a.status === 'pending' ? 'border-threat-high/20' : 'border-bg-border opacity-75'
      )}
      glow={a.status === 'pending' && a.threatLevel === 'critical' ? 'red' : 'none'}
    >
      <div className="flex items-start gap-3">
        {/* Snapshot thumbnail */}
        <div className="w-20 flex-shrink-0">
          <SnapshotPlaceholder emotion={a.emotion} score={a.emotionScore} threatLevel={a.threatLevel} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-1.5">
            <div className="flex items-center gap-2 flex-wrap">
              <ThreatBadge level={a.threatLevel} pulse={a.status === 'pending' && a.threatLevel === 'critical'} />
              <span className={clsx('text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded border', sc.color)}>
                {sc.label}
              </span>
            </div>
            <div className="flex items-center gap-1 text-text-muted flex-shrink-0">
              <Clock className="w-3 h-3" />
              <span className="text-[11px] font-mono">
                {new Date(a.timestamp).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3 mb-2">
            <div className="flex items-center gap-1.5">
              <Camera className="w-3 h-3 text-text-muted" />
              <span className="text-[11px] font-mono font-medium text-text-primary">{a.cameraName}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Brain className="w-3 h-3 text-text-muted" />
              <span className={clsx('text-[11px] font-mono font-semibold px-1.5 py-0.5 rounded border', emotionColors[a.emotion])}>
                {emotionLabels[a.emotion]} {a.emotionScore}%
              </span>
              {a.asymmetry && (
                <span className="text-[11px] font-mono px-1.5 py-0.5 rounded border text-red-400 bg-red-500/10 border-red-500/30">
                  + Asymétrie
                </span>
              )}
            </div>
          </div>

          {/* Score bar */}
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-3 h-3 text-accent-orange flex-shrink-0" />
            <span className="text-[11px] text-text-muted">Score Menace:</span>
            <div className="flex-1 h-1.5 bg-bg-border rounded-full overflow-hidden">
              <div
                className={clsx('h-full rounded-full transition-all', a.threatScore >= 90 ? 'bg-red-500' : a.threatScore >= 75 ? 'bg-threat-high' : 'bg-threat-medium')}
                style={{ width: `${a.threatScore}%` }}
              />
            </div>
            <span className={clsx('text-[11px] font-mono font-bold flex-shrink-0', a.threatScore >= 90 ? 'text-red-400' : a.threatScore >= 75 ? 'text-threat-high' : 'text-threat-medium')}>
              {a.threatScore}%
            </span>
          </div>

          {a.agentName && (
            <p className="text-[11px] text-text-muted mb-2">
              <span className="text-text-secondary">Agent:</span> {a.agentName}
              {a.note && <span className="ml-1 italic">— {a.note}</span>}
            </p>
          )}

          {/* Expand for replay */}
          {expanded && (
            <div className="mt-2 mb-2 animate-fade-in">
              <ReplayBar />
            </div>
          )}

          {/* Actions */}
          {a.status === 'pending' && (
            <div className="flex gap-2 flex-wrap mt-2">
              <button
                onClick={() => onAction(a.id, 'acknowledged')}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-threat-low/10 border border-threat-low/30 text-threat-low text-xs font-semibold rounded-lg hover:bg-threat-low/20 transition-all"
              >
                <CheckCircle className="w-3 h-3" />
                Acquitter (Fausse alerte)
              </button>
              <button
                onClick={() => onAction(a.id, 'intervention')}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-threat-medium/10 border border-threat-medium/30 text-threat-medium text-xs font-semibold rounded-lg hover:bg-threat-medium/20 transition-all"
              >
                <AlertOctagon className="w-3 h-3" />
                Intervention requise
              </button>
              <button
                onClick={() => onAction(a.id, 'escalated')}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-accent-orange/10 border border-accent-orange/30 text-accent-orange text-xs font-semibold rounded-lg hover:bg-accent-orange/20 transition-all"
              >
                <Send className="w-3 h-3" />
                Signaler à la direction
              </button>
            </div>
          )}
        </div>

        {/* Right: expand + download */}
        <div className="flex flex-col gap-1 flex-shrink-0">
          <button
            onClick={() => setExpanded(!expanded)}
            className={clsx(
              'p-1.5 rounded-lg border transition-all text-text-muted hover:text-text-primary',
              expanded ? 'bg-accent-orange/10 border-accent-orange/30 text-accent-orange' : 'bg-bg-elevated border-bg-border hover:border-accent-orange/20'
            )}
            title="Replay vidéo"
          >
            <Play className="w-3.5 h-3.5" />
          </button>
          <button className="p-1.5 rounded-lg border border-bg-border bg-bg-elevated text-text-muted hover:text-text-primary hover:border-accent-orange/20 transition-all" title="Télécharger">
            <Download className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </Card>
  )
}

export default function AlertsPage() {
  const [alertList, setAlertList] = useState(alerts)
  const [filter, setFilter] = useState<'all' | 'pending' | 'acknowledged' | 'intervention' | 'escalated'>('all')
  const [sortBy, setSortBy] = useState<'time' | 'threat'>('threat')

  const handleAction = (id: string, action: AlertStatus) => {
    setAlertList(prev => prev.map(a => a.id === id ? { ...a, status: action, agentName: 'Agent Connecté' } : a))
  }

  const filtered = alertList
    .filter(a => filter === 'all' || a.status === filter)
    .sort((a, b) => sortBy === 'threat' ? b.threatScore - a.threatScore : new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())

  const counts = {
    pending:      alertList.filter(a => a.status === 'pending').length,
    acknowledged: alertList.filter(a => a.status === 'acknowledged').length,
    intervention: alertList.filter(a => a.status === 'intervention').length,
    escalated:    alertList.filter(a => a.status === 'escalated').length,
  }

  return (
    <div className="h-full flex flex-col gap-4 max-w-5xl mx-auto">
      {/* Stats row */}
      <div className="grid grid-cols-4 gap-3">
        {([
          { key: 'pending',      label: 'En attente',    value: counts.pending,      color: 'text-threat-high',   bg: 'bg-threat-high/10',   border: 'border-threat-high/20' },
          { key: 'intervention', label: 'Intervention',  value: counts.intervention, color: 'text-threat-medium', bg: 'bg-threat-medium/10', border: 'border-threat-medium/20' },
          { key: 'escalated',    label: 'Signalées',     value: counts.escalated,    color: 'text-accent-orange', bg: 'bg-accent-orange/10', border: 'border-accent-orange/20' },
          { key: 'acknowledged', label: 'Acquittées',    value: counts.acknowledged, color: 'text-threat-low',    bg: 'bg-threat-low/10',    border: 'border-threat-low/20' },
        ] as const).map(s => (
          <button
            key={s.key}
            onClick={() => setFilter(s.key === filter ? 'all' : s.key)}
            className={clsx(
              'p-3 rounded-xl border text-left transition-all',
              filter === s.key ? `${s.bg} ${s.border}` : 'bg-bg-card border-bg-border hover:border-bg-elevated'
            )}
          >
            <p className="text-text-muted text-[11px] uppercase tracking-wider">{s.label}</p>
            <p className={clsx('text-2xl font-bold font-mono mt-1', s.color)}>{s.value}</p>
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-text-muted">Filtre:</span>
          {(['all', 'pending', 'acknowledged', 'intervention', 'escalated'] as const).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={clsx(
                'px-3 py-1 text-xs font-medium rounded-lg border transition-all',
                filter === f ? 'bg-accent-orange/10 border-accent-orange/30 text-accent-orange' : 'bg-bg-card border-bg-border text-text-muted hover:text-text-secondary'
              )}
            >
              {f === 'all' ? 'Toutes' : f === 'pending' ? 'En attente' : f === 'acknowledged' ? 'Acquittées' : f === 'intervention' ? 'Intervention' : 'Signalées'}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-text-muted">Trier par:</span>
          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value as 'time' | 'threat')}
            className="bg-bg-card border border-bg-border text-text-secondary text-xs rounded-lg px-2 py-1.5 outline-none"
          >
            <option value="threat">Score de Menace</option>
            <option value="time">Heure</option>
          </select>
        </div>
      </div>

      {/* Alert list */}
      <div className="flex-1 overflow-y-auto space-y-3">
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 text-text-muted">
            <CheckCircle className="w-10 h-10 mb-3 text-threat-low opacity-50" />
            <p className="text-sm">Aucune alerte dans cette catégorie</p>
          </div>
        ) : (
          filtered.map(a => (
            <AlertCard key={a.id} alert={a} onAction={handleAction} />
          ))
        )}
      </div>
    </div>
  )
}
