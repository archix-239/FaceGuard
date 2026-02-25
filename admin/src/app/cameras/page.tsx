'use client'

import { useState } from 'react'
import clsx from 'clsx'
import {
  Plus, Trash2, Edit, RefreshCw, Wifi, WifiOff, AlertTriangle,
  Camera, MapPin, Network, Clock, Activity, X, Check
} from 'lucide-react'
import { cameras, type CameraFeed, type CameraStatus } from '@/lib/mockData'
import { StatusBadge, ThreatBadge } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'

function PingBar({ uptime }: { uptime: number }) {
  const bars = 12
  const active = Math.round((uptime / 100) * bars)
  return (
    <div className="flex gap-0.5 items-end h-4">
      {[...Array(bars)].map((_, i) => (
        <div
          key={i}
          className={clsx('w-1 rounded-sm transition-all', i < active ? 'bg-threat-low' : 'bg-bg-border')}
          style={{ height: `${40 + (i / bars) * 60}%` }}
        />
      ))}
    </div>
  )
}

function CameraRow({ cam, onEdit, onDelete }: { cam: CameraFeed; onEdit: (c: CameraFeed) => void; onDelete: (id: string) => void }) {
  const [pinging, setPinging] = useState(false)
  const [lastPingResult, setLastPingResult] = useState<string | null>(null)

  const handlePing = () => {
    setPinging(true)
    setLastPingResult(null)
    setTimeout(() => {
      setPinging(false)
      setLastPingResult(cam.status === 'online' ? '12ms' : 'Timeout')
    }, 1200)
  }

  return (
    <div className={clsx(
      'grid items-center gap-4 px-4 py-3 border-b border-bg-border hover:bg-bg-elevated/50 transition-colors',
    )} style={{ gridTemplateColumns: '40px 1.2fr 1.5fr 1.2fr 80px 80px 80px 100px 100px' }}>
      {/* ID */}
      <span className="font-mono text-xs font-bold text-accent-orange">{cam.id.replace('CAM-', '#')}</span>

      {/* Name + zone */}
      <div>
        <p className="text-xs font-semibold text-text-primary">{cam.name}</p>
        <div className="flex items-center gap-1 mt-0.5">
          <MapPin className="w-2.5 h-2.5 text-text-muted" />
          <span className="text-[10px] text-text-muted">{cam.location}</span>
        </div>
      </div>

      {/* IP / RTSP */}
      <div>
        <div className="flex items-center gap-1.5">
          <Network className="w-3 h-3 text-text-muted" />
          <span className="font-mono text-[11px] text-text-secondary">{cam.ip}</span>
        </div>
        <span className="text-[10px] text-text-muted font-mono block mt-0.5 truncate">{cam.rtsp}</span>
      </div>

      {/* Status */}
      <StatusBadge status={cam.status} />

      {/* FPS */}
      <div className="text-center">
        <span className={clsx('font-mono text-xs font-bold', cam.fps > 0 ? 'text-text-primary' : 'text-text-muted')}>
          {cam.fps > 0 ? `${cam.fps}fps` : '—'}
        </span>
      </div>

      {/* Resolution */}
      <span className="font-mono text-[11px] text-text-secondary text-center">{cam.resolution}</span>

      {/* Uptime */}
      <div className="flex flex-col items-center gap-1">
        <PingBar uptime={cam.uptime} />
        <span className={clsx('text-[10px] font-mono', cam.uptime > 95 ? 'text-threat-low' : cam.uptime > 70 ? 'text-threat-medium' : 'text-threat-high')}>
          {cam.uptime}%
        </span>
      </div>

      {/* Ping */}
      <div className="text-center">
        <button
          onClick={handlePing}
          className={clsx(
            'flex items-center gap-1.5 px-2 py-1 text-[10px] font-mono rounded border transition-all',
            pinging ? 'border-accent-orange/30 text-accent-orange' : 'border-bg-border text-text-muted hover:border-accent-orange/20 hover:text-text-secondary'
          )}
        >
          {pinging ? (
            <><RefreshCw className="w-2.5 h-2.5 animate-spin" /> Ping…</>
          ) : lastPingResult ? (
            lastPingResult === 'Timeout' ? (
              <><WifiOff className="w-2.5 h-2.5 text-threat-high" /> <span className="text-threat-high">Timeout</span></>
            ) : (
              <><Check className="w-2.5 h-2.5 text-threat-low" /> <span className="text-threat-low">{lastPingResult}</span></>
            )
          ) : (
            <><Wifi className="w-2.5 h-2.5" /> Ping</>
          )}
        </button>
      </div>

      {/* Actions */}
      <div className="flex gap-1 justify-end">
        <button onClick={() => onEdit(cam)} className="p-1.5 rounded-lg border border-bg-border hover:border-accent-orange/30 hover:text-accent-orange text-text-muted transition-all">
          <Edit className="w-3 h-3" />
        </button>
        <button onClick={() => onDelete(cam.id)} className="p-1.5 rounded-lg border border-bg-border hover:border-threat-high/30 hover:text-threat-high text-text-muted transition-all">
          <Trash2 className="w-3 h-3" />
        </button>
      </div>
    </div>
  )
}

// Add / Edit modal
function CameraModal({ cam, onClose, onSave }: { cam?: CameraFeed; onClose: () => void; onSave: (data: Partial<CameraFeed>) => void }) {
  const [form, setForm] = useState({
    name: cam?.name ?? '',
    location: cam?.location ?? '',
    ip: cam?.ip ?? '',
    rtsp: cam?.rtsp ?? '',
    resolution: cam?.resolution ?? '1920x1080',
  })

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-bg-card border border-bg-border rounded-2xl w-full max-w-lg p-6 animate-fade-in">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-sm font-bold text-text-primary">{cam ? 'Modifier la Caméra' : 'Ajouter une Caméra'}</h2>
            {cam && <p className="text-[11px] text-text-muted font-mono mt-0.5">{cam.id}</p>}
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-bg-elevated text-text-muted hover:text-text-primary transition-all">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="space-y-4">
          {[
            { key: 'name', label: 'Nom de la caméra', placeholder: 'ex: Pont-Bascule Nord' },
            { key: 'location', label: 'Zone / Emplacement', placeholder: 'ex: Entrée principale' },
            { key: 'ip', label: 'Adresse IP', placeholder: '192.168.1.xxx' },
            { key: 'rtsp', label: 'URL RTSP', placeholder: 'rtsp://192.168.1.xxx:554/stream1' },
          ].map(f => (
            <div key={f.key}>
              <label className="block text-[11px] text-text-muted mb-1.5 font-medium">{f.label}</label>
              <input
                type="text"
                value={form[f.key as keyof typeof form]}
                onChange={e => setForm(prev => ({ ...prev, [f.key]: e.target.value }))}
                placeholder={f.placeholder}
                className="w-full bg-bg-elevated border border-bg-border rounded-lg px-3 py-2 text-xs text-text-secondary placeholder-text-muted outline-none focus:border-accent-orange/50 transition-all"
              />
            </div>
          ))}
          <div>
            <label className="block text-[11px] text-text-muted mb-1.5 font-medium">Résolution</label>
            <select
              value={form.resolution}
              onChange={e => setForm(prev => ({ ...prev, resolution: e.target.value }))}
              className="w-full bg-bg-elevated border border-bg-border rounded-lg px-3 py-2 text-xs text-text-secondary outline-none focus:border-accent-orange/50"
            >
              {['1280x720', '1920x1080', '2560x1440', '3840x2160'].map(r => <option key={r}>{r}</option>)}
            </select>
          </div>
        </div>

        <div className="flex gap-3 mt-6 pt-4 border-t border-bg-border">
          <button onClick={onClose} className="flex-1 px-4 py-2.5 text-xs font-semibold text-text-secondary border border-bg-border rounded-xl hover:border-accent-orange/20 transition-all">
            Annuler
          </button>
          <button
            onClick={() => { onSave(form); onClose() }}
            className="flex-1 px-4 py-2.5 text-xs font-semibold text-black bg-accent-orange rounded-xl hover:bg-accent-orange/90 transition-all"
          >
            {cam ? 'Enregistrer' : 'Ajouter'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function CamerasPage() {
  const [cameraList, setCameraList] = useState<CameraFeed[]>(cameras)
  const [modal, setModal] = useState<{ open: boolean; cam?: CameraFeed }>({ open: false })
  const [statusFilter, setStatusFilter] = useState<'all' | CameraStatus>('all')

  const handleDelete = (id: string) => {
    if (confirm(`Supprimer la caméra ${id} ?`)) {
      setCameraList(prev => prev.filter(c => c.id !== id))
    }
  }

  const handleSave = (data: Partial<CameraFeed>) => {
    if (modal.cam) {
      setCameraList(prev => prev.map(c => c.id === modal.cam!.id ? { ...c, ...data } : c))
    } else {
      const newId = `CAM-${String(cameraList.length + 1).padStart(2, '0')}`
      setCameraList(prev => [...prev, {
        id: newId,
        name: data.name ?? 'Nouvelle Caméra',
        location: data.location ?? '—',
        ip: data.ip ?? '0.0.0.0',
        rtsp: data.rtsp ?? '',
        resolution: data.resolution ?? '1920x1080',
        status: 'offline',
        fps: 0,
        lastPing: '—',
        threatLevel: 'low',
        detectionActive: false,
        personCount: 0,
        uptime: 0,
      }])
    }
  }

  const filtered = cameraList.filter(c => statusFilter === 'all' || c.status === statusFilter)
  const counts = { online: cameraList.filter(c => c.status === 'online').length, offline: cameraList.filter(c => c.status === 'offline').length, degraded: cameraList.filter(c => c.status === 'degraded').length }

  return (
    <div className="h-full flex flex-col gap-4">
      {/* Stats */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: 'En ligne',    value: counts.online,   color: 'text-threat-low',    icon: <Wifi className="w-4 h-4" />,        accent: 'green' as const },
          { label: 'Hors ligne', value: counts.offline,  color: 'text-threat-high',   icon: <WifiOff className="w-4 h-4" />,     accent: 'red' as const },
          { label: 'Dégradées',  value: counts.degraded, color: 'text-threat-medium', icon: <AlertTriangle className="w-4 h-4" />,accent: 'orange' as const },
          { label: 'Total',      value: cameraList.length,color: 'text-text-primary', icon: <Camera className="w-4 h-4" />,      accent: 'blue' as const },
        ].map(s => (
          <Card key={s.label} className="flex items-center gap-3">
            <div className={clsx('p-2.5 rounded-lg border flex-shrink-0',
              s.accent === 'green' ? 'bg-threat-low/10 border-threat-low/20 text-threat-low' :
              s.accent === 'red' ? 'bg-threat-high/10 border-threat-high/20 text-threat-high' :
              s.accent === 'orange' ? 'bg-threat-medium/10 border-threat-medium/20 text-threat-medium' :
              'bg-accent-blue/10 border-accent-blue/20 text-accent-blue'
            )}>
              {s.icon}
            </div>
            <div>
              <p className="text-text-muted text-[11px]">{s.label}</p>
              <p className={clsx('text-2xl font-bold font-mono', s.color)}>{s.value}</p>
            </div>
          </Card>
        ))}
      </div>

      {/* Toolbar */}
      <div className="flex items-center justify-between">
        <div className="flex gap-1">
          {(['all', 'online', 'offline', 'degraded', 'maintenance'] as const).map(s => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={clsx(
                'px-3 py-1.5 text-xs font-medium rounded-lg border transition-all',
                statusFilter === s ? 'bg-accent-orange/10 border-accent-orange/30 text-accent-orange' : 'bg-bg-card border-bg-border text-text-muted hover:text-text-secondary'
              )}
            >
              {s === 'all' ? 'Toutes' : s === 'online' ? 'En ligne' : s === 'offline' ? 'Hors ligne' : s === 'degraded' ? 'Dégradées' : 'Maintenance'}
            </button>
          ))}
        </div>
        <button
          onClick={() => setModal({ open: true })}
          className="flex items-center gap-2 px-4 py-2 bg-accent-orange text-black text-xs font-bold rounded-xl hover:bg-accent-orange/90 transition-all"
        >
          <Plus className="w-3.5 h-3.5" />
          Ajouter une caméra
        </button>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        <div className="bg-bg-card border border-bg-border rounded-xl overflow-hidden min-w-[900px]">
          {/* Header */}
          <div
            className="grid text-[11px] font-semibold text-text-muted uppercase tracking-wider px-4 py-2 bg-bg-elevated border-b border-bg-border"
            style={{ gridTemplateColumns: '40px 1.2fr 1.5fr 1.2fr 80px 80px 80px 100px 100px' }}
          >
            <span>#</span>
            <span>Nom / Zone</span>
            <span>Réseau</span>
            <span>Statut</span>
            <span className="text-center">FPS</span>
            <span className="text-center">Résolution</span>
            <span className="text-center">Uptime</span>
            <span className="text-center">Ping</span>
            <span className="text-right">Actions</span>
          </div>
          <div>
            {filtered.map(cam => (
              <CameraRow
                key={cam.id}
                cam={cam}
                onEdit={c => setModal({ open: true, cam: c })}
                onDelete={handleDelete}
              />
            ))}
          </div>
        </div>
      </div>

      {modal.open && (
        <CameraModal
          cam={modal.cam}
          onClose={() => setModal({ open: false })}
          onSave={handleSave}
        />
      )}
    </div>
  )
}
