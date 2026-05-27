// ─── Bug Report Types & Helpers ─────────────────────────
// Shared between user panel and admin panel via localStorage

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
  status: 'open' | 'in-progress' | 'fixed'
  reporterName: string
  reporterEmail: string
  createdAt: string
  updatedAt: string
  replies: Reply[]
  assignedTo?: string
  assignedToName?: string
  readByUser: boolean
  readByAdmin: boolean
}

const STORAGE_KEY = 'rhythmerp-bug-reports'

export function getBugReports(): BugReport[] {
  if (typeof window === 'undefined') return []
  try {
    const data = localStorage.getItem(STORAGE_KEY)
    if (!data) return []
    const reports: BugReport[] = JSON.parse(data)
    // Migrate old records that lack new fields
    let migrated = false
    for (const r of reports) {
      if (!Array.isArray(r.replies)) { r.replies = []; migrated = true }
      if (typeof r.readByUser !== 'boolean') { r.readByUser = true; migrated = true }
      if (typeof r.readByAdmin !== 'boolean') { r.readByAdmin = true; migrated = true }
    }
    if (migrated) localStorage.setItem(STORAGE_KEY, JSON.stringify(reports))
    return reports
  } catch {
    return []
  }
}

export function addBugReport(report: Omit<BugReport, 'id' | 'status' | 'createdAt' | 'updatedAt' | 'replies' | 'readByUser' | 'readByAdmin'>): BugReport {
  const reports = getBugReports()
  const newReport: BugReport = {
    ...report,
    id: `BR-${String(reports.length + 1).padStart(3, '0')}`,
    status: 'open',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    replies: [],
    readByUser: true,
    readByAdmin: false,
  }
  reports.unshift(newReport) // newest first
  localStorage.setItem(STORAGE_KEY, JSON.stringify(reports))
  // Add notification
  addNotification({
    type: 'schedule',
    title: 'New bug report filed',
    message: `${report.reporterName} filed ${newReport.id} for ${report.testDescription}`,
    ticketId: newReport.id,
  })
  return newReport
}

export function updateBugReportStatus(id: string, status: BugReport['status']): BugReport | null {
  const reports = getBugReports()
  const idx = reports.findIndex((r) => r.id === id)
  if (idx < 0) return null
  const oldStatus = reports[idx].status
  reports[idx] = { ...reports[idx], status, updatedAt: new Date().toISOString(), readByUser: false }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(reports))
  // Add notification if status changed
  if (oldStatus !== status) {
    addNotification({
      type: 'status_change',
      title: `Status updated`,
      message: `${id} status changed to ${status}`,
      ticketId: id,
    })
  }
  return reports[idx]
}

export function getOpenBugCount(): number {
  return getBugReports().filter((r) => r.status === 'open').length
}

export function addReplyToReport(reportId: string, reply: Omit<Reply, 'id' | 'createdAt'>): BugReport | null {
  const reports = getBugReports()
  const idx = reports.findIndex((r) => r.id === reportId)
  if (idx < 0) return null
  const newReply: Reply = {
    ...reply,
    id: `reply-${Date.now()}`,
    createdAt: new Date().toISOString(),
  }
  reports[idx] = {
    ...reports[idx],
    replies: [...reports[idx].replies, newReply],
    updatedAt: new Date().toISOString(),
    readByUser: reply.authorRole === 'admin' ? false : reports[idx].readByUser,
    readByAdmin: reply.authorRole === 'user' ? false : reports[idx].readByAdmin,
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(reports))
  // Add notification
  if (reply.authorRole === 'admin') {
    addNotification({
      type: 'reply',
      title: 'Admin replied',
      message: `Admin replied to ${reportId}`,
      ticketId: reportId,
    })
  } else {
    addNotification({
      type: 'reply',
      title: 'User followed up',
      message: `User replied to ${reportId}`,
      ticketId: reportId,
    })
  }
  return reports[idx]
}

export function markReportReadByUser(reportId: string): void {
  const reports = getBugReports()
  const idx = reports.findIndex((r) => r.id === reportId)
  if (idx < 0) return
  reports[idx] = { ...reports[idx], readByUser: true }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(reports))
}

export function markReportReadByAdmin(reportId: string): void {
  const reports = getBugReports()
  const idx = reports.findIndex((r) => r.id === reportId)
  if (idx < 0) return
  reports[idx] = { ...reports[idx], readByAdmin: true }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(reports))
}

export function assignReport(reportId: string, assignedTo: string, assignedToName: string): BugReport | null {
  const reports = getBugReports()
  const idx = reports.findIndex((r) => r.id === reportId)
  if (idx < 0) return null
  reports[idx] = { ...reports[idx], assignedTo, assignedToName, updatedAt: new Date().toISOString() }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(reports))
  return reports[idx]
}

// ─── Notification Types & Helpers ──────────────────────────
export interface Notification {
  id: string
  type: 'status_change' | 'reply' | 'schedule' | 'run_complete'
  title: string
  message: string
  ticketId?: string
  createdAt: string
  read: boolean
}

const NOTIF_STORAGE_KEY = 'rhythmerp-notifications'

export function getNotifications(): Notification[] {
  if (typeof window === 'undefined') return []
  try {
    const data = localStorage.getItem(NOTIF_STORAGE_KEY)
    return data ? JSON.parse(data) : []
  } catch {
    return []
  }
}

export function addNotification(notification: Omit<Notification, 'id' | 'createdAt' | 'read'>): Notification {
  const notifications = getNotifications()
  const newNotif: Notification = {
    ...notification,
    id: `notif-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
    createdAt: new Date().toISOString(),
    read: false,
  }
  notifications.unshift(newNotif)
  // Keep only last 50
  if (notifications.length > 50) notifications.length = 50
  localStorage.setItem(NOTIF_STORAGE_KEY, JSON.stringify(notifications))
  return newNotif
}

export function markNotificationRead(id: string): void {
  const notifications = getNotifications()
  const idx = notifications.findIndex((n) => n.id === id)
  if (idx < 0) return
  notifications[idx] = { ...notifications[idx], read: true }
  localStorage.setItem(NOTIF_STORAGE_KEY, JSON.stringify(notifications))
}

export function markAllNotificationsRead(): void {
  const notifications = getNotifications()
  localStorage.setItem(NOTIF_STORAGE_KEY, JSON.stringify(notifications.map((n) => ({ ...n, read: true }))))
}

export function getUnreadNotificationCount(): number {
  return getNotifications().filter((n) => !n.read).length
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
  lastRunAt?: string
}

const SCHED_STORAGE_KEY = 'rhythmerp-scheduled-runs'

export function getScheduledRuns(): ScheduledRun[] {
  if (typeof window === 'undefined') return []
  try {
    const data = localStorage.getItem(SCHED_STORAGE_KEY)
    return data ? JSON.parse(data) : []
  } catch {
    return []
  }
}

export function addScheduledRun(run: Omit<ScheduledRun, 'id' | 'createdAt'>): ScheduledRun {
  const runs = getScheduledRuns()
  const newRun: ScheduledRun = {
    ...run,
    id: `sched-${Date.now()}`,
    createdAt: new Date().toISOString(),
  }
  runs.push(newRun)
  localStorage.setItem(SCHED_STORAGE_KEY, JSON.stringify(runs))
  // Add notification
  addNotification({
    type: 'schedule',
    title: 'New schedule created',
    message: `Schedule created for ${run.moduleName} (${run.frequency})`,
  })
  return newRun
}

export function updateScheduledRun(id: string, updates: Partial<ScheduledRun>): ScheduledRun | null {
  const runs = getScheduledRuns()
  const idx = runs.findIndex((r) => r.id === id)
  if (idx < 0) return null
  runs[idx] = { ...runs[idx], ...updates }
  localStorage.setItem(SCHED_STORAGE_KEY, JSON.stringify(runs))
  return runs[idx]
}

export function deleteScheduledRun(id: string): void {
  const runs = getScheduledRuns()
  localStorage.setItem(SCHED_STORAGE_KEY, JSON.stringify(runs.filter((r) => r.id !== id)))
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
  if (status === 'fixed') return { label: 'Resolved', color: 'text-green-700 bg-green-100 dark:text-green-300 dark:bg-green-900/40', remaining: '—', overdue: false }

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
  const elapsedMs = now.getTime() - new Date(createdAt).getTime()
  const pctRemaining = (diffMs / totalMs) * 100

  const hours = Math.floor(diffMs / (1000 * 60 * 60))
  const mins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60))
  const remaining = hours > 0 ? `${hours}h ${mins}m remaining` : `${mins}m remaining`

  if (pctRemaining < 50) {
    return { label: 'At Risk', color: 'text-orange-700 bg-orange-100 dark:text-orange-300 dark:bg-orange-900/40', remaining, overdue: false }
  }
  return { label: 'On Track', color: 'text-green-700 bg-green-100 dark:text-green-300 dark:bg-green-900/40', remaining, overdue: false }
}
