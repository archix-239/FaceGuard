'use client'

import { useState } from 'react'
import clsx from 'clsx'
import {
  Plus, Trash2, Edit, Shield, User, Clock, Activity,
  CheckCircle, XCircle, Lock, Unlock, X, Eye, EyeOff,
  ChevronRight, AlertTriangle
} from 'lucide-react'
import { users, auditLogs, type User as UserType, type UserRole } from '@/lib/mockData'
import { RoleBadge } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'

const PERMISSIONS = [
  { key: 'live',      label: 'Live Monitoring',    description: 'Voir le flux caméras en direct', icon: '📹' },
  { key: 'alerts',   label: 'Gestion Alertes',     description: 'Traiter les alertes IA',         icon: '🔔' },
  { key: 'logs',     label: 'Historique & Logs',   description: 'Accès aux logs et replay',       icon: '📋' },
  { key: 'analytics',label: 'Analytique',          description: 'Voir les stats et tendances',    icon: '📊' },
  { key: 'cameras',  label: 'Gestion Caméras',     description: 'Ajouter/modifier les caméras',   icon: '📷' },
  { key: 'settings', label: 'Config IA',           description: 'Modifier les paramètres IA',    icon: '⚙️' },
  { key: 'users',    label: 'Gestion Utilisateurs',description: 'RBAC et audit',                 icon: '👥' },
]

const ROLE_DEFAULTS: Record<UserRole, string[]> = {
  admin:   ['all'],
  manager: ['live', 'alerts', 'analytics', 'logs'],
  agent:   ['live', 'alerts'],
}

function hasPermission(user: UserType, key: string) {
  return user.permissions.includes('all') || user.permissions.includes(key)
}

// User card
function UserCard({ user: u, onEdit, onToggle, onDelete }: {
  user: UserType
  onEdit: (u: UserType) => void
  onToggle: (id: string) => void
  onDelete: (id: string) => void
}) {
  const lastLogin = new Date(u.lastLogin).toLocaleString('fr-FR', {
    day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'
  })

  return (
    <Card className={clsx('transition-all', u.status === 'suspended' ? 'opacity-60' : '')}>
      <div className="flex items-start gap-3">
        {/* Avatar */}
        <div className={clsx(
          'w-10 h-10 rounded-xl border flex items-center justify-center text-sm font-bold flex-shrink-0',
          u.role === 'admin' ? 'bg-accent-orange/15 border-accent-orange/30 text-accent-orange' :
          u.role === 'manager' ? 'bg-accent-blue/15 border-accent-blue/30 text-accent-blue' :
          'bg-bg-elevated border-bg-border text-text-secondary'
        )}>
          {u.avatar}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <p className="text-sm font-semibold text-text-primary truncate">{u.name}</p>
            <RoleBadge role={u.role} />
            {u.status === 'suspended' && (
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded border text-threat-high border-threat-high/30 bg-threat-high/10">SUSPENDU</span>
            )}
          </div>
          <p className="text-[11px] text-text-muted font-mono mb-2">{u.email}</p>

          {/* Permissions grid */}
          <div className="flex flex-wrap gap-1 mb-2">
            {u.permissions.includes('all') ? (
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded border text-accent-orange border-accent-orange/30 bg-accent-orange/10">
                Toutes les permissions
              </span>
            ) : (
              PERMISSIONS.map(p => (
                <span
                  key={p.key}
                  className={clsx(
                    'text-[10px] font-mono px-1.5 py-0.5 rounded border',
                    hasPermission(u, p.key)
                      ? 'text-threat-low border-threat-low/30 bg-threat-low/5'
                      : 'text-text-muted border-bg-border bg-bg-elevated opacity-50'
                  )}
                >
                  {hasPermission(u, p.key) ? '✓' : '✗'} {p.label}
                </span>
              ))
            )}
          </div>

          <div className="flex items-center gap-3 text-[11px] text-text-muted">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              Dernière connexion: <span className="text-text-secondary font-mono ml-1">{lastLogin}</span>
            </span>
            <span className="flex items-center gap-1">
              Créé le: <span className="text-text-secondary font-mono ml-1">{new Date(u.createdAt).toLocaleDateString('fr-FR')}</span>
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-1 flex-shrink-0">
          <button
            onClick={() => onToggle(u.id)}
            className={clsx(
              'p-1.5 rounded-lg border transition-all text-xs',
              u.status === 'active'
                ? 'border-bg-border text-text-muted hover:border-threat-medium/30 hover:text-threat-medium'
                : 'border-threat-low/30 text-threat-low hover:bg-threat-low/10'
            )}
            title={u.status === 'active' ? 'Suspendre' : 'Activer'}
          >
            {u.status === 'active' ? <Lock className="w-3.5 h-3.5" /> : <Unlock className="w-3.5 h-3.5" />}
          </button>
          <button onClick={() => onEdit(u)} className="p-1.5 rounded-lg border border-bg-border text-text-muted hover:border-accent-orange/30 hover:text-accent-orange transition-all">
            <Edit className="w-3.5 h-3.5" />
          </button>
          {u.role !== 'admin' && (
            <button onClick={() => onDelete(u.id)} className="p-1.5 rounded-lg border border-bg-border text-text-muted hover:border-threat-high/30 hover:text-threat-high transition-all">
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>
    </Card>
  )
}

// User modal
function UserModal({ user: u, onClose, onSave }: { user?: UserType; onClose: () => void; onSave: (data: Partial<UserType>) => void }) {
  const [form, setForm] = useState({
    name: u?.name ?? '',
    email: u?.email ?? '',
    role: (u?.role ?? 'agent') as UserRole,
    permissions: u?.permissions ?? [...ROLE_DEFAULTS.agent],
  })
  const [showPass, setShowPass] = useState(false)

  const updateRole = (role: UserRole) => {
    setForm(prev => ({ ...prev, role, permissions: [...ROLE_DEFAULTS[role]] }))
  }

  const togglePerm = (key: string) => {
    if (form.permissions.includes('all')) return
    setForm(prev => ({
      ...prev,
      permissions: prev.permissions.includes(key)
        ? prev.permissions.filter(p => p !== key)
        : [...prev.permissions, key]
    }))
  }

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-bg-card border border-bg-border rounded-2xl w-full max-w-lg p-6 animate-fade-in max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-sm font-bold text-text-primary">
            {u ? `Modifier — ${u.name}` : 'Créer un Compte'}
          </h2>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-bg-elevated text-text-muted hover:text-text-primary transition-all">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="space-y-4">
          {/* Name + email */}
          {[
            { key: 'name', label: 'Nom complet', placeholder: 'Jean Dupont' },
            { key: 'email', label: 'Email', placeholder: 'j.dupont@faceguard.io' },
          ].map(f => (
            <div key={f.key}>
              <label className="block text-[11px] text-text-muted mb-1.5">{f.label}</label>
              <input
                type="text"
                value={form[f.key as 'name' | 'email']}
                onChange={e => setForm(prev => ({ ...prev, [f.key]: e.target.value }))}
                placeholder={f.placeholder}
                className="w-full bg-bg-elevated border border-bg-border rounded-lg px-3 py-2 text-xs text-text-secondary outline-none focus:border-accent-orange/50 transition-all"
              />
            </div>
          ))}

          {/* Password (new users) */}
          {!u && (
            <div>
              <label className="block text-[11px] text-text-muted mb-1.5">Mot de passe temporaire</label>
              <div className="relative">
                <input
                  type={showPass ? 'text' : 'password'}
                  placeholder="Minimum 12 caractères"
                  className="w-full bg-bg-elevated border border-bg-border rounded-lg px-3 pr-9 py-2 text-xs text-text-secondary outline-none focus:border-accent-orange/50 transition-all"
                />
                <button onClick={() => setShowPass(!showPass)} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-text-muted">
                  {showPass ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>
          )}

          {/* Role */}
          <div>
            <label className="block text-[11px] text-text-muted mb-1.5">Rôle</label>
            <div className="grid grid-cols-3 gap-2">
              {(['admin', 'manager', 'agent'] as const).map(r => (
                <button
                  key={r}
                  onClick={() => updateRole(r)}
                  className={clsx(
                    'py-2.5 text-xs font-semibold rounded-xl border transition-all capitalize',
                    form.role === r
                      ? r === 'admin' ? 'bg-accent-orange/10 border-accent-orange/30 text-accent-orange'
                        : r === 'manager' ? 'bg-accent-blue/10 border-accent-blue/30 text-accent-blue'
                        : 'bg-bg-elevated border-accent-orange/20 text-text-primary'
                      : 'bg-bg-elevated border-bg-border text-text-muted hover:text-text-secondary'
                  )}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>

          {/* Permissions */}
          {form.role !== 'admin' && (
            <div>
              <label className="block text-[11px] text-text-muted mb-2">Permissions</label>
              <div className="space-y-1.5">
                {PERMISSIONS.map(p => (
                  <label
                    key={p.key}
                    className={clsx(
                      'flex items-center gap-3 p-2.5 rounded-lg border cursor-pointer transition-all',
                      form.permissions.includes(p.key)
                        ? 'border-accent-orange/20 bg-accent-orange/5'
                        : 'border-bg-border bg-bg-elevated hover:border-bg-elevated'
                    )}
                  >
                    <input
                      type="checkbox"
                      checked={form.permissions.includes(p.key)}
                      onChange={() => togglePerm(p.key)}
                      className="hidden"
                    />
                    <div className={clsx(
                      'w-4 h-4 rounded border flex items-center justify-center flex-shrink-0',
                      form.permissions.includes(p.key) ? 'bg-accent-orange border-accent-orange' : 'border-bg-border'
                    )}>
                      {form.permissions.includes(p.key) && <CheckCircle className="w-3 h-3 text-black" />}
                    </div>
                    <span className="text-[9px]">{p.icon}</span>
                    <div className="flex-1">
                      <p className="text-xs font-medium text-text-primary">{p.label}</p>
                      <p className="text-[10px] text-text-muted">{p.description}</p>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="flex gap-3 mt-6 pt-4 border-t border-bg-border">
          <button onClick={onClose} className="flex-1 px-4 py-2.5 text-xs font-semibold text-text-secondary border border-bg-border rounded-xl hover:border-accent-orange/20 transition-all">
            Annuler
          </button>
          <button
            onClick={() => { onSave(form); onClose() }}
            className="flex-1 px-4 py-2.5 text-xs font-semibold text-black bg-accent-orange rounded-xl hover:bg-accent-orange/90 transition-all"
          >
            {u ? 'Enregistrer' : 'Créer le compte'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function UsersPage() {
  const [userList, setUserList] = useState<UserType[]>(users)
  const [modal, setModal] = useState<{ open: boolean; user?: UserType }>({ open: false })
  const [tab, setTab] = useState<'users' | 'audit'>('users')

  const handleToggle = (id: string) => {
    setUserList(prev => prev.map(u => u.id === id
      ? { ...u, status: u.status === 'active' ? 'suspended' : 'active' }
      : u
    ))
  }

  const handleDelete = (id: string) => {
    if (confirm('Supprimer cet utilisateur ? Cette action est irréversible.')) {
      setUserList(prev => prev.filter(u => u.id !== id))
    }
  }

  const handleSave = (data: Partial<UserType>) => {
    if (modal.user) {
      setUserList(prev => prev.map(u => u.id === modal.user!.id ? { ...u, ...data } : u))
    } else {
      setUserList(prev => [...prev, {
        id: `USR-${String(prev.length + 1).padStart(2, '0')}`,
        name: data.name ?? 'Nouvel Utilisateur',
        email: data.email ?? '',
        role: (data.role ?? 'agent') as UserRole,
        avatar: (data.name ?? 'NU').split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase(),
        status: 'active',
        lastLogin: new Date().toISOString(),
        createdAt: new Date().toISOString().split('T')[0],
        permissions: data.permissions ?? [...ROLE_DEFAULTS.agent],
      }])
    }
  }

  const roleCounts = {
    admin: userList.filter(u => u.role === 'admin').length,
    manager: userList.filter(u => u.role === 'manager').length,
    agent: userList.filter(u => u.role === 'agent').length,
    active: userList.filter(u => u.status === 'active').length,
  }

  const auditLevelColor = { info: 'text-text-secondary', warning: 'text-threat-medium', critical: 'text-threat-high' }

  return (
    <div className="h-full flex flex-col gap-4">
      {/* Stats */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: 'Administrateurs', value: roleCounts.admin, color: 'text-accent-orange', bg: 'bg-accent-orange/10', border: 'border-accent-orange/20' },
          { label: 'Managers',        value: roleCounts.manager, color: 'text-accent-blue', bg: 'bg-accent-blue/10', border: 'border-accent-blue/20' },
          { label: 'Agents',          value: roleCounts.agent, color: 'text-text-primary', bg: 'bg-bg-elevated', border: 'border-bg-border' },
          { label: 'Comptes actifs',  value: roleCounts.active, color: 'text-threat-low', bg: 'bg-threat-low/10', border: 'border-threat-low/20' },
        ].map(s => (
          <div key={s.label} className={clsx('p-3 rounded-xl border', s.bg, s.border)}>
            <p className="text-text-muted text-[11px]">{s.label}</p>
            <p className={clsx('text-2xl font-bold font-mono mt-1', s.color)}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex items-center justify-between">
        <div className="flex gap-1">
          {([['users', 'Utilisateurs'], ['audit', "Journal d'Audit"]] as const).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={clsx(
                'px-4 py-2 text-xs font-semibold rounded-xl border transition-all',
                tab === key ? 'bg-accent-orange/10 border-accent-orange/30 text-accent-orange' : 'bg-bg-card border-bg-border text-text-muted hover:text-text-secondary'
              )}
            >{label}</button>
          ))}
        </div>
        {tab === 'users' && (
          <button
            onClick={() => setModal({ open: true })}
            className="flex items-center gap-2 px-4 py-2 bg-accent-orange text-black text-xs font-bold rounded-xl hover:bg-accent-orange/90 transition-all"
          >
            <Plus className="w-3.5 h-3.5" />
            Créer un compte
          </button>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {tab === 'users' ? (
          <div className="space-y-3">
            {userList.map(u => (
              <UserCard
                key={u.id}
                user={u}
                onEdit={u => setModal({ open: true, user: u })}
                onToggle={handleToggle}
                onDelete={handleDelete}
              />
            ))}
          </div>
        ) : (
          <div className="bg-bg-card border border-bg-border rounded-xl overflow-hidden">
            {/* Audit table header */}
            <div
              className="grid text-[11px] font-semibold text-text-muted uppercase tracking-wider px-4 py-2 bg-bg-elevated border-b border-bg-border"
              style={{ gridTemplateColumns: '1.5fr 2fr 2fr 1.5fr 1fr 80px' }}
            >
              <span>Heure</span>
              <span>Agent</span>
              <span>Action</span>
              <span>Cible</span>
              <span>IP</span>
              <span>Niveau</span>
            </div>
            <div className="divide-y divide-bg-border">
              {auditLogs.map(entry => (
                <div
                  key={entry.id}
                  className="grid items-center px-4 py-2.5 hover:bg-bg-elevated/50 transition-colors"
                  style={{ gridTemplateColumns: '1.5fr 2fr 2fr 1.5fr 1fr 80px' }}
                >
                  <span className="font-mono text-[11px] text-text-muted">
                    {new Date(entry.timestamp).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
                  </span>
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded bg-bg-elevated border border-bg-border flex items-center justify-center flex-shrink-0">
                      <span className="text-[9px] font-bold text-text-secondary">{entry.userName.split(' ').map(n => n[0]).join('')}</span>
                    </div>
                    <span className="text-xs text-text-primary truncate">{entry.userName}</span>
                  </div>
                  <span className={clsx('text-xs font-medium', auditLevelColor[entry.level])}>{entry.action}</span>
                  <span className="text-[11px] text-text-muted truncate">{entry.target}</span>
                  <span className="font-mono text-[11px] text-text-muted">{entry.ip}</span>
                  <span className={clsx(
                    'text-[10px] font-mono font-bold px-1.5 py-0.5 rounded border w-fit',
                    entry.level === 'critical' ? 'text-threat-high border-threat-high/30 bg-threat-high/10' :
                    entry.level === 'warning' ? 'text-threat-medium border-threat-medium/30 bg-threat-medium/10' :
                    'text-text-muted border-bg-border bg-bg-elevated'
                  )}>
                    {entry.level.toUpperCase()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {modal.open && (
        <UserModal
          user={modal.user}
          onClose={() => setModal({ open: false })}
          onSave={handleSave}
        />
      )}
    </div>
  )
}
