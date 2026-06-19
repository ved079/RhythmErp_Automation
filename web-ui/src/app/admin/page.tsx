'use client'

import React, { useState, useEffect, useCallback, useMemo } from 'react'
import Image from 'next/image'
import { useRouter } from 'next/navigation'
import { useTheme } from 'next-themes'
import {
  getBugReports, updateBugReportStatus, addReplyToReport,
  markReportReadByAdmin, getSLAStatus, type BugReport,
} from '@/lib/bug-reports'
import { fetchTestCases } from '@/lib/api'
import { withCsrf } from '@/lib/csrf-client'
import { ALL_SIDEBAR_MODULES } from '@/data/sidebarModules'
import { ModuleAccessPicker, type ModuleItem } from '@/components/admin/ModuleAccessPicker'
import { TestUserVisibilityDialog } from '@/components/admin/TestUserVisibilityDialog'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Progress } from '@/components/ui/progress'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'

import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription,
} from '@/components/ui/dialog'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import {
  Search, Plus, Eye, Pencil, Trash2, ClipboardList, Clock, List,
  ChevronLeft, ChevronDown, Loader2, Lock, LogOut,
  Globe, Settings, LayoutDashboard, Users as UsersIcon,
  Shield, Server, Activity, AlertTriangle, CheckCircle2,
  XCircle, Circle, Sun, Moon, Home, FolderTree, Inbox,
  Send, Timer, Database, Cpu, Zap, BarChart3, FileText,
  RotateCcw, Save, Monitor, Key, Bell, ChevronRight,
  Menu, HardDrive, EyeOff, Check, X,
} from 'lucide-react'

// ─── Types ───────────────────────────────────────────────
interface AuthUser { id: string; email: string; name: string; role: string }
interface AdminTest {
  id: string; description: string; className: string
  status: 'active' | 'draft' | 'disabled'; priority: 'smoke' | 'regression' | 'sanity'
  steps: string; expected: string; moduleId: string; moduleName: string
  error?: string; lastResult?: 'passed' | 'failed' | 'not-run'; lastRun?: string
}
interface AdminModule {
  id: string; name: string; label: string; parentId?: string; parentLabel?: string
  badge?: string; testCount: number; sortOrder: number; status: 'active' | 'draft' | 'disabled'
  description?: string
}
interface Environment {
  id: string; name: string; baseUrl: string; browser: string
  status: 'active' | 'inactive'; lastUsed?: string; color: string
}
interface AdminUser {
  id: string; email: string; name: string
  role: 'admin' | 'tester' | 'viewer' | 'client'
  status: 'active' | 'inactive'; lastLogin?: string; moduleAccess: string[]
}
interface SystemSetting {
  id: string; key: string; label: string; value: string
  type: 'text' | 'number' | 'boolean' | 'select'; description: string; category: string
  options?: string[]
}
interface AuditEntry {
  id: string; userId: string; userName: string; action: string
  targetType: string; targetId: string; targetLabel: string
  details: string; createdAt: string
}

const roleConfig: Record<string, { label: string; color: string }> = {
  admin: { label: 'Admin', color: 'text-[#3F51B5] bg-[#E8EAF6] dark:text-[#7986CB] dark:bg-[#1A237E]/30' },
  tester: { label: 'Tester', color: 'text-[#2E7D32] bg-[#E8F5E9] dark:text-[#66BB6A] dark:bg-[#1B5E20]/40' },
  viewer: { label: 'Viewer', color: 'text-[#616161] bg-[#F5F5F5] dark:text-[#9E9E9E] dark:bg-[#424242]/40' },
  client: { label: 'Client', color: 'text-[#E65100] bg-[#FFF3E0] dark:text-[#FFB74D] dark:bg-[#BF360C]/40' },
}

const priorityConfig: Record<string, { label: string; color: string }> = {
  smoke: { label: 'Smoke', color: 'text-orange-700 bg-orange-100 dark:text-orange-300 dark:bg-orange-900/40' },
  regression: { label: 'Regression', color: 'text-[#3F51B5] bg-[#E8EAF6] dark:text-[#7986CB] dark:bg-[#1A237E]/30' },
  sanity: { label: 'Sanity', color: 'text-purple-700 bg-purple-100 dark:text-purple-300 dark:bg-purple-900/40' },
}

// ─── ADMIN PAGE COMPONENT ────────────────────────────────
export default function AdminPage() {
  const router = useRouter()
  const { theme, setTheme } = useTheme()
  const isDark = theme === 'dark'

  const [user, setUser] = useState<AuthUser | null>(null)
  const [authLoading, setAuthLoading] = useState(true)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [activeSection, setActiveSection] = useState('overview')

  // Data state
  const [tests, setTests] = useState<AdminTest[]>([])
  const [modules, setModules] = useState<AdminModule[]>([])
  const [environments, setEnvironments] = useState<Environment[]>([])
  const [users, setUsers] = useState<AdminUser[]>([])
  const [settings, setSettings] = useState<SystemSetting[]>([])
  const [bugReports, setBugReports] = useState<BugReport[]>([])
  const [auditLog, setAuditLog] = useState<AuditEntry[]>([])

  // Loading flags
  const [testsLoaded, setTestsLoaded] = useState(false)
  const [modulesLoaded, setModulesLoaded] = useState(false)
  const [usersLoaded, setUsersLoaded] = useState(false)
  const [envLoaded, setEnvLoaded] = useState(false)
  const [settingsLoaded, setSettingsLoaded] = useState(false)
  const [bugsLoaded, setBugsLoaded] = useState(false)
  const [auditLoaded, setAuditLoaded] = useState(false)

  // Test filters
  const [testSearch, setTestSearch] = useState('')
  const [testStatusFilter, setTestStatusFilter] = useState('all')
  const [testModuleFilter, setTestModuleFilter] = useState('all')
  const [testPriorityFilter, setTestPriorityFilter] = useState('all')
  const [testPage, setTestPage] = useState(1)

  // Bug filters
  const [bugStatusFilter, setBugStatusFilter] = useState('all')
  const [bugSearch, setBugSearch] = useState('')
  const [bugModuleFilter, setBugModuleFilter] = useState('all')
  const [bugPriorityFilter, setBugPriorityFilter] = useState('all')
  const [expandedBug, setExpandedBug] = useState<string | null>(null)
  const [bugReplyText, setBugReplyText] = useState<Record<string, string>>({})
  const [pendingBugStatus, setPendingBugStatus] = useState<Record<string, string>>({})

  // Audit pagination & filters
  const [auditPage, setAuditPage] = useState(1)
  const [auditSearch, setAuditSearch] = useState('')
  const [auditActionFilter, setAuditActionFilter] = useState('all')
  const [auditUserFilter, setAuditUserFilter] = useState('all')

  // Dialogs
  const [envDialogOpen, setEnvDialogOpen] = useState(false)
  const [editingEnv, setEditingEnv] = useState<Environment | null>(null)
  const [userDialogOpen, setUserDialogOpen] = useState(false)
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<{ type: string; id: string; label: string } | null>(null)
  const [moduleDialogOpen, setModuleDialogOpen] = useState(false)
  const [editingModule, setEditingModule] = useState<AdminModule | null>(null)

  // Reset password dialog
  const [resetPasswordDialogOpen, setResetPasswordDialogOpen] = useState(false)
  const [resetPasswordUser, setResetPasswordUser] = useState<AdminUser | null>(null)

  // Bulk user actions
  const [selectedUserIds, setSelectedUserIds] = useState<Set<string>>(new Set())
  const [bulkActionConfirmOpen, setBulkActionConfirmOpen] = useState(false)
  const [bulkActionType, setBulkActionType] = useState<string>('')

  // Test Visibility
  const [overrides, setOverrides] = useState<Record<string, { displayName?: string; disabled: boolean }>>({})
  const [syncingTests, setSyncingTests] = useState(false)
  const [exclusionCounts, setExclusionCounts] = useState<Record<string, number>>({})
  const [modulesTree, setModulesTree] = useState<{ name: string; display: string; sub_modules: { name: string; display: string; tests: { name: string; display_name: string; type?: string }[] }[] }[]>([])
  const [testVisibilitySearch, setTestVisibilitySearch] = useState('')
  const [selectedVisModule, setSelectedVisModule] = useState<string>('')
  const [selectedVisSubModule, setSelectedVisSubModule] = useState<string>('')
  const [visSelectedTests, setVisSelectedTests] = useState<Set<string>>(new Set())
  const [visCollapsedSubs, setVisCollapsedSubs] = useState<Set<string>>(new Set())
  const [batchActionLoading, setBatchActionLoading] = useState(false)
  const [visSelectedType, setVisSelectedType] = useState<'all' | 'ui' | 'api' | null>(null)
  const [visActionMode, setVisActionMode] = useState<'name' | 'visibility' | null>(null)
  const [showRawNames, setShowRawNames] = useState(() => typeof window !== 'undefined' && localStorage.getItem('showRawNames') === 'true')
  const loadOverrides = useCallback(async () => {
    try {
      const [ovRes, exRes] = await Promise.all([
        fetch('/api/admin/tests/overrides'),
        fetch('/api/admin/tests/exclusions'),
      ])
      if (ovRes.ok) {
        const ovData = await ovRes.json()
        const map: Record<string, { displayName?: string; disabled: boolean }> = {}
        for (const o of ovData.overrides || []) {
          map[o.testName] = { displayName: o.displayName, disabled: o.disabled }
        }
        setOverrides(map)
      }
      if (exRes.ok) {
        const exData = await exRes.json()
        const counts: Record<string, number> = {}
        for (const e of exData.exclusions || []) {
          counts[e.testName] = (counts[e.testName] || 0) + 1
        }
        setExclusionCounts(counts)
      }
    } catch { /* silent */ }
  }, [])
  const syncTestsFromBackend = useCallback(async () => {
    setSyncingTests(true)
    try {
      const res = await fetch('/api/proxy?path=modules')
      if (!res.ok) { toast.error('Failed to fetch modules from backend'); return }
      const data = await res.json()
      const modules: { name: string; sub_modules: { name: string; tests: { name: string; display_name?: string }[] }[] }[] = data.modules || []
      const testNames: { name: string; displayName: string }[] = []
      for (const mod of modules) {
        for (const sub of mod.sub_modules) {
          for (const t of sub.tests) {
            testNames.push({ name: t.name, displayName: t.display_name || t.name.split('::').pop() || t.name })
          }
        }
      }
      if (testNames.length === 0) { toast.error('No tests found in backend'); return }
      setModulesTree(modules)
      let upserted = 0
      for (const t of testNames) {
        const r = await fetch('/api/admin/tests/overrides', withCsrf({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ testName: t.name, displayName: t.displayName }),
        }))
        if (r.ok) upserted++
      }
      toast.success(`Synced ${upserted} tests from backend`)
      loadOverrides()
    } catch (e) {
      toast.error('Sync failed: ' + (e instanceof Error ? e.message : 'Unknown error'))
    } finally {
      setSyncingTests(false)
    }
  }, [loadOverrides])
  const [visibilityDialogOpen, setVisibilityDialogOpen] = useState(false)
  const [visibilityDialogTest, setVisibilityDialogTest] = useState<{ testName: string; displayName: string } | null>(null)
  const [editingOverrideName, setEditingOverrideName] = useState<string | null>(null)
  const [editingNameValue, setEditingNameValue] = useState('')
  const [visDetailOpen, setVisDetailOpen] = useState(false)
  const [visDetailTest, setVisDetailTest] = useState<{ testName: string; displayName: string; testType: string; disabled: boolean; excluded: number } | null>(null)

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

  // System health
  const [systemHealthData, setSystemHealthData] = useState<Record<string, unknown> | null>(null)
  const [healthLoaded, setHealthLoaded] = useState(false)
  const [appStartTime] = useState(() => Date.now())

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

  const loadModulesTree = useCallback(async () => {
    try {
      const res = await fetch('/api/proxy?path=modules')
      if (res.ok) {
        const data = await res.json()
        setModulesTree(data.modules || [])
      }
    } catch { /* silent */ }
  }, [])

  useEffect(() => {
    if (activeSection === 'test-visibility') {
      loadOverrides()
      loadModulesTree()
    }
  }, [activeSection, loadOverrides, loadModulesTree])

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

  // Settings
  useEffect(() => {
    (async () => {
      try {
        const res = await fetch('/api/admin/settings')
        if (res.ok) {
          const data = await res.json()
          setSettings(data.settings || [])
        }
      } catch { /* empty */ } finally { setSettingsLoaded(true) }
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

  // System health — load when switching to system-health section
  useEffect(() => {
    if (activeSection === 'system-health') {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setHealthLoaded(false)
      fetch('/api/admin/system-health')
        .then(res => res.ok ? res.json() : null)
        .then(data => { setSystemHealthData(data) })
        .catch(() => { /* empty */ })
        .finally(() => { setHealthLoaded(true) })
    }
  }, [activeSection])

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

  // Filtered tests
  const filteredTests = useMemo(() => {
    return tests.filter(t => {
      const ms = !testSearch || t.id.toLowerCase().includes(testSearch.toLowerCase()) || t.description.toLowerCase().includes(testSearch.toLowerCase()) || t.className.toLowerCase().includes(testSearch.toLowerCase())
      const mst = testStatusFilter === 'all' || t.status === testStatusFilter
      const mm = testModuleFilter === 'all' || t.moduleId === testModuleFilter
      const mp = testPriorityFilter === 'all' || t.priority === testPriorityFilter
      return ms && mst && mm && mp
    })
  }, [tests, testSearch, testStatusFilter, testModuleFilter, testPriorityFilter])

  const uniqueTestModules = useMemo(() => {
    const m = new Map<string, string>()
    for (const t of tests) if (!m.has(t.moduleId)) m.set(t.moduleId, t.moduleName)
    return Array.from(m.entries()).sort((a, b) => a[1].localeCompare(b[1]))
  }, [tests])

  // Filtered audit log
  const filteredAuditLog = useMemo(() => {
    return auditLog.filter(a => {
      const ms = !auditSearch || a.userName.toLowerCase().includes(auditSearch.toLowerCase()) || a.targetLabel.toLowerCase().includes(auditSearch.toLowerCase()) || a.details.toLowerCase().includes(auditSearch.toLowerCase()) || a.targetType.toLowerCase().includes(auditSearch.toLowerCase())
      const mst = auditActionFilter === 'all' || a.action === auditActionFilter
      const mu = auditUserFilter === 'all' || a.userName === auditUserFilter
      return ms && mst && mu
    })
  }, [auditLog, auditSearch, auditActionFilter, auditUserFilter])

  const uniqueAuditUsers = useMemo(() => {
    const s = new Set<string>()
    for (const a of auditLog) s.add(a.userName)
    return Array.from(s).sort()
  }, [auditLog])

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

  const handleSaveSetting = useCallback(async (setting: SystemSetting, newValue: string) => {
    try {
      const res = await fetch(`/api/admin/settings/${setting.id}`, withCsrf({
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: newValue }),
      }))
      if (!res.ok) throw new Error('Failed to save')
      setSettings(prev => prev.map(s => s.id === setting.id ? { ...s, value: newValue } : s))
      toast.success('Setting saved')
    } catch (err) { toast.error(err instanceof Error ? err.message : 'Failed') }
  }, [])

  const handleSeedSettings = useCallback(async () => {
    try {
      const res = await fetch('/api/admin/settings/seed', withCsrf({ method: 'POST' }))
      if (!res.ok) throw new Error('Failed to reset')
      const data = await res.json()
      setSettings(data.settings || [])
      toast.success('Settings reset to defaults')
    } catch (err) { toast.error(err instanceof Error ? err.message : 'Failed') }
  }, [])

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

  // ─── Sidebar items ──────────────────────────────────
  const sidebarItems = [
    { id: 'overview', icon: LayoutDashboard, label: 'Overview' },
    { id: 'tests', icon: ClipboardList, label: 'Test Management' },
    { id: 'modules', icon: FolderTree, label: 'Modules' },
    { id: 'test-visibility', icon: EyeOff, label: 'Test Visibility' },
    { id: 'bug-reports', icon: Inbox, label: 'Bug Reports' },
    { id: 'environments', icon: Globe, label: 'Environments' },
    { id: 'users', icon: UsersIcon, label: 'Users' },
    { id: 'settings', icon: Settings, label: 'Settings' },
    { id: 'system-health', icon: Activity, label: 'System Health' },
    { id: 'audit-log', icon: FileText, label: 'Audit Log' },
  ]

  // ─── Loading screen ──────────────────────────────────
  if (authLoading) {
    return (
      <div className="h-screen flex items-center justify-center bg-[#F1F2F7] dark:bg-gray-900">
        <div className="flex flex-col items-center gap-3">
          <Image src="/agdi-logo-new.webp" width={40} height={40} className="object-contain animate-pulse" alt="agDi Logo" />
          <Loader2 className="size-5 text-[#6777EF] animate-spin" />
        </div>
      </div>
    )
  }
  if (!user) return null
  const userInitials = user.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)

  // ─── SECTION RENDERERS ────────────────────────────────

  // 1. Overview
  const renderOverview = () => {
    const passCount = tests.filter(t => t.lastResult === 'passed').length
    const failCount = tests.filter(t => t.lastResult === 'failed').length
    const notRunCount = tests.filter(t => t.lastResult === 'not-run' || !t.lastResult).length
    const total = passCount + failCount + notRunCount || 1
    const passPct = Math.round((passCount / total) * 100)
    const failPct = Math.round((failCount / total) * 100)

    const statCards = [
      { label: 'Active Tests', value: stats.activeTests, icon: ClipboardList, color: '#4CAF50', bg: '#E8F5E9' },
      { label: 'Modules', value: stats.totalModules, icon: FolderTree, color: '#3F51B5', bg: '#DFE9FB' },
      { label: 'Environments', value: stats.activeEnvs, icon: Globe, color: '#FF9800', bg: '#FFF3E0' },
      { label: 'Users', value: stats.activeUsers, icon: UsersIcon, color: '#F44336', bg: '#FFEBEE' },
    ]

    const allWidgets = [
      { id: 'stat-cards', label: 'Stat Cards' },
      { id: 'pass-rate', label: 'Pass Rate' },
      { id: 'environments', label: 'Active Environments' },
      { id: 'recent-failures', label: 'Recent Failures' },
      { id: 'recent-activity', label: 'Recent Activity' },
    ]

    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">Dashboard Overview</h2>
          <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => setWidgetDialogOpen(true)} title="Customize widgets">
            <Settings className="size-4 text-[#888]" />
          </Button>
        </div>
        {/* Stat cards */}
        {!hiddenWidgets.has('stat-cards') && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {statCards.map(c => (
              <div key={c.label} className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700 flex items-center gap-4">
                <div className="w-11 h-11 rounded-xl flex items-center justify-center" style={{ background: c.bg }}>
                  <c.icon className="size-5" style={{ color: c.color }} />
                </div>
                <div>
                  <p className="text-2xl font-bold font-['Poppins'] text-[#333] dark:text-gray-100">{c.value}</p>
                  <p className="text-xs text-[#888] dark:text-gray-400 font-['Manrope']">{c.label}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Pass Rate Donut */}
          {!hiddenWidgets.has('pass-rate') && (
            <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
              <h3 className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100 mb-4">Pass Rate</h3>
              <div className="flex items-center justify-center">
                <svg width="160" height="160" viewBox="0 0 160 160">
                  <circle cx="80" cy="80" r="60" fill="none" stroke={isDark ? '#374151' : '#E5E7EB'} strokeWidth="18" />
                  <circle cx="80" cy="80" r="60" fill="none" stroke="#4CAF50" strokeWidth="18"
                    strokeDasharray={`${passPct * 3.77} ${377 - passPct * 3.77}`} strokeDashoffset="94.25"
                    strokeLinecap="round" className="transition-all duration-700" />
                  <circle cx="80" cy="80" r="60" fill="none" stroke="#F44336" strokeWidth="18"
                    strokeDasharray={`${failPct * 3.77} ${377 - failPct * 3.77}`}
                    strokeDashoffset={94.25 - passPct * 3.77} strokeLinecap="round" className="transition-all duration-700" />
                  <text x="80" y="72" textAnchor="middle" className="fill-[#333] dark:fill-gray-100 text-2xl font-bold font-['Poppins']">{stats.passRate}%</text>
                  <text x="80" y="92" textAnchor="middle" className="fill-[#888] dark:fill-gray-400 text-xs font-['Manrope']">Pass Rate</text>
                </svg>
              </div>
              <div className="flex justify-center gap-4 mt-3 text-xs font-['Manrope']">
                <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-[#4CAF50]" />Passed {passCount}</span>
                <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-[#F44336]" />Failed {failCount}</span>
                <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-gray-300 dark:bg-gray-600" />Not Run {notRunCount}</span>
              </div>
            </div>
          )}

          {/* Active Environments */}
          {!hiddenWidgets.has('environments') && (
            <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
              <h3 className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100 mb-3">Active Environments</h3>
              {envLoaded ? (
                <div className="space-y-2 max-h-[200px] overflow-y-auto">
                  {environments.filter(e => e.status === 'active').map(e => (
                    <div key={e.id} className="flex items-center gap-3 p-2 rounded-lg bg-[#F1F2F7] dark:bg-gray-700/50">
                      <span className={`w-2.5 h-2.5 rounded-full ${e.color || 'bg-green-500'}`} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-[#333] dark:text-gray-100 truncate">{e.name}</p>
                        <p className="text-xs text-[#888] dark:text-gray-400 truncate">{e.baseUrl}</p>
                      </div>
                      <Badge variant="outline" className="text-[10px]">{e.browser}</Badge>
                    </div>
                  ))}
                  {environments.filter(e => e.status === 'active').length === 0 && <p className="text-xs text-[#888] dark:text-gray-400 text-center py-4">No active environments</p>}
                </div>
              ) : <Loader2 className="size-5 animate-spin text-[#3F51B5] mx-auto" />}
            </div>
          )}

          {/* Recent Failures */}
          {!hiddenWidgets.has('recent-failures') && (
            <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
              <h3 className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100 mb-3">Recent Failures</h3>
              {testsLoaded ? (
                <div className="space-y-2 max-h-[200px] overflow-y-auto">
                  {stats.failedTests.slice(0, 6).map(t => (
                    <div key={t.id} className="flex items-start gap-2 p-2 rounded-lg bg-red-50 dark:bg-red-900/20">
                      <XCircle className="size-4 text-[#F44336] shrink-0 mt-0.5" />
                      <div className="min-w-0">
                        <p className="text-xs font-medium text-[#333] dark:text-gray-100 truncate">{t.description}</p>
                        <p className="text-[10px] text-[#888] dark:text-gray-400">{t.moduleName}</p>
                      </div>
                    </div>
                  ))}
                  {stats.failedTests.length === 0 && <p className="text-xs text-[#888] dark:text-gray-400 text-center py-4">No failures 🎉</p>}
                </div>
              ) : <Loader2 className="size-5 animate-spin text-[#3F51B5] mx-auto" />}
            </div>
          )}
        </div>

        {/* Recent Audit */}
        {!hiddenWidgets.has('recent-activity') && (
          <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
            <h3 className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100 mb-3">Recent Activity</h3>
            {auditLog.length > 0 ? (
              <div className="space-y-2">
                {auditLog.slice(0, 5).map(a => (
                  <div key={a.id} className="flex items-center gap-3 p-2 rounded-lg bg-[#F1F2F7] dark:bg-gray-700/50 text-xs font-['Manrope']">
                    <Badge className={`text-[9px] px-1.5 py-0 border-0 ${a.action === 'create' ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300' : a.action === 'delete' ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300' : 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'}`}>{a.action}</Badge>
                    <span className="text-[#333] dark:text-gray-100">{a.userName}</span>
                    <span className="text-[#888] dark:text-gray-400">{a.targetLabel}</span>
                    <span className="ml-auto text-[#888] dark:text-gray-400">{new Date(a.createdAt).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-[#888] dark:text-gray-400 text-center py-4">No recent activity</p>
            )}
          </div>
        )}

        {/* Widget Customization Dialog */}
        <Dialog open={widgetDialogOpen} onOpenChange={setWidgetDialogOpen}>
          <DialogContent className="sm:max-w-[400px]">
            <DialogHeader>
              <DialogTitle className="font-['Poppins'] text-[#333] dark:text-gray-100">Customize Widgets</DialogTitle>
              <DialogDescription className="font-['Manrope'] text-[#888]">
                Toggle which overview widgets are visible.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-3 py-2">
              {allWidgets.map(w => (
                <div key={w.id} className="flex items-center gap-3 p-2 rounded-lg bg-[#F1F2F7] dark:bg-gray-700/50">
                  <Checkbox checked={!hiddenWidgets.has(w.id)} onCheckedChange={() => toggleWidgetVisibility(w.id)} />
                  <span className="text-sm font-['Manrope'] text-[#333] dark:text-gray-100">{w.label}</span>
                </div>
              ))}
            </div>
            <DialogFooter>
              <Button onClick={() => setWidgetDialogOpen(false)} className="bg-[#2D3FC7] hover:bg-[#3F51B5] text-white font-['Roboto']">Done</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    )
  }

  // 2. Test Management
  const renderTests = () => {
    const perPage = 25
    const totalPages = Math.ceil(filteredTests.length / perPage) || 1
    const paged = filteredTests.slice((testPage - 1) * perPage, testPage * perPage)

    return (
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <h2 className="text-xl font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">Test Management</h2>
          <Badge variant="outline" className="text-xs font-['Manrope']">{filteredTests.length} tests</Badge>
        </div>
        {/* Filters */}
        <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-2.5 size-4 text-[#888]" />
              <Input placeholder="Search tests..." value={testSearch} onChange={e => { setTestSearch(e.target.value); setTestPage(1) }}
                className="pl-9 h-9 text-sm font-['Manrope']" />
            </div>
            <Select value={testStatusFilter} onValueChange={v => { setTestStatusFilter(v); setTestPage(1) }}>
              <SelectTrigger className="h-9 text-sm"><SelectValue placeholder="Status" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="draft">Draft</SelectItem>
                <SelectItem value="disabled">Disabled</SelectItem>
              </SelectContent>
            </Select>
            <Select value={testModuleFilter} onValueChange={v => { setTestModuleFilter(v); setTestPage(1) }}>
              <SelectTrigger className="h-9 text-sm"><SelectValue placeholder="Module" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Modules</SelectItem>
                {uniqueTestModules.map(([id, label]) => <SelectItem key={id} value={id}>{label}</SelectItem>)}
              </SelectContent>
            </Select>
            <Select value={testPriorityFilter} onValueChange={v => { setTestPriorityFilter(v); setTestPage(1) }}>
              <SelectTrigger className="h-9 text-sm"><SelectValue placeholder="Priority" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Priorities</SelectItem>
                <SelectItem value="smoke">Smoke</SelectItem>
                <SelectItem value="regression">Regression</SelectItem>
                <SelectItem value="sanity">Sanity</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        {/* Test Cases */}
        <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {!testsLoaded ? (
            <div className="flex justify-center py-12"><Loader2 className="size-6 animate-spin text-[#3F51B5]" /></div>
          ) : filteredTests.length === 0 ? (
            <div className="text-center py-12 text-[#888] dark:text-gray-400 font-['Manrope'] text-sm">No tests found</div>
          ) : (
            <>
              <div className="space-y-1 p-3">
                {paged.map(t => (
                  <div key={t.id} className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-white dark:bg-gray-800/20 border border-gray-100 dark:border-gray-700/40 hover:bg-gray-50/50 dark:hover:bg-gray-800/30 transition-colors">
                    <span className="text-[11px] font-mono text-[#545454] dark:text-gray-400 w-12 shrink-0">{t.id}</span>
                    <span className="flex-1 text-[13px] font-['Manrope'] text-[#333] dark:text-gray-100 truncate">{t.description}</span>
                    <span className="text-[11px] font-['Manrope'] text-[#545454] dark:text-gray-400 shrink-0">{t.moduleName}</span>
                    <Badge variant="outline" className="text-[10px] shrink-0">{t.status}</Badge>
                    <Badge className={`text-[10px] border-0 shrink-0 ${priorityConfig[t.priority]?.color || ''}`}>{priorityConfig[t.priority]?.label || t.priority}</Badge>
                    <span className="shrink-0">
                      {t.lastResult === 'passed' ? <CheckCircle2 className="size-4 text-[#4CAF50]" />
                        : t.lastResult === 'failed' ? <XCircle className="size-4 text-[#F44336]" />
                        : <Circle className="size-4 text-gray-400" />}
                    </span>
                  </div>
                ))}
              </div>
              {/* Pagination */}
              <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100 dark:border-gray-700">
                <span className="text-xs text-[#888] dark:text-gray-400 font-['Manrope']">
                  Showing {(testPage - 1) * perPage + 1}–{Math.min(testPage * perPage, filteredTests.length)} of {filteredTests.length}
                </span>
                <div className="flex gap-1">
                  <Button size="sm" variant="outline" disabled={testPage <= 1} onClick={() => setTestPage(p => p - 1)} className="h-7 text-xs"><ChevronLeft className="size-3" /></Button>
                  <span className="flex items-center px-2 text-xs text-[#545454] dark:text-gray-300 font-['Manrope']">{testPage} / {totalPages}</span>
                  <Button size="sm" variant="outline" disabled={testPage >= totalPages} onClick={() => setTestPage(p => p + 1)} className="h-7 text-xs"><ChevronRight className="size-3" /></Button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    )
  }

  const renderTestVisibility = () => {
    const hasOverrides = Object.keys(overrides).length > 0
    const searchLower = testVisibilitySearch.toLowerCase()

    const testMatches = (t: { name: string; display_name: string; type?: string }) =>
      (visSelectedType === 'all' || (t.type || 'ui') === visSelectedType) &&
      (!searchLower || t.name.toLowerCase().includes(searchLower) || t.display_name.toLowerCase().includes(searchLower))

    const saveOverride = async (tName: string, data: { displayName?: string | null; disabled?: boolean }) => {
      try {
        const res = await fetch('/api/admin/tests/overrides', withCsrf({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ testName: tName, ...data }),
        }))
        if (res.ok) loadOverrides()
      } catch { /* silent */ }
    }

    const batchUpdate = async (updates: { testName: string; disabled?: boolean; displayName?: string | null }[]) => {
      if (updates.length === 0) return
      setBatchActionLoading(true)
      try {
        const res = await fetch('/api/admin/tests/overrides/batch', withCsrf({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ updates }),
        }))
        if (res.ok) {
          setVisSelectedTests(new Set())
          loadOverrides()
          toast.success(`Updated ${updates.length} test${updates.length !== 1 ? 's' : ''}`)
        } else {
          toast.error('Batch update failed')
        }
      } catch {
        toast.error('Batch update failed')
      } finally {
        setBatchActionLoading(false)
      }
    }

    const saveExclusions = async (tName: string, userIds: string[]) => {
      try {
        const exRes = await fetch(`/api/admin/tests/exclusions?testName=${encodeURIComponent(tName)}`)
        if (!exRes.ok) return
        const exData = await exRes.json()
        const currentIds = new Set(exData.exclusions?.map((e: { userId: string }) => e.userId) || [])
        const toRemove = (exData.exclusions || []).filter((e: { userId: string }) => !userIds.includes(e.userId))
        for (const e of toRemove) {
          await fetch(`/api/admin/tests/exclusions/${e.id}`, withCsrf({ method: 'DELETE' }))
        }
        const toAdd = userIds.filter(id => !currentIds.has(id))
        if (toAdd.length > 0) {
          await fetch('/api/admin/tests/exclusions', withCsrf({
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ testName: tName, userIds: toAdd }),
          }))
        }
        loadOverrides()
      } catch { /* silent */ }
    }

    const commitRename = async () => {
      if (!editingOverrideName) return
      await saveOverride(editingOverrideName, { displayName: editingNameValue || null })
      setEditingOverrideName(null)
      setEditingNameValue('')
    }

    const handleDetailRename = async () => {
      if (!visDetailTest) return
      await saveOverride(visDetailTest.testName, { displayName: editingNameValue || null })
      setEditingNameValue('')
      setVisDetailOpen(false)
    }

    const toggleTestSelection = (testName: string) => {
      setVisSelectedTests(prev => {
        const next = new Set(prev)
        if (next.has(testName)) next.delete(testName); else next.add(testName)
        return next
      })
    }

    // Empty state
    if (!hasOverrides) {
      return (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">Test Visibility</h2>
            <Button onClick={syncTestsFromBackend} disabled={syncingTests} className="h-8 text-xs bg-[#2D3FC7] hover:bg-[#3F51B5] cursor-pointer gap-1.5">
              {syncingTests ? <Loader2 className="size-3.5 animate-spin" /> : <RotateCcw className="size-3.5" />}
              {syncingTests ? 'Syncing...' : 'Sync from Backend'}
            </Button>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-6 border border-gray-100 dark:border-gray-700 text-center">
            <EyeOff className="size-8 mx-auto mb-2 text-[#888]" />
            <p className="text-sm text-[#888] font-['Manrope']">No test overrides yet. Click &quot;Sync from Backend&quot; to discover tests, then hide or rename them.</p>
          </div>
        </div>
      )
    }

    // Compute totals from overrides (not just modulesTree)
    const totalDisabled = Object.values(overrides).filter(o => o.disabled).length
    const totalHidden = Object.values(exclusionCounts).reduce((a, c) => a + c, 0)

    // Module options for the select
    const moduleOptions = modulesTree.length > 0
      ? modulesTree.map(m => ({ value: m.name, label: m.display }))
      : []

    // Selected module data
    const selectedMod = selectedVisModule ? modulesTree.find(m => m.name === selectedVisModule) : null

    // Sub-module filtering: if a specific sub-module is selected, only show that one
    const activeSubModules = selectedMod && selectedVisSubModule && selectedVisSubModule !== '__all__'
      ? selectedMod.sub_modules.filter(s => s.name === selectedVisSubModule)
      : selectedMod?.sub_modules || []

    // All tests for the selected view (with overrides info)
    const selectedModTests = activeSubModules.flatMap(s => s.tests.map(t => ({
        ...t,
        modName: selectedMod!.name,
        modDisplay: selectedMod!.display,
        subName: s.name,
        subDisplay: s.display,
      })))

    const selectedModTestNames = new Set(selectedModTests.map(t => t.name))

    // Toggle all in current view
    const allSelectedDisabled = selectedModTests.length > 0 && selectedModTests.every(t => overrides[t.name]?.disabled)

    return (
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            <h2 className="text-xl font-semibold font-['Poppins'] text-[#333] dark:text-gray-100 whitespace-nowrap">Test Visibility</h2>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs font-['Manrope'] shrink-0">{Object.keys(overrides).length} overrides</Badge>
              {totalDisabled > 0 && <Badge variant="outline" className="text-xs text-red-600 border-red-200 bg-red-50 dark:bg-red-900/20 dark:border-red-800 shrink-0">{totalDisabled} disabled</Badge>}
              {totalHidden > 0 && <Badge variant="outline" className="text-xs text-orange-600 border-orange-200 bg-orange-50 dark:bg-orange-900/20 dark:border-orange-800 shrink-0">{totalHidden} hidden</Badge>}
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {visActionMode !== null && (
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-[#888]" />
                <Input
                  value={testVisibilitySearch}
                  onChange={e => setTestVisibilitySearch(e.target.value)}
                  placeholder="Search tests..."
                  className="h-8 pl-8 pr-3 text-[12px] font-['Manrope'] w-48"
                />
              </div>
            )}
            <Button onClick={syncTestsFromBackend} disabled={syncingTests} className="h-8 text-xs bg-[#2D3FC7] hover:bg-[#3F51B5] cursor-pointer gap-1.5">
              {syncingTests ? <Loader2 className="size-3.5 animate-spin" /> : <RotateCcw className="size-3.5" />}
              {syncingTests ? 'Syncing...' : 'Sync'}
            </Button>
          </div>
        </div>

        {/* Breadcrumb — directory-style path */}
        {selectedVisModule && (
          <div className="flex items-center flex-wrap gap-0.5 text-[12px] font-['Manrope'] bg-gray-50 dark:bg-gray-800/50 rounded-lg px-2.5 py-1.5 border border-gray-100 dark:border-gray-700/50">
            <button onClick={() => { setSelectedVisModule(''); setSelectedVisSubModule(''); setVisSelectedTests(new Set()); setTestVisibilitySearch(''); setVisSelectedType(null); setVisActionMode(null) }}
              className="flex items-center gap-1 px-2 py-1 rounded-md text-[#888] hover:text-white hover:bg-[#3F51B5] transition-all">
              <FolderTree className="size-3.5" />
              <span>Modules</span>
            </button>
            <ChevronRight className="size-3 text-[#ccc] shrink-0" />
            <button onClick={() => { setSelectedVisSubModule(''); setVisSelectedTests(new Set()); setTestVisibilitySearch(''); setVisSelectedType(null); setVisActionMode(null) }}
              className={`px-2 py-1 rounded-md transition-all flex items-center gap-1.5 ${
                !selectedVisSubModule && visSelectedType === null
                  ? 'bg-[#3F51B5] text-white font-semibold'
                  : 'text-[#888] hover:text-white hover:bg-[#3F51B5]'
              }`}>
              <FolderTree className="size-3.5" />
              <span>{selectedMod?.display}</span>
            </button>
            {selectedVisSubModule && (
              <>
                <ChevronRight className="size-3 text-[#ccc] shrink-0" />
                <button onClick={() => { setVisSelectedType(null); setVisActionMode(null); setVisSelectedTests(new Set()) }}
                  className={`px-2 py-1 rounded-md transition-all flex items-center gap-1.5 ${
                    visSelectedType === null
                      ? 'bg-[#3F51B5] text-white font-semibold'
                      : 'text-[#888] hover:text-white hover:bg-[#3F51B5]'
                  }`}>
                  <FolderTree className="size-3.5" />
                  <span>{selectedVisSubModule === '__all__' ? 'All sub-modules' : selectedMod?.sub_modules.find(s => s.name === selectedVisSubModule)?.display || selectedVisSubModule}</span>
                </button>
              </>
            )}
            {visSelectedType !== null && (
              <>
                <ChevronRight className="size-3 text-[#ccc] shrink-0" />
                <button onClick={() => { setVisActionMode(null) }}
                  className={`px-2 py-1 rounded-md transition-all flex items-center gap-1.5 ${
                    visActionMode === null
                      ? 'bg-[#3F51B5] text-white font-semibold'
                      : 'text-[#888] hover:text-white hover:bg-[#3F51B5]'
                  }`}>
                  {visSelectedType === 'all' ? <List className="size-3.5" /> : visSelectedType === 'ui' ? <Monitor className="size-3.5" /> : <Server className="size-3.5" />}
                  <span>{visSelectedType === 'all' ? 'All' : visSelectedType.toUpperCase()}</span>
                </button>
              </>
            )}
            {visActionMode !== null && (
              <>
                <ChevronRight className="size-3 text-[#ccc] shrink-0" />
                <span className="px-2 py-1 rounded-md bg-[#3F51B5] text-white font-semibold flex items-center gap-1.5">
                  {visActionMode === 'name' ? <Pencil className="size-3.5" /> : <Eye className="size-3.5" />}
                  <span>{visActionMode === 'name' ? 'Rename' : 'Visibility'}</span>
                </span>
              </>
            )}
          </div>
        )}

        {/* Module content */}

        {/* Step 1: Module cards */}
        {!selectedVisModule ? (
          <>
            <p className="text-[13px] text-[#888] font-['Manrope']">Select a module to manage test visibility</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
              {moduleOptions.map(mo => {
                const mod = modulesTree.find(x => x.name === mo.value)
                if (!mod) return null
                const modTotal = mod.sub_modules.reduce((a, s) => a + s.tests.length, 0)
                const modDisabled = mod.sub_modules.reduce((a, s) => a + s.tests.filter(t => overrides[t.name]?.disabled).length, 0)
                const modHidden = mod.sub_modules.reduce((a, s) => a + s.tests.filter(t => (exclusionCounts[t.name] || 0) > 0).length, 0)
                return (
                  <button
                    key={mo.value}
                    onClick={() => { setSelectedVisModule(mo.value); setSelectedVisSubModule(''); setVisSelectedTests(new Set()); setTestVisibilitySearch(''); setVisSelectedType(null); setVisActionMode(null) }}
                    className="text-left bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4 hover:shadow-md hover:border-[#3F51B5]/40 dark:hover:border-[#7986CB]/40 transition-all cursor-pointer group"
                  >
                    <div className="flex items-center gap-2.5 mb-2.5">
                      <div className="w-8 h-8 rounded-lg bg-[#E8EAF6] dark:bg-[#1A237E]/30 flex items-center justify-center group-hover:bg-[#C5CAE9] dark:group-hover:bg-[#1A237E]/50 transition-colors">
                        <FolderTree className="size-4 text-[#3F51B5]" />
                      </div>
                      <span className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100 group-hover:text-[#3F51B5] transition-colors">{mod.display}</span>
                    </div>
                    <div className="flex items-center gap-2.5 text-[11px] font-['Manrope']">
                      <span className="text-[#888]">{modTotal} test{modTotal !== 1 ? 's' : ''}</span>
                      {modDisabled > 0 && <span className="text-red-500 font-medium">{modDisabled} off</span>}
                      {modHidden > 0 && <span className="text-orange-500 font-medium">{modHidden} hid</span>}
                    </div>
                    <div className="mt-1.5 text-[10px] text-[#999] font-['Manrope']">{mod.sub_modules.length} sub-module{mod.sub_modules.length !== 1 ? 's' : ''}</div>
                  </button>
                )
              })}
            </div>
          </>

        /* Step 2: Sub-module cards */
        ) : !selectedVisSubModule ? (
          <>
            <p className="text-[13px] text-[#888] font-['Manrope']">Select a sub-module in <span className="font-semibold text-[#333] dark:text-gray-100">{selectedMod?.display}</span></p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {activeSubModules.map(sm => {
                const smDisabled = sm.tests.filter(t => overrides[t.name]?.disabled).length
                const smHidden = sm.tests.filter(t => (exclusionCounts[t.name] || 0) > 0).length
                return (
                  <button
                    key={sm.name}
                    onClick={() => { setSelectedVisSubModule(sm.name); setVisSelectedTests(new Set()); setVisSelectedType(null); setVisActionMode(null) }}
                    className="text-left bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4 hover:shadow-md hover:border-[#3F51B5]/40 dark:hover:border-[#7986CB]/40 transition-all cursor-pointer group"
                  >
                    <div className="flex items-center gap-2.5 mb-2">
                      <div className="w-8 h-8 rounded-lg bg-[#E8EAF6] dark:bg-[#1A237E]/30 flex items-center justify-center group-hover:bg-[#C5CAE9] dark:group-hover:bg-[#1A237E]/50 transition-colors">
                        <FolderTree className="size-4 text-[#3F51B5]" />
                      </div>
                      <span className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100 group-hover:text-[#3F51B5] transition-colors">{sm.display}</span>
                    </div>
                    <div className="flex items-center gap-2.5 text-[11px] font-['Manrope']">
                      <span className="text-[#888]">{sm.tests.length} test{sm.tests.length !== 1 ? 's' : ''}</span>
                      {smDisabled > 0 && <span className="text-red-500 font-medium">{smDisabled} off</span>}
                      {smHidden > 0 && <span className="text-orange-500 font-medium">{smHidden} hid</span>}
                    </div>
                  </button>
                )
              })}
              <button
                onClick={() => { setSelectedVisSubModule('__all__'); setVisSelectedTests(new Set()); setVisSelectedType(null); setVisActionMode(null) }}
                className="col-span-full text-center bg-gradient-to-r from-[#2D3FC7]/5 via-transparent to-[#2D3FC7]/5 dark:from-[#1A237E]/20 dark:to-[#1A237E]/20 rounded-xl border-2 border-dashed border-[#3F51B5]/30 dark:border-[#7986CB]/30 p-4 hover:border-[#3F51B5]/60 dark:hover:border-[#7986CB]/60 hover:from-[#2D3FC7]/10 hover:to-[#2D3FC7]/10 dark:hover:from-[#1A237E]/30 dark:hover:to-[#1A237E]/30 transition-all cursor-pointer"
              >
                <div className="flex items-center justify-center gap-2">
                  <List className="size-4 text-[#3F51B5] dark:text-[#7986CB]" />
                  <span className="text-sm font-semibold font-['Poppins'] text-[#3F51B5] dark:text-[#7986CB]">Load All Sub-modules</span>
                </div>
                <p className="text-[11px] text-[#888] font-['Manrope'] mt-1">{selectedModTests.length} tests total</p>
              </button>
            </div>
          </>

        /* Step 3: Type selection */
        ) : visSelectedType === null ? (
          <div className="space-y-3">
            <p className="text-[13px] text-[#888] font-['Manrope']">Select test type to view in <span className="font-semibold text-[#333] dark:text-gray-100">{selectedMod?.display} &rsaquo; {selectedVisSubModule === '__all__' ? 'All sub-modules' : selectedMod?.sub_modules.find(s => s.name === selectedVisSubModule)?.display}</span></p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {(['all', 'ui', 'api'] as const).filter(type => {
                if (type === 'all') return true
                const allTypes = new Set(selectedMod!.sub_modules.flatMap(s => s.tests.map(t => t.type || 'ui')))
                return allTypes.has(type)
              }).map(type => (
                <button
                  key={type}
                  onClick={() => { setVisSelectedType(type); setVisActionMode(null) }}
                  className="text-left bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5 hover:shadow-md hover:border-[#3F51B5]/40 dark:hover:border-[#7986CB]/40 transition-all cursor-pointer group"
                >
                  <div className="w-10 h-10 rounded-lg bg-[#E8EAF6] dark:bg-[#1A237E]/30 flex items-center justify-center mb-3 group-hover:bg-[#C5CAE9] dark:group-hover:bg-[#1A237E]/50 transition-colors">
                    {type === 'all' ? <List className="size-5 text-[#3F51B5]" /> : type === 'ui' ? <Monitor className="size-5 text-[#3F51B5]" /> : <Server className="size-5 text-[#3F51B5]" />}
                  </div>
                  <div className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100 group-hover:text-[#3F51B5] transition-colors">
                    {type === 'all' ? 'All Tests' : type === 'ui' ? 'UI Tests' : 'API Tests'}
                  </div>
                  <div className="text-[11px] text-[#888] font-['Manrope'] mt-1.5">
                    {type === 'all'
                      ? `${selectedModTests.length} tests total`
                      : `${selectedModTests.filter(t => (t.type || 'ui') === type).length} ${type.toUpperCase()} tests`
                    }
                  </div>
                </button>
              ))}
            </div>
          </div>
        ) : !selectedMod ? (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-8 border border-gray-100 dark:border-gray-700 text-center">
            <AlertTriangle className="size-10 text-orange-500 mx-auto mb-2" />
            <p className="text-sm text-[#888] dark:text-gray-400 font-['Manrope']">Module data not loaded. Sync from backend first.</p>
          </div>
        /* Step 4: Action mode selection */
        ) : visActionMode === null ? (
          <div className="space-y-3">
            <p className="text-[13px] text-[#888] font-['Manrope']">What would you like to do with <span className="font-semibold text-[#333] dark:text-gray-100">{selectedMod?.display} &rsaquo; {selectedVisSubModule === '__all__' ? 'All sub-modules' : selectedMod?.sub_modules.find(s => s.name === selectedVisSubModule)?.display} &rsaquo; {visSelectedType === 'all' ? 'All' : visSelectedType?.toUpperCase()} tests</span></p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <button
                onClick={() => setVisActionMode('name')}
                className="text-left bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5 hover:shadow-md hover:border-[#3F51B5]/40 dark:hover:border-[#7986CB]/40 transition-all cursor-pointer group"
              >
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-lg bg-[#E8EAF6] dark:bg-[#1A237E]/30 flex items-center justify-center shrink-0 group-hover:bg-[#C5CAE9] dark:group-hover:bg-[#1A237E]/50 transition-colors">
                    <Pencil className="size-5 text-[#3F51B5]" />
                  </div>
                  <div className="min-w-0">
                    <div className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100 group-hover:text-[#3F51B5] transition-colors">Change Name</div>
                    <p className="text-[12px] text-[#888] font-['Manrope'] mt-1 leading-relaxed">Rename display names of tests. Click any test card to edit.</p>
                    <div className="flex items-center gap-3 mt-2 text-[11px] font-['Manrope']">
                      <span className="text-[#888]">{selectedModTests.length} tests</span>
                      <span className="text-[#3F51B5] font-medium">{Object.keys(overrides).length} renamed</span>
                    </div>
                  </div>
                </div>
              </button>
              <button
                onClick={() => setVisActionMode('visibility')}
                className="text-left bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-5 hover:shadow-md hover:border-[#3F51B5]/40 dark:hover:border-[#7986CB]/40 transition-all cursor-pointer group"
              >
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-lg bg-[#E8EAF6] dark:bg-[#1A237E]/30 flex items-center justify-center shrink-0 group-hover:bg-[#C5CAE9] dark:group-hover:bg-[#1A237E]/50 transition-colors">
                    <Eye className="size-5 text-[#3F51B5]" />
                  </div>
                  <div className="min-w-0">
                    <div className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100 group-hover:text-[#3F51B5] transition-colors">Change Visibility</div>
                    <p className="text-[12px] text-[#888] font-['Manrope'] mt-1 leading-relaxed">Enable or disable tests and control per-user visibility.</p>
                    <div className="flex items-center gap-3 mt-2 text-[11px] font-['Manrope']">
                      <span className="text-[#888]">{selectedModTests.length} tests</span>
                      {totalDisabled > 0 && <span className="text-red-500 font-medium">{totalDisabled} disabled</span>}
                      {totalHidden > 0 && <span className="text-orange-500 font-medium">{totalHidden} hidden</span>}
                    </div>
                  </div>
                </div>
              </button>
            </div>
          </div>
        ) : !selectedMod ? (
          <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-8 border border-gray-100 dark:border-gray-700 text-center">
            <AlertTriangle className="size-10 text-orange-500 mx-auto mb-2" />
            <p className="text-sm text-[#888] dark:text-gray-400 font-['Manrope']">Module data not loaded. Sync from backend first.</p>
          </div>
        ) : visActionMode === 'name' ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between px-4 py-2.5 bg-gradient-to-r from-[#E8EAF6] to-transparent dark:from-[#1A237E]/20 dark:to-transparent rounded-xl border border-gray-100 dark:border-gray-700">
              <div className="flex items-center gap-3">
                <span className="text-sm font-semibold font-['Poppins'] text-[#3F51B5] dark:text-[#7986CB]">Rename Tests</span>
                <span className="text-[11px] text-[#888] font-['Manrope']">{selectedMod.display} &rsaquo; {visSelectedType === 'all' ? 'All' : visSelectedType?.toUpperCase()}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-[#888] font-['Manrope']">raw</span>
                <Switch checked={showRawNames} onCheckedChange={(val) => { setShowRawNames(val); localStorage.setItem('showRawNames', String(val)) }} className="shrink-0 scale-75" />
              </div>
            </div>

            {/* Sub-module sections — Name mode */}
            {activeSubModules.map(sub => {
              const filteredTests = sub.tests.filter(testMatches)
              if (filteredTests.length === 0) return null
              const subKey = `${selectedMod.name}::${sub.name}`

              return (
                <div key={subKey} className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
                  <div className="flex items-center gap-2 px-4 py-2.5 border-b border-gray-50 dark:border-gray-700/50 bg-gray-50/50 dark:bg-gray-800/50">
                    <Pencil className="size-3.5 text-[#888]" />
                    <span className="text-xs font-semibold font-['Manrope'] text-[#555] dark:text-gray-300">{sub.display}</span>
                    <span className="text-[11px] text-[#888] font-['Manrope']">— {filteredTests.length} test{filteredTests.length !== 1 ? 's' : ''}</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2.5 p-3">
                    {filteredTests.map(t => {
                      const ov = overrides[t.name]
                      const displayName = ov?.displayName || t.display_name || t.name.split('::').pop() || t.name
                      const testType = t.type || 'ui'
                      const cardKey = `${selectedMod.name}::${sub.name}::${t.name}`
                      const hasCustomName = ov?.displayName != null && ov.displayName !== t.display_name

                      return (
                        <button
                          key={cardKey}
                          onClick={() => { setVisDetailTest({ testName: t.name, displayName, testType, disabled: false, excluded: 0 }); setEditingNameValue(displayName); setVisDetailOpen(true) }}
                          className="text-left bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 hover:border-[#3F51B5]/40 dark:hover:border-[#7986CB]/40 hover:shadow-sm transition-all cursor-pointer group w-full"
                        >
                          <div className="flex items-start gap-2 px-3 pt-3 pb-2">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span className={`text-[13px] font-['Manrope'] leading-tight block truncate text-[#333] dark:text-gray-100 group-hover:text-[#3F51B5] transition-colors ${hasCustomName ? 'font-semibold' : ''}`}>
                                  {displayName}
                                </span>
                                {hasCustomName && (
                                  <Badge variant="outline" className="text-[9px] px-1.5 py-0 h-4 border-[#3F51B5]/30 text-[#3F51B5] dark:text-[#7986CB] shrink-0 font-['Manrope']">edited</Badge>
                                )}
                              </div>
                              <div className="flex items-center gap-1.5 mt-1.5">
                                <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${
                                  testType === 'api'
                                    ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
                                    : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                                }`}>{testType.toUpperCase()}</span>
                              </div>
                            </div>
                          </div>
                          {showRawNames && (
                            <div className="px-3 pb-2.5">
                              <div className="text-[10px] font-mono text-[#999] dark:text-gray-500 truncate leading-relaxed" title={t.name}>{t.name}</div>
                            </div>
                          )}
                        </button>
                      )
                    })}
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center justify-between px-4 py-2.5 bg-gradient-to-r from-[#E8EAF6] to-transparent dark:from-[#1A237E]/20 dark:to-transparent rounded-xl border border-gray-100 dark:border-gray-700">
              <div className="flex items-center gap-3">
                <span className="text-sm font-semibold font-['Poppins'] text-[#3F51B5] dark:text-[#7986CB]">{selectedMod.display}</span>
                <span className="text-[11px] text-[#888] font-['Manrope']">{selectedModTests.length} test{selectedModTests.length !== 1 ? 's' : ''}</span>
                {selectedModTests.filter(t => overrides[t.name]?.disabled).length > 0 && (
                  <span className="text-[11px] text-red-500 font-medium font-['Manrope']">{selectedModTests.filter(t => overrides[t.name]?.disabled).length} disabled</span>
                )}
                {selectedModTests.filter(t => (exclusionCounts[t.name] || 0) > 0).length > 0 && (
                  <span className="text-[11px] text-orange-500 font-medium font-['Manrope']">{selectedModTests.filter(t => (exclusionCounts[t.name] || 0) > 0).length} hidden</span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] text-[#888] font-['Manrope']">Toggle all</span>
                <Switch
                  checked={!allSelectedDisabled}
                  onCheckedChange={() => {
                    batchUpdate(selectedModTests.map(t => ({ testName: t.name, disabled: !allSelectedDisabled })))
                  }}
                  disabled={batchActionLoading}
                  className="shrink-0 scale-75"
                />
              </div>
            </div>

            {/* Sub-module sections — Visibility mode */}
            {activeSubModules.map(sub => {
              const filteredTests = sub.tests.filter(testMatches)
              if (filteredTests.length === 0) return null
              const subKey = `${selectedMod.name}::${sub.name}`
              const subDisabled = filteredTests.filter(t => overrides[t.name]?.disabled).length
              const subHidden = filteredTests.filter(t => (exclusionCounts[t.name] || 0) > 0).length
              const subAllSelected = filteredTests.every(t => visSelectedTests.has(t.name))
              const subSomeSelected = filteredTests.some(t => visSelectedTests.has(t.name))

              return (
                <div key={subKey} className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
                  <div className="flex items-center gap-2 px-4 py-2.5 border-b border-gray-50 dark:border-gray-700/50 bg-gray-50/50 dark:bg-gray-800/50">
                    <button
                      onClick={() => setVisCollapsedSubs(prev => { const n = new Set(prev); if (n.has(subKey)) n.delete(subKey); else n.add(subKey); return n })}
                      className="p-0.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      <ChevronRight className={`size-3.5 text-[#888] dark:text-gray-400 transition-transform ${visCollapsedSubs.has(subKey) ? '' : 'rotate-90'}`} />
                    </button>
                    <Checkbox
                      checked={subAllSelected}
                      indeterminate={subSomeSelected && !subAllSelected ? true : undefined}
                      onCheckedChange={() => {
                        if (subAllSelected) {
                          setVisSelectedTests(prev => { const n = new Set(prev); filteredTests.forEach(t => n.delete(t.name)); return n })
                        } else {
                          setVisSelectedTests(prev => { const n = new Set(prev); filteredTests.forEach(t => n.add(t.name)); return n })
                        }
                      }}
                      className="shrink-0"
                    />
                    <span className="text-xs font-semibold font-['Manrope'] text-[#555] dark:text-gray-300">{sub.display}</span>
                    <span className="text-[11px] text-[#888] font-['Manrope']">— {filteredTests.length} test{filteredTests.length !== 1 ? 's' : ''}</span>
                    {subDisabled > 0 && <span className="text-[11px] text-red-500 font-medium font-['Manrope']">{subDisabled} off</span>}
                    {subHidden > 0 && <span className="text-[11px] text-orange-500 font-medium font-['Manrope']">{subHidden} hid</span>}
                  </div>

                  {/* Visibility cards */}
                  {!visCollapsedSubs.has(subKey) && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2 p-3">
                      {filteredTests.map(t => {
                        const ov = overrides[t.name]
                        const displayName = ov?.displayName || t.display_name || t.name.split('::').pop() || t.name
                        const disabled = ov?.disabled ?? false
                        const excluded = exclusionCounts[t.name] || 0
                        const testType = t.type || 'ui'
                        const cardKey = `${selectedMod.name}::${sub.name}::${t.name}`

                        return (
                          <div
                            key={cardKey}
                            className={`relative bg-white dark:bg-gray-800 rounded-xl border transition-all cursor-pointer ${
                              visSelectedTests.has(t.name)
                                ? 'border-[#3F51B5]/50 dark:border-[#7986CB]/50 shadow-sm ring-1 ring-[#3F51B5]/20 dark:ring-[#7986CB]/20'
                                : 'border-gray-100 dark:border-gray-700 hover:border-[#3F51B5]/40 dark:hover:border-[#7986CB]/40 hover:shadow-sm'
                            } ${disabled ? 'opacity-60' : ''}`}
                            onClick={() => { setVisDetailTest({ testName: t.name, displayName, testType, disabled, excluded }); setVisDetailOpen(true) }}
                          >
                            <div className="flex items-start gap-2 px-3 pt-3 pb-2">
                              <Checkbox
                                checked={visSelectedTests.has(t.name)}
                                onCheckedChange={() => toggleTestSelection(t.name)}
                                onClick={e => e.stopPropagation()}
                                className="mt-0.5 shrink-0"
                              />
                              <div className="flex-1 min-w-0">
                                <span className="text-[13px] font-['Manrope'] leading-tight block truncate text-[#333] dark:text-gray-100">{displayName}</span>
                                <div className="flex items-center gap-1.5 mt-1.5">
                                  <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${
                                    testType === 'api'
                                      ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
                                      : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                                  }`}>{testType.toUpperCase()}</span>
                                  {disabled && (
                                    <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-300">Off</span>
                                  )}
                                  {excluded > 0 && (
                                    <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-orange-100 text-orange-600 dark:bg-orange-900/30 dark:text-orange-300 flex items-center gap-1"><EyeOff className="size-3" />{excluded}</span>
                                  )}
                                </div>
                              </div>
                            </div>
                            <div className="px-3 pb-2.5">
                              <div className="text-[10px] font-mono text-[#999] dark:text-gray-500 truncate leading-relaxed" title={t.name}>{t.name}</div>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}

        {/* Batch action bar — visibility mode only */}
        {visSelectedTests.size > 0 && selectedVisModule && selectedMod && visActionMode === 'visibility' && (
          <div className="sticky bottom-4 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-300 dark:border-gray-500/70 px-4 py-3 flex items-center justify-between z-10 backdrop-blur-sm bg-white/95 dark:bg-gray-800/95">
            <span className="text-sm font-semibold font-['Manrope'] text-[#333] dark:text-gray-100">{visSelectedTests.size} test{visSelectedTests.size !== 1 ? 's' : ''} selected</span>
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="outline"
                disabled={batchActionLoading}
                onClick={() => batchUpdate(Array.from(visSelectedTests).map(n => ({ testName: n, disabled: true })))}
                className="h-8 text-xs font-['Roboto']"
              >
                {batchActionLoading ? <Loader2 className="size-3 animate-spin mr-1" /> : <XCircle className="size-3 mr-1" />}
                Disable
              </Button>
              <Button
                size="sm"
                variant="outline"
                disabled={batchActionLoading}
                onClick={() => batchUpdate(Array.from(visSelectedTests).map(n => ({ testName: n, disabled: false })))}
                className="h-8 text-xs font-['Roboto']"
              >
                {batchActionLoading ? <Loader2 className="size-3 animate-spin mr-1" /> : <CheckCircle2 className="size-3 mr-1" />}
                Enable
              </Button>
              <Button
                size="sm"
                variant="outline"
                disabled={batchActionLoading}
                onClick={() => batchUpdate(Array.from(visSelectedTests).map(n => ({ testName: n, displayName: null, disabled: false })))}
                className="h-8 text-xs text-red-600 font-['Roboto']"
              >
                <RotateCcw className="size-3 mr-1" />
                Reset
              </Button>
              <Button
                size="sm"
                variant="default"
                className="h-8 text-xs bg-[#2D3FC7] hover:bg-[#3F51B5] font-['Roboto']"
                onClick={() => {
                  const first = selectedModTests.find(t => t.name === Array.from(visSelectedTests)[0])
                  setVisibilityDialogTest({ testName: Array.from(visSelectedTests)[0], displayName: first ? (overrides[first.name]?.displayName || first.display_name) : '' })
                  setVisibilityDialogOpen(true)
                }}
              >
                <EyeOff className="size-3 mr-1" />
                Hide for Users
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setVisSelectedTests(new Set())}
                className="h-8 text-xs font-['Roboto'] text-[#888]"
              >
                Clear
              </Button>
            </div>
          </div>
        )}

        <TestUserVisibilityDialog
          open={visibilityDialogOpen}
          onOpenChange={setVisibilityDialogOpen}
          testName={visibilityDialogTest?.testName || ''}
          testDisplayName={visibilityDialogTest?.displayName || ''}
          onSave={(userIds) => {
            if (visibilityDialogTest) saveExclusions(visibilityDialogTest.testName, userIds)
          }}
        />

        {/* Detail dialog */}
        <Dialog open={visDetailOpen} onOpenChange={setVisDetailOpen}>
          <DialogContent className="sm:max-w-[440px]">
            <DialogHeader>
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-[#E8EAF6] dark:bg-[#1A237E]/30 flex items-center justify-center">
                  {visActionMode === 'name' ? <Pencil className="size-4 text-[#3F51B5]" /> : <Eye className="size-4 text-[#3F51B5]" />}
                </div>
                <div>
                  <DialogTitle className="font-['Poppins'] text-[#333] dark:text-gray-100 text-base">
                    {visActionMode === 'name' ? 'Rename Test' : 'Test Visibility'}
                  </DialogTitle>
                  <p className="text-[11px] font-['Manrope'] text-[#888] mt-0.5 font-mono truncate max-w-[360px]">{visDetailTest?.testName || ''}</p>
                </div>
              </div>
            </DialogHeader>

            {visActionMode === 'name' && visDetailTest && (
              <div className="space-y-4 py-1">
                <div>
                  <label className="text-xs font-medium font-['Manrope'] text-[#555] dark:text-gray-300 mb-1.5 block">Display Name</label>
                  <div className="relative">
                    <Input
                      value={editingNameValue}
                      onChange={e => setEditingNameValue(e.target.value)}
                      onKeyDown={e => { if (e.key === 'Enter') handleDetailRename(); if (e.key === 'Escape') setVisDetailOpen(false) }}
                      className="h-10 text-[13px] font-['Manrope'] pr-20"
                      autoFocus
                      placeholder="Enter display name..."
                    />
                    <div className="absolute right-2 top-1/2 -translate-y-1/2">
                      <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${
                        visDetailTest.testType === 'api'
                          ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
                          : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                      }`}>{visDetailTest.testType.toUpperCase()}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2 pt-1">
                  <Button
                    onClick={handleDetailRename}
                    className="h-9 text-xs bg-[#2D3FC7] hover:bg-[#3F51B5] font-['Roboto'] flex-1"
                  >
                    <Save className="size-3.5 mr-1.5" />
                    Save Name
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => { saveOverride(visDetailTest.testName, { displayName: null }); setVisDetailOpen(false) }}
                    className="h-9 text-xs font-['Roboto'] text-red-600 flex-1"
                  >
                    <RotateCcw className="size-3 mr-1.5" />
                    Revert
                  </Button>
                </div>
              </div>
            )}

            {visActionMode === 'visibility' && visDetailTest && (
              <div className="space-y-3 py-1">
                <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3 flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className={`w-2 h-2 rounded-full ${visDetailTest.disabled ? 'bg-red-400' : 'bg-green-400'}`} />
                    <span className="text-sm font-['Manrope'] text-[#333] dark:text-gray-100">Test Status</span>
                  </div>
                  <div className="flex items-center gap-2.5">
                    <Switch
                      checked={!visDetailTest.disabled}
                      onCheckedChange={v => { saveOverride(visDetailTest.testName, { disabled: !v }); setVisDetailTest(prev => prev ? { ...prev, disabled: !v } : null) }}
                    />
                    <span className={`text-xs font-medium font-['Manrope'] ${visDetailTest.disabled ? 'text-red-500' : 'text-green-600'}`}>
                      {visDetailTest.disabled ? 'Disabled' : 'Enabled'}
                    </span>
                  </div>
                </div>

                <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <EyeOff className="size-3.5 text-[#888]" />
                      <span className="text-xs font-['Manrope'] text-[#555] dark:text-gray-300">Hidden from users</span>
                    </div>
                    <span className="text-xs font-semibold font-['Manrope'] text-orange-600">{visDetailTest.excluded} user{visDetailTest.excluded !== 1 ? 's' : ''}</span>
                  </div>
                  <Button
                    variant="outline"
                    onClick={() => { setVisibilityDialogTest({ testName: visDetailTest.testName, displayName: visDetailTest.displayName }); setVisibilityDialogOpen(true) }}
                    className="w-full h-8 text-xs font-['Roboto'] justify-center"
                  >
                    <EyeOff className="size-3 mr-1.5" />
                    {visDetailTest.excluded > 0 ? 'Manage Hidden Users' : 'Hide from Users'}
                  </Button>
                </div>

                <Button
                  variant="outline"
                  onClick={() => { saveOverride(visDetailTest.testName, { displayName: null, disabled: false }); setVisDetailOpen(false) }}
                  className="w-full h-9 text-xs font-['Roboto'] text-red-600 justify-center"
                >
                  <RotateCcw className="size-3.5 mr-1.5" />
                  Revert to Defaults
                </Button>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    )
  }

  // 3. Modules
  const renderModules = () => {
    const parents = modules.filter(m => !m.parentId)
    const getChildren = (parentId: string) => modules.filter(m => m.parentId === parentId)
    const activeCount = modules.filter(m => m.status === 'active').length
    const draftCount = modules.filter(m => m.status === 'draft').length
    const disabledCount = modules.filter(m => m.status === 'disabled').length

    const statusBadge = (status: string) => {
      if (status === 'active') return 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300'
      if (status === 'draft') return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300'
      return 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300'
    }

    return (
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <h2 className="text-xl font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">Modules</h2>
          <div className="flex gap-2">
            <Button onClick={handleSeedModules}
              className="bg-[#00897B] hover:bg-[#00695C] text-white font-['Roboto'] text-xs h-8">
              <Database className="size-3.5 mr-1" /> Seed Defaults
            </Button>
            <Button onClick={() => { setEditingModule(null); setModuleDialogOpen(true) }}
              className="bg-[#2D3FC7] hover:bg-[#3F51B5] text-white font-['Roboto'] text-xs h-8">
              <Plus className="size-3.5 mr-1" /> Add Module
            </Button>
          </div>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700 flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-green-100 dark:bg-green-900/40">
              <CheckCircle2 className="size-4 text-green-700 dark:text-green-300" />
            </div>
            <div>
              <p className="text-lg font-bold font-['Poppins'] text-[#333] dark:text-gray-100">{activeCount}</p>
              <p className="text-[10px] text-[#888] dark:text-gray-400 font-['Manrope']">Active</p>
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700 flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-yellow-100 dark:bg-yellow-900/40">
              <Clock className="size-4 text-yellow-700 dark:text-yellow-300" />
            </div>
            <div>
              <p className="text-lg font-bold font-['Poppins'] text-[#333] dark:text-gray-100">{draftCount}</p>
              <p className="text-[10px] text-[#888] dark:text-gray-400 font-['Manrope']">Draft</p>
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700 flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-red-100 dark:bg-red-900/40">
              <XCircle className="size-4 text-red-700 dark:text-red-300" />
            </div>
            <div>
              <p className="text-lg font-bold font-['Poppins'] text-[#333] dark:text-gray-100">{disabledCount}</p>
              <p className="text-[10px] text-[#888] dark:text-gray-400 font-['Manrope']">Disabled</p>
            </div>
          </div>
        </div>

        {!modulesLoaded ? (
          <div className="flex justify-center py-12"><Loader2 className="size-6 animate-spin text-[#3F51B5]" /></div>
        ) : modules.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-12 border border-gray-100 dark:border-gray-700 text-center">
            <FolderTree className="size-10 text-[#888] dark:text-gray-500 mx-auto mb-2" />
            <p className="text-sm text-[#888] dark:text-gray-400 font-['Manrope']">No modules configured</p>
            <p className="text-xs text-[#888] dark:text-gray-400 font-['Manrope'] mt-1">Click &quot;Seed Defaults&quot; to create default modules, or add one manually.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {parents.map(parent => {
              const children = getChildren(parent.id)
              return (
                <div key={parent.id} className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
                  <div className="flex items-center gap-3 p-4 bg-[#E8EAF6] dark:bg-[#1A237E]/30">
                    <FolderTree className="size-4 text-[#3F51B5]" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold font-['Poppins'] text-[#3F51B5] dark:text-[#7986CB]">{parent.label}</span>
                        <Badge className={`text-[9px] border-0 ${statusBadge(parent.status)}`}>{parent.status}</Badge>
                      </div>
                      {parent.description && <p className="text-[10px] text-[#888] dark:text-gray-400 font-['Manrope'] mt-0.5 truncate">{parent.description}</p>}
                    </div>
                    <Badge variant="outline" className="text-[10px]">{parent.testCount} tests</Badge>
                    <div className="flex gap-1">
                      <Button size="sm" variant="ghost" className="size-7 p-0" onClick={() => handleToggleModuleStatus(parent)} title="Toggle status">
                        {parent.status === 'active' ? <CheckCircle2 className="size-3 text-green-600" /> : parent.status === 'draft' ? <Clock className="size-3 text-yellow-600" /> : <XCircle className="size-3 text-red-600" />}
                      </Button>
                      <Button size="sm" variant="ghost" className="size-7 p-0" onClick={() => { setEditingModule(parent); setModuleDialogOpen(true) }}>
                        <Pencil className="size-3 text-[#3F51B5]" />
                      </Button>
                      <Button size="sm" variant="ghost" className="size-7 p-0" onClick={() => { setDeleteTarget({ type: 'module', id: parent.id, label: parent.label }); setDeleteDialogOpen(true) }}>
                        <Trash2 className="size-3 text-[#F44336]" />
                      </Button>
                    </div>
                  </div>
                  {children.length > 0 && (
                    <div className="divide-y divide-gray-50 dark:divide-gray-700/50">
                      {children.map(child => (
                        <div key={child.id} className="flex items-center gap-3 px-4 py-2.5 ml-6 border-l-2 border-[#3F51B5]/20 dark:border-[#7986CB]/20">
                          <ChevronRight className="size-3 text-[#888] dark:text-gray-400" />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-['Manrope'] text-[#333] dark:text-gray-100">{child.label}</span>
                              <Badge className={`text-[8px] border-0 px-1 py-0 ${statusBadge(child.status)}`}>{child.status}</Badge>
                            </div>
                            {child.description && <p className="text-[10px] text-[#888] dark:text-gray-400 font-['Manrope'] truncate">{child.description}</p>}
                          </div>
                          <Badge variant="outline" className="text-[9px]">{child.testCount} tests</Badge>
                          <div className="flex gap-1">
                            <Button size="sm" variant="ghost" className="size-6 p-0" onClick={() => handleToggleModuleStatus(child)} title="Toggle status">
                              {child.status === 'active' ? <CheckCircle2 className="size-3 text-green-600" /> : child.status === 'draft' ? <Clock className="size-3 text-yellow-600" /> : <XCircle className="size-3 text-red-600" />}
                            </Button>
                            <Button size="sm" variant="ghost" className="size-6 p-0" onClick={() => { setEditingModule(child); setModuleDialogOpen(true) }}>
                              <Pencil className="size-3 text-[#3F51B5]" />
                            </Button>
                            <Button size="sm" variant="ghost" className="size-6 p-0" onClick={() => { setDeleteTarget({ type: 'module', id: child.id, label: child.label }); setDeleteDialogOpen(true) }}>
                              <Trash2 className="size-3 text-[#F44336]" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
            {/* Orphan children (no parent found) */}
            {modules.filter(m => m.parentId && !modules.find(p => p.id === m.parentId)).length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
                <div className="flex items-center gap-3 p-4 bg-orange-50 dark:bg-orange-900/20">
                  <AlertTriangle className="size-4 text-orange-600" />
                  <span className="text-sm font-semibold font-['Poppins'] text-orange-700 dark:text-orange-300">Orphaned Modules</span>
                </div>
                <div className="divide-y divide-gray-50 dark:divide-gray-700/50">
                  {modules.filter(m => m.parentId && !modules.find(p => p.id === m.parentId)).map(child => (
                    <div key={child.id} className="flex items-center gap-3 px-4 py-2.5">
                      <ChevronRight className="size-3 text-[#888] dark:text-gray-400" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-['Manrope'] text-[#333] dark:text-gray-100">{child.label}</span>
                          <Badge className={`text-[8px] border-0 px-1 py-0 ${statusBadge(child.status)}`}>{child.status}</Badge>
                        </div>
                      </div>
                      <div className="flex gap-1">
                        <Button size="sm" variant="ghost" className="size-6 p-0" onClick={() => { setEditingModule(child); setModuleDialogOpen(true) }}>
                          <Pencil className="size-3 text-[#3F51B5]" />
                        </Button>
                        <Button size="sm" variant="ghost" className="size-6 p-0" onClick={() => { setDeleteTarget({ type: 'module', id: child.id, label: child.label }); setDeleteDialogOpen(true) }}>
                          <Trash2 className="size-3 text-[#F44336]" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    )
  }

  // 4. Bug Reports
  const renderBugReports = () => {
    const filteredByStatus = bugStatusFilter === 'all' ? bugReports : bugReports.filter(b => b.status === bugStatusFilter)
    const filtered = filteredByStatus.filter(b => {
      const ms = !bugSearch || b.testDescription.toLowerCase().includes(bugSearch.toLowerCase()) || b.error.toLowerCase().includes(bugSearch.toLowerCase()) || b.id.toLowerCase().includes(bugSearch.toLowerCase()) || b.reporterName.toLowerCase().includes(bugSearch.toLowerCase())
      const mm = bugModuleFilter === 'all' || b.moduleName.toLowerCase().replace(/\s+/g, '-') === bugModuleFilter || b.moduleName === bugModuleFilter
      const mp = bugPriorityFilter === 'all' || b.priority === bugPriorityFilter
      return ms && mm && mp
    })
    const uniqueBugModules = [...new Set(bugReports.map(b => b.moduleName))].sort()
    const tabs = [
      { id: 'all', label: 'All', count: bugReports.length },
      { id: 'open', label: 'Open', count: bugReports.filter(b => b.status === 'open').length },
      { id: 'in-progress', label: 'In Progress', count: bugReports.filter(b => b.status === 'in-progress').length },
      { id: 'fixed', label: 'Fixed', count: bugReports.filter(b => b.status === 'fixed').length },
      { id: 'closed', label: 'Closed', count: bugReports.filter(b => b.status === 'closed').length },
      { id: 'rejected', label: 'Rejected', count: bugReports.filter(b => b.status === 'rejected').length },
    ]

    const statusConfig: Record<string, { bg: string; text: string; dot: string }> = {
      open: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-300', dot: 'bg-red-500' },
      'in-progress': { bg: 'bg-yellow-100 dark:bg-yellow-900/30', text: 'text-yellow-700 dark:text-yellow-300', dot: 'bg-yellow-500' },
      fixed: { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-300', dot: 'bg-green-500' },
      closed: { bg: 'bg-gray-100 dark:bg-gray-700', text: 'text-gray-600 dark:text-gray-400', dot: 'bg-gray-400' },
      rejected: { bg: 'bg-orange-100 dark:bg-orange-900/30', text: 'text-orange-700 dark:text-orange-300', dot: 'bg-orange-500' },
    }

    const priorityStyles: Record<string, string> = {
      high: 'border-l-red-400',
      medium: 'border-l-yellow-400',
      low: 'border-l-blue-400',
    }

    return (
      <>
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <h2 className="text-xl font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">Bug Reports</h2>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-[#888]" />
              <Input placeholder="Search bugs..." value={bugSearch} onChange={e => setBugSearch(e.target.value)}
                className="h-8 pl-8 pr-3 text-xs font-['Manrope'] w-48" />
            </div>
            <Select value={bugModuleFilter} onValueChange={setBugModuleFilter}>
              <SelectTrigger className="h-8 text-xs w-32"><SelectValue placeholder="Module" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all" className="text-xs">All Modules</SelectItem>
                {uniqueBugModules.map(m => <SelectItem key={m} value={m} className="text-xs">{m}</SelectItem>)}
              </SelectContent>
            </Select>
            <Select value={bugPriorityFilter} onValueChange={setBugPriorityFilter}>
              <SelectTrigger className="h-8 text-xs w-28"><SelectValue placeholder="Priority" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all" className="text-xs">All</SelectItem>
                <SelectItem value="high" className="text-xs">High</SelectItem>
                <SelectItem value="medium" className="text-xs">Medium</SelectItem>
                <SelectItem value="low" className="text-xs">Low</SelectItem>
              </SelectContent>
            </Select>
            {(bugSearch || bugModuleFilter !== 'all' || bugPriorityFilter !== 'all') && (
              <Button variant="ghost" size="sm" className="h-8 text-xs text-[#888]" onClick={() => { setBugSearch(''); setBugModuleFilter('all'); setBugPriorityFilter('all') }}>
                <RotateCcw className="size-3 mr-1" /> Clear
              </Button>
            )}
          </div>
        </div>

        {/* Status tabs */}
        <div className="flex gap-1.5 flex-wrap bg-gray-50 dark:bg-gray-800/50 rounded-xl p-1 border border-gray-100 dark:border-gray-700/50">
          {tabs.map(tab => (
            <button key={tab.id} onClick={() => setBugStatusFilter(tab.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-['Manrope'] font-medium transition-all cursor-pointer ${
                bugStatusFilter === tab.id
                  ? 'bg-white dark:bg-gray-700 text-[#3F51B5] dark:text-[#7986CB] shadow-sm'
                  : 'text-[#888] dark:text-gray-400 hover:text-[#333] dark:hover:text-gray-100'
              }`}>
              {tab.label}
              <span className={`ml-1.5 ${bugStatusFilter === tab.id ? 'text-[#3F51B5] dark:text-[#7986CB]' : 'text-[#aaa]'}`}>({tab.count})</span>
            </button>
          ))}
        </div>

        {!bugsLoaded ? (
          <div className="flex justify-center py-12"><Loader2 className="size-6 animate-spin text-[#3F51B5]" /></div>
        ) : filtered.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-12 border border-gray-100 dark:border-gray-700 text-center">
            <Inbox className="size-10 text-[#888] dark:text-gray-500 mx-auto mb-2" />
            <p className="text-sm text-[#888] dark:text-gray-400 font-['Manrope']">No bug reports found</p>
          </div>
        ) : (
          <div className="space-y-2.5">
            {filtered.map(bug => {
              const sla = getSLAStatus(bug.priority, bug.createdAt, bug.status)
              const sc = statusConfig[bug.status] || statusConfig.open
              return (
                <div key={bug.id} className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
                  <button onClick={() => { setExpandedBug(bug.id); if (!bug.readByAdmin) handleMarkBugRead(bug.id) }}
                    className="w-full flex items-start gap-3 p-4 text-left cursor-pointer transition-colors hover:bg-gray-50/50 dark:hover:bg-gray-700/30">
                    <div className={`w-1 self-stretch rounded-full shrink-0 ${priorityStyles[bug.priority] || 'border-l-gray-300 border-l-2'}`} />
                    {!bug.readByAdmin && <span className="w-2 h-2 rounded-full bg-[#3F51B5] shrink-0 mt-1.5" />}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2.5 flex-wrap">
                        <span className="text-[11px] font-mono font-semibold text-[#3F51B5] dark:text-[#7986CB]">#{bug.id.slice(0, 8).toUpperCase()}</span>
                        <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${sc.bg} ${sc.text}`}>{bug.status}</span>
                        <span className={`text-[10px] font-medium ${bug.priority === 'high' ? 'text-red-600' : bug.priority === 'medium' ? 'text-yellow-600' : 'text-blue-600'}`}>{bug.priority}</span>
                        <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${sla.color || 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'}`}>{sla.label}</span>
                      </div>
                      <p className="text-sm font-['Manrope'] font-medium text-[#333] dark:text-gray-100 mt-1.5 leading-snug line-clamp-2">{bug.testDescription}</p>
                      <div className="flex items-center gap-3 mt-1.5 text-[11px] text-[#888] font-['Manrope']">
                        <span className="flex items-center gap-1"><FolderTree className="size-3" />{bug.moduleName}</span>
                        <span>·</span>
                        <span className="flex items-center gap-1"><UsersIcon className="size-3" />{bug.reporterName}</span>
                        <span>·</span>
                        <span className="flex items-center gap-1"><Clock className="size-3" />{sla.remaining}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      {bug.replies.length > 0 && (
                        <span className="text-[10px] text-[#888] font-['Manrope'] flex items-center gap-1">
                          <Send className="size-3" />{bug.replies.length}
                        </span>
                      )}
                      <ChevronRight className="size-4 text-[#aaa]" />
                    </div>
                  </button>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Bug detail dialog */}
      <Dialog open={expandedBug !== null} onOpenChange={(open) => { if (!open) { setExpandedBug(null); setPendingBugStatus(prev => { const n = { ...prev }; if (expandedBug) delete n[expandedBug]; return n }) }}}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
          {(() => {
            const bug = bugReports.find(b => b.id === expandedBug)
            if (!bug) return null
            const sla = getSLAStatus(bug.priority, bug.createdAt, bug.status)
            const sc = statusConfig[bug.status] || statusConfig.open
            return (
              <div className="font-['Manrope']">
                {/* Header */}
                <div className="flex items-start justify-between gap-4 mb-5">
                  <div>
                    <div className="flex items-center gap-2.5 mb-1">
                      <span className="text-lg font-mono font-bold text-[#3F51B5] dark:text-[#7986CB]">#{bug.id.slice(0, 8).toUpperCase()}</span>
                      <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${sc.bg} ${sc.text}`}>{bug.status}</span>
                      <span className={`text-[11px] font-medium ${bug.priority === 'high' ? 'text-red-600' : bug.priority === 'medium' ? 'text-yellow-600' : 'text-blue-600'}`}>{bug.priority}</span>
                      <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${sla.color || 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'}`}>{sla.label}</span>
                    </div>
                    <p className="text-sm font-semibold text-[#333] dark:text-gray-100">{bug.testDescription}</p>
                    <div className="flex items-center gap-3 mt-1.5 text-xs text-[#888]">
                      <span className="flex items-center gap-1"><FolderTree className="size-3.5" />{bug.moduleName}</span>
                      <span>·</span>
                      <span className="flex items-center gap-1"><UsersIcon className="size-3.5" />{bug.reporterName}</span>
                      <span>·</span>
                      <span className="flex items-center gap-1"><Clock className="size-3.5" />{sla.remaining}</span>
                    </div>
                  </div>
                </div>

                {/* Detail grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-px bg-gray-200 dark:bg-gray-700 rounded-lg overflow-hidden mb-5">
                  <div className="bg-gray-50 dark:bg-gray-800/50 px-4 py-3">
                    <span className="text-[10px] text-[#888] uppercase tracking-wider font-medium">Test ID</span>
                    <p className="text-xs text-[#333] dark:text-gray-100 mt-0.5 font-mono">{bug.testId}</p>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-800/50 px-4 py-3">
                    <span className="text-[10px] text-[#888] uppercase tracking-wider font-medium">Reported by</span>
                    <p className="text-xs text-[#333] dark:text-gray-100 mt-0.5">{bug.reporterName}</p>
                  </div>
                  <div className="sm:col-span-2 bg-gray-50 dark:bg-gray-800/50 px-4 py-3">
                    <span className="text-[10px] text-[#888] uppercase tracking-wider font-medium">Error Message</span>
                    <p className="text-xs text-red-600 dark:text-red-400 mt-0.5 font-mono leading-relaxed">{bug.error}</p>
                  </div>
                  {bug.userNote && (
                    <div className="sm:col-span-2 bg-gray-50 dark:bg-gray-800/50 px-4 py-3">
                      <span className="text-[10px] text-[#888] uppercase tracking-wider font-medium">User Note</span>
                      <p className="text-xs text-[#333] dark:text-gray-100 mt-0.5">{bug.userNote}</p>
                    </div>
                  )}
                </div>

                {/* Status change */}
                <div className="mb-5">
                  <span className="text-xs text-[#888] font-semibold uppercase tracking-wider block mb-2">Change Status</span>
                  <div className="flex items-center gap-2 flex-wrap">
                    {(['open', 'in-progress', 'fixed', 'closed', 'rejected'] as const).map(s => {
                      const isCurrent = bug.status === s
                      const isPending = pendingBugStatus[bug.id] === s
                      const colors = statusConfig[s]
                      return (
                        <button key={s} onClick={() => { if (s !== bug.status) setPendingBugStatus(prev => ({ ...prev, [bug.id]: s })) }}
                          className={`text-xs font-['Manrope'] px-3 py-1.5 rounded-lg border transition-all cursor-pointer ${
                            isCurrent
                              ? `${colors.bg} ${colors.text} border-transparent font-semibold`
                              : isPending
                                ? 'border-[#3F51B5] ring-1 ring-[#3F51B5] text-[#3F51B5] dark:text-[#7986CB] font-semibold'
                                : 'border-gray-200 dark:border-gray-600 text-[#888] dark:text-gray-400 hover:border-[#3F51B5]/40 hover:text-[#3F51B5]'
                          }`}>
                          {s.charAt(0).toUpperCase() + s.slice(1).replace('-', ' ')}
                        </button>
                      )
                    })}
                  </div>
                  {pendingBugStatus[bug.id] && pendingBugStatus[bug.id] !== bug.status && (
                    <div className="flex items-center gap-2 mt-3 pt-3 border-t border-gray-100 dark:border-gray-700/50">
                      <button onClick={() => {
                        handleBugStatusChange(bug.id, pendingBugStatus[bug.id] as BugReport['status'])
                        setPendingBugStatus(prev => { const n = { ...prev }; delete n[bug.id]; return n })
                      }}
                        className="text-xs font-['Manrope'] px-4 py-1.5 rounded-lg bg-[#3F51B5] text-white hover:bg-[#2D3FC7] font-medium transition-colors">
                        <Check className="size-3.5 inline mr-1.5" />Confirm & Update
                      </button>
                      <button onClick={() => setPendingBugStatus(prev => { const n = { ...prev }; delete n[bug.id]; return n })}
                        className="text-xs font-['Manrope'] px-3 py-1.5 rounded-lg text-[#888] hover:text-[#555] hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                        Cancel
                      </button>
                      <span className="text-[10px] text-[#aaa]">Status will change from <strong>{bug.status}</strong> to <strong>{pendingBugStatus[bug.id]}</strong></span>
                    </div>
                  )}
                </div>

                {/* Discussion */}
                <div>
                  <span className="text-xs text-[#888] font-semibold uppercase tracking-wider block mb-3">Discussion ({bug.replies.length})</span>
                  {bug.replies.length > 0 && (
                    <div className="space-y-3 max-h-60 overflow-y-auto mb-3 pr-1">
                      {bug.replies.map(r => (
                        <div key={r.id} className={`flex gap-3 ${r.authorRole === 'admin' ? 'justify-end' : 'justify-start'}`}>
                          {r.authorRole !== 'admin' && (
                            <div className="w-8 h-8 rounded-full bg-[#E8EAF6] dark:bg-[#1A237E]/30 flex items-center justify-center shrink-0">
                              <span className="text-xs font-semibold text-[#3F51B5]">{r.authorName.charAt(0).toUpperCase()}</span>
                            </div>
                          )}
                          <div className={`max-w-[75%] rounded-xl px-3.5 py-2.5 text-sm font-['Manrope'] ${
                            r.authorRole === 'admin'
                              ? 'bg-[#3F51B5] text-white rounded-br-sm'
                              : 'bg-gray-100 dark:bg-gray-700 text-[#333] dark:text-gray-100 rounded-bl-sm'
                          }`}>
                            <div className="flex items-center gap-2 mb-0.5">
                              <span className={`text-xs font-semibold ${r.authorRole === 'admin' ? 'text-white/80' : 'text-[#555] dark:text-gray-300'}`}>{r.authorName}</span>
                              <span className={`text-[10px] ${r.authorRole === 'admin' ? 'text-white/60' : 'text-[#888]'}`}>{r.authorRole}</span>
                            </div>
                            <p className={r.authorRole === 'admin' ? 'text-white/90 leading-relaxed' : 'leading-relaxed'}>{r.message}</p>
                            <p className={`text-[10px] mt-1 ${r.authorRole === 'admin' ? 'text-white/50' : 'text-[#aaa]'}`}>
                              {new Date(r.createdAt).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
                            </p>
                          </div>
                          {r.authorRole === 'admin' && (
                            <div className="w-8 h-8 rounded-full bg-[#3F51B5] flex items-center justify-center shrink-0">
                              <span className="text-xs font-semibold text-white">{r.authorName.charAt(0).toUpperCase()}</span>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="flex gap-2">
                    <Input placeholder="Type a reply..." value={bugReplyText[bug.id] || ''}
                      onChange={e => setBugReplyText(prev => ({ ...prev, [bug.id]: e.target.value }))}
                      onKeyDown={e => { if (e.key === 'Enter') handleBugReply(bug.id) }}
                      className="h-10 text-sm font-['Manrope']" />
                    <Button size="sm" onClick={() => handleBugReply(bug.id)}
                      className="h-10 w-10 p-0 bg-[#3F51B5] hover:bg-[#2D3FC7] text-white shrink-0">
                      <Send className="size-4" />
                    </Button>
                  </div>
                </div>
              </div>
            )
          })()}
        </DialogContent>
      </Dialog>
      </>
    )
  }

  // 5. Environments
  const renderEnvironments = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">Environments</h2>
        <Button onClick={() => { setEditingEnv(null); setEnvDialogOpen(true) }}
          className="bg-[#2D3FC7] hover:bg-[#3F51B5] text-white font-['Roboto'] text-xs h-8">
          <Plus className="size-3.5 mr-1" /> Add Environment
        </Button>
      </div>
      {!envLoaded ? (
        <div className="flex justify-center py-12"><Loader2 className="size-6 animate-spin text-[#3F51B5]" /></div>
      ) : environments.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-12 border border-gray-100 dark:border-gray-700 text-center">
          <Globe className="size-10 text-[#888] dark:text-gray-500 mx-auto mb-2" />
          <p className="text-sm text-[#888] dark:text-gray-400 font-['Manrope']">No environments configured</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {environments.map(env => (
            <div key={env.id} className={`bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700 border-l-4 ${env.status === 'active' ? 'border-l-[#4CAF50]' : 'border-l-gray-400 dark:border-l-gray-600'}`}>
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className={`w-3 h-3 rounded-full ${env.color || 'bg-green-500'}`} />
                  <h3 className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">{env.name}</h3>
                </div>
                <Badge className={`text-[9px] border-0 ${env.status === 'active' ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300' : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'}`}>
                  {env.status}
                </Badge>
              </div>
              <div className="space-y-1 text-xs font-['Manrope']">
                <p className="text-[#545454] dark:text-gray-300"><span className="text-[#888] dark:text-gray-400">URL:</span> {env.baseUrl}</p>
                <p className="text-[#545454] dark:text-gray-300"><span className="text-[#888] dark:text-gray-400">Browser:</span> {env.browser}</p>
                {env.lastUsed && <p className="text-[#545454] dark:text-gray-300"><span className="text-[#888] dark:text-gray-400">Last used:</span> {env.lastUsed}</p>}
              </div>
              <div className="flex gap-2 mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
                <Button size="sm" variant="outline" className="h-7 text-[10px] font-['Roboto']"
                  onClick={() => { setEditingEnv(env); setEnvDialogOpen(true) }}><Pencil className="size-3 mr-1" /> Edit</Button>
                <Button size="sm" variant="outline" className="h-7 text-[10px] font-['Roboto']"
                  onClick={() => handleToggleEnv(env)}>{env.status === 'active' ? 'Deactivate' : 'Activate'}</Button>
                <Button size="sm" variant="ghost" className="h-7 text-[10px] text-[#F44336] hover:text-[#D32F2F] hover:bg-red-50 dark:hover:bg-red-900/20 font-['Roboto']"
                  onClick={() => { setDeleteTarget({ type: 'environment', id: env.id, label: env.name }); setDeleteDialogOpen(true) }}><Trash2 className="size-3" /></Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )

  // 6. Users
  const renderUsers = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">Users</h2>
        <Button onClick={() => { setEditingUser(null); setUserDialogOpen(true) }}
          className="bg-[#2D3FC7] hover:bg-[#3F51B5] text-white font-['Roboto'] text-xs h-8">
          <Plus className="size-3.5 mr-1" /> Add User
        </Button>
      </div>
      {/* Bulk action bar */}
      {selectedUserIds.size > 0 && (
        <div className="bg-[#E8EAF6] dark:bg-[#1A237E]/30 rounded-[14px] shadow-sm p-3 flex items-center gap-3 flex-wrap">
          <span className="text-xs font-semibold font-['Poppins'] text-[#3F51B5] dark:text-[#7986CB]">
            {selectedUserIds.size} selected
          </span>
          <Button size="sm" className="h-7 text-[10px] bg-green-600 hover:bg-green-700 text-white font-['Roboto']"
            onClick={() => { setBulkActionType('activate'); setBulkActionConfirmOpen(true) }}>
            <CheckCircle2 className="size-3 mr-1" /> Activate
          </Button>
          <Button size="sm" className="h-7 text-[10px] bg-orange-500 hover:bg-orange-600 text-white font-['Roboto']"
            onClick={() => { setBulkActionType('deactivate'); setBulkActionConfirmOpen(true) }}>
            <XCircle className="size-3 mr-1" /> Deactivate
          </Button>
          <Button size="sm" className="h-7 text-[10px] bg-[#F44336] hover:bg-[#D32F2F] text-white font-['Roboto']"
            onClick={() => { setBulkActionType('delete'); setBulkActionConfirmOpen(true) }}>
            <Trash2 className="size-3 mr-1" /> Delete
          </Button>
          <Button size="sm" variant="ghost" className="h-7 text-[10px] font-['Roboto'] text-[#888]"
            onClick={() => setSelectedUserIds(new Set())}>
            Clear
          </Button>
        </div>
      )}
      {!usersLoaded ? (
        <div className="flex justify-center py-12"><Loader2 className="size-6 animate-spin text-[#3F51B5]" /></div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div className="space-y-1 p-3">
            {users.map(u => (
              <div key={u.id} className={`flex items-center gap-3 px-3 py-2.5 rounded-lg border transition-colors ${selectedUserIds.has(u.id) ? 'bg-[#E8EAF6]/50 dark:bg-[#1A237E]/20 border-[#3F51B5]/30 dark:border-[#7986CB]/30' : 'bg-white dark:bg-gray-800/20 border-gray-100 dark:border-gray-700/40 hover:bg-gray-50/50 dark:hover:bg-gray-800/30'}`}>
                <Checkbox
                  checked={selectedUserIds.has(u.id)}
                  onCheckedChange={() => toggleUserSelection(u.id)}
                />
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <Avatar className="size-7 shrink-0"><AvatarFallback className="bg-[#E8EAF6] dark:bg-[#1A237E]/30 text-[#3F51B5] dark:text-[#7986CB] text-[10px] font-semibold">
                    {u.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
                  </AvatarFallback></Avatar>
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-[#333] dark:text-gray-100 truncate">{u.name}</p>
                    <p className="text-[10px] text-[#888] dark:text-gray-400 truncate">{u.email}</p>
                  </div>
                </div>
                <Badge className={`text-[10px] border-0 shrink-0 ${roleConfig[u.role]?.color || ''}`}>{roleConfig[u.role]?.label || u.role}</Badge>
                <Badge className={`text-[10px] border-0 shrink-0 ${u.status === 'active' ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300' : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'}`}>{u.status}</Badge>
                <span className="text-[10px] font-['Manrope'] text-[#545454] dark:text-gray-300 shrink-0">
                  {u.moduleAccess.includes('all') ? 'All modules' : `${u.moduleAccess.length} modules`}
                </span>
                <span className="text-[10px] font-['Manrope'] text-[#888] dark:text-gray-400 shrink-0">{u.lastLogin || '—'}</span>
                <div className="flex gap-1 shrink-0">
                  <Button size="sm" variant="ghost" className="size-7 p-0" onClick={() => { setEditingUser(u); setUserDialogOpen(true) }}><Pencil className="size-3 text-[#3F51B5]" /></Button>
                  <Button size="sm" variant="ghost" className="size-7 p-0" onClick={() => { setResetPasswordUser(u); setResetPasswordDialogOpen(true) }} title="Reset password"><Key className="size-3 text-[#F57C00]" /></Button>
                  <Button size="sm" variant="ghost" className="size-7 p-0" onClick={() => { setDeleteTarget({ type: 'user', id: u.id, label: u.name }); setDeleteDialogOpen(true) }}><Trash2 className="size-3 text-[#F44336]" /></Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Bulk Action Confirmation Dialog */}
      <Dialog open={bulkActionConfirmOpen} onOpenChange={setBulkActionConfirmOpen}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle className="font-['Poppins'] text-[#333] dark:text-gray-100">Confirm Bulk Action</DialogTitle>
            <DialogDescription className="font-['Manrope'] text-[#888]">
              Are you sure you want to {bulkActionType === 'activate' ? 'activate' : bulkActionType === 'deactivate' ? 'deactivate' : 'delete'} <strong>{selectedUserIds.size} user(s)</strong>?
              {bulkActionType === 'delete' && ' This action cannot be undone.'}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setBulkActionConfirmOpen(false)} className="font-['Roboto']">Cancel</Button>
            <Button onClick={handleBulkAction}
              className={`text-white font-['Roboto'] ${bulkActionType === 'delete' ? 'bg-[#F44336] hover:bg-[#D32F2F]' : bulkActionType === 'deactivate' ? 'bg-orange-500 hover:bg-orange-600' : 'bg-green-600 hover:bg-green-700'}`}>
              {bulkActionType === 'activate' ? 'Activate' : bulkActionType === 'deactivate' ? 'Deactivate' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )

  // 7. Settings - rendered via SettingsSection component
  const renderSettings = () => (
    <SettingsSection
      settings={settings}
      settingsLoaded={settingsLoaded}
      onSaveSetting={handleSaveSetting}
      onSeedSettings={handleSeedSettings}
    />
  )

  // 8. System Health
  const renderSystemHealth = () => {
    const uptimeSeconds = Math.floor((Date.now() - appStartTime) / 1000)
    const formatUptime = (s: number) => {
      const d = Math.floor(s / 86400); const h = Math.floor((s % 86400) / 3600); const m = Math.floor((s % 3600) / 60)
      return d > 0 ? `${d}d ${h}h ${m}m` : h > 0 ? `${h}h ${m}m` : `${m}m`
    }

    const dbStats = (systemHealthData?.dbStats || {}) as Record<string, number>
    const dbFileSize = (systemHealthData?.dbFileSize || '—') as string
    const lastRun = (systemHealthData?.lastRun || null) as { id: string; moduleName: string; status: string; completedAt: string } | null
    const activeModules = (systemHealthData?.activeModules || 0) as number
    const totalTestCases = (systemHealthData?.totalTestCases || 0) as number
    const serverUptime = (systemHealthData?.serverUptime || 0) as number

    const statusColor = (ok: boolean, warn = false) =>
      ok ? 'bg-green-500' : warn ? 'bg-yellow-500' : 'bg-red-500'

    const apiOk = modulesLoaded
    const dbOk = dbStats.users !== undefined
    const lastRunOk = lastRun?.status === 'completed'

    return (
      <div className="space-y-4">
        <h2 className="text-xl font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">System Health</h2>
        {!healthLoaded ? (
          <div className="flex justify-center py-12"><Loader2 className="size-6 animate-spin text-[#3F51B5]" /></div>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* API Connectivity */}
              <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[#E8EAF6] dark:bg-[#1A237E]/30">
                    <Activity className="size-5 text-[#3F51B5] dark:text-[#7986CB]" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">API Connectivity</p>
                    <p className="text-[10px] text-[#888] dark:text-gray-400 font-['Manrope']">Backend API status</p>
                  </div>
                  <span className={`ml-auto w-3 h-3 rounded-full ${statusColor(apiOk)}`} />
                </div>
                <p className="text-xs font-['Manrope'] text-[#545454] dark:text-gray-300">
                  {apiOk ? 'API is reachable and responding' : 'API connection failed'}
                </p>
              </div>

              {/* Database Stats */}
              <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[#E0F2F1] dark:bg-[#004D40]/40">
                    <Database className="size-5 text-[#00897B] dark:text-[#4DB6AC]" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">Database</p>
                    <p className="text-[10px] text-[#888] dark:text-gray-400 font-['Manrope']">SQLite record counts</p>
                  </div>
                  <span className={`ml-auto w-3 h-3 rounded-full ${statusColor(dbOk)}`} />
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs font-['Manrope']">
                  <span className="text-[#888] dark:text-gray-400">Users: <strong className="text-[#333] dark:text-gray-100">{dbStats.users ?? '—'}</strong></span>
                  <span className="text-[#888] dark:text-gray-400">Runs: <strong className="text-[#333] dark:text-gray-100">{dbStats.runs ?? '—'}</strong></span>
                  <span className="text-[#888] dark:text-gray-400">Bugs: <strong className="text-[#333] dark:text-gray-100">{dbStats.bugs ?? '—'}</strong></span>
                  <span className="text-[#888] dark:text-gray-400">Modules: <strong className="text-[#333] dark:text-gray-100">{dbStats.modules ?? '—'}</strong></span>
                  <span className="text-[#888] dark:text-gray-400">Envs: <strong className="text-[#333] dark:text-gray-100">{dbStats.environments ?? '—'}</strong></span>
                  <span className="text-[#888] dark:text-gray-400">Notifs: <strong className="text-[#333] dark:text-gray-100">{dbStats.notifications ?? '—'}</strong></span>
                </div>
              </div>

              {/* Disk Usage */}
              <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[#FFF3E0] dark:bg-[#BF360C]/40">
                    <HardDrive className="size-5 text-[#F57C00] dark:text-[#FFB74D]" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">Disk Usage</p>
                    <p className="text-[10px] text-[#888] dark:text-gray-400 font-['Manrope']">Database file size</p>
                  </div>
                  <span className={`ml-auto w-3 h-3 rounded-full ${statusColor(true)}`} />
                </div>
                <p className="text-2xl font-bold font-['Poppins'] text-[#333] dark:text-gray-100">{dbFileSize}</p>
              </div>

              {/* Last Run Status */}
              <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[#F3E5F5] dark:bg-[#4A148C]/40">
                    <Zap className="size-5 text-[#7B1FA2] dark:text-[#CE93D8]" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">Last Run</p>
                    <p className="text-[10px] text-[#888] dark:text-gray-400 font-['Manrope']">Most recent test run</p>
                  </div>
                  <span className={`ml-auto w-3 h-3 rounded-full ${statusColor(lastRunOk, !lastRun && !lastRunOk)}`} />
                </div>
                {lastRun ? (
                  <div className="space-y-1">
                    <p className="text-xs font-medium text-[#333] dark:text-gray-100 font-['Manrope']">{lastRun.moduleName}</p>
                    <Badge className={`text-[10px] border-0 ${lastRun.status === 'completed' ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300' : lastRun.status === 'failed' ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300' : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300'}`}>{lastRun.status}</Badge>
                    <p className="text-[10px] text-[#888] dark:text-gray-400 font-['Manrope']">{lastRun.completedAt ? new Date(lastRun.completedAt).toLocaleString() : 'In progress'}</p>
                  </div>
                ) : (
                  <p className="text-xs text-[#888] dark:text-gray-400 font-['Manrope']">No runs yet</p>
                )}
              </div>

              {/* Uptime */}
              <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[#E8F5E9] dark:bg-[#1B5E20]/40">
                    <Timer className="size-5 text-[#2E7D32] dark:text-[#66BB6A]" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">Uptime</p>
                    <p className="text-[10px] text-[#888] dark:text-gray-400 font-['Manrope']">Since page loaded</p>
                  </div>
                  <span className="ml-auto w-3 h-3 rounded-full bg-green-500" />
                </div>
                <p className="text-2xl font-bold font-['Poppins'] text-[#333] dark:text-gray-100">{formatUptime(uptimeSeconds)}</p>
                <p className="text-[10px] text-[#888] dark:text-gray-400 font-['Manrope']">Server: {formatUptime(serverUptime)}</p>
              </div>

              {/* Active Modules & Test Cases */}
              <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[#E8EAF6] dark:bg-[#1A237E]/30">
                    <FolderTree className="size-5 text-[#3F51B5] dark:text-[#7986CB]" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">Modules & Tests</p>
                    <p className="text-[10px] text-[#888] dark:text-gray-400 font-['Manrope']">Active counts</p>
                  </div>
                  <span className={`ml-auto w-3 h-3 rounded-full ${statusColor(activeModules > 0)}`} />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs font-['Manrope']">
                    <span className="text-[#888] dark:text-gray-400">Active Modules</span>
                    <strong className="text-[#333] dark:text-gray-100">{activeModules}</strong>
                  </div>
                  <div className="flex items-center justify-between text-xs font-['Manrope']">
                    <span className="text-[#888] dark:text-gray-400">Total Test Cases</span>
                    <strong className="text-[#333] dark:text-gray-100">{totalTestCases}</strong>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    )
  }

  // 9. Audit Log
  const renderAuditLog = () => {
    const perPage = 25
    const totalPages = Math.ceil(filteredAuditLog.length / perPage) || 1
    const paged = filteredAuditLog.slice((auditPage - 1) * perPage, auditPage * perPage)

    const actionColor = (action: string) => {
      if (action === 'create') return 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300'
      if (action === 'update') return 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
      if (action === 'delete') return 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300'
      if (action === 'login') return 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300'
      if (action === 'logout') return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
      if (action === 'reset_password') return 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300'
      if (action === 'toggle') return 'bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-300'
      return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
    }

    return (
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <h2 className="text-xl font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">Audit Log</h2>
          <Badge variant="outline" className="text-xs font-['Manrope']">{filteredAuditLog.length} entries</Badge>
        </div>
        {/* Filters */}
        <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-2.5 size-4 text-[#888]" />
              <Input placeholder="Search user, target, details..." value={auditSearch} onChange={e => { setAuditSearch(e.target.value); setAuditPage(1) }}
                className="pl-9 h-9 text-sm font-['Manrope']" />
            </div>
            <Select value={auditActionFilter} onValueChange={v => { setAuditActionFilter(v); setAuditPage(1) }}>
              <SelectTrigger className="h-9 text-sm"><SelectValue placeholder="Action" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Actions</SelectItem>
                <SelectItem value="create">Create</SelectItem>
                <SelectItem value="update">Update</SelectItem>
                <SelectItem value="delete">Delete</SelectItem>
                <SelectItem value="login">Login</SelectItem>
                <SelectItem value="logout">Logout</SelectItem>
                <SelectItem value="reset_password">Reset Password</SelectItem>
                <SelectItem value="toggle">Toggle</SelectItem>
              </SelectContent>
            </Select>
            <Select value={auditUserFilter} onValueChange={v => { setAuditUserFilter(v); setAuditPage(1) }}>
              <SelectTrigger className="h-9 text-sm"><SelectValue placeholder="User" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Users</SelectItem>
                {uniqueAuditUsers.map(u => <SelectItem key={u} value={u}>{u}</SelectItem>)}
              </SelectContent>
            </Select>
            <Button variant="outline" className="h-9 text-xs font-['Roboto']" onClick={() => { setAuditSearch(''); setAuditActionFilter('all'); setAuditUserFilter('all'); setAuditPage(1) }}>
              <RotateCcw className="size-3 mr-1" /> Clear Filters
            </Button>
          </div>
        </div>
        {!auditLoaded ? (
          <div className="flex justify-center py-12"><Loader2 className="size-6 animate-spin text-[#3F51B5]" /></div>
        ) : filteredAuditLog.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-12 border border-gray-100 dark:border-gray-700 text-center">
            <FileText className="size-10 text-[#888] dark:text-gray-500 mx-auto mb-2" />
            <p className="text-sm text-[#888] dark:text-gray-400 font-['Manrope']">No audit entries match your filters</p>
          </div>
        ) : (
          <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
            <div className="space-y-1 p-3">
              {paged.map(a => (
                <div key={a.id} className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-white dark:bg-gray-800/20 border border-gray-100 dark:border-gray-700/40 hover:bg-gray-50/50 dark:hover:bg-gray-800/30 transition-colors">
                  <span className="text-[10px] font-['Manrope'] text-[#888] dark:text-gray-400 shrink-0 w-32">
                    {new Date(a.createdAt).toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                  </span>
                  <span className="text-xs font-['Manrope'] text-[#333] dark:text-gray-100 shrink-0 w-28 truncate">{a.userName}</span>
                  <Badge className={`text-[9px] border-0 shrink-0 ${actionColor(a.action)}`}>{a.action.replace('_', ' ')}</Badge>
                  <div className="text-xs font-['Manrope'] min-w-0 flex-1">
                    <span className="text-[#888] dark:text-gray-400">{a.targetType}</span>
                    <span className="text-[#333] dark:text-gray-100 ml-1">{a.targetLabel}</span>
                  </div>
                  <span className="text-[10px] font-['Manrope'] text-[#545454] dark:text-gray-300 max-w-[200px] truncate shrink-0">{a.details}</span>
                </div>
              ))}
            </div>
            <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100 dark:border-gray-700">
              <span className="text-xs text-[#888] dark:text-gray-400 font-['Manrope']">
                Showing {(auditPage - 1) * perPage + 1}–{Math.min(auditPage * perPage, filteredAuditLog.length)} of {filteredAuditLog.length}
              </span>
              <div className="flex gap-1">
                <Button size="sm" variant="outline" disabled={auditPage <= 1} onClick={() => setAuditPage(p => p - 1)} className="h-7 text-xs"><ChevronLeft className="size-3" /></Button>
                <span className="flex items-center px-2 text-xs text-[#545454] dark:text-gray-300 font-['Manrope']">{auditPage} / {totalPages}</span>
                <Button size="sm" variant="outline" disabled={auditPage >= totalPages} onClick={() => setAuditPage(p => p + 1)} className="h-7 text-xs"><ChevronRight className="size-3" /></Button>
              </div>
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col bg-[#F1F2F7] dark:bg-gray-900 overflow-hidden">
      {/* ─── HEADER ─────────────────────────────────── */}
      <header className="h-[60px] bg-white dark:bg-gray-900 shrink-0 z-10 flex items-center px-4 border-b border-[#e0e0e0] dark:border-gray-700 shadow-[0_2px_8px_rgba(0,0,0,0.06)]">
        <div className="flex items-center gap-3 flex-1">
          <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(!sidebarOpen)}
            className="size-8 cursor-pointer shrink-0 text-[#888888] dark:text-gray-400 hover:text-[#333333] dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800">
            <Menu className={`size-[18px] transition-transform duration-200 ${sidebarOpen ? '' : 'rotate-90'}`} />
          </Button>
          <Separator orientation="vertical" className="h-5" />
          <div className="flex items-center gap-2">
            <Image src="/agdi-logo-new.webp" width={70} height={28} className="object-contain" alt="agDi Logo" />
            <span className="text-[#888888] dark:text-gray-500 text-[13px] font-['Manrope'] ml-1">Admin Panel</span>
          </div>
          <Badge className="bg-[#6777EF] text-white text-[10px] font-semibold px-1.5 py-0 ml-1 border-0">
            ADMIN
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" onClick={() => setTheme(isDark ? 'light' : 'dark')}
            className="size-8 text-[#888888] dark:text-gray-400 hover:text-[#333333] dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer">
            {isDark ? <Sun className="size-4" /> : <Moon className="size-4" />}
          </Button>
          <Button variant="ghost" size="icon" onClick={() => router.push('/')}
            className="size-8 text-[#888888] dark:text-gray-400 hover:text-[#333333] dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer"
            title="Back to User Panel">
            <Home className="size-4" />
          </Button>
          <Separator orientation="vertical" className="h-5 mx-1" />
          <div className="flex items-center gap-2">
            <Avatar className="size-7">
              <AvatarFallback className="bg-[#6777EF] text-white text-xs font-semibold">
                {userInitials}
              </AvatarFallback>
            </Avatar>
            <div className="flex flex-col">
              <span className="text-[12px] text-[#333333] dark:text-gray-200 font-medium max-w-[120px] truncate leading-tight">{user.name}</span>
              <span className="text-[10px] text-[#888888] dark:text-gray-500 leading-tight">Admin</span>
            </div>
            <Button variant="ghost" size="icon" onClick={handleLogout} className="size-7 text-[#888888] hover:text-red-500 cursor-pointer">
              <LogOut className="size-4" />
            </Button>
          </div>
        </div>
      </header>

      {/* ─── BODY ──────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">
        {/* ─── SIDEBAR ────────────────────────────── */}
        <div className={`shrink-0 transition-all duration-200 ease-in-out overflow-hidden ${sidebarOpen ? 'w-60' : 'w-0'}`}>
          <aside className="w-60 bg-gradient-to-b from-[#F7FBF8] via-[#EAF5EC] to-[#D6EDDC] dark:from-[#1e293b] dark:via-[#1e293b] dark:to-[#1e293b] h-full flex flex-col font-['Poppins'] shadow-[-1px_0px_0px_#D4E3D9] dark:shadow-[-1px_0px_0px_#334155]">
            <div className="px-3 py-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Shield className="size-3.5 text-[#1B4332] dark:text-green-300" />
                <span className="text-[13px] font-medium text-[#1B4332] dark:text-green-300 font-['Poppins']">Admin Controls</span>
              </div>
              <button onClick={() => setSidebarOpen(false)} className="text-[#495584] dark:text-gray-400 hover:text-[#1B4332] dark:hover:text-green-300 transition-colors cursor-pointer p-0.5 rounded hover:bg-[rgba(82,183,136,0.08)]">
                <ChevronLeft className="size-4" />
              </button>
            </div>
            <ScrollArea className="flex-1">
              <div className="py-2 px-2">
                {sidebarItems.map(item => {
                  const Icon = item.icon
                  const isActive = activeSection === item.id
                  return (
                    <button key={item.id} onClick={() => setActiveSection(item.id)}
                      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-[13px] font-['Poppins'] transition-all duration-150 cursor-pointer mb-0.5 ${
                        isActive
                          ? 'bg-gradient-to-r from-[#DFF3E3] via-[#C8E6C9] to-[#B7E4C7] dark:bg-[#1B4332]/25 text-[#1B4332] dark:text-green-300 font-semibold shadow-[rgba(34,197,94,0.25)_2px_0px_4px_inset,rgba(34,197,94,0.15)_0px_2px_6px] rounded-[5px]'
                          : 'text-[#545454] dark:text-gray-300 font-medium hover:text-[#6777EF] dark:hover:text-indigo-400 hover:bg-[rgba(82,183,136,0.08)] hover:shadow-[rgba(82,183,136,0.5)_2px_0px_inset] hover:rounded-[5px]'
                      }`}>
                      <Icon className="size-4 shrink-0" />
                      <span>{item.label}</span>
                    </button>
                  )
                })}
              </div>
            </ScrollArea>
            <div className="relative shrink-0 overflow-hidden" style={{ height: 99 }}>
              <Image src="/agri2.png" alt="" fill className="object-cover" sizes="280px" style={{ objectPosition: 'center 25%' }} />
            </div>
          </aside>
        </div>

        {/* ─── MAIN CONTENT ────────────────────────── */}
        <main className="flex-1 overflow-y-auto p-6">
          {activeSection === 'overview' ? renderOverview() :
            activeSection === 'tests' ? renderTests() :
            activeSection === 'test-visibility' ? renderTestVisibility() :
            activeSection === 'modules' ? renderModules() :
            activeSection === 'bug-reports' ? renderBugReports() :
            activeSection === 'environments' ? renderEnvironments() :
            activeSection === 'users' ? renderUsers() :
            activeSection === 'settings' ? renderSettings() :
            activeSection === 'system-health' ? renderSystemHealth() :
            activeSection === 'audit-log' ? renderAuditLog() : null}
        </main>
      </div>

      {/* ─── ENVIRONMENT DIALOG ────────────────────── */}
      <EnvDialog key={editingEnv?.id || 'new'} open={envDialogOpen} onOpenChange={setEnvDialogOpen} editingEnv={editingEnv} onSave={handleSaveEnv} />

      {/* ─── USER DIALOG ────────────────────────────── */}
      <UserDialog key={editingUser?.id || 'user-new'} open={userDialogOpen} onOpenChange={setUserDialogOpen} editingUser={editingUser} onSave={handleSaveUser} allModules={modules} />

      {/* ─── RESET PASSWORD DIALOG ───────────────────── */}
      <ResetPasswordDialog open={resetPasswordDialogOpen} onOpenChange={setResetPasswordDialogOpen} user={resetPasswordUser} onReset={handleResetPassword} />

      {/* ─── MODULE DIALOG ──────────────────────────── */}
      <ModuleDialog key={editingModule?.id || 'module-new'} open={moduleDialogOpen} onOpenChange={setModuleDialogOpen} editingModule={editingModule} onSave={handleSaveModule} allModules={modules} />

      {/* ─── DELETE CONFIRM DIALOG ──────────────────── */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle className="font-['Poppins'] text-[#333] dark:text-gray-100">Confirm Delete</DialogTitle>
            <DialogDescription className="font-['Manrope'] text-[#888]">
              Are you sure you want to delete <strong>{deleteTarget?.label}</strong>? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)} className="font-['Roboto']">Cancel</Button>
            <Button onClick={handleDelete} className="bg-[#F44336] hover:bg-[#D32F2F] text-white font-['Roboto']">Delete</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

// ─── Reset Password Dialog Component ──────────────────────────
function ResetPasswordDialog({ open, onOpenChange, user, onReset }: {
  open: boolean; onOpenChange: (v: boolean) => void
  user: AdminUser | null; onReset: (userId: string, password: string) => void
}) {
  const [password, setPassword] = useState('changeme')
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState<{ id: string; resetBy: string; date: string; password: string }[]>([])

  // Fetch reset history when dialog opens
  const [historyLoading, setHistoryLoading] = useState(false)
  const [fetchedUserId, setFetchedUserId] = useState<string | null>(null)

  if (open && user && user.id !== fetchedUserId) {
    setFetchedUserId(user.id)
    setHistoryLoading(true)
    setHistory([])
    fetch(`/api/admin/users/${user.id}/reset-password`)
      .then(res => res.ok ? res.json() : { history: [] })
      .then(data => {
        setHistory(data.history || [])
        setHistoryLoading(false)
      })
      .catch(() => { setHistory([]); setHistoryLoading(false) })
  }
  if (!open && fetchedUserId) {
    setFetchedUserId(null)
    setPassword('changeme')
    setHistory([])
  }

  if (!user) return null

  const handleReset = async () => {
    setLoading(true)
    await onReset(user.id, password)
    setLoading(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle className="font-['Poppins'] text-[#333] dark:text-gray-100 flex items-center gap-2">
            <Key className="size-4 text-[#F57C00]" />
            Reset Password
          </DialogTitle>
          <DialogDescription className="font-['Manrope'] text-[#888] dark:text-gray-400">
            Set a new password for <strong className="text-[#333] dark:text-gray-200">{user.name}</strong> ({user.email})
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 mt-2">
          {/* Password input */}
          <div className="space-y-2">
            <Label className="font-['Manrope'] text-xs text-[#555] dark:text-gray-400">New Password</Label>
            <Input
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter new password"
              className="font-['Manrope'] h-9"
            />
            <p className="text-[10px] text-[#999] dark:text-gray-500">
              Default: <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded text-[10px]">changeme</code> — min 6 characters
            </p>
          </div>

          {/* Warning */}
          <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-3">
            <p className="text-[11px] text-amber-700 dark:text-amber-400 flex items-center gap-1.5">
              <AlertTriangle className="size-3 shrink-0" />
              This will invalidate all active sessions for this user. They will need to log in again.
            </p>
          </div>

          {/* Reset History */}
          {history.length > 0 && (
            <div className="space-y-2">
              <Label className="font-['Manrope'] text-xs text-[#555] dark:text-gray-400">Recent Reset History</Label>
              <div className="space-y-1 border rounded-lg dark:border-gray-700 p-2">
                {history.map((entry) => (
                  <div key={entry.id} className="flex items-center gap-3 px-3 py-2 rounded-lg bg-white dark:bg-gray-800/20 border border-gray-100 dark:border-gray-700/40">
                    <span className="text-[11px] font-['Manrope'] flex-1">{entry.resetBy}</span>
                    <span className="text-[11px] font-['Manrope'] text-[#888] dark:text-gray-400 shrink-0">
                      {new Date(entry.date).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                    </span>
                    <code className="bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded text-[10px] shrink-0">{entry.password}</code>
                  </div>
                ))}
              </div>
            </div>
          )}
          {historyLoading && (
            <div className="flex justify-center py-2"><Loader2 className="size-4 animate-spin text-[#3F51B5]" /></div>
          )}
        </div>

        <DialogFooter className="mt-4">
          <Button variant="outline" onClick={() => onOpenChange(false)} className="font-['Roboto']">Cancel</Button>
          <Button onClick={handleReset} disabled={loading || password.length < 6} className="bg-[#F57C00] hover:bg-[#E65100] text-white font-['Roboto']">
            {loading ? <Loader2 className="size-4 animate-spin mr-1" /> : <Key className="size-3.5 mr-1" />}
            Reset Password
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─── Environment Dialog Component ──────────────────────────
function EnvDialog({ open, onOpenChange, editingEnv, onSave }: {
  open: boolean; onOpenChange: (v: boolean) => void
  editingEnv: Environment | null; onSave: (data: Partial<Environment>) => void
}) {
  const [name, setName] = useState(editingEnv?.name || '')
  const [baseUrl, setBaseUrl] = useState(editingEnv?.baseUrl || '')
  const [browser, setBrowser] = useState(editingEnv?.browser || 'Chrome')
  const [color, setColor] = useState(editingEnv?.color || 'bg-green-500')

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle className="font-['Poppins'] text-[#333] dark:text-gray-100">{editingEnv ? 'Edit Environment' : 'Add Environment'}</DialogTitle>
          <DialogDescription className="font-['Manrope'] text-[#888]">
            {editingEnv ? 'Update environment configuration.' : 'Configure a new test environment.'}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <div className="space-y-1.5">
            <Label className="text-xs font-['Manrope']">Name</Label>
            <Input value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Staging" className="h-9 text-sm font-['Manrope']" />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs font-['Manrope']">Base URL</Label>
            <Input value={baseUrl} onChange={e => setBaseUrl(e.target.value)} placeholder="https://staging.rhythmerp.com" className="h-9 text-sm font-['Manrope']" />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs font-['Manrope']">Browser</Label>
            <Select value={browser} onValueChange={setBrowser}>
              <SelectTrigger className="h-9 text-sm"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="Chrome">Chrome</SelectItem>
                <SelectItem value="Firefox">Firefox</SelectItem>
                <SelectItem value="Edge">Edge</SelectItem>
                <SelectItem value="Safari">Safari</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs font-['Manrope']">Color</Label>
            <div className="flex gap-2">
              {['bg-green-500', 'bg-blue-500', 'bg-orange-500', 'bg-red-500', 'bg-purple-500', 'bg-teal-500'].map(c => (
                <button key={c} onClick={() => setColor(c)}
                  className={`w-7 h-7 rounded-full ${c} cursor-pointer transition-transform ${color === c ? 'ring-2 ring-[#3F51B5] ring-offset-2 scale-110' : 'hover:scale-110'}`} />
              ))}
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} className="font-['Roboto']">Cancel</Button>
          <Button onClick={() => onSave({ name, baseUrl, browser, color })} disabled={!name || !baseUrl}
            className="bg-[#2D3FC7] hover:bg-[#3F51B5] text-white font-['Roboto']">
            {editingEnv ? 'Update' : 'Create'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─── User Dialog Component ─────────────────────────────────
function UserDialog({ open, onOpenChange, editingUser, onSave, allModules }: {
  open: boolean; onOpenChange: (v: boolean) => void
  editingUser: AdminUser | null; onSave: (data: Partial<AdminUser> & { password?: string }) => void
  allModules: AdminModule[]
}) {
  const [name, setName] = useState(editingUser?.name || '')
  const [email, setEmail] = useState(editingUser?.email || '')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState<string>(editingUser?.role || 'tester')
  const [status, setStatus] = useState<string>(editingUser?.status || 'active')
  const [moduleAccess, setModuleAccess] = useState<string[]>(editingUser?.moduleAccess || [])
  const [modulePickerOpen, setModulePickerOpen] = useState(false)

  // Build ModuleItem[] for the ModuleAccessPicker — ALWAYS use sidebar structure
  // so that preset slugs ('registration', 'common-settings', etc.) match module IDs.
  // DB modules use UUIDs which break the preset resolution logic.
  const pickerModules: ModuleItem[] = useMemo(() => {
    const result: ModuleItem[] = []
    for (const sm of ALL_SIDEBAR_MODULES) {
      if (sm.id === 'dashboard' || sm.id === 'my-tickets') continue
      result.push({
        id: sm.id, name: sm.id, label: sm.label,
        parentId: undefined, parentLabel: undefined,
      })
      if (sm.children) {
        for (const child of sm.children) {
          if (child.children) {
            for (const grandChild of child.children) {
              result.push({
                id: grandChild.id, name: grandChild.id, label: grandChild.label,
                parentId: child.id, parentLabel: child.label,
              })
            }
            result.push({
              id: child.id, name: child.id, label: child.label,
              parentId: sm.id, parentLabel: sm.label,
            })
          } else {
            result.push({
              id: child.id, name: child.id, label: child.label,
              parentId: sm.id, parentLabel: sm.label,
            })
          }
        }
      }
    }
    return result
  }, [])

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[560px]">
        <DialogHeader>
          <DialogTitle className="font-['Poppins'] text-[#333] dark:text-gray-100">{editingUser ? 'Edit User' : 'Add User'}</DialogTitle>
          <DialogDescription className="font-['Manrope'] text-[#888]">
            {editingUser ? 'Update user details and permissions.' : 'Create a new user account.'}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-2 max-h-[60vh] overflow-y-auto">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs font-['Manrope']">Name</Label>
              <Input value={name} onChange={e => setName(e.target.value)} placeholder="Full Name" className="h-9 text-sm font-['Manrope']" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs font-['Manrope']">Email</Label>
              <Input value={email} onChange={e => setEmail(e.target.value)} placeholder="email@example.com" type="email" className="h-9 text-sm font-['Manrope']" />
            </div>
          </div>
          {!editingUser && (
            <div className="space-y-1.5">
              <Label className="text-xs font-['Manrope']">Password</Label>
              <Input value={password} onChange={e => setPassword(e.target.value)} placeholder="changeme" type="password" className="h-9 text-sm font-['Manrope']" />
            </div>
          )}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs font-['Manrope']">Role</Label>
              <Select value={role} onValueChange={setRole}>
                <SelectTrigger className="h-9 text-sm"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">Admin</SelectItem>
                  <SelectItem value="tester">Tester</SelectItem>
                  <SelectItem value="viewer">Viewer</SelectItem>
                  <SelectItem value="client">Client</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs font-['Manrope']">Status</Label>
              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger className="h-9 text-sm"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="inactive">Inactive</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          {/* Module Access */}
          <div className="space-y-2">
            <Label className="text-xs font-['Manrope']">Module Access</Label>
            <Button
              type="button"
              variant="outline"
              className="w-full justify-start text-left h-auto min-h-[36px] py-2 px-3 font-['Manrope'] text-xs"
              onClick={() => setModulePickerOpen(true)}
            >
              <Shield className="size-4 mr-2 shrink-0 text-[#2E7D32]" />
              {moduleAccess.includes('all')
                ? 'Full Access (all modules)'
                : moduleAccess.length === 0
                  ? 'No modules selected — click to assign'
                  : `${moduleAccess.length} module${moduleAccess.length !== 1 ? 's' : ''} selected`}
            </Button>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} className="font-['Roboto']">Cancel</Button>
          <Button onClick={() => onSave({ name, email, password: password || undefined, role: role as AdminUser['role'], status: status as AdminUser['status'], moduleAccess })}
            disabled={!name || !email}
            className="bg-[#2D3FC7] hover:bg-[#3F51B5] text-white font-['Roboto']">
            {editingUser ? 'Update' : 'Create'}
          </Button>
        </DialogFooter>
      </DialogContent>
      <ModuleAccessPicker
        open={modulePickerOpen}
        onOpenChange={setModulePickerOpen}
        value={moduleAccess}
        onChange={setModuleAccess}
        allModules={pickerModules}
        userName={name || undefined}
      />
    </Dialog>
  )
}

// ─── Module Dialog Component ─────────────────────────────────
function ModuleDialog({ open, onOpenChange, editingModule, onSave, allModules }: {
  open: boolean; onOpenChange: (v: boolean) => void
  editingModule: AdminModule | null; onSave: (data: Partial<AdminModule> & { name: string; label: string }) => void
  allModules: AdminModule[]
}) {
  const [name, setName] = useState(editingModule?.name || '')
  const [label, setLabel] = useState(editingModule?.label || '')
  const [parentId, setParentId] = useState<string>(editingModule?.parentId || 'none')
  const [description, setDescription] = useState(editingModule?.description || '')
  const [status, setStatus] = useState<string>(editingModule?.status || 'active')
  const [sortOrder, setSortOrder] = useState(String(editingModule?.sortOrder ?? 0))

  const parentModules = allModules.filter(m => !m.parentId)
  
  // When editing, exclude self from parent list (if it's a parent)
  const availableParents = editingModule
    ? parentModules.filter(p => p.id !== editingModule.id)
    : parentModules

  const handleSave = () => {
    if (!name.trim() || !label.trim()) return
    const selectedParent = parentId !== 'none' ? parentId : undefined
    const parentMod = selectedParent ? allModules.find(m => m.id === selectedParent) : undefined
    onSave({
      name: name.trim(),
      label: label.trim(),
      parentId: selectedParent,
      parentLabel: parentMod?.label,
      description: description.trim(),
      sortOrder: Number(sortOrder) || 0,
      status: status as AdminModule['status'],
    })
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[520px]">
        <DialogHeader>
          <DialogTitle className="font-['Poppins'] text-[#333] dark:text-gray-100">{editingModule ? 'Edit Module' : 'Add Module'}</DialogTitle>
          <DialogDescription className="font-['Manrope'] text-[#888]">
            {editingModule ? 'Update module configuration.' : 'Create a new test module.'}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-2 max-h-[60vh] overflow-y-auto">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs font-['Manrope']">Name (slug) <span className="text-red-500">*</span></Label>
              <Input value={name} onChange={e => setName(e.target.value)} placeholder="e.g. registration-farmer" className="h-9 text-sm font-['Manrope']" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs font-['Manrope']">Label (display) <span className="text-red-500">*</span></Label>
              <Input value={label} onChange={e => setLabel(e.target.value)} placeholder="e.g. Farmer" className="h-9 text-sm font-['Manrope']" />
            </div>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs font-['Manrope']">Parent Module</Label>
            <Select value={parentId} onValueChange={setParentId}>
              <SelectTrigger className="h-9 text-sm"><SelectValue placeholder="None (Top-level)" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="none">None (Top-level)</SelectItem>
                {availableParents.map(p => (
                  <SelectItem key={p.id} value={p.id}>{p.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs font-['Manrope']">Description</Label>
            <Textarea value={description} onChange={e => setDescription(e.target.value)} placeholder="Brief description of this module..." className="min-h-[60px] text-sm font-['Manrope']" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs font-['Manrope']">Status</Label>
              <Select value={status} onValueChange={setStatus}>
                <SelectTrigger className="h-9 text-sm"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="draft">Draft</SelectItem>
                  <SelectItem value="disabled">Disabled</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs font-['Manrope']">Sort Order</Label>
              <Input type="number" value={sortOrder} onChange={e => setSortOrder(e.target.value)} className="h-9 text-sm font-['Manrope']" />
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} className="font-['Roboto']">Cancel</Button>
          <Button onClick={handleSave} disabled={!name.trim() || !label.trim()}
            className="bg-[#2D3FC7] hover:bg-[#3F51B5] text-white font-['Roboto']">
            {editingModule ? 'Update' : 'Create'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─── Settings Section Component ─────────────────────────────
function SettingsSection({ settings, settingsLoaded, onSaveSetting, onSeedSettings }: {
  settings: SystemSetting[]; settingsLoaded: boolean
  onSaveSetting: (setting: SystemSetting, newValue: string) => void
  onSeedSettings: () => void
}) {
  // Track only locally-modified (unsaved) values
  const [dirtyMap, setDirtyMap] = useState<Record<string, string>>({})

  const getLocalValue = (s: SystemSetting) => dirtyMap[s.id] ?? s.value

  const setLocalValue = (id: string, value: string) => {
    setDirtyMap(prev => ({ ...prev, [id]: value }))
  }

  const categories = [...new Set(settings.map(s => s.category))]

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">Settings</h2>
        <Button variant="outline" onClick={onSeedSettings} className="text-xs h-8 font-['Roboto']">
          <RotateCcw className="size-3.5 mr-1" /> Reset to Defaults
        </Button>
      </div>
      {!settingsLoaded ? (
        <div className="flex justify-center py-12"><Loader2 className="size-6 animate-spin text-[#3F51B5]" /></div>
      ) : settings.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-12 border border-gray-100 dark:border-gray-700 text-center">
          <Settings className="size-10 text-[#888] dark:text-gray-500 mx-auto mb-2" />
          <p className="text-sm text-[#888] dark:text-gray-400 font-['Manrope']">No settings loaded</p>
        </div>
      ) : (
        <div className="space-y-6">
          {categories.map(cat => (
            <div key={cat} className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
              <div className="px-5 py-3 bg-[#E8EAF6] dark:bg-[#1A237E]/30">
                <h3 className="text-sm font-semibold font-['Poppins'] text-[#3F51B5] dark:text-[#7986CB]">{cat}</h3>
              </div>
              <div className="divide-y divide-gray-50 dark:divide-gray-700/50">
                {settings.filter(s => s.category === cat).map(s => (
                  <div key={s.id} className="flex items-center gap-4 px-5 py-4">
                    <div className="flex-1 min-w-0">
                      <Label className="text-xs font-medium text-[#333] dark:text-gray-100 font-['Manrope']">{s.label}</Label>
                      <p className="text-[10px] text-[#888] dark:text-gray-400 font-['Manrope'] mt-0.5">{s.description}</p>
                    </div>
                    <div className="w-48 shrink-0">
                      {s.type === 'boolean' ? (
                        <div className="flex items-center gap-2">
                          <Switch checked={getLocalValue(s) === 'true'}
                            onCheckedChange={v => setLocalValue(s.id, String(v))} />
                          <span className="text-[10px] text-[#888] dark:text-gray-400 font-['Manrope']">{getLocalValue(s) === 'true' ? 'On' : 'Off'}</span>
                        </div>
                      ) : s.type === 'select' ? (
                        <Select value={getLocalValue(s)} onValueChange={v => setLocalValue(s.id, v)}>
                          <SelectTrigger className="h-8 text-xs"><SelectValue /></SelectTrigger>
                          <SelectContent>
                            {(s.options || ['info', 'debug', 'warning', 'error']).map(o => <SelectItem key={o} value={o}>{o}</SelectItem>)}
                          </SelectContent>
                        </Select>
                      ) : (
                        <Input type={s.type} value={getLocalValue(s)} onChange={e => setLocalValue(s.id, e.target.value)}
                          className="h-8 text-xs font-['Manrope']" />
                      )}
                    </div>
                    <Button size="sm" onClick={() => { onSaveSetting(s, getLocalValue(s)); setDirtyMap(prev => { const n = { ...prev }; delete n[s.id]; return n }) }}
                      disabled={getLocalValue(s) === s.value}
                      className="h-7 text-[10px] bg-[#3F51B5] hover:bg-[#2D3FC7] text-white font-['Roboto']">
                      <Save className="size-3 mr-1" /> Save
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
