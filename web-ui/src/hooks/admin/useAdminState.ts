'use client'

import React, { useState, useEffect, useCallback, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { fetchTestCases } from '@/lib/api'
import { withCsrf } from '@/lib/csrf-client'
import {
  getBugReports, updateBugReportStatus, addReplyToReport,
  markReportReadByAdmin, type BugReport,
} from '@/lib/bug-reports'
import { toast } from 'sonner'

// ─── Types ───────────────────────────────────────────────
export interface AuthUser { id: string; email: string; name: string; role: string }
export interface AdminTest {
  id: string; description: string; className: string
  status: 'active' | 'draft' | 'disabled'; priority: 'smoke' | 'regression' | 'sanity'
  steps: string; expected: string; moduleId: string; moduleName: string
  error?: string; lastResult?: 'passed' | 'failed' | 'not-run'; lastRun?: string
}
export interface AdminModule {
  id: string; name: string; label: string; parentId?: string; parentLabel?: string
  badge?: string; testCount: number; sortOrder: number; status: 'active' | 'draft' | 'disabled'
  description?: string
}
export interface Environment {
  id: string; name: string; baseUrl: string; browser: string
  status: 'active' | 'inactive'; lastUsed?: string; color: string
}
export interface AdminUser {
  id: string; email: string; name: string
  role: 'admin' | 'tester' | 'viewer' | 'client'
  status: 'active' | 'inactive'; lastLogin?: string; moduleAccess: string[]
}
export interface AuditEntry {
  id: string; userId: string; userName: string; action: string
  targetType: string; targetId: string; targetLabel: string
  details: string; createdAt: string
}

// ─── Delete Target ──────────────────────────────────────
export interface DeleteTarget {
  type: string; id: string; label: string
}

// ─── Hook Return ─────────────────────────────────────────
export interface AdminState {
  user: AuthUser | null
  authLoading: boolean
  sidebarOpen: boolean
  setSidebarOpen: (v: boolean) => void
  activeSection: string
  setActiveSection: (v: string) => void
  tests: AdminTest[]
  testsLoaded: boolean
  modules: AdminModule[]
  modulesLoaded: boolean
  loadModules: () => Promise<void>
  environments: Environment[]
  envLoaded: boolean
  users: AdminUser[]
  usersLoaded: boolean
  bugReports: BugReport[]
  setBugReports: (v: BugReport[]) => void
  bugsLoaded: boolean
  auditLog: AuditEntry[]
  auditLoaded: boolean
  // Dialogs
  envDialogOpen: boolean
  setEnvDialogOpen: (v: boolean) => void
  editingEnv: Environment | null
  setEditingEnv: (v: Environment | null) => void
  userDialogOpen: boolean
  setUserDialogOpen: (v: boolean) => void
  editingUser: AdminUser | null
  setEditingUser: (v: AdminUser | null) => void
  deleteDialogOpen: boolean
  setDeleteDialogOpen: (v: boolean) => void
  deleteTarget: DeleteTarget | null
  setDeleteTarget: (v: DeleteTarget | null) => void
  moduleDialogOpen: boolean
  setModuleDialogOpen: (v: boolean) => void
  editingModule: AdminModule | null
  setEditingModule: (v: AdminModule | null) => void
  resetPasswordDialogOpen: boolean
  setResetPasswordDialogOpen: (v: boolean) => void
  resetPasswordUser: AdminUser | null
  setResetPasswordUser: (v: AdminUser | null) => void
  // Bug filters
  bugSubTab: 'reports' | 'chats'
  setBugSubTab: (v: 'reports' | 'chats') => void
  bugStatusFilter: string
  setBugStatusFilter: (v: string) => void
  bugSearch: string
  setBugSearch: (v: string) => void
  bugModuleFilter: string
  setBugModuleFilter: (v: string) => void
  bugPriorityFilter: string
  setBugPriorityFilter: (v: string) => void
  expandedBug: string | null
  setExpandedBug: (v: string | null) => void
  bugReplyText: Record<string, string>
  setBugReplyText: React.Dispatch<React.SetStateAction<Record<string, string>>>
  pendingBugStatus: Record<string, string>
  setPendingBugStatus: React.Dispatch<React.SetStateAction<Record<string, string>>>
  adminUnreadChats: number
  // Bulk actions
  selectedUserIds: Set<string>
  setSelectedUserIds: (v: Set<string>) => void
  bulkActionConfirmOpen: boolean
  setBulkActionConfirmOpen: (v: boolean) => void
  bulkActionType: string
  setBulkActionType: (v: string) => void
  // Widgets
  hiddenWidgets: Set<string>
  widgetDialogOpen: boolean
  setWidgetDialogOpen: (v: boolean) => void
  toggleWidgetVisibility: (widgetId: string) => void
  // Computed
  stats: {
    activeTests: number; totalModules: number; activeEnvs: number
    activeUsers: number; passRate: number; failedTests: AdminTest[]; totalTests: number
  }
  // Handlers
  handleLogout: () => Promise<void>
  handleSaveEnv: (data: Partial<Environment>) => Promise<void>
  handleToggleEnv: (env: Environment) => Promise<void>
  handleSaveUser: (data: Partial<AdminUser> & { password?: string }) => Promise<void>
  handleResetPassword: (userId: string, password: string) => Promise<void>
  handleDelete: () => Promise<void>
  handleBugStatusChange: (id: string, status: BugReport['status']) => Promise<void>
  handleBugReply: (reportId: string) => Promise<void>
  handleMarkBugRead: (id: string) => Promise<void>
  handleSaveModule: (data: Partial<AdminModule> & { name: string; label: string }) => Promise<void>
  handleDeleteModule: (moduleId: string) => Promise<void>
  handleSeedModules: () => Promise<void>
  handleToggleModuleStatus: (mod: AdminModule) => Promise<void>
  handleBulkAction: () => Promise<void>
  toggleUserSelection: (id: string) => void
  toggleAllUsers: () => void
}

export function useAdminState(): AdminState {
  const router = useRouter()

  const [user, setUser] = useState<AuthUser | null>(null)
  const [authLoading, setAuthLoading] = useState(true)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [activeSection, setActiveSection] = useState('overview')

  // Data state
  const [tests, setTests] = useState<AdminTest[]>([])
  const [modules, setModules] = useState<AdminModule[]>([])
  const [environments, setEnvironments] = useState<Environment[]>([])
  const [users, setUsers] = useState<AdminUser[]>([])
  const [bugReports, setBugReports] = useState<BugReport[]>([])
  const [auditLog, setAuditLog] = useState<AuditEntry[]>([])

  // Loading flags
  const [testsLoaded, setTestsLoaded] = useState(false)
  const [modulesLoaded, setModulesLoaded] = useState(false)
  const [usersLoaded, setUsersLoaded] = useState(false)
  const [envLoaded, setEnvLoaded] = useState(false)
  const [bugsLoaded, setBugsLoaded] = useState(false)
  const [auditLoaded, setAuditLoaded] = useState(false)

  // Bug filters
  const [bugSubTab, setBugSubTab] = useState<'reports' | 'chats'>('reports')
  const [bugStatusFilter, setBugStatusFilter] = useState('all')
  const [bugSearch, setBugSearch] = useState('')
  const [bugModuleFilter, setBugModuleFilter] = useState('all')
  const [bugPriorityFilter, setBugPriorityFilter] = useState('all')
  const [expandedBug, setExpandedBug] = useState<string | null>(null)
  const [bugReplyText, setBugReplyText] = useState<Record<string, string>>({})
  const [pendingBugStatus, setPendingBugStatus] = useState<Record<string, string>>({})

  const adminUnreadChats = useMemo(() =>
    bugReports.filter(r => !r.readByAdmin && (r.replies.length > 0 || r.status === 'open' || r.status === 'in-progress')).length,
  [bugReports])

  // Dialogs
  const [envDialogOpen, setEnvDialogOpen] = useState(false)
  const [editingEnv, setEditingEnv] = useState<Environment | null>(null)
  const [userDialogOpen, setUserDialogOpen] = useState(false)
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<DeleteTarget | null>(null)
  const [moduleDialogOpen, setModuleDialogOpen] = useState(false)
  const [editingModule, setEditingModule] = useState<AdminModule | null>(null)

  // Reset password dialog
  const [resetPasswordDialogOpen, setResetPasswordDialogOpen] = useState(false)
  const [resetPasswordUser, setResetPasswordUser] = useState<AdminUser | null>(null)

  // Bulk user actions
  const [selectedUserIds, setSelectedUserIds] = useState<Set<string>>(new Set())
  const [bulkActionConfirmOpen, setBulkActionConfirmOpen] = useState(false)
  const [bulkActionType, setBulkActionType] = useState<string>('')

  // Dashboard widget customization
  const [hiddenWidgets, setHiddenWidgets] = useState<Set<string>>(() => {
    if (typeof window === 'undefined') return new Set()
    try {
      const saved = localStorage.getItem('admin-overview-widgets')
      if (saved) { const arr: string[] = JSON.parse(saved); const allDefaults = ['stat-cards', 'pass-rate', 'environments', 'recent-failures', 'recent-activity']; return new Set(allDefaults.filter(w => !arr.includes(w))) }
    } catch { /* empty */ }
    return new Set()
  })
  const [widgetDialogOpen, setWidgetDialogOpen] = useState(false)

  // ─── Auth check ──────────────────────────────────────
  useEffect(() => {
    (async () => {
      try {
        const res = await fetch('/api/auth/me')
        if (!res.ok) { router.push('/'); return }
        const data = await res.json()
        if (data.user.role !== 'admin') {
          router.push('/'); return
        }
        setUser(data.user)
      } catch { router.push('/') } finally { setAuthLoading(false) }
    })()
  }, [router])

  // ─── Data loading effects ─────────────────────────────
  // Tests
  useEffect(() => {
    (async () => {
      try {
        const data = await fetchTestCases()
        const mapped: AdminTest[] = []
        for (const [, mod] of Object.entries(data)) {
          for (const t of mod.tests) {
            mapped.push({
              id: t.id, description: t.description || t.screenName, className: t.screenName,
              status: (t.status === 'Passed' || t.status === 'Failed') ? 'active' : 'draft',
              priority: 'regression', steps: t.steps || '', expected: t.expected || '',
              moduleId: mod.label.toLowerCase().replace(/\s+/g, '-'), moduleName: mod.label,
              lastResult: t.status === 'Passed' ? 'passed' : t.status === 'Failed' ? 'failed' : 'not-run',
              lastRun: t.date || '—', error: t.actual && t.actual !== t.expected ? t.actual : undefined,
            })
          }
        }
        setTests(mapped)
      } catch { /* empty on failure */ } finally { setTestsLoaded(true) }
    })()
  }, [])

  // Modules — load from native Prisma API
  const loadModules = useCallback(async () => {
    setModulesLoaded(false)
    try {
      const res = await fetch('/api/admin/modules')
      if (res.ok) {
        const data = await res.json()
        const arr = data.modules || []
        setModules(arr.map((m: Record<string, unknown>) => ({
          id: String(m.id || ''),
          name: String(m.name || ''),
          label: String(m.label || ''),
          parentId: m.parentId ? String(m.parentId) : undefined,
          parentLabel: m.parentLabel ? String(m.parentLabel) : undefined,
          testCount: Number(m.testCount || 0),
          sortOrder: Number(m.sortOrder || 0),
          status: String(m.status || 'active') as AdminModule['status'],
          description: m.description ? String(m.description) : undefined,
        })))
      }
    } catch { /* empty */ } finally { setModulesLoaded(true) }
  }, [])

  // Initial load
  useEffect(() => {
    (async () => { await loadModules() })()
  }, [])

  // Refresh modules when switching to modules section
  useEffect(() => {
    if (activeSection === 'modules') {
      (async () => { await loadModules() })()
    }
  }, [activeSection, loadModules])

  // Users
  useEffect(() => {
    (async () => {
      try {
        const res = await fetch('/api/admin/users')
        if (res.ok) {
          const data = await res.json()
          const arr = data.users || []
          setUsers(arr.map((u: Record<string, unknown>) => ({
            id: String(u.id || ''), email: String(u.email || ''), name: String(u.name || ''),
            role: String(u.role || 'tester') as AdminUser['role'],
            status: String(u.status || 'active') as AdminUser['status'],
            lastLogin: u.lastLogin ? String(u.lastLogin) : undefined,
            moduleAccess: Array.isArray(u.moduleAccess) ? u.moduleAccess.map(String) : ['all'],
          })))
        }
      } catch { /* empty */ } finally { setUsersLoaded(true) }
    })()
  }, [])

  // Environments
  useEffect(() => {
    (async () => {
      try {
        const res = await fetch('/api/admin/environments')
        if (res.ok) {
          const data = await res.json()
          setEnvironments(data.environments || [])
        }
      } catch { /* empty */ } finally { setEnvLoaded(true) }
    })()
  }, [])

  // Bug reports
  useEffect(() => {
    (async () => {
      try { setBugReports(await getBugReports()) } catch { /* empty */ }
      finally { setBugsLoaded(true) }
    })()
  }, [])

  // Refresh bugs when switching to bug tab
  useEffect(() => {
    if (activeSection === 'bug-reports') {
      getBugReports().then(setBugReports).catch(() => {})
    }
  }, [activeSection])

  // Audit log — load on initial page load (for overview) and refresh when visiting audit-log section
  const loadAuditLog = useCallback(async () => {
    setAuditLoaded(false)
    try {
      const res = await fetch('/api/admin/audit-log')
      if (res.ok) {
        const data = await res.json()
        setAuditLog(data.entries || [])
      }
    } catch { /* empty */ } finally { setAuditLoaded(true) }
  }, [])

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { loadAuditLog() }, [loadAuditLog])

  // Refresh when switching to audit-log section
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (activeSection === 'audit-log') { loadAuditLog() }
  }, [activeSection, loadAuditLog])

  // Widget toggle helper
  const toggleWidgetVisibility = useCallback((widgetId: string) => {
    setHiddenWidgets(prev => {
      const next = new Set(prev)
      if (next.has(widgetId)) next.delete(widgetId)
      else next.add(widgetId)
      const visible = ['stat-cards', 'pass-rate', 'environments', 'recent-failures', 'recent-activity'].filter(w => !next.has(w))
      localStorage.setItem('admin-overview-widgets', JSON.stringify(visible))
      return next
    })
  }, [])

  // ─── Handlers ──────────────────────────────────────────
  const handleLogout = useCallback(async () => {
    await fetch('/api/auth/logout', withCsrf({ method: 'POST' }))
    router.push('/')
  }, [router])

  // Stats
  const stats = useMemo(() => {
    const activeTests = tests.filter(t => t.status === 'active').length
    const totalModules = modules.filter(m => !m.parentId).length
    const activeEnvs = environments.filter(e => e.status === 'active').length
    const activeUsers = users.filter(u => u.status === 'active').length
    const ran = tests.filter(t => t.lastResult !== 'not-run')
    const passRate = ran.length ? Math.round((tests.filter(t => t.lastResult === 'passed').length / ran.length) * 100) : 0
    const failedTests = tests.filter(t => t.lastResult === 'failed')
    return { activeTests, totalModules, activeEnvs, activeUsers, passRate, failedTests, totalTests: tests.length }
  }, [tests, modules, environments, users])

  // Environment CRUD
  const handleSaveEnv = useCallback(async (envData: Partial<Environment>) => {
    try {
      if (editingEnv) {
        const res = await fetch(`/api/admin/environments/${editingEnv.id}`, withCsrf({
          method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(envData),
        }))
        if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || 'Failed to update') }
        const updated = await res.json()
        setEnvironments(prev => prev.map(e => e.id === editingEnv.id ? { ...e, ...updated } : e))
        toast.success('Environment updated')
      } else {
        const res = await fetch('/api/admin/environments', withCsrf({
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ...envData, status: 'active', color: envData.color || 'bg-green-500' }),
        }))
        if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || 'Failed to create') }
        const created = await res.json()
        setEnvironments(prev => [...prev, { ...envData, id: created.id, name: created.name, baseUrl: created.baseUrl, browser: created.browser, status: created.status, color: created.color, lastUsed: created.lastUsed } as Environment])
        toast.success('Environment created')
      }
    } catch (err) { toast.error(err instanceof Error ? err.message : 'Operation failed') }
    finally { setEnvDialogOpen(false); setEditingEnv(null) }
  }, [editingEnv])

  const handleToggleEnv = useCallback(async (env: Environment) => {
    const newStatus = env.status === 'active' ? 'inactive' : 'active'
    try {
      const res = await fetch(`/api/admin/environments/${env.id}`, withCsrf({
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      }))
      if (!res.ok) throw new Error('Failed to toggle')
      setEnvironments(prev => prev.map(e => e.id === env.id ? { ...e, status: newStatus } : e))
      toast.success(`Environment ${newStatus}`)
    } catch (err) { toast.error(err instanceof Error ? err.message : 'Failed') }
  }, [])

  // User CRUD
  const handleSaveUser = useCallback(async (userData: Partial<AdminUser> & { password?: string }) => {
    try {
      if (editingUser) {
        const res = await fetch(`/api/admin/users/${editingUser.id}`, withCsrf({
          method: 'PUT', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: userData.name, email: userData.email, role: userData.role, status: userData.status, module_access: userData.moduleAccess }),
        }))
        if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || 'Failed') }
        const updated = await res.json()
        setUsers(prev => prev.map(u => u.id === editingUser.id ? { ...u, name: updated.name, email: updated.email, role: updated.role, status: updated.status, moduleAccess: updated.moduleAccess } : u))
        toast.success('User updated')
      } else {
        const res = await fetch('/api/admin/users', withCsrf({
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: userData.name, email: userData.email, password: userData.password || 'changeme', role: userData.role, module_access: userData.moduleAccess || [] }),
        }))
        if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || 'Failed') }
        const created = await res.json()
        setUsers(prev => [...prev, { id: created.id, email: created.email, name: created.name, role: created.role, status: created.status || 'active', moduleAccess: created.moduleAccess || userData.moduleAccess || [] } as AdminUser])
        toast.success('User created')
      }
    } catch (err) { toast.error(err instanceof Error ? err.message : 'Failed') }
    finally { setUserDialogOpen(false); setEditingUser(null) }
  }, [editingUser])

  const handleResetPassword = useCallback(async (userId: string, password: string) => {
    try {
      const res = await fetch(`/api/admin/users/${userId}/reset-password`, withCsrf({ method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ password }) }))
      if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || 'Failed to reset password') }
      toast.success(`Password reset to: ${password}`)
      setResetPasswordDialogOpen(false)
      setResetPasswordUser(null)
    } catch (err) { toast.error(err instanceof Error ? err.message : 'Failed') }
  }, [])

  const handleDelete = useCallback(async () => {
    if (!deleteTarget) return
    try {
      if (deleteTarget.type === 'user') {
        const res = await fetch(`/api/admin/users/${deleteTarget.id}`, withCsrf({ method: 'DELETE' }))
        if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || 'Failed to delete') }
        setUsers(prev => prev.filter(u => u.id !== deleteTarget.id))
        toast.success('User deleted')
      } else if (deleteTarget.type === 'environment') {
        const res = await fetch(`/api/admin/environments/${deleteTarget.id}`, withCsrf({ method: 'DELETE' }))
        if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || 'Failed to delete') }
        setEnvironments(prev => prev.filter(e => e.id !== deleteTarget.id))
        toast.success('Environment deleted')
      } else if (deleteTarget.type === 'module') {
        const res = await fetch(`/api/admin/modules/${deleteTarget.id}`, withCsrf({ method: 'DELETE' }))
        if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || 'Failed to delete') }
        setModules(prev => prev.filter(m => m.id !== deleteTarget.id))
        toast.success('Module deleted')
      }
    } catch (err) { toast.error(err instanceof Error ? err.message : 'Failed') }
    finally { setDeleteDialogOpen(false); setDeleteTarget(null) }
  }, [deleteTarget])

  const handleBugStatusChange = useCallback(async (id: string, status: BugReport['status']) => {
    const result = await updateBugReportStatus(id, status)
    if (result) { setBugReports(prev => prev.map(b => b.id === id ? result : b)); toast.success(`Status changed to ${status}`) }
    else toast.error('Failed to update status')
  }, [])

  const handleBugReply = useCallback(async (reportId: string) => {
    const message = bugReplyText[reportId]?.trim()
    if (!message || !user) return
    const result = await addReplyToReport(reportId, { authorName: user.name, authorRole: 'admin', message })
    if (result) {
      setBugReports(prev => prev.map(b => b.id === reportId ? result : b))
      setBugReplyText(prev => ({ ...prev, [reportId]: '' }))
      toast.success('Reply added')
    } else toast.error('Failed to add reply')
  }, [bugReplyText, user])

  const handleMarkBugRead = useCallback(async (id: string) => {
    await markReportReadByAdmin(id)
    setBugReports(prev => prev.map(b => b.id === id ? { ...b, readByAdmin: true } : b))
  }, [])

  // Module CRUD
  const handleSaveModule = useCallback(async (moduleData: Partial<AdminModule> & { name: string; label: string }) => {
    try {
      if (editingModule) {
        const res = await fetch(`/api/admin/modules/${editingModule.id}`, withCsrf({
          method: 'PUT', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: moduleData.name, label: moduleData.label,
            parentId: moduleData.parentId || null, parentLabel: moduleData.parentLabel || null,
            description: moduleData.description || '', sortOrder: moduleData.sortOrder ?? 0,
            status: moduleData.status || 'active',
          }),
        }))
        if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || 'Failed to update') }
        toast.success('Module updated')
        loadModules()
      } else {
        const res = await fetch('/api/admin/modules', withCsrf({
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: moduleData.name, label: moduleData.label,
            parentId: moduleData.parentId || null, parentLabel: moduleData.parentLabel || null,
            description: moduleData.description || '', sortOrder: moduleData.sortOrder ?? 0,
            status: moduleData.status || 'active',
          }),
        }))
        if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || 'Failed to create') }
        toast.success('Module created')
        loadModules()
      }
    } catch (err) { toast.error(err instanceof Error ? err.message : 'Operation failed') }
    finally { setModuleDialogOpen(false); setEditingModule(null) }
  }, [editingModule, loadModules])

  const handleDeleteModule = useCallback(async (moduleId: string) => {
    try {
      const res = await fetch(`/api/admin/modules/${moduleId}`, withCsrf({ method: 'DELETE' }))
      if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || 'Failed to delete') }
      setModules(prev => prev.filter(m => m.id !== moduleId))
      toast.success('Module deleted')
    } catch (err) { toast.error(err instanceof Error ? err.message : 'Failed') }
  }, [])

  const handleSeedModules = useCallback(async () => {
    try {
      const res = await fetch('/api/admin/modules/seed', withCsrf({ method: 'POST' }))
      if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || 'Failed to seed') }
      const data = await res.json()
      toast.success(`Modules seeded: ${data.created || 0} created, ${data.updated || 0} updated`)
      loadModules()
    } catch (err) { toast.error(err instanceof Error ? err.message : 'Failed') }
  }, [loadModules])

  const handleToggleModuleStatus = useCallback(async (mod: AdminModule) => {
    const statusCycle: Record<string, AdminModule['status']> = { active: 'draft', draft: 'disabled', disabled: 'active' }
    const newStatus = statusCycle[mod.status] || 'active'
    try {
      const res = await fetch(`/api/admin/modules/${mod.id}`, withCsrf({
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      }))
      if (!res.ok) throw new Error('Failed to toggle status')
      setModules(prev => prev.map(m => m.id === mod.id ? { ...m, status: newStatus } : m))
      toast.success(`Module status changed to ${newStatus}`)
    } catch (err) { toast.error(err instanceof Error ? err.message : 'Failed') }
  }, [])

  // Bulk user action handlers
  const handleBulkAction = useCallback(async () => {
    const ids = Array.from(selectedUserIds)
    if (ids.length === 0) return
    try {
      if (bulkActionType === 'activate') {
        await Promise.all(ids.map(id => fetch(`/api/admin/users/${id}`, withCsrf({ method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status: 'active' }) }))))
        setUsers(prev => prev.map(u => ids.includes(u.id) ? { ...u, status: 'active' as const } : u))
        toast.success(`${ids.length} user(s) activated`)
      } else if (bulkActionType === 'deactivate') {
        await Promise.all(ids.map(id => fetch(`/api/admin/users/${id}`, withCsrf({ method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status: 'inactive' }) }))))
        setUsers(prev => prev.map(u => ids.includes(u.id) ? { ...u, status: 'inactive' as const } : u))
        toast.success(`${ids.length} user(s) deactivated`)
      } else if (bulkActionType === 'delete') {
        await Promise.all(ids.map(id => fetch(`/api/admin/users/${id}`, withCsrf({ method: 'DELETE' }))))
        setUsers(prev => prev.filter(u => !ids.includes(u.id)))
        toast.success(`${ids.length} user(s) deleted`)
      }
      setSelectedUserIds(new Set())
    } catch (err) { toast.error(err instanceof Error ? err.message : 'Bulk action failed') }
    finally { setBulkActionConfirmOpen(false); setBulkActionType('') }
  }, [selectedUserIds, bulkActionType])

  const toggleUserSelection = useCallback((id: string) => {
    setSelectedUserIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  const toggleAllUsers = useCallback(() => {
    if (selectedUserIds.size === users.length && users.length > 0) {
      setSelectedUserIds(new Set())
    } else {
      setSelectedUserIds(new Set(users.map(u => u.id)))
    }
  }, [selectedUserIds.size, users])

  return {
    user, authLoading,
    sidebarOpen, setSidebarOpen,
    activeSection, setActiveSection,
    tests, testsLoaded,
    modules, modulesLoaded, loadModules,
    environments, envLoaded,
    users, usersLoaded,
    bugReports, setBugReports, bugsLoaded,
    auditLog, auditLoaded,
    envDialogOpen, setEnvDialogOpen, editingEnv, setEditingEnv,
    userDialogOpen, setUserDialogOpen, editingUser, setEditingUser,
    deleteDialogOpen, setDeleteDialogOpen, deleteTarget, setDeleteTarget,
    moduleDialogOpen, setModuleDialogOpen, editingModule, setEditingModule,
    resetPasswordDialogOpen, setResetPasswordDialogOpen,
    resetPasswordUser, setResetPasswordUser,
    bugSubTab, setBugSubTab,
    bugStatusFilter, setBugStatusFilter,
    bugSearch, setBugSearch,
    bugModuleFilter, setBugModuleFilter,
    bugPriorityFilter, setBugPriorityFilter,
    expandedBug, setExpandedBug,
    bugReplyText, setBugReplyText,
    pendingBugStatus, setPendingBugStatus,
    adminUnreadChats,
    selectedUserIds, setSelectedUserIds,
    bulkActionConfirmOpen, setBulkActionConfirmOpen,
    bulkActionType, setBulkActionType,
    hiddenWidgets, widgetDialogOpen, setWidgetDialogOpen,
    toggleWidgetVisibility,
    stats,
    handleLogout,
    handleSaveEnv, handleToggleEnv,
    handleSaveUser, handleResetPassword,
    handleDelete,
    handleBugStatusChange, handleBugReply, handleMarkBugRead,
    handleSaveModule, handleDeleteModule, handleSeedModules, handleToggleModuleStatus,
    handleBulkAction, toggleUserSelection, toggleAllUsers,
  }
}
