'use client'

import clsx from 'clsx'
import { type ThreatLevel } from '@/lib/mockData'

interface BadgeProps {
  level: ThreatLevel | 'info'
  label?: string
  pulse?: boolean
  size?: 'sm' | 'md'
}

const levelConfig = {
  low:      { text: 'text-threat-low',     bg: 'bg-threat-low/10',      border: 'border-threat-low/30',      dot: 'bg-threat-low',      label: 'FAIBLE' },
  medium:   { text: 'text-threat-medium',  bg: 'bg-threat-medium/10',   border: 'border-threat-medium/30',   dot: 'bg-threat-medium',   label: 'MODÉRÉ' },
  high:     { text: 'text-threat-high',    bg: 'bg-threat-high/10',     border: 'border-threat-high/30',     dot: 'bg-threat-high',     label: 'ÉLEVÉ' },
  critical: { text: 'text-red-400',        bg: 'bg-red-500/10',         border: 'border-red-500/30',         dot: 'bg-red-500',         label: 'CRITIQUE' },
  info:     { text: 'text-text-secondary', bg: 'bg-bg-elevated',        border: 'border-bg-border',          dot: 'bg-text-muted',      label: 'INFO' },
}

export function ThreatBadge({ level, label, pulse = false, size = 'md' }: BadgeProps) {
  const cfg = levelConfig[level]
  return (
    <span className={clsx(
      'inline-flex items-center gap-1.5 font-mono font-semibold rounded border',
      cfg.text, cfg.bg, cfg.border,
      size === 'sm' ? 'text-[10px] px-1.5 py-0.5' : 'text-xs px-2 py-1'
    )}>
      <span className={clsx('rounded-full flex-shrink-0', cfg.dot, size === 'sm' ? 'w-1.5 h-1.5' : 'w-2 h-2', pulse && 'animate-pulse')} />
      {label ?? cfg.label}
    </span>
  )
}

export function StatusBadge({ status }: { status: 'online' | 'offline' | 'degraded' | 'maintenance' }) {
  const cfg = {
    online:      { text: 'text-threat-low',    bg: 'bg-threat-low/10',    border: 'border-threat-low/30',    dot: 'bg-threat-low',    label: 'EN LIGNE' },
    offline:     { text: 'text-threat-high',   bg: 'bg-threat-high/10',   border: 'border-threat-high/30',   dot: 'bg-threat-high',   label: 'HORS LIGNE' },
    degraded:    { text: 'text-threat-medium', bg: 'bg-threat-medium/10', border: 'border-threat-medium/30', dot: 'bg-threat-medium', label: 'DÉGRADÉ' },
    maintenance: { text: 'text-accent-blue',   bg: 'bg-accent-blue/10',   border: 'border-accent-blue/30',   dot: 'bg-accent-blue',   label: 'MAINTENANCE' },
  }[status]
  return (
    <span className={clsx('inline-flex items-center gap-1.5 text-xs font-mono font-semibold rounded border px-2 py-1', cfg.text, cfg.bg, cfg.border)}>
      <span className={clsx('w-2 h-2 rounded-full', cfg.dot, status === 'online' && 'status-online')} />
      {cfg.label}
    </span>
  )
}

export function RoleBadge({ role }: { role: 'admin' | 'manager' | 'agent' }) {
  const cfg = {
    admin:   { text: 'text-accent-orange', bg: 'bg-accent-orange/10', border: 'border-accent-orange/30', label: 'ADMIN' },
    manager: { text: 'text-accent-blue',   bg: 'bg-accent-blue/10',   border: 'border-accent-blue/30',   label: 'MANAGER' },
    agent:   { text: 'text-text-secondary',bg: 'bg-bg-elevated',      border: 'border-bg-border',        label: 'AGENT' },
  }[role]
  return (
    <span className={clsx('inline-flex items-center text-xs font-mono font-semibold rounded border px-2 py-1', cfg.text, cfg.bg, cfg.border)}>
      {cfg.label}
    </span>
  )
}
