'use client'

import { useState } from 'react'
import clsx from 'clsx'
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, PieChart, Pie, Cell, RadarChart,
  Radar, PolarGrid, PolarAngleAxis
} from 'recharts'
import { TrendingUp, TrendingDown, AlertTriangle, Clock, ThumbsDown, BarChart2 } from 'lucide-react'
import { weeklyEmotionData, dailyAlerts, cameraPerformance, globalStats } from '@/lib/mockData'
import { Card, StatCard } from '@/components/ui/Card'

const COLORS = {
  stress:   '#f97316',
  colere:   '#ef4444',
  peur:     '#f59e0b',
  fatigue:  '#3b82f6',
  neutral:  '#4b5563',
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-bg-elevated border border-bg-border rounded-xl p-3 text-xs shadow-lg">
      <p className="text-text-secondary font-mono mb-2">{label}</p>
      {payload.map((p: any) => (
        <div key={p.name} className="flex items-center gap-2 mb-1">
          <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="text-text-muted capitalize">{p.name}:</span>
          <span className="font-mono font-semibold" style={{ color: p.color }}>{p.value}{p.name === 'alertCount' ? '' : '%'}</span>
        </div>
      ))}
    </div>
  )
}

// Performance data for agents
const agentPerformance = [
  { agent: 'Agent Dupont', total: 28, avgResp: 32, falsePos: 9 },
  { agent: 'Agent Martin', total: 22, avgResp: 28, falsePos: 4 },
  { agent: 'Agent Leroy',  total: 18, avgResp: 45, falsePos: 6 },
  { agent: 'Agent Bernard',total: 12, avgResp: 62, falsePos: 7 },
]

// Emotion distribution pie
const emotionDist = [
  { name: 'Stress',  value: 32, color: '#f97316' },
  { name: 'Colère',  value: 24, color: '#ef4444' },
  { name: 'Peur',    value: 18, color: '#f59e0b' },
  { name: 'Fatigue', value: 15, color: '#3b82f6' },
  { name: 'Neutre',  value: 11, color: '#4b5563' },
]

// Weekly heatmap data (simplified)
const heatmapData = [
  { day: 'Lun', h6: 12, h8: 35, h10: 52, h12: 48, h14: 55, h16: 38, h18: 22, h20: 10 },
  { day: 'Mar', h6: 18, h8: 42, h10: 60, h12: 55, h14: 62, h16: 45, h18: 28, h20: 14 },
  { day: 'Mer', h6: 8,  h8: 28, h10: 45, h12: 40, h14: 50, h16: 32, h18: 18, h20: 8  },
  { day: 'Jeu', h6: 22, h8: 48, h10: 65, h12: 60, h14: 72, h16: 52, h18: 35, h20: 18 },
  { day: 'Ven', h6: 15, h8: 40, h10: 58, h12: 52, h14: 65, h16: 42, h18: 25, h20: 12 },
  { day: 'Sam', h6: 5,  h8: 18, h10: 30, h12: 28, h14: 32, h16: 20, h18: 12, h20: 5  },
  { day: 'Dim', h6: 3,  h8: 10, h10: 18, h12: 15, h14: 20, h16: 12, h18: 8,  h20: 3  },
]

function HeatCell({ value }: { value: number }) {
  const intensity = Math.min(value / 75, 1)
  const color = value >= 60 ? `rgba(239,68,68,${0.2 + intensity * 0.8})`
    : value >= 40 ? `rgba(245,158,11,${0.2 + intensity * 0.8})`
    : value >= 20 ? `rgba(249,115,22,${0.1 + intensity * 0.6})`
    : `rgba(30,42,61,${0.5 + intensity * 0.5})`
  return (
    <div
      className="rounded flex items-center justify-center text-[9px] font-mono font-bold transition-all cursor-default"
      style={{ background: color, height: 28 }}
      title={`${value}%`}
    >
      <span style={{ color: value > 30 ? '#fff' : '#4b5563' }}>{value}</span>
    </div>
  )
}

export default function AnalyticsPage() {
  const [period, setPeriod] = useState<'day' | 'week' | 'month'>('day')

  const falsePositiveRate = ((dailyAlerts.reduce((s, d) => s + d.falsePositive, 0) / dailyAlerts.reduce((s, d) => s + d.total, 0)) * 100).toFixed(1)

  return (
    <div className="h-full overflow-y-auto space-y-4">
      {/* KPIs */}
      <div className="grid grid-cols-4 gap-3">
        <StatCard
          label="Alertes (7 jours)"
          value={dailyAlerts.reduce((s, d) => s + d.total, 0)}
          sub="↑ 12% vs semaine passée"
          icon={<AlertTriangle className="w-4 h-4" />}
          trend="up"
          trendValue="+12% vs sem. passée"
          accent="red"
        />
        <StatCard
          label="Taux faux positifs"
          value={`${falsePositiveRate}%`}
          sub="Objectif: < 30%"
          icon={<ThumbsDown className="w-4 h-4" />}
          trend={parseFloat(falsePositiveRate) > 30 ? 'up' : 'down'}
          trendValue={parseFloat(falsePositiveRate) > 30 ? 'Au-dessus objectif' : 'Dans la cible'}
          accent={parseFloat(falsePositiveRate) > 30 ? 'red' : 'green'}
        />
        <StatCard
          label="Temps réponse moyen"
          value={`${globalStats.avgResponseTime}s`}
          sub="Objectif: < 60s"
          icon={<Clock className="w-4 h-4" />}
          trend="down"
          trendValue="-8s vs semaine passée"
          accent="green"
        />
        <StatCard
          label="Score Calibration IA"
          value="87/100"
          sub="Dernière calibration: 24/02"
          icon={<BarChart2 className="w-4 h-4" />}
          accent="orange"
        />
      </div>

      <div className="grid grid-cols-3 gap-4">
        {/* Emotion heatmap by hour */}
        <div className="col-span-2">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-semibold text-text-primary">Heatmap Stress — Par Heure & Jour</h3>
                <p className="text-[11px] text-text-muted mt-0.5">Score de stress moyen (%) — Semaine du 18/02 au 25/02</p>
              </div>
              <div className="flex items-center gap-2 text-[10px] text-text-muted">
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded bg-bg-border/80" />0%</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded bg-accent-orange/60" />40%</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded bg-threat-high" />70%+</span>
              </div>
            </div>
            <div>
              <div className="grid mb-1 text-[10px] text-text-muted font-mono" style={{ gridTemplateColumns: '40px repeat(8, 1fr)' }}>
                <span />
                {['6h', '8h', '10h', '12h', '14h', '16h', '18h', '20h'].map(h => (
                  <span key={h} className="text-center">{h}</span>
                ))}
              </div>
              <div className="space-y-1">
                {heatmapData.map(row => (
                  <div key={row.day} className="grid items-center gap-1" style={{ gridTemplateColumns: '40px repeat(8, 1fr)' }}>
                    <span className="text-[11px] font-mono text-text-muted">{row.day}</span>
                    {[row.h6, row.h8, row.h10, row.h12, row.h14, row.h16, row.h18, row.h20].map((v, i) => (
                      <HeatCell key={i} value={v} />
                    ))}
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </div>

        {/* Emotion distribution pie */}
        <Card>
          <h3 className="text-sm font-semibold text-text-primary mb-1">Distribution des Émotions</h3>
          <p className="text-[11px] text-text-muted mb-4">7 derniers jours</p>
          <ResponsiveContainer width="100%" height={160}>
            <PieChart>
              <Pie data={emotionDist} cx="50%" cy="50%" innerRadius={45} outerRadius={70} paddingAngle={3} dataKey="value">
                {emotionDist.map((entry, i) => (
                  <Cell key={i} fill={entry.color} stroke="transparent" />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: '#111827', border: '1px solid #1e2a3d', borderRadius: '8px', fontSize: 11 }}
                formatter={(v: number, name: string) => [`${v}%`, name]}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="space-y-1.5 mt-2">
            {emotionDist.map(e => (
              <div key={e.name} className="flex items-center justify-between text-[11px]">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ background: e.color }} />
                  <span className="text-text-secondary">{e.name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-16 h-1 bg-bg-border rounded overflow-hidden">
                    <div className="h-full rounded" style={{ width: `${e.value}%`, background: e.color }} />
                  </div>
                  <span className="font-mono text-text-primary w-8 text-right">{e.value}%</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Emotion trends over day */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-text-primary">Évolution des Émotions — Aujourd'hui</h3>
            <p className="text-[11px] text-text-muted mt-0.5">Scores par heure — 25/02/2026</p>
          </div>
          <div className="flex gap-1">
            {(['day', 'week', 'month'] as const).map(p => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={clsx('px-2.5 py-1 text-xs rounded border transition-all',
                  period === p ? 'bg-accent-orange/10 border-accent-orange/30 text-accent-orange' : 'bg-bg-elevated border-bg-border text-text-muted'
                )}
              >
                {p === 'day' ? 'Jour' : p === 'week' ? 'Semaine' : 'Mois'}
              </button>
            ))}
          </div>
        </div>
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={weeklyEmotionData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
            <defs>
              {Object.entries(COLORS).map(([key, color]) => (
                <linearGradient key={key} id={`grad-${key}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={color} stopOpacity={0} />
                </linearGradient>
              ))}
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e2a3d" />
            <XAxis dataKey="hour" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={{ stroke: '#1e2a3d' }} tickLine={false} />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={{ stroke: '#1e2a3d' }} tickLine={false} unit="%" />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: 11, color: '#94a3b8' }} />
            <Area type="monotone" dataKey="stress" name="Stress" stroke={COLORS.stress} fill={`url(#grad-stress)`} strokeWidth={2} />
            <Area type="monotone" dataKey="colere" name="Colère" stroke={COLORS.colere} fill={`url(#grad-colere)`} strokeWidth={2} />
            <Area type="monotone" dataKey="peur" name="Peur" stroke={COLORS.peur} fill={`url(#grad-peur)`} strokeWidth={2} />
            <Area type="monotone" dataKey="fatigue" name="Fatigue" stroke={COLORS.fatigue} fill={`url(#grad-fatigue)`} strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </Card>

      <div className="grid grid-cols-2 gap-4">
        {/* Daily alerts vs false positives */}
        <Card>
          <h3 className="text-sm font-semibold text-text-primary mb-1">Alertes — 7 Derniers Jours</h3>
          <p className="text-[11px] text-text-muted mb-4">Vraies alertes vs Faux positifs</p>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={dailyAlerts} margin={{ top: 5, right: 10, left: -20, bottom: 0 }} barSize={14} barGap={2}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2a3d" vertical={false} />
              <XAxis dataKey="day" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={{ stroke: '#1e2a3d' }} tickLine={false} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: '#111827', border: '1px solid #1e2a3d', borderRadius: '8px', fontSize: 11 }} />
              <Bar dataKey="real" name="Vraies alertes" fill="#ef4444" radius={[2, 2, 0, 0]} />
              <Bar dataKey="falsePositive" name="Faux positifs" fill="#1e2a3d" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Agent performance */}
        <Card>
          <h3 className="text-sm font-semibold text-text-primary mb-1">Performance des Agents</h3>
          <p className="text-[11px] text-text-muted mb-4">Temps de réaction moyen & alertes traitées</p>
          <div className="space-y-3">
            {agentPerformance.map(a => (
              <div key={a.agent} className="flex items-center gap-3">
                <div className="w-7 h-7 rounded-lg bg-accent-orange/10 border border-accent-orange/20 flex items-center justify-center flex-shrink-0">
                  <span className="text-accent-orange text-[9px] font-bold">{a.agent.split(' ')[1]?.[0]}{a.agent.split(' ')[0]?.[0]}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-text-primary truncate">{a.agent}</span>
                    <div className="flex gap-3 text-[11px] font-mono flex-shrink-0">
                      <span className={clsx(a.avgResp <= 40 ? 'text-threat-low' : a.avgResp <= 60 ? 'text-threat-medium' : 'text-threat-high')}>
                        {a.avgResp}s
                      </span>
                      <span className="text-text-muted">{a.total} alertes</span>
                    </div>
                  </div>
                  <div className="h-1.5 bg-bg-border rounded-full overflow-hidden">
                    <div
                      className={clsx('h-full rounded-full', a.avgResp <= 40 ? 'bg-threat-low' : a.avgResp <= 60 ? 'bg-threat-medium' : 'bg-threat-high')}
                      style={{ width: `${Math.min((a.avgResp / 90) * 100, 100)}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-3 border-t border-bg-border flex justify-between text-[11px]">
            <span className="text-text-muted">Taux global faux positifs</span>
            <span className="font-mono font-bold text-threat-medium">{falsePositiveRate}%</span>
          </div>
        </Card>
      </div>
    </div>
  )
}
