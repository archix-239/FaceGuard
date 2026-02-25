"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area
} from "recharts";
import { TrendingUp, Users, AlertTriangle, CheckCircle2 } from "lucide-react";

const data = [
  { name: "00h", stress: 20, fatige: 40 },
  { name: "04h", stress: 15, fatige: 60 },
  { name: "08h", stress: 45, fatige: 30 },
  { name: "12h", stress: 80, fatige: 20 },
  { name: "16h", stress: 65, fatige: 25 },
  { name: "20h", stress: 30, fatige: 45 },
];

const performanceData = [
  { day: "Lun", reaction: 12 },
  { day: "Mar", reaction: 10 },
  { day: "Mer", reaction: 15 },
  { day: "Jeu", reaction: 8 },
  { day: "Ven", reaction: 11 },
  { day: "Sam", reaction: 14 },
  { day: "Dim", reaction: 9 },
];

export default function AnalyticsPage() {
  return (
    <div className="p-6 space-y-6 flex flex-col h-full overflow-y-auto">
      <header>
        <h1 className="text-2xl font-bold tracking-tight">Statistiques & Analytique</h1>
        <p className="text-muted-foreground text-sm">Tendances de sécurité et performance de l&apos;IA</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Alertes Totales", value: "1,284", change: "+12%", icon: AlertTriangle, color: "text-amber-500" },
          { label: "Taux Faux Positifs", value: "4.2%", change: "-2%", icon: CheckCircle2, color: "text-emerald-500" },
          { label: "Temps Réaction Moyen", value: "12s", change: "-3s", icon: TrendingUp, color: "text-primary" },
          { label: "Individus Scannés", value: "45.2k", change: "+5%", icon: Users, color: "text-blue-500" },
        ].map((stat, i) => (
          <div key={i} className="p-4 rounded-xl border bg-card flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-muted-foreground uppercase">{stat.label}</span>
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
            </div>
            <div className="flex items-end justify-between">
              <span className="text-2xl font-bold">{stat.value}</span>
              <span className={`text-[10px] font-bold ${stat.change.startsWith('+') ? 'text-destructive' : 'text-emerald-500'}`}>
                {stat.change}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Heatmap/Trends Chart */}
        <div className="p-6 rounded-xl border bg-card space-y-4">
          <h3 className="text-sm font-semibold">Évolution du Stress & Fatigue (24h)</h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data}>
                <defs>
                  <linearGradient id="colorStress" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--destructive)" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="var(--destructive)" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.1)" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} fontSize={12} tick={{fill: '#888'}} />
                <YAxis axisLine={false} tickLine={false} fontSize={12} tick={{fill: '#888'}} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#18181b', border: '1px solid #27272a', borderRadius: '8px' }}
                  itemStyle={{ fontSize: '12px' }}
                />
                <Area type="monotone" dataKey="stress" stroke="var(--destructive)" fillOpacity={1} fill="url(#colorStress)" />
                <Area type="monotone" dataKey="fatige" stroke="#3b82f6" fillOpacity={0} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Reaction Time Chart */}
        <div className="p-6 rounded-xl border bg-card space-y-4">
          <h3 className="text-sm font-semibold">Temps de Réaction Moyen des Agents (sec)</h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.1)" />
                <XAxis dataKey="day" axisLine={false} tickLine={false} fontSize={12} tick={{fill: '#888'}} />
                <YAxis axisLine={false} tickLine={false} fontSize={12} tick={{fill: '#888'}} />
                <Tooltip
                  cursor={{fill: 'rgba(255,255,255,0.05)'}}
                  contentStyle={{ backgroundColor: '#18181b', border: '1px solid #27272a', borderRadius: '8px' }}
                />
                <Bar dataKey="reaction" fill="var(--primary)" radius={[4, 4, 0, 0]} barSize={30} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
