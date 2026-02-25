'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import clsx from 'clsx'
import {
  Monitor, Bell, Clock, BarChart2, Camera, Settings, Users,
  ChevronLeft, ChevronRight, Shield, Wifi, WifiOff, AlertTriangle
} from 'lucide-react'
import { globalStats } from '@/lib/mockData'

const navGroups = [
  {
    label: 'Pôle Opérationnel',
    items: [
      { href: '/dashboard', icon: Monitor, label: 'Surveillance Live', badge: null },
      { href: '/alerts', icon: Bell, label: 'Gestion Alertes', badge: globalStats.pendingAlerts },
    ]
  },
  {
    label: 'Pôle Managérial',
    items: [
      { href: '/logs', icon: Clock, label: 'Historique & Logs', badge: null },
      { href: '/analytics', icon: BarChart2, label: 'Analytique', badge: null },
    ]
  },
  {
    label: 'Pôle Technique',
    items: [
      { href: '/cameras', icon: Camera, label: 'Caméras', badge: null },
      { href: '/settings', icon: Settings, label: 'Config IA', badge: null },
      { href: '/users', icon: Users, label: 'Utilisateurs', badge: null },
    ]
  },
]

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const pathname = usePathname()

  const onlineCams = 6
  const totalCams = 8

  return (
    <aside className={clsx(
      'flex flex-col bg-bg-secondary border-r border-bg-border transition-all duration-300 flex-shrink-0 h-full relative',
      collapsed ? 'w-16' : 'w-60'
    )}>
      {/* Logo */}
      <div className={clsx(
        'flex items-center border-b border-bg-border flex-shrink-0',
        collapsed ? 'px-3 py-4 justify-center' : 'px-5 py-4 gap-3'
      )}>
        <div className="relative flex-shrink-0">
          <div className="w-9 h-9 rounded-lg bg-accent-orange/15 border border-accent-orange/30 flex items-center justify-center">
            <Shield className="w-5 h-5 text-accent-orange" />
          </div>
          <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-threat-low rounded-full border-2 border-bg-secondary status-online" />
        </div>
        {!collapsed && (
          <div>
            <p className="text-text-primary font-bold text-sm leading-tight">FaceGuard</p>
            <p className="text-accent-orange text-[10px] font-mono font-medium tracking-widest">ADMIN v2.0</p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-5">
        {navGroups.map((group) => (
          <div key={group.label}>
            {!collapsed && (
              <p className="text-text-muted text-[10px] font-semibold uppercase tracking-widest px-3 mb-2">
                {group.label}
              </p>
            )}
            <ul className="space-y-0.5">
              {group.items.map(({ href, icon: Icon, label, badge }) => {
                const active = pathname === href || pathname.startsWith(href + '/')
                return (
                  <li key={href}>
                    <Link
                      href={href}
                      title={collapsed ? label : undefined}
                      className={clsx(
                        'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 group relative',
                        active
                          ? 'bg-accent-orange/10 text-accent-orange border border-accent-orange/20'
                          : 'text-text-secondary hover:text-text-primary hover:bg-bg-elevated',
                        collapsed && 'justify-center'
                      )}
                    >
                      <Icon className={clsx('flex-shrink-0', active ? 'w-[18px] h-[18px]' : 'w-[18px] h-[18px]')} />
                      {!collapsed && (
                        <>
                          <span className="flex-1 truncate">{label}</span>
                          {badge !== null && badge !== undefined && badge > 0 && (
                            <span className="min-w-[20px] h-5 px-1.5 bg-threat-high text-white text-[10px] font-bold rounded-full flex items-center justify-center animate-pulse">
                              {badge}
                            </span>
                          )}
                        </>
                      )}
                      {collapsed && badge !== null && badge !== undefined && badge > 0 && (
                        <span className="absolute top-1 right-1 w-2 h-2 bg-threat-high rounded-full" />
                      )}
                    </Link>
                  </li>
                )
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* Camera status */}
      {!collapsed && (
        <div className="px-3 py-3 mx-2 mb-3 rounded-lg bg-bg-elevated border border-bg-border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] text-text-muted font-semibold uppercase tracking-wider">Caméras</span>
            <span className="text-[10px] font-mono text-text-primary">{onlineCams}/{totalCams}</span>
          </div>
          <div className="w-full bg-bg-border rounded-full h-1.5">
            <div
              className="bg-threat-low h-1.5 rounded-full transition-all"
              style={{ width: `${(onlineCams / totalCams) * 100}%` }}
            />
          </div>
          <div className="flex gap-3 mt-2">
            <span className="flex items-center gap-1 text-[10px] text-threat-low">
              <Wifi className="w-3 h-3" />{onlineCams} en ligne
            </span>
            <span className="flex items-center gap-1 text-[10px] text-threat-high">
              <WifiOff className="w-3 h-3" />{totalCams - onlineCams} off
            </span>
          </div>
        </div>
      )}

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-bg-elevated border border-bg-border flex items-center justify-center text-text-secondary hover:text-accent-orange hover:border-accent-orange/30 transition-all z-10"
      >
        {collapsed ? <ChevronRight className="w-3 h-3" /> : <ChevronLeft className="w-3 h-3" />}
      </button>
    </aside>
  )
}
