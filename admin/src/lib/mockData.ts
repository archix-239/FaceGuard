// ============================================================
// FACEGUARD ADMIN – Mock Data (frontend-only)
// ============================================================

export type ThreatLevel = 'low' | 'medium' | 'high' | 'critical'
export type AlertStatus = 'pending' | 'acknowledged' | 'intervention' | 'escalated'
export type CameraStatus = 'online' | 'offline' | 'degraded' | 'maintenance'
export type UserRole = 'admin' | 'manager' | 'agent'
export type EmotionType = 'colere' | 'peur' | 'degoût' | 'tristesse' | 'neutral' | 'stress' | 'fatigue'

// ---------------------------------------------------------------
// Camera Feeds
// ---------------------------------------------------------------
export interface CameraFeed {
  id: string
  name: string
  location: string
  ip: string
  rtsp: string
  status: CameraStatus
  fps: number
  resolution: string
  lastPing: string
  threatLevel: ThreatLevel
  detectionActive: boolean
  personCount: number
  uptime: number // percentage
}

export const cameras: CameraFeed[] = [
  { id: 'CAM-01', name: 'Pont-Bascule Nord', location: 'Entrée principale', ip: '192.168.1.101', rtsp: 'rtsp://192.168.1.101:554/stream1', status: 'online', fps: 25, resolution: '1920x1080', lastPing: '2s ago', threatLevel: 'low', detectionActive: true, personCount: 1, uptime: 99.8 },
  { id: 'CAM-02', name: 'Sortie Stock Est', location: 'Entrepôt A', ip: '192.168.1.102', rtsp: 'rtsp://192.168.1.102:554/stream1', status: 'online', fps: 25, resolution: '1920x1080', lastPing: '1s ago', threatLevel: 'medium', detectionActive: true, personCount: 2, uptime: 98.2 },
  { id: 'CAM-03', name: 'Porte Sud Sortie', location: 'Porte B2', ip: '192.168.1.103', rtsp: 'rtsp://192.168.1.103:554/stream1', status: 'online', fps: 30, resolution: '2560x1440', lastPing: '3s ago', threatLevel: 'high', detectionActive: true, personCount: 1, uptime: 97.4 },
  { id: 'CAM-04', name: 'Couloir Administratif', location: 'Bâtiment B', ip: '192.168.1.104', rtsp: 'rtsp://192.168.1.104:554/stream1', status: 'degraded', fps: 12, resolution: '1280x720', lastPing: '15s ago', threatLevel: 'low', detectionActive: false, personCount: 0, uptime: 72.1 },
  { id: 'CAM-05', name: 'Zone de Chargement', location: 'Dock 3', ip: '192.168.1.105', rtsp: 'rtsp://192.168.1.105:554/stream1', status: 'online', fps: 25, resolution: '1920x1080', lastPing: '2s ago', threatLevel: 'low', detectionActive: true, personCount: 3, uptime: 99.1 },
  { id: 'CAM-06', name: 'Pont-Bascule Sud', location: 'Sortie camions', ip: '192.168.1.106', rtsp: 'rtsp://192.168.1.106:554/stream1', status: 'offline', fps: 0, resolution: '1920x1080', lastPing: '4m ago', threatLevel: 'low', detectionActive: false, personCount: 0, uptime: 0 },
  { id: 'CAM-07', name: 'Parking Visiteurs', location: 'Zone P1', ip: '192.168.1.107', rtsp: 'rtsp://192.168.1.107:554/stream1', status: 'online', fps: 25, resolution: '1920x1080', lastPing: '1s ago', threatLevel: 'low', detectionActive: true, personCount: 0, uptime: 100 },
  { id: 'CAM-08', name: 'Accès Serveurs', location: 'Datacenter', ip: '192.168.1.108', rtsp: 'rtsp://192.168.1.108:554/stream1', status: 'online', fps: 30, resolution: '1920x1080', lastPing: '1s ago', threatLevel: 'low', detectionActive: true, personCount: 0, uptime: 100 },
]

// ---------------------------------------------------------------
// Alerts
// ---------------------------------------------------------------
export interface Alert {
  id: string
  cameraId: string
  cameraName: string
  timestamp: string
  threatScore: number
  threatLevel: ThreatLevel
  emotion: EmotionType
  emotionScore: number
  asymmetry: boolean
  status: AlertStatus
  agentId?: string
  agentName?: string
  note?: string
  snapshotUrl?: string
}

export const alerts: Alert[] = [
  { id: 'ALT-001', cameraId: 'CAM-03', cameraName: 'Porte Sud Sortie', timestamp: '2026-02-25T14:32:11', threatScore: 92, threatLevel: 'critical', emotion: 'colere', emotionScore: 88, asymmetry: true, status: 'pending' },
  { id: 'ALT-002', cameraId: 'CAM-02', cameraName: 'Sortie Stock Est', timestamp: '2026-02-25T14:28:47', threatScore: 81, threatLevel: 'high', emotion: 'stress', emotionScore: 81, asymmetry: false, status: 'pending' },
  { id: 'ALT-003', cameraId: 'CAM-01', cameraName: 'Pont-Bascule Nord', timestamp: '2026-02-25T14:21:03', threatScore: 76, threatLevel: 'high', emotion: 'peur', emotionScore: 76, asymmetry: true, status: 'pending' },
  { id: 'ALT-004', cameraId: 'CAM-05', cameraName: 'Zone de Chargement', timestamp: '2026-02-25T14:15:22', threatScore: 79, threatLevel: 'high', emotion: 'colere', emotionScore: 79, asymmetry: false, status: 'acknowledged', agentId: 'USR-02', agentName: 'Agent Dupont', note: 'Conducteur stressé par retard livraison - Fausse alerte' },
  { id: 'ALT-005', cameraId: 'CAM-03', cameraName: 'Porte Sud Sortie', timestamp: '2026-02-25T13:58:14', threatScore: 85, threatLevel: 'critical', emotion: 'peur', emotionScore: 85, asymmetry: true, status: 'intervention', agentId: 'USR-03', agentName: 'Agent Martin' },
  { id: 'ALT-006', cameraId: 'CAM-01', cameraName: 'Pont-Bascule Nord', timestamp: '2026-02-25T13:44:50', threatScore: 77, threatLevel: 'high', emotion: 'stress', emotionScore: 77, asymmetry: false, status: 'acknowledged', agentId: 'USR-02', agentName: 'Agent Dupont' },
  { id: 'ALT-007', cameraId: 'CAM-02', cameraName: 'Sortie Stock Est', timestamp: '2026-02-25T13:30:05', threatScore: 82, threatLevel: 'high', emotion: 'degoût', emotionScore: 82, asymmetry: true, status: 'escalated', agentId: 'USR-03', agentName: 'Agent Martin', note: 'Signalé à la direction - Comportement suspect répété' },
  { id: 'ALT-008', cameraId: 'CAM-05', cameraName: 'Zone de Chargement', timestamp: '2026-02-25T13:12:38', threatScore: 78, threatLevel: 'high', emotion: 'fatigue', emotionScore: 78, asymmetry: false, status: 'acknowledged', agentId: 'USR-02', agentName: 'Agent Dupont' },
]

// ---------------------------------------------------------------
// Live Event Ticker
// ---------------------------------------------------------------
export interface TickerEvent {
  id: string
  timestamp: string
  cameraName: string
  type: 'detection' | 'alert' | 'system' | 'acknowledged'
  message: string
  level: ThreatLevel | 'info'
}

export const tickerEvents: TickerEvent[] = [
  { id: 'EVT-001', timestamp: '14:32', cameraName: 'CAM-03', type: 'alert', message: 'Colère 88% + Asymétrie détectée', level: 'critical' },
  { id: 'EVT-002', timestamp: '14:30', cameraName: 'CAM-02', type: 'alert', message: 'Score Menace 81% – Stress', level: 'high' },
  { id: 'EVT-003', timestamp: '14:28', cameraName: 'CAM-01', type: 'detection', message: 'Personne détectée à l\'entrée', level: 'info' },
  { id: 'EVT-004', timestamp: '14:25', cameraName: 'CAM-04', type: 'system', message: 'Flux dégradé – 12 FPS', level: 'medium' },
  { id: 'EVT-005', timestamp: '14:21', cameraName: 'CAM-01', type: 'alert', message: 'Peur 76% + Asymétrie détectée', level: 'high' },
  { id: 'EVT-006', timestamp: '14:18', cameraName: 'CAM-06', type: 'system', message: 'Caméra hors ligne', level: 'high' },
  { id: 'EVT-007', timestamp: '14:15', cameraName: 'CAM-05', type: 'acknowledged', message: 'Alerte acquittée par Agent Dupont', level: 'info' },
  { id: 'EVT-008', timestamp: '14:12', cameraName: 'CAM-03', type: 'detection', message: '3 personnes en zone restreinte', level: 'medium' },
  { id: 'EVT-009', timestamp: '14:08', cameraName: 'CAM-02', type: 'alert', message: 'Dégoût 78% détecté', level: 'high' },
  { id: 'EVT-010', timestamp: '14:05', cameraName: 'CAM-01', type: 'detection', message: 'Véhicule poids lourd identifié', level: 'info' },
  { id: 'EVT-011', timestamp: '14:02', cameraName: 'CAM-07', type: 'detection', message: 'Mouvement détecté – Parking', level: 'info' },
  { id: 'EVT-012', timestamp: '13:58', cameraName: 'CAM-03', type: 'alert', message: 'Peur 85% + Asymétrie – CRITIQUE', level: 'critical' },
]

// ---------------------------------------------------------------
// Analytics Data
// ---------------------------------------------------------------
export interface HourlyData {
  hour: string
  stress: number
  colere: number
  peur: number
  fatigue: number
  neutral: number
  alertCount: number
}

export const weeklyEmotionData: HourlyData[] = [
  { hour: '00h', stress: 5, colere: 2, peur: 3, fatigue: 8, neutral: 82, alertCount: 1 },
  { hour: '02h', stress: 8, colere: 5, peur: 7, fatigue: 15, neutral: 65, alertCount: 3 },
  { hour: '04h', stress: 6, colere: 3, peur: 9, fatigue: 18, neutral: 64, alertCount: 2 },
  { hour: '06h', stress: 12, colere: 4, peur: 6, fatigue: 22, neutral: 56, alertCount: 4 },
  { hour: '08h', stress: 28, colere: 15, peur: 12, fatigue: 10, neutral: 35, alertCount: 12 },
  { hour: '10h', stress: 35, colere: 22, peur: 18, fatigue: 8, neutral: 17, alertCount: 18 },
  { hour: '12h', stress: 42, colere: 28, peur: 20, fatigue: 5, neutral: 5, alertCount: 24 },
  { hour: '14h', stress: 48, colere: 35, peur: 25, fatigue: 7, neutral: 0, alertCount: 31 },
  { hour: '16h', stress: 38, colere: 25, peur: 18, fatigue: 12, neutral: 7, alertCount: 21 },
  { hour: '18h', stress: 22, colere: 14, peur: 10, fatigue: 20, neutral: 34, alertCount: 10 },
  { hour: '20h', stress: 14, colere: 7, peur: 6, fatigue: 25, neutral: 48, alertCount: 5 },
  { hour: '22h', stress: 8, colere: 3, peur: 4, fatigue: 15, neutral: 70, alertCount: 2 },
]

export const dailyAlerts = [
  { day: 'Lun', total: 45, falsePositive: 12, real: 33 },
  { day: 'Mar', total: 52, falsePositive: 18, real: 34 },
  { day: 'Mer', total: 38, falsePositive: 8, real: 30 },
  { day: 'Jeu', total: 61, falsePositive: 22, real: 39 },
  { day: 'Ven', total: 55, falsePositive: 15, real: 40 },
  { day: 'Sam', total: 28, falsePositive: 5, real: 23 },
  { day: 'Dim', total: 15, falsePositive: 3, real: 12 },
]

export const cameraPerformance = [
  { camera: 'CAM-01', alerts: 38, falsePos: 12, avgResponse: 45 },
  { camera: 'CAM-02', alerts: 52, falsePos: 18, avgResponse: 38 },
  { camera: 'CAM-03', alerts: 71, falsePos: 8, avgResponse: 29 },
  { camera: 'CAM-05', alerts: 24, falsePos: 6, avgResponse: 52 },
]

// ---------------------------------------------------------------
// Log Entries
// ---------------------------------------------------------------
export interface LogEntry {
  id: string
  timestamp: string
  cameraId: string
  cameraName: string
  emotion: EmotionType
  emotionScore: number
  threatScore: number
  threatLevel: ThreatLevel
  asymmetry: boolean
  duration: number // seconds
  actionTaken: 'none' | 'acknowledged' | 'intervention' | 'escalated'
  agentName?: string
}

export const logs: LogEntry[] = [
  { id: 'LOG-001', timestamp: '2026-02-25T14:32:11', cameraId: 'CAM-03', cameraName: 'Porte Sud', emotion: 'colere', emotionScore: 88, threatScore: 92, threatLevel: 'critical', asymmetry: true, duration: 12, actionTaken: 'none' },
  { id: 'LOG-002', timestamp: '2026-02-25T14:28:47', cameraId: 'CAM-02', cameraName: 'Sortie Stock Est', emotion: 'stress', emotionScore: 81, threatScore: 81, threatLevel: 'high', asymmetry: false, duration: 8, actionTaken: 'none' },
  { id: 'LOG-003', timestamp: '2026-02-25T14:21:03', cameraId: 'CAM-01', cameraName: 'Pont-Bascule Nord', emotion: 'peur', emotionScore: 76, threatScore: 76, threatLevel: 'high', asymmetry: true, duration: 5, actionTaken: 'none' },
  { id: 'LOG-004', timestamp: '2026-02-25T14:15:22', cameraId: 'CAM-05', cameraName: 'Zone Chargement', emotion: 'colere', emotionScore: 79, threatScore: 79, threatLevel: 'high', asymmetry: false, duration: 15, actionTaken: 'acknowledged', agentName: 'Agent Dupont' },
  { id: 'LOG-005', timestamp: '2026-02-25T13:58:14', cameraId: 'CAM-03', cameraName: 'Porte Sud', emotion: 'peur', emotionScore: 85, threatScore: 85, threatLevel: 'critical', asymmetry: true, duration: 22, actionTaken: 'intervention', agentName: 'Agent Martin' },
  { id: 'LOG-006', timestamp: '2026-02-25T13:44:50', cameraId: 'CAM-01', cameraName: 'Pont-Bascule Nord', emotion: 'stress', emotionScore: 77, threatScore: 77, threatLevel: 'high', asymmetry: false, duration: 9, actionTaken: 'acknowledged', agentName: 'Agent Dupont' },
  { id: 'LOG-007', timestamp: '2026-02-25T13:30:05', cameraId: 'CAM-02', cameraName: 'Sortie Stock Est', emotion: 'degoût', emotionScore: 82, threatScore: 82, threatLevel: 'high', asymmetry: true, duration: 18, actionTaken: 'escalated', agentName: 'Agent Martin' },
  { id: 'LOG-008', timestamp: '2026-02-25T13:12:38', cameraId: 'CAM-05', cameraName: 'Zone Chargement', emotion: 'fatigue', emotionScore: 78, threatScore: 78, threatLevel: 'high', asymmetry: false, duration: 7, actionTaken: 'acknowledged', agentName: 'Agent Dupont' },
  { id: 'LOG-009', timestamp: '2026-02-25T12:55:21', cameraId: 'CAM-03', cameraName: 'Porte Sud', emotion: 'stress', emotionScore: 69, threatScore: 72, threatLevel: 'medium', asymmetry: false, duration: 6, actionTaken: 'acknowledged', agentName: 'Agent Leroy' },
  { id: 'LOG-010', timestamp: '2026-02-25T12:40:15', cameraId: 'CAM-01', cameraName: 'Pont-Bascule Nord', emotion: 'colere', emotionScore: 71, threatScore: 74, threatLevel: 'medium', asymmetry: false, duration: 11, actionTaken: 'acknowledged', agentName: 'Agent Dupont' },
]

// ---------------------------------------------------------------
// Users
// ---------------------------------------------------------------
export interface User {
  id: string
  name: string
  email: string
  role: UserRole
  avatar: string
  status: 'active' | 'inactive' | 'suspended'
  lastLogin: string
  createdAt: string
  permissions: string[]
}

export const users: User[] = [
  { id: 'USR-01', name: 'Jean-Pierre Moreau', email: 'jp.moreau@faceguard.io', role: 'admin', avatar: 'JM', status: 'active', lastLogin: '2026-02-25T08:12:00', createdAt: '2024-01-15', permissions: ['all'] },
  { id: 'USR-02', name: 'Sophie Dupont', email: 's.dupont@faceguard.io', role: 'manager', avatar: 'SD', status: 'active', lastLogin: '2026-02-25T07:45:00', createdAt: '2024-03-20', permissions: ['live', 'alerts', 'analytics', 'logs'] },
  { id: 'USR-03', name: 'Marc Martin', email: 'm.martin@faceguard.io', role: 'agent', avatar: 'MM', status: 'active', lastLogin: '2026-02-25T06:00:00', createdAt: '2024-06-10', permissions: ['live', 'alerts'] },
  { id: 'USR-04', name: 'Isabelle Leroy', email: 'i.leroy@faceguard.io', role: 'agent', avatar: 'IL', status: 'active', lastLogin: '2026-02-24T22:30:00', createdAt: '2024-08-05', permissions: ['live', 'alerts'] },
  { id: 'USR-05', name: 'Thomas Bernard', email: 't.bernard@faceguard.io', role: 'agent', avatar: 'TB', status: 'inactive', lastLogin: '2026-02-20T18:00:00', createdAt: '2024-09-12', permissions: ['live', 'alerts'] },
  { id: 'USR-06', name: 'Claire Petit', email: 'c.petit@faceguard.io', role: 'manager', avatar: 'CP', status: 'active', lastLogin: '2026-02-25T09:00:00', createdAt: '2024-11-01', permissions: ['live', 'alerts', 'analytics', 'logs'] },
]

// ---------------------------------------------------------------
// Audit Trail
// ---------------------------------------------------------------
export interface AuditEntry {
  id: string
  userId: string
  userName: string
  action: string
  target: string
  timestamp: string
  ip: string
  level: 'info' | 'warning' | 'critical'
}

export const auditLogs: AuditEntry[] = [
  { id: 'AUD-001', userId: 'USR-01', userName: 'J.P. Moreau', action: 'Modification seuil alerte', target: 'FaceGuard Config > Score Menace', timestamp: '2026-02-25T10:32:00', ip: '192.168.1.10', level: 'warning' },
  { id: 'AUD-002', userId: 'USR-02', userName: 'S. Dupont', action: 'Acquittement alerte ALT-004', target: 'Alert Management', timestamp: '2026-02-25T14:17:00', ip: '192.168.1.12', level: 'info' },
  { id: 'AUD-003', userId: 'USR-03', userName: 'M. Martin', action: 'Intervention requise ALT-005', target: 'Alert Management', timestamp: '2026-02-25T14:00:00', ip: '192.168.1.15', level: 'warning' },
  { id: 'AUD-004', userId: 'USR-01', userName: 'J.P. Moreau', action: 'Création compte utilisateur', target: 'USR-06 – C. Petit', timestamp: '2026-02-25T09:05:00', ip: '192.168.1.10', level: 'info' },
  { id: 'AUD-005', userId: 'USR-02', userName: 'S. Dupont', action: 'Export logs vidéo', target: 'LOG-005 – CAM-03 13:58', timestamp: '2026-02-25T08:50:00', ip: '192.168.1.12', level: 'info' },
  { id: 'AUD-006', userId: 'USR-01', userName: 'J.P. Moreau', action: 'Désactivation module CLAHE', target: 'FaceGuard Settings', timestamp: '2026-02-24T23:12:00', ip: '192.168.1.10', level: 'critical' },
  { id: 'AUD-007', userId: 'USR-03', userName: 'M. Martin', action: 'Connexion système', target: 'Dashboard Live', timestamp: '2026-02-25T06:00:00', ip: '192.168.1.15', level: 'info' },
  { id: 'AUD-008', userId: 'USR-02', userName: 'S. Dupont', action: 'Signalement direction ALT-007', target: 'Alert Management', timestamp: '2026-02-25T13:32:00', ip: '192.168.1.12', level: 'warning' },
]

// ---------------------------------------------------------------
// AI Settings
// ---------------------------------------------------------------
export interface AISettings {
  threatThreshold: number
  angerThreshold: number
  fearThreshold: number
  stressThreshold: number
  asymmetryWeight: number
  claheEnabled: boolean
  asymmetryDetection: boolean
  privacyMode: boolean
  nightVisionFilter: boolean
  arOverlay: boolean
  temporalSmoothing: boolean
  smoothingWindow: number
  replayBufferSeconds: number
  snapshotOnAlert: boolean
  alertCooldownSeconds: number
}

export const defaultAISettings: AISettings = {
  threatThreshold: 80,
  angerThreshold: 75,
  fearThreshold: 70,
  stressThreshold: 72,
  asymmetryWeight: 15,
  claheEnabled: true,
  asymmetryDetection: true,
  privacyMode: false,
  nightVisionFilter: true,
  arOverlay: true,
  temporalSmoothing: true,
  smoothingWindow: 5,
  replayBufferSeconds: 3,
  snapshotOnAlert: true,
  alertCooldownSeconds: 30,
}

// ---------------------------------------------------------------
// Global Stats
// ---------------------------------------------------------------
export const globalStats = {
  totalAlerts24h: 89,
  pendingAlerts: 3,
  falsePositiveRate: 34.8,
  avgResponseTime: 38, // seconds
  camerasOnline: 6,
  camerasTotal: 8,
  threatsNeutralized: 12,
  globalThreatLevel: 'high' as ThreatLevel,
}
