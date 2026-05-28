// ─── Bug Report Types & Helpers ─────────────────────────
// All data now lives in SQLite via API routes (not localStorage)

export interface Reply {
  id: string
  authorName: string
  authorRole: 'user' | 'admin'
  message: string
  createdAt: string
}

export interface BugReport {
  id: string
  testId: string
  testDescription: string
  moduleName: string
  error: string
  userNote: string
  priority: 'low' | 'medium' | 'high'
  status: 'open' | 'in-progress' | 'fixed' | 'closed' | 'rejected'
  reporterName: string
  reporterEmail: string
  createdAt: string
  updatedAt: string
  replies: Reply[]
  assignedTo?: string | null
  assignedToName?: string | null
  readByUser: boolean
  readByAdmin: boolean
}

// ─── Bug Report API Calls ──────────────────────────────

export async function getBugReports(): Promise<BugReport[]> {
  try {
    const res = await fetch('/api/bugs')
    if (!res.ok) return []
    const data = await res.json()
    return data.map((r: Record<string, unknown>) => ({
      ...r,
      assignedTo: r.assignedTo || undefined,
      assignedToName: r.assignedToName || undefined,
      replies: Array.isArray(r.replies) ? r.replies : [],
    }))
  } catch {
    return []
  }
}

export async function addBugReport(report: Omit<BugReport, 'id' | 'status' | 'createdAt' | 'updatedAt' | 'replies' | 'readByUser' | 'readByAdmin'>): Promise<BugReport> {
  const res = await fetch('/api/bugs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(report),
  })
  if (!res.ok) throw new Error('Failed to create bug report')
  return res.json()
}

export async function updateBugReportStatus(id: string, status: BugReport['status']): Promise<BugReport | null> {
  try {
    const res = await fetch(`/api/bugs/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    })
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}

export async function getOpenBugCount(): Promise<number> {
  const reports = await getBugReports()
  return reports.filter((r) => r.status === 'open').length
}

export async function addReplyToReport(reportId: string, reply: Omit<Reply, 'id' | 'createdAt'>): Promise<BugReport | null> {
  try {
    const res = await fetch(`/api/bugs/${reportId}/replies`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(reply),
    })
    if (!res.ok) return null
    // Re-fetch the full bug report to get updated replies + read flags
    const reportRes = await fetch(`/api/bugs`)
    if (!reportRes.ok) return null
    const allReports = await reportRes.json()
    return allReports.find((r: BugReport) => r.id === reportId) || null
  } catch {
    return null
  }
}

export async function markReportReadByUser(reportId: string): Promise<void> {
  try {
    await fetch(`/api/bugs/${reportId}/read`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role: 'user' }),
    })
  } catch {
    // silent fail
  }
}

export async function markReportReadByAdmin(reportId: string): Promise<void> {
  try {
    await fetch(`/api/bugs/${reportId}/read`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role: 'admin' }),
    })
  } catch {
    // silent fail
  }
}

export async function assignReport(reportId: string, assignedTo: string, assignedToName: string): Promise<BugReport | null> {
  try {
    const res = await fetch(`/api/bugs/${reportId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ assignedTo, assignedToName }),
    })
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}

// ─── Notification Types & Helpers ──────────────────────────
export interface Notification {
  id: string
  type: 'status_change' | 'reply' | 'schedule' | 'run_complete'
  title: string
  message: string
  ticketId?: string | null
  createdAt: string
  read: boolean
}

export async function getNotifications(): Promise<Notification[]> {
  try {
    const res = await fetch('/api/notifications')
    if (!res.ok) return []
    return res.json()
  } catch {
    return []
  }
}

export async function addNotification(notification: Omit<Notification, 'id' | 'createdAt' | 'read'>): Promise<Notification> {
  const res = await fetch('/api/notifications', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(notification),
  })
  if (!res.ok) throw new Error('Failed to create notification')
  return res.json()
}

export async function markNotificationRead(id: string): Promise<void> {
  try {
    await fetch(`/api/notifications/${id}`, { method: 'PATCH' })
  } catch {
    // silent fail
  }
}

export async function markAllNotificationsRead(): Promise<void> {
  try {
    await fetch('/api/notifications/read-all', { method: 'PATCH' })
  } catch {
    // silent fail
  }
}

export async function getUnreadNotificationCount(): Promise<number> {
  try {
    const res = await fetch('/api/notifications/unread-count')
    if (!res.ok) return 0
    const data = await res.json()
    return data.count || 0
  } catch {
    return 0
  }
}

// ─── Scheduled Run Types & Helpers ──────────────────────────
export interface ScheduledRun {
  id: string
  moduleId: string
  moduleName: string
  frequency: 'one-time' | 'daily' | 'weekly'
  scheduledTime: string // ISO date string
  testSelection: 'all' | 'priority' | 'selected'
  selectedTestIds?: string[]
  enabled: boolean
  createdBy: string
  createdAt: string
  lastRunAt?: string | null
}

export async function getScheduledRuns(): Promise<ScheduledRun[]> {
  try {
    const res = await fetch('/api/schedules')
    if (!res.ok) return []
    return res.json()
  } catch {
    return []
  }
}

export async function addScheduledRun(run: Omit<ScheduledRun, 'id' | 'createdAt'>): Promise<ScheduledRun> {
  const res = await fetch('/api/schedules', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(run),
  })
  if (!res.ok) throw new Error('Failed to create scheduled run')
  return res.json()
}

export async function updateScheduledRun(id: string, updates: Partial<ScheduledRun>): Promise<ScheduledRun | null> {
  try {
    const res = await fetch(`/api/schedules/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    })
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}

export async function deleteScheduledRun(id: string): Promise<void> {
  try {
    await fetch(`/api/schedules/${id}`, { method: 'DELETE' })
  } catch {
    // silent fail
  }
}

// ─── SLA Helper ──────────────────────────────────────────
export function getSLADeadline(priority: BugReport['priority'], createdAt: string): Date {
  const created = new Date(createdAt)
  switch (priority) {
    case 'high': return new Date(created.getTime() + 24 * 60 * 60 * 1000)
    case 'medium': return new Date(created.getTime() + 48 * 60 * 60 * 1000)
    case 'low': return new Date(created.getTime() + 7 * 24 * 60 * 60 * 1000)
  }
}

export function getSLAStatus(priority: BugReport['priority'], createdAt: string, status: BugReport['status']): { label: string; color: string; remaining: string; overdue: boolean } {
  if (status === 'fixed' || status === 'closed') return { label: 'Resolved', color: 'text-green-700 bg-green-100 dark:text-green-300 dark:bg-green-900/40', remaining: '—', overdue: false }
  if (status === 'rejected') return { label: 'Rejected', color: 'text-gray-700 bg-gray-100 dark:text-gray-400 dark:bg-gray-700/40', remaining: '—', overdue: false }

  const deadline = getSLADeadline(priority, createdAt)
  const now = new Date()
  const diffMs = deadline.getTime() - now.getTime()
  const overdue = diffMs < 0

  if (overdue) {
    const overdueMs = Math.abs(diffMs)
    const overdueHours = Math.floor(overdueMs / (1000 * 60 * 60))
    const overdueMins = Math.floor((overdueMs % (1000 * 60 * 60)) / (1000 * 60))
    const remaining = overdueHours > 0 ? `${overdueHours}h ${overdueMins}m overdue` : `${overdueMins}m overdue`
    return { label: 'Overdue', color: 'text-red-700 bg-red-100 dark:text-red-300 dark:bg-red-900/40', remaining, overdue: true }
  }

  // Check percentage remaining
  const totalMs = deadline.getTime() - new Date(createdAt).getTime()
  const pctRemaining = (diffMs / totalMs) * 100

  const hours = Math.floor(diffMs / (1000 * 60 * 60))
  const mins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60))
  const remaining = hours > 0 ? `${hours}h ${mins}m remaining` : `${mins}m remaining`

  if (pctRemaining < 50) {
    return { label: 'At Risk', color: 'text-orange-700 bg-orange-100 dark:text-orange-300 dark:bg-orange-900/40', remaining, overdue: false }
  }
  return { label: 'On Track', color: 'text-green-700 bg-green-100 dark:text-green-300 dark:bg-green-900/40', remaining, overdue: false }
}
