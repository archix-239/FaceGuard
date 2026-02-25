'use client'

import { useState, useEffect } from 'react'
import clsx from 'clsx'
import { Bell, Search, User, ChevronDown, Shield, Wifi } from 'lucide-react'
import { globalStats } from '@/lib/mockData'
import { ThreatBadge } from '@/components/ui/Badge'

const pageTitles: Record<string, { title: string; sub: string }> = {
  '/dashboard': { title: 'Surveillance Live', sub: 'Monitoring temps réel — 8 caméras actives' },
  '/alerts':    { title: 'Gestion des Alertes', sub: 'Triage et traitement des incidents' },
  '/logs':      { title: 'Historique & Logs', sub: 'Recherche et replay des événements passés' },
  '/analytics': { title: 'Analytique', sub: 'Tendances et statistiques comportementales' },
  '/cameras':   { title: 'Gestion des Caméras', sub: 'Devices — Statut et configuration des flux' },
  '/settings':  { title: 'Configuration IA', sub: 'Paramètres du moteur FaceGuard' },
  '/users':     { title: 'Gestion des Utilisateurs', sub: 'Contrôle d\'accès et audit RBAC' },
}

export default function TopBar({ pathname }: { pathname: string }) {
  const [time, setTime] = useState(new Date())
  const page = pageTitles[pathname] ?? { title: 'FaceGuard Admin', sub: '' }

  useEffect(() => {
    const interval = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(interval)
  }, [])

  const threatColor = {
    low: 'text-threat-low',
    medium: 'text-threat-medium',
    high: 'text-threat-high',
    critical: 'text-red-400',
  }[globalStats.globalThreatLevel]

  return (
    <header className="h-14 flex items-center justify-between px-6 border-b border-bg-border bg-bg-secondary flex-shrink-0">
      {/* Left: Page title */}
      <div className="flex items-center gap-3">
        <div>
          <h1 className="text-text-primary font-semibold text-sm leading-tight">{page.title}</h1>
          <p className="text-text-muted text-[11px]">{page.sub}</p>
        </div>
      </div>

      {/* Center: Search */}
      <div className="flex-1 max-w-sm mx-8">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-muted" />
          <input
            type="text"
            placeholder="Rechercher caméra, alerte, agent..."
            className="w-full bg-bg-elevated border border-bg-border rounded-lg pl-9 pr-4 py-1.5 text-xs text-text-secondary placeholder-text-muted outline-none focus:border-accent-orange/50 focus:bg-bg-card transition-all"
          />
        </div>
      </div>

      {/* Right: Status + User */}
      <div className="flex items-center gap-4">
        {/* Global Threat */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-bg-elevated border border-bg-border">
          <Shield className={clsx('w-3.5 h-3.5', threatColor)} />
          <span className="text-[11px] text-text-secondary">Menace:</span>
          <ThreatBadge level={globalStats.globalThreatLevel} size="sm" pulse />
        </div>

        {/* Network */}
        <div className="flex items-center gap-1.5 text-text-secondary">
          <Wifi className="w-3.5 h-3.5 text-threat-low" />
          <span className="text-[11px] font-mono">{globalStats.camerasOnline}/{globalStats.camerasTotal}</span>
        </div>

        {/* Clock */}
        <div className="font-mono text-xs text-text-secondary tabular-nums">
          {time.toLocaleTimeString('fr-FR')}
        </div>

        {/* Alerts bell */}
        <button className="relative p-1.5 rounded-lg hover:bg-bg-elevated transition-colors">
          <Bell className="w-4 h-4 text-text-secondary" />
          {globalStats.pendingAlerts > 0 && (
            <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-threat-high text-white text-[9px] font-bold rounded-full flex items-center justify-center">
              {globalStats.pendingAlerts}
            </span>
          )}
        </button>

        {/* User menu */}
        <button className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-bg-elevated transition-colors">
          <div className="w-7 h-7 rounded-lg bg-accent-orange/15 border border-accent-orange/30 flex items-center justify-center">
            <span className="text-accent-orange text-[10px] font-bold">JM</span>
          </div>
          <div className="text-left hidden md:block">
            <p className="text-xs text-text-primary font-medium leading-tight">J.P. Moreau</p>
            <p className="text-[10px] text-accent-orange font-mono">ADMIN</p>
          </div>
          <ChevronDown className="w-3 h-3 text-text-muted" />
        </button>
      </div>
    </header>
  )
}
