'use client'

import { useState } from 'react'
import clsx from 'clsx'
import { Search, Filter, Download, Play, Calendar, Camera, Brain, ChevronDown, ChevronUp, X } from 'lucide-react'
import { logs, cameras, type LogEntry } from '@/lib/mockData'
import { ThreatBadge } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'

const emotionLabels: Record<string, string> = {
  colere: 'Colère', peur: 'Peur', stress: 'Stress',
  fatigue: 'Fatigue', degoût: 'Dégoût', tristesse: 'Tristesse', neutral: 'Neutre'
}

const emotionColors: Record<string, string> = {
  colere:   'text-red-400',
  peur:     'text-threat-medium',
  stress:   'text-orange-400',
  fatigue:  'text-accent-blue',
  degoût:   'text-purple-400',
  tristesse:'text-sky-400',
  neutral:  'text-text-secondary',
}

const actionConfig = {
  none:         { label: 'Aucune',      color: 'text-text-muted bg-bg-elevated border-bg-border' },
  acknowledged: { label: 'Acquitté',   color: 'text-threat-low bg-threat-low/10 border-threat-low/30' },
  intervention: { label: 'Intervention',color: 'text-threat-medium bg-threat-medium/10 border-threat-medium/30' },
  escalated:    { label: 'Signalé',    color: 'text-accent-orange bg-accent-orange/10 border-accent-orange/30' },
}

// Inline mini replay for expanded row
function MiniReplay({ log: l }: { log: LogEntry }) {
  const color = l.emotion === 'colere' ? '#ef4444' : l.emotion === 'peur' ? '#f59e0b' : '#f97316'
  return (
    <div className="mt-4 p-4 bg-bg-elevated rounded-xl border border-bg-border animate-fade-in">
      <div className="grid grid-cols-3 gap-4">
        {/* Snapshot */}
        <div>
          <p className="text-[11px] text-text-muted mb-2 font-semibold uppercase tracking-wider">Snapshot</p>
          <div className="aspect-[4/3] rounded-lg bg-[#050810] border border-bg-border relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-[#05080f] to-[#0a0d16]" />
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="relative w-1/3 h-1/2 border-2 rounded" style={{ borderColor: color }}>
                <div className="absolute inset-0" style={{
                  backgroundImage: `linear-gradient(${color}20 1px, transparent 1px), linear-gradient(90deg, ${color}20 1px, transparent 1px)`,
                  backgroundSize: '25% 20%'
                }} />
              </div>
            </div>
            <div className="absolute top-2 left-2">
              <span className="text-[9px] font-mono px-1 py-0.5 rounded font-bold" style={{ background: color, color: '#000' }}>
                {emotionLabels[l.emotion]?.toUpperCase()} {l.emotionScore}%
              </span>
            </div>
          </div>
        </div>

        {/* Replay player */}
        <div className="col-span-2">
          <p className="text-[11px] text-text-muted mb-2 font-semibold uppercase tracking-wider">Replay — {l.duration * 2}s</p>
          <div className="aspect-video rounded-lg bg-[#050810] border border-bg-border relative overflow-hidden mb-3">
            <div className="absolute inset-0 bg-gradient-to-br from-[#05080f] to-[#0a0d16]" />
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-10 h-10 rounded-full border border-accent-orange/50 flex items-center justify-center cursor-pointer hover:bg-accent-orange/10 transition-all">
                <Play className="w-4 h-4 text-accent-orange ml-0.5" />
              </div>
            </div>
            <div className="absolute bottom-2 left-2 right-2">
              <div className="h-1 bg-bg-border rounded overflow-hidden">
                <div className="h-full bg-accent-orange rounded" style={{ width: '0%' }} />
              </div>
            </div>
            <div className="absolute top-2 right-2">
              <span className="text-[9px] font-mono text-text-muted">-{l.duration}s → +{l.duration}s</span>
            </div>
          </div>

          {/* Details */}
          <div className="grid grid-cols-2 gap-2 text-[11px]">
            {[
              { label: 'Score Menace', value: `${l.threatScore}%`, color: l.threatScore >= 85 ? 'text-red-400' : 'text-threat-high' },
              { label: 'Asymétrie', value: l.asymmetry ? 'Oui (+15pts)' : 'Non', color: l.asymmetry ? 'text-threat-high' : 'text-text-secondary' },
              { label: 'Durée', value: `${l.duration}s`, color: 'text-text-primary' },
              { label: 'Agent', value: l.agentName ?? '—', color: 'text-text-primary' },
            ].map(d => (
              <div key={d.label} className="flex justify-between bg-bg-card rounded px-2 py-1.5 border border-bg-border">
                <span className="text-text-muted">{d.label}</span>
                <span className={clsx('font-mono font-semibold', d.color)}>{d.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="flex gap-2 mt-3">
        <button className="flex items-center gap-2 px-4 py-2 bg-accent-orange/10 border border-accent-orange/30 text-accent-orange text-xs font-semibold rounded-lg hover:bg-accent-orange/20 transition-all">
          <Download className="w-3.5 h-3.5" />
          Télécharger séquence anonymisée
        </button>
        <button className="flex items-center gap-2 px-4 py-2 bg-bg-card border border-bg-border text-text-secondary text-xs font-semibold rounded-lg hover:border-accent-orange/20 transition-all">
          <Download className="w-3.5 h-3.5" />
          Exporter rapport PDF
        </button>
      </div>
    </div>
  )
}

export default function LogsPage() {
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [searchDate, setSearchDate] = useState('2026-02-25')
  const [searchCam, setSearchCam] = useState('all')
  const [searchEmotion, setSearchEmotion] = useState('all')
  const [searchHourStart, setSearchHourStart] = useState('00')
  const [searchHourEnd, setSearchHourEnd] = useState('23')

  const filtered = logs.filter(l => {
    const d = new Date(l.timestamp)
    const dateStr = d.toISOString().split('T')[0]
    const hour = d.getHours()
    return (
      (!searchDate || dateStr === searchDate) &&
      (searchCam === 'all' || l.cameraId === searchCam) &&
      (searchEmotion === 'all' || l.emotion === searchEmotion) &&
      hour >= parseInt(searchHourStart) &&
      hour <= parseInt(searchHourEnd)
    )
  })

  return (
    <div className="h-full flex flex-col gap-4">
      {/* Search filters */}
      <Card className="flex-shrink-0">
        <div className="flex items-center gap-2 mb-3">
          <Filter className="w-4 h-4 text-accent-orange" />
          <span className="text-sm font-semibold text-text-primary">Filtres de Recherche</span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <div>
            <label className="block text-[11px] text-text-muted mb-1.5">Date</label>
            <div className="relative">
              <Calendar className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3 h-3 text-text-muted" />
              <input
                type="date"
                value={searchDate}
                onChange={e => setSearchDate(e.target.value)}
                className="w-full bg-bg-elevated border border-bg-border rounded-lg pl-8 pr-3 py-2 text-xs text-text-secondary outline-none focus:border-accent-orange/50 transition-all"
              />
            </div>
          </div>
          <div>
            <label className="block text-[11px] text-text-muted mb-1.5">Caméra</label>
            <div className="relative">
              <Camera className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3 h-3 text-text-muted" />
              <select
                value={searchCam}
                onChange={e => setSearchCam(e.target.value)}
                className="w-full bg-bg-elevated border border-bg-border rounded-lg pl-8 pr-3 py-2 text-xs text-text-secondary outline-none focus:border-accent-orange/50 appearance-none"
              >
                <option value="all">Toutes les caméras</option>
                {cameras.map(c => <option key={c.id} value={c.id}>{c.id} — {c.name}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-[11px] text-text-muted mb-1.5">Émotion</label>
            <div className="relative">
              <Brain className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3 h-3 text-text-muted" />
              <select
                value={searchEmotion}
                onChange={e => setSearchEmotion(e.target.value)}
                className="w-full bg-bg-elevated border border-bg-border rounded-lg pl-8 pr-3 py-2 text-xs text-text-secondary outline-none focus:border-accent-orange/50 appearance-none"
              >
                <option value="all">Toutes les émotions</option>
                {Object.entries(emotionLabels).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-[11px] text-text-muted mb-1.5">Heure début</label>
            <select
              value={searchHourStart}
              onChange={e => setSearchHourStart(e.target.value)}
              className="w-full bg-bg-elevated border border-bg-border rounded-lg px-3 py-2 text-xs text-text-secondary outline-none focus:border-accent-orange/50"
            >
              {[...Array(24)].map((_, i) => <option key={i} value={String(i).padStart(2,'0')}>{String(i).padStart(2,'0')}:00</option>)}
            </select>
          </div>
          <div>
            <label className="block text-[11px] text-text-muted mb-1.5">Heure fin</label>
            <select
              value={searchHourEnd}
              onChange={e => setSearchHourEnd(e.target.value)}
              className="w-full bg-bg-elevated border border-bg-border rounded-lg px-3 py-2 text-xs text-text-secondary outline-none focus:border-accent-orange/50"
            >
              {[...Array(24)].map((_, i) => <option key={i} value={String(i).padStart(2,'0')}>{String(i).padStart(2,'0')}:59</option>)}
            </select>
          </div>
        </div>
        <div className="flex items-center justify-between mt-3 pt-3 border-t border-bg-border">
          <p className="text-[11px] text-text-muted">
            <span className="text-text-primary font-mono font-bold">{filtered.length}</span> événement{filtered.length !== 1 ? 's' : ''} trouvé{filtered.length !== 1 ? 's' : ''}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => { setSearchDate(''); setSearchCam('all'); setSearchEmotion('all'); setSearchHourStart('00'); setSearchHourEnd('23') }}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-text-muted border border-bg-border rounded-lg hover:border-accent-orange/20 transition-all"
            >
              <X className="w-3 h-3" /> Réinitialiser
            </button>
            <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-accent-orange border border-accent-orange/30 bg-accent-orange/10 rounded-lg hover:bg-accent-orange/20 transition-all">
              <Download className="w-3 h-3" /> Exporter CSV
            </button>
          </div>
        </div>
      </Card>

      {/* Log table */}
      <div className="flex-1 overflow-auto">
        <div className="bg-bg-card border border-bg-border rounded-xl overflow-hidden">
          {/* Header */}
          <div className="grid text-[11px] font-semibold text-text-muted uppercase tracking-wider px-4 py-2 bg-bg-elevated border-b border-bg-border"
            style={{ gridTemplateColumns: '2fr 1.5fr 1fr 1fr 1fr 0.8fr 1fr 0.6fr' }}
          >
            <span>Horodatage</span>
            <span>Caméra</span>
            <span>Émotion</span>
            <span>Score</span>
            <span>Menace</span>
            <span>Durée</span>
            <span>Action</span>
            <span></span>
          </div>

          {/* Rows */}
          <div className="divide-y divide-bg-border">
            {filtered.length === 0 ? (
              <div className="py-12 text-center text-text-muted text-sm">
                Aucun événement ne correspond aux filtres
              </div>
            ) : (
              filtered.map(l => (
                <div key={l.id}>
                  <div
                    className={clsx(
                      'grid items-center px-4 py-2.5 cursor-pointer hover:bg-bg-elevated transition-colors',
                      expandedId === l.id ? 'bg-bg-elevated' : ''
                    )}
                    style={{ gridTemplateColumns: '2fr 1.5fr 1fr 1fr 1fr 0.8fr 1fr 0.6fr' }}
                    onClick={() => setExpandedId(expandedId === l.id ? null : l.id)}
                  >
                    <span className="font-mono text-[11px] text-text-secondary">
                      {new Date(l.timestamp).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </span>
                    <span className="text-xs font-medium text-text-primary truncate">{l.cameraName}</span>
                    <span className={clsx('text-xs font-semibold font-mono', emotionColors[l.emotion])}>
                      {emotionLabels[l.emotion]}
                    </span>
                    <div className="flex items-center gap-1.5">
                      <div className="w-12 h-1 bg-bg-border rounded overflow-hidden">
                        <div
                          className={clsx('h-full rounded', l.threatScore >= 85 ? 'bg-red-500' : l.threatScore >= 75 ? 'bg-threat-high' : 'bg-threat-medium')}
                          style={{ width: `${l.threatScore}%` }}
                        />
                      </div>
                      <span className="font-mono text-[11px] text-text-primary">{l.threatScore}%</span>
                    </div>
                    <ThreatBadge level={l.threatLevel} size="sm" />
                    <span className="font-mono text-[11px] text-text-secondary">{l.duration}s</span>
                    <span className={clsx('text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded border w-fit', actionConfig[l.actionTaken].color)}>
                      {actionConfig[l.actionTaken].label}
                    </span>
                    <div className="flex justify-end">
                      {expandedId === l.id
                        ? <ChevronUp className="w-3.5 h-3.5 text-accent-orange" />
                        : <ChevronDown className="w-3.5 h-3.5 text-text-muted" />
                      }
                    </div>
                  </div>
                  {expandedId === l.id && (
                    <div className="px-4 pb-4">
                      <MiniReplay log={l} />
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
