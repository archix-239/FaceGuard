'use client'

import clsx from 'clsx'
import { type ReactNode } from 'react'

interface CardProps {
  children: ReactNode
  className?: string
  glow?: 'orange' | 'red' | 'green' | 'blue' | 'none'
  padding?: 'none' | 'sm' | 'md' | 'lg'
}

export function Card({ children, className, glow = 'none', padding = 'md' }: CardProps) {
  const glowClass = {
    orange: 'shadow-[0_0_20px_rgba(249,115,22,0.12)] border-accent-orange/20',
    red:    'shadow-[0_0_20px_rgba(239,68,68,0.15)] border-red-500/20',
    green:  'shadow-[0_0_20px_rgba(34,197,94,0.12)] border-green-500/20',
    blue:   'shadow-[0_0_20px_rgba(59,130,246,0.12)] border-blue-500/20',
    none:   'border-bg-border',
  }[glow]

  const paddingClass = {
    none: '',
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6',
  }[padding]

  return (
    <div className={clsx(
      'bg-bg-card rounded-xl border',
      glowClass,
      paddingClass,
      className
    )}>
      {children}
    </div>
  )
}

interface StatCardProps {
  label: string
  value: string | number
  sub?: string
  icon: ReactNode
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
  accent?: 'orange' | 'red' | 'green' | 'blue'
}

export function StatCard({ label, value, sub, icon, trend, trendValue, accent = 'orange' }: StatCardProps) {
  const accentColor = {
    orange: 'text-accent-orange bg-accent-orange/10 border-accent-orange/20',
    red:    'text-threat-high bg-threat-high/10 border-threat-high/20',
    green:  'text-threat-low bg-threat-low/10 border-threat-low/20',
    blue:   'text-accent-blue bg-accent-blue/10 border-accent-blue/20',
  }[accent]

  const trendColor = trend === 'up' ? 'text-threat-high' : trend === 'down' ? 'text-threat-low' : 'text-text-secondary'

  return (
    <Card className="flex items-start gap-4">
      <div className={clsx('p-3 rounded-lg border flex-shrink-0', accentColor)}>
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-text-secondary text-xs font-medium uppercase tracking-wider mb-1">{label}</p>
        <p className="text-2xl font-bold text-text-primary font-mono">{value}</p>
        {sub && <p className="text-text-muted text-xs mt-0.5">{sub}</p>}
        {trendValue && (
          <p className={clsx('text-xs mt-1 font-mono', trendColor)}>
            {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'} {trendValue}
          </p>
        )}
      </div>
    </Card>
  )
}
