'use client'

import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { useNotificationsSocket, emitNotification } from '@/hooks/use-notifications-socket'
import Link from 'next/link'
import Image from 'next/image'
import { useTheme } from 'next-themes'
import { toast } from 'sonner'
import { fetchModules, sidebarToFolderMapping, startRun, stopRun, fetchTestCases, fetchScreenshot, saveRunResults, syncModulesToDB, type ApiModule, type TestCasesData, type RunCompletionSummary } from '@/lib/api'
import { ALL_SIDEBAR_MODULES } from '@/data/sidebarModules'
import { testSpecGroups, initialTests, type TestPriority, type TestItem, type TestSpecItem, type TestClassGroup } from '@/data/testSpecGroups'
import { buildSidebarModules, filterSidebarByAccess } from '@/lib/sidebar-helpers'
import { getTestsForSidebarModule } from '@/lib/test-helpers'
import NavToast from '@/components/nav-toast/NavToast'
import {
  getBugReports,
  getNotifications,
  markAllNotificationsRead,
  getUnreadNotificationCount,
  addNotification,
  type Notification as NotifType,
} from '@/lib/bug-reports'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog'
import {
  Search, Play, RefreshCw, Square, RotateCcw, X, Minimize2, CheckCircle2,
  XCircle, Circle, AlertTriangle, Loader2, Menu, Sun, Moon, LayoutDashboard,
  BarChart3, Activity, Zap, Shield, MessageSquare, Send, Bell, CalendarClock,
  Terminal, Monitor, HelpCircle, Copyright, ExternalLink, Bug, Clock,
  ChevronRight, LogOut, GitCompare, RotateCcw as RotateCcwIcon,
} from 'lucide-react'
import { AppTour, startAppTour } from '@/components/tour/AppTour'
import { LoginPage } from '@/components/auth/LoginPage'
import type { AuthUser } from '@/lib/types'
import { SidebarModuleItem } from '@/components/sidebar/SidebarModuleItem'
import type { SidebarModule } from '@/components/sidebar/SidebarModuleItem'
import { Sparkline } from '@/components/ui/sparkline'
import { PassRateTrendChart, ModuleHealthBarChart, BugDistributionPie, TestExecutionTimeline } from '@/components/dashboard/DashboardCharts'
import { ScreenshotGallery, ScreenshotLightbox, ScreenshotCompare } from '@/components/screenshot/ScreenshotGallery'
import RunComparisonDialog from '@/components/comparison/RunComparisonDialog'
import { ExportMenu } from '@/components/export/ExportUtils'
import type { ScreenshotEntry } from '@/components/screenshot/ScreenshotGallery'

// Extracted tab components
import { DashboardTab } from '@/components/dashboard/DashboardTab'
import { OperationsTab } from '@/components/operations/OperationsTab'
import { TestRunnerTab } from '@/components/test-runner/TestRunnerTab'
import { LiveExecutionTab } from '@/components/live-execution/LiveExecutionTab'
import { ScheduleRunsTab } from '@/components/schedule/ScheduleRunsTab'
import { ResultsTab } from '@/components/results/ResultsTab'
import { MyTicketsTab } from '@/components/tickets/MyTicketsTab'
import { ReportToAdminDialog } from '@/components/dialogs/ReportToAdminDialog'
import { CompletionSummaryModal } from '@/components/dialogs/CompletionSummaryModal'
import { UserProfileDialog } from '@/components/dialogs/UserProfileDialog'
import { RunDetailDialog } from '@/components/dialogs/RunDetailDialog'
// AI Features — temporarily disabled (can be re-enabled later)
// import { AiBugTriage } from '@/components/ai/AiBugTriage'
// import { AiTestSuggestions } from '@/components/ai/AiTestSuggestions'
// import { AiNlRunBar } from '@/components/ai/AiNlRunBar'
// import { AiFailureAnalysis } from '@/components/ai/AiFailureAnalysis'

// Types — imported from shared types
import type { RunSnapshot, ModuleHealth } from '@/lib/types'

// ─── MAIN PAGE COMPONENT ─────────────────────────────────
export default function Home() {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)
  const [sidebarModules, setSidebarModules] = useState<SidebarModule[]>([])
  const [apiModules, setApiModules] = useState<ApiModule[]>([])
  const [selectedModule, setSelectedModule] = useState<string>('dashboard')
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())
  const [justExpandedId, setJustExpandedId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('operations')
  const [consoleOpen, setConsoleOpen] = useState(false)
  const [hashReady, setHashReady] = useState(false)
  const [testChecks, setTestChecks] = useState<Set<string>>(new Set())
  const [tests, setTests] = useState<TestItem[]>(initialTests)
  const [currentTestGroups, setCurrentTestGroups] = useState<TestClassGroup[]>(testSpecGroups)
  const [allTestCases, setAllTestCases] = useState<TestCasesData>({})
  const [isRunning, setIsRunning] = useState(false)
  const [runningProgress, setRunningProgress] = useState('')
  const [dashboardStats, setDashboardStats] = useState<Record<string, unknown> | null>(null)
  const [dashboardLoading, setDashboardLoading] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [sidebarWidth, setSidebarWidth] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('sidebar-width')
      return saved ? Number(saved) : 240
    }
    return 240
  })
  const handleResizeStart = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    const startX = e.clientX
    const startWidth = sidebarWidth
    const onMouseMove = (ev: MouseEvent) => {
      const newWidth = Math.max(180, Math.min(400, startWidth + (ev.clientX - startX)))
      setSidebarWidth(newWidth)
    }
    const onMouseUp = () => {
      document.removeEventListener('mousemove', onMouseMove)
      document.removeEventListener('mouseup', onMouseUp)
      localStorage.setItem('sidebar-width', String(sidebarWidth))
    }
    document.addEventListener('mousemove', onMouseMove)
    document.addEventListener('mouseup', onMouseUp)
  }, [sidebarWidth])
  const [quickSwitcherOpen, setQuickSwitcherOpen] = useState(false)
  const [quickSearch, setQuickSearch] = useState('')

  // Feature 1: Completion modal
  const [completionModalOpen, setCompletionModalOpen] = useState(false)
  const prevIsRunningRef = useRef(false)
  const [completionStats, setCompletionStats] = useState({ passed: 0, failed: 0, duration: '' })

  // Bug report dialog
  const [reportDialogOpen, setReportDialogOpen] = useState(false)
  const [reportingTest, setReportingTest] = useState<{ id: string; name: string; error?: string } | null>(null)

  // Notifications
  const [notifDropdownOpen, setNotifDropdownOpen] = useState(false)
  const [unreadCount, setUnreadCount] = useState(0)
  const [notifications, setNotifications] = useState<NotifType[]>([])

  // Keyboard shortcuts cheat sheet
  const [showShortcuts, setShowShortcuts] = useState(false)

  // Feature 2: User Profile Dialog
  const [profileDialogOpen, setProfileDialogOpen] = useState(false)

  // Feature 4: Run Detail Dialog
  const [runDetailDialogOpen, setRunDetailDialogOpen] = useState(false)
  const [selectedRunForDetail, setSelectedRunForDetail] = useState<RunSnapshot | null>(null)

  // AI Features state — temporarily disabled
  // const [aiBugTriageOpen, setAiBugTriageOpen] = useState(false)
  // const [aiTriageTest, setAiTriageTest] = useState<{ id: string; name: string; error?: string } | null>(null)
  // const [aiFailureAnalysisOpen, setAiFailureAnalysisOpen] = useState(false)
  // const [aiAnalysisTest, setAiAnalysisTest] = useState<{ id: string; name: string; error?: string } | null>(null)

  // Phase 4: Run Comparison Dialog
  const [runComparisonOpen, setRunComparisonOpen] = useState(false)

  // Phase 4: Screenshot Gallery state
  const [screenshotEntries, setScreenshotEntries] = useState<ScreenshotEntry[]>([])
  const [lightboxOpen, setLightboxOpen] = useState(false)
  const [lightboxIndex, setLightboxIndex] = useState(0)
  const [screenshotCompareOpen, setScreenshotCompareOpen] = useState(false)
  const [compareScreenshots, setCompareScreenshots] = useState<[ScreenshotEntry | null, ScreenshotEntry | null]>([null, null])

  // ─── Real-time WebSocket notifications ──────────────────────
  const { connected: wsConnected, on: wsOn } = useNotificationsSocket(user?.id)

  // Initial load + periodic refresh (fallback)
  const refreshNotifications = useCallback(async () => {
    setUnreadCount(await getUnreadNotificationCount())
    setNotifications(await getNotifications())
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refreshNotifications()
    const interval = setInterval(refreshNotifications, 30000) // Reduced from 2s to 30s
    return () => clearInterval(interval)
  }, [refreshNotifications])

  // ─── Fetch real modules from API ──────────────────────
  useEffect(() => {
    if (!user) return

    fetchModules()
      .then((mods) => {
        setApiModules(mods)
        setSidebarModules(filterSidebarByAccess(buildSidebarModules(mods), user))
        if (mods.length > 0) {
          syncModulesToDB(mods).catch(() => {})
        }
      })
      .catch(async () => {
        try {
          const res = await fetch('/api/admin/modules')
          if (res.ok) {
            const data = await res.json()
            const dbMods = data.modules || []
            if (dbMods.length > 0) {
              const sidebarFromDb: SidebarModule[] = [
                { id: 'dashboard', label: 'Dashboard' },
              ]
              const parents = dbMods.filter((m: Record<string, unknown>) => !m.parentId && m.status === 'active')
              for (const parent of parents) {
                const children = dbMods
                  .filter((m: Record<string, unknown>) => m.parentId === (parent as Record<string, unknown>).id && m.status === 'active')
                  .sort((a: Record<string, unknown>, b: Record<string, unknown>) => ((a.sortOrder as number) || 0) - ((b.sortOrder as number) || 0))
                const hasChildren = children.length > 0
                const testCount = (parent.testCount as number) || 0
                const childTotal = children.reduce((s: number, c: Record<string, unknown>) => s + ((c.testCount as number) || 0), 0)
                const totalTests = testCount + childTotal
                sidebarFromDb.push({
                  id: (parent.name as string).toLowerCase().replace(/\s+/g, '-'),
                  label: parent.label as string,
                  badge: totalTests > 0 ? `${totalTests} tests` : undefined,
                  badgeType: totalTests > 0 ? 'success' : 'none',
                  defaultExpanded: hasChildren,
                  children: hasChildren ? children.map((c: Record<string, unknown>) => ({
                    id: (c.name as string).toLowerCase().replace(/\s+/g, '-'),
                    label: c.label as string,
                    badge: (c.testCount as number) > 0 ? `${c.testCount} tests` : '📝 No tests',
                    badgeType: (c.testCount as number) > 0 ? 'success' as const : 'none' as const,
                  })) : undefined,
                })
              }
              sidebarFromDb.push({ id: 'my-tickets', label: 'My Tickets' })
              setSidebarModules(filterSidebarByAccess(sidebarFromDb, user))
            } else {
              setSidebarModules(filterSidebarByAccess(ALL_SIDEBAR_MODULES, user))
            }
          } else {
            setSidebarModules(filterSidebarByAccess(ALL_SIDEBAR_MODULES, user))
          }
        } catch {
          setSidebarModules(filterSidebarByAccess(ALL_SIDEBAR_MODULES, user))
        }
      })
  }, [user])

  // Fetch test cases from backend
  useEffect(() => {
    if (!user) return
    fetchTestCases()
      .then((data) => {
        setAllTestCases(data)
        if (typeof window !== 'undefined') {
          (window as any).__ALL_TEST_CASES__ = data
        }
      })
      .catch(() => {})
  }, [user])

  const handleMarkAllRead = useCallback(async () => {
    await markAllNotificationsRead()
    setUnreadCount(0)
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))
  }, [])

  // Feature 5: Run history
  const [runHistory, setRunHistory] = useState<RunSnapshot[]>([])
  const currentRunIdRef = useRef<string | null>(null)
  const [consoleLogs, setConsoleLogs] = useState<string[]>(['> Waiting for tests to start...', '> Select tests in Test Runner and click Run.'])
  const [bugReportsList, setBugReportsList] = useState<{ id: string; testId: string; desc: string; status: string }[]>([])

  // Load run history from Prisma
  const loadRunHistory = useCallback(async () => {
    try {
      const res = await fetch('/api/runs?limit=50')
      if (res.ok) {
        const data = await res.json()
        const mapped: RunSnapshot[] = (data as Array<{
          id: string; moduleId: string; moduleName: string; passed: number; failed: number;
          total: number; duration: string; rate: number;
          results: { testId: string; status: string }[] | null; startedAt: string;
          completedAt: string | null; status: string;
        }>).map((r) => ({
          id: r.id,
          date: r.startedAt ? new Date(r.startedAt).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—',
          moduleId: r.moduleId,
          results: Array.isArray(r.results) ? r.results.map((x: { testId: string; status: string }) => ({
            testId: x.testId, status: x.status === 'passed' ? 'passed' as const : 'failed' as const,
          })) : [],
          passed: r.passed || 0, failed: r.failed || 0, total: r.total || 0,
          duration: r.duration || '—', rate: r.rate || 0,
        }))
        setRunHistory(mapped)
      }
    } catch {}
  }, [])

  // Load bug reports from Prisma
  const loadBugReports = useCallback(async () => {
    try {
      const reports = await getBugReports()
      setBugReportsList(reports.map((r) => ({
        id: r.id, testId: r.testId, desc: r.error || r.testDescription,
        status: r.status === 'open' ? 'Open' : r.status === 'in_progress' ? 'In Progress' : 'Fixed',
      })))
    } catch {}
  }, [])

  // Load dashboard stats
  const loadDashboardStats = useCallback(async () => {
    setDashboardLoading(true)
    try {
      const res = await fetch('/api/dashboard/stats')
      if (res.ok) { const data = await res.json(); setDashboardStats(data) }
    } catch {} finally { setDashboardLoading(false) }
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (selectedModule === 'dashboard') loadDashboardStats()
  }, [selectedModule, loadDashboardStats])

  useEffect(() => {
    if (!user) return
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadRunHistory()
    loadBugReports()
  }, [user, loadRunHistory, loadBugReports])

  // ─── WebSocket event handlers (after loadRunHistory/loadDashboardStats) ──
  useEffect(() => {
    const unsubRunComplete = wsOn('run_complete', (data) => {
      toast.success(`Run complete: ${data.moduleName}`, { description: `${data.passed}/${data.total} passed (${data.rate}% pass rate)` })
      refreshNotifications()
      loadRunHistory()
      if (selectedModule === 'dashboard') loadDashboardStats()
    })

    const unsubBugReply = wsOn('bug_reply', (data) => {
      toast.info(`Reply on bug #${data.bugReportId}`, { description: `${data.replyAuthor}: ${data.message}` })
      refreshNotifications()
    })

    const unsubBugStatus = wsOn('bug_status_change', (data) => {
      toast.info(`Bug #${data.bugReportId} updated`, { description: `Status changed to ${data.newStatus} by ${data.changedBy}` })
      refreshNotifications()
    })

    const unsubNotif = wsOn('notification', (data) => {
      toast.info(data.title, { description: data.message })
      refreshNotifications()
    })

    return () => {
      unsubRunComplete()
      unsubBugReply()
      unsubBugStatus()
      unsubNotif()
    }
  }, [wsOn, refreshNotifications, loadRunHistory, loadDashboardStats, selectedModule])

  // Compute module health
  const moduleHealth = useMemo(() => {
    const moduleInfo = new Map<string, { name: string; parentGroup: string }>()
    function collectModules(items: SidebarModule[], parent?: string) {
      for (const item of items) {
        if (item.id !== 'dashboard' && item.id !== 'my-tickets') {
          const group = parent || (item.children ? item.label : undefined) || 'Standalone'
          moduleInfo.set(item.id, { name: item.label, parentGroup: group })
          if (item.children) collectModules(item.children, item.label)
        }
      }
    }
    collectModules(sidebarModules)
    const runsByModule = new Map<string, RunSnapshot[]>()
    for (const run of runHistory) {
      const existing = runsByModule.get(run.moduleId) || []
      existing.push(run)
      runsByModule.set(run.moduleId, existing)
    }
    const health: ModuleHealth[] = []
    for (const [modId, info] of moduleInfo) {
      const runs = runsByModule.get(modId) || []
      if (runs.length === 0) {
        health.push({ moduleId: modId, moduleName: info.name, parentGroup: info.parentGroup, passRate: 0, totalTests: 0, passedTests: 0, failedTests: 0, lastRun: '—' })
      } else {
        const latestRun = runs[0]
        const passedTests = latestRun.passed
        const failedTests = latestRun.failed
        const totalTests = latestRun.total
        const passRate = totalTests > 0 ? Math.round((passedTests / totalTests) * 100) : 0
        const sortedRuns = [...runs].reverse().slice(-7)
        const trend = sortedRuns.map((r) => r.total > 0 ? Math.round((r.passed / r.total) * 100) : 0)
        health.push({ moduleId: modId, moduleName: info.name, parentGroup: info.parentGroup, passRate, totalTests, passedTests, failedTests, lastRun: latestRun.date, trend })
      }
    }
    return health
  }, [runHistory, sidebarModules])

  // Dark mode
  const [navToast, setNavToast] = useState<{ key: number; label: string; parent?: string | null } | null>(null)
  const { theme, setTheme } = useTheme()
  const darkMode = theme === 'dark'
  const toggleDarkMode = useCallback(() => { setTheme(darkMode ? 'light' : 'dark') }, [darkMode, setTheme])

  // Auto-hide sidebar on Live Execution
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (activeTab === 'live-execution') setSidebarOpen(false)
    else setSidebarOpen(true)
  }, [activeTab])

  // Feature 1: Detect run completion
  useEffect(() => {
    if (prevIsRunningRef.current && !isRunning) {
      const passed = tests.filter((t) => t.status === 'passed').length
      const failed = tests.filter((t) => t.status === 'failed').length
      const total = passed + failed
      if (total > 0) {
        const durations = tests.filter((t) => t.duration && t.duration !== '—' && t.duration !== '...' && t.duration !== '').map((t) => { const parts = t.duration.split(':'); return parseInt(parts[0]) * 60 + parseInt(parts[1]) })
        const totalSecs = durations.reduce((a, b) => a + b, 0)
        const mins = Math.floor(totalSecs / 60); const secs = totalSecs % 60
        const durationStr = `${mins}:${String(secs).padStart(2, '0')}`
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setCompletionStats({ passed, failed, duration: durationStr })
        setCompletionModalOpen(true)
        const moduleName = (() => {
          for (const mod of sidebarModules) {
            if (mod.id === selectedModule) return mod.label
            if (mod.children) { const child = mod.children.find(c => c.id === selectedModule); if (child) return child.label }
          }
          return selectedModule
        })()
        fetch('/api/runs', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ moduleId: selectedModule, moduleName, passed, failed, total, duration: durationStr, rate: total > 0 ? Math.round((passed / total) * 100) : 0, results: tests.filter(t => t.status === 'passed' || t.status === 'failed').map(t => ({ testId: t.id, status: t.status })), status: 'completed', startedAt: new Date().toISOString(), completedAt: new Date().toISOString() }),
        }).then(() => { loadRunHistory() }).catch(() => {})
        currentRunIdRef.current = null
      }
    }
    prevIsRunningRef.current = isRunning
  }, [isRunning, tests, selectedModule, sidebarModules, loadRunHistory])

  // Check session on mount
  useEffect(() => {
    const init = async () => {
      try {
        await fetch('/api/auth/seed', { method: 'POST' })
        const res = await fetch('/api/auth/me')
        if (res.ok) { const data = await res.json(); setUser(data.user); setSidebarModules(filterSidebarByAccess(ALL_SIDEBAR_MODULES, data.user)) }
      } catch {} finally { setLoading(false) }
    }
    init()
  }, [])

  const handleLogin = useCallback((u: AuthUser) => {
    setUser(u); setSidebarModules(filterSidebarByAccess(ALL_SIDEBAR_MODULES, u)); setSelectedModule('dashboard')
  }, [])

  const handleLogout = useCallback(async () => {
    await fetch('/api/auth/logout', { method: 'POST' }); setUser(null)
  }, [])

  const toggleExpand = useCallback((id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) { next.delete(id); setJustExpandedId(null) }
      else {
        const isTopLevel = ALL_SIDEBAR_MODULES.some(m => m.id === id)
        if (isTopLevel) { ALL_SIDEBAR_MODULES.forEach(m => next.delete(m.id)) }
        else {
          const findSiblings = (modules: SidebarModule[]): string[] => {
            for (const mod of modules) {
              if (mod.id === id) return []
              if (mod.children) {
                const childIds = mod.children.map(c => c.id)
                if (childIds.includes(id)) return mod.children.filter(c => c.children && c.children.length > 0).map(c => c.id)
                const deeper = findSiblings(mod.children); if (deeper.length > 0) return deeper
              }
            }
            return []
          }
          const siblings = findSiblings(ALL_SIDEBAR_MODULES); siblings.forEach(s => next.delete(s))
        }
        next.add(id); setJustExpandedId(id)
      }
      return next
    })
  }, [])

  useEffect(() => {
    if (justExpandedId) { const timer = setTimeout(() => setJustExpandedId(null), 600); return () => clearTimeout(timer) }
  }, [justExpandedId])

  // Hash routing
  useEffect(() => {
    const readHash = () => {
      const h = window.location.hash.slice(1)
      if (h) { const [mod, tab] = h.split('/'); if (mod && mod !== 'dashboard') setSelectedModule(mod); if (tab) setActiveTab(tab) }
      setHashReady(true)
    }
    readHash(); window.addEventListener('hashchange', readHash); return () => window.removeEventListener('hashchange', readHash)
  }, [])

  useEffect(() => {
    if (!hashReady) return
    const hash = selectedModule === 'dashboard' ? '' : activeTab === 'operations' ? selectedModule : selectedModule + '/' + activeTab
    window.location.hash = hash
  }, [selectedModule, activeTab, hashReady])

  const handleSelectModule = useCallback((id: string) => {
    setSelectedModule(id)
    const found = (() => {
      for (const mod of sidebarModules) {
        if (mod.id === id) return { label: mod.label, parent: null }
        for (const child of mod.children ?? []) { if (child.id === id) return { label: child.label, parent: mod.label }; for (const grand of child.children ?? []) { if (grand.id === id) return { label: grand.label, parent: child.label } } }
      }
      return { label: id, parent: null }
    })()
    setNavToast({ key: Date.now(), label: found.label, parent: found.parent })
    setActiveTab('operations')
    setTestChecks(new Set())
    const moduleKey = id.toLowerCase().replace(" ", "_").replace("-", "_")
    if (allTestCases[moduleKey]) {
      const moduleData = allTestCases[moduleKey]
      const mapTestCaseStatus = (s: string): TestSpecItem['status'] => { const upper = s.toUpperCase().trim(); if (upper === 'PASSED' || upper === 'PASS') return 'passed'; if (upper === 'BUG') return 'bug'; if (upper === 'TODO') return 'todo'; if (upper === 'FAILED' || upper === 'FAIL') return 'failed'; return 'not-run' }
      const specGroups: TestClassGroup[] = [{ className: moduleData.label, tests: moduleData.tests.map((t) => ({ id: t.id, screenName: t.screenName, description: t.description, status: mapTestCaseStatus(t.status), duration: '', steps: t.steps, expected: t.expected, actual: t.actual || '', bugDetails: t.status === 'BUG' ? t.actual : undefined, priority: undefined, date: t.date || undefined })) }]
      setCurrentTestGroups(specGroups)
      const mapToTestItemStatus = (s: string): 'passed' | 'failed' | 'pending' => { const upper = s.toUpperCase().trim(); if (upper === 'PASSED' || upper === 'PASS') return 'passed'; if (upper === 'BUG' || upper === 'FAILED' || upper === 'FAIL') return 'failed'; return 'pending' }
      setTests(moduleData.tests.map((t) => ({ id: t.id, name: t.description, status: mapToTestItemStatus(t.status), duration: '' })))
    } else {
      const { groups, items } = getTestsForSidebarModule(id, apiModules)
      if (groups.length > 0) { setCurrentTestGroups(groups); setTests(items) }
      else { setCurrentTestGroups([]); setTests([]) }
    }
  }, [apiModules, allTestCases])

  // Re-load current module tests when data changes
  useEffect(() => {
    if (selectedModule === 'dashboard' || selectedModule === 'my-tickets') return
    const moduleKey = selectedModule.toLowerCase().replace(" ", "_").replace("-", "_")
    if (allTestCases[moduleKey]) {
      const moduleData = allTestCases[moduleKey]
      const mapTestCaseStatus = (s: string): TestSpecItem['status'] => { const upper = s.toUpperCase().trim(); if (upper === 'PASSED' || upper === 'PASS') return 'passed'; if (upper === 'BUG') return 'bug'; if (upper === 'TODO') return 'todo'; if (upper === 'FAILED' || upper === 'FAIL') return 'failed'; return 'not-run' }
      const specGroups: TestClassGroup[] = [{ className: moduleData.label, tests: moduleData.tests.map((t) => ({ id: t.id, screenName: t.screenName, description: t.description, status: mapTestCaseStatus(t.status), duration: '', steps: t.steps, expected: t.expected, actual: t.actual || '', bugDetails: t.status === 'BUG' ? t.actual : undefined, priority: undefined, date: t.date || undefined })) }]
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setCurrentTestGroups(specGroups)
      const mapToTestItemStatus = (s: string): 'passed' | 'failed' | 'pending' => { const upper = s.toUpperCase().trim(); if (upper === 'PASSED' || upper === 'PASS') return 'passed'; if (upper === 'BUG' || upper === 'FAILED' || upper === 'FAIL') return 'failed'; return 'pending' }
      setTests(moduleData.tests.map((t) => ({ id: t.id, name: t.description, status: mapToTestItemStatus(t.status), duration: '' })))
    } else {
      const { groups, items } = getTestsForSidebarModule(selectedModule, apiModules)
      if (groups.length > 0) { setCurrentTestGroups(groups); setTests(items) }
    }
  }, [allTestCases, apiModules, selectedModule])

  const handleGoHome = useCallback(() => { setSelectedModule('dashboard'); setActiveTab('operations'); setSidebarOpen(true) }, [])

  const handleRunModule = useCallback((moduleId: string) => {
    handleSelectModule(moduleId)
    setTimeout(() => { setActiveTab('test-runner') }, 100)
  }, [handleSelectModule])

  const toggleTestCheck = useCallback((id: string) => {
    setTestChecks((prev) => { const next = new Set(prev); if (next.has(id)) next.delete(id); else next.add(id); return next })
  }, [])

  const rerunTestIds = useCallback((ids: string[]) => {
    setTests((prev) => prev.map((t) => (ids.includes(t.id) ? { ...t, status: 'pending' as const, duration: '' } : t)))
    setTestChecks(new Set(ids))
  }, [])

  const getTestError = useCallback((id: string): string | undefined => {
    for (const g of testSpecGroups) { const t = g.tests.find((x) => x.id === id); if (t) return t.bugDetails || (t.status === 'bug' ? t.actual : undefined) }
    for (const g of currentTestGroups) { const t = g.tests.find((x) => x.id === id); if (t) return t.bugDetails || (t.status === 'bug' ? t.actual : undefined) }
    return undefined
  }, [currentTestGroups])

  // Mock run animation
  const runTests = useCallback(
    (selectedOnly: boolean, forceIds?: string[]) => {
      if (isRunning) return
      let testsToRun: TestItem[]
      if (forceIds) testsToRun = tests.filter((t) => forceIds.includes(t.id))
      else if (selectedOnly) testsToRun = tests.filter((t) => testChecks.has(t.id))
      else testsToRun = tests.filter((t) => t.status === 'pending' || t.status === 'failed')
      if (testsToRun.length === 0) { toast.info('No tests to run'); return }
      const mapping = sidebarToFolderMapping(selectedModule)
      if (!mapping) { toast.error('Cannot determine module path for: ' + selectedModule); return }
      setTests((prev) => prev.map((t) => testsToRun.some((r) => r.id === t.id) ? { ...t, status: (t.id === testsToRun[0].id ? 'running' as const : 'pending' as const), duration: '' } : t))
      setIsRunning(true); setRunningProgress('Starting tests...'); setActiveTab('live-execution'); setConsoleLogs([])
      const testNames = testsToRun.map((t) => t.id)
      const runOnlyTests = selectedOnly || forceIds ? testNames : null
      startRun(mapping.module, mapping.subModule, runOnlyTests,
        (event) => {
          if (!currentRunIdRef.current && (event as Record<string, unknown>).run_id) currentRunIdRef.current = (event as Record<string, unknown>).run_id as string
          if (event.type === 'log') { setRunningProgress(event.message); setConsoleLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${event.message}`]) }
          else if (event.type === 'test_end') {
            const statusLabel = event.status === 'passed' ? 'PASSED' : event.status === 'failed' ? 'FAILED' : 'SKIPPED'
            setConsoleLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${event.test_name} — ${statusLabel}${event.message ? ': ' + event.message : ''}`])
            if (event.test_name && event.status) {
              const testId = testsToRun.find((t) => t.id.endsWith('::' + event.test_name))?.id || testsToRun.find((t) => t.id.includes(event.test_name || ''))?.id
              if (testId) {
                setTests((prev) => prev.map((t) => t.id === testId ? { ...t, status: event.status === 'passed' ? ('passed' as const) : event.status === 'failed' ? ('failed' as const) : ('pending' as const), duration: event.duration ? `${(event.duration / 1000).toFixed(1)}s` : '--' } : t))
                if (event.status === 'failed') toast.error(`Failed: ${event.test_name}`, { description: event.message || '', duration: 8000 })
              }
            }
          } else if (event.type === 'run_end') { setRunningProgress('Run complete!'); setConsoleLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] Run complete!`]) }
          else if (event.type === 'error') { toast.error('Run error', { description: event.message, duration: 8000 }); setConsoleLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ERROR: ${event.message}`]) }
        },
        (summary: RunCompletionSummary) => {
          setIsRunning(false); setRunningProgress(''); toast.success('Test run finished!')
          if (summary.total > 0) {
            saveRunResults(summary, user?.id).then((saved) => { if (saved) { loadRunHistory(); if (selectedModule === 'dashboard') loadDashboardStats(); addNotification({ type: 'run_complete', title: `Run complete: ${summary.passed}/${summary.total} passed`, message: `${summary.module}${summary.subModule ? ' → ' + summary.subModule : ''} — ${summary.failed} failed, ${summary.passed} passed` }).catch(() => {}) } })
          }
        },
        (err) => { setIsRunning(false); setRunningProgress(''); toast.error('Connection failed', { description: err.message, duration: 8000 }) }
      )
    },
    [isRunning, tests, testChecks, selectedModule, user, loadRunHistory, loadDashboardStats]
  )

  const runByPriority = useCallback((priority: TestPriority) => {
    if (isRunning) return
    const priorityIds = tests.filter((t) => t.priority === priority).map((t) => t.id)
    if (priorityIds.length === 0) return
    rerunTestIds(priorityIds); runTests(true, priorityIds); setActiveTab('live-execution')
  }, [isRunning, tests, rerunTestIds, runTests])

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement
      const isInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable
      if (e.key === 'Escape') { if (quickSwitcherOpen) { setQuickSwitcherOpen(false); return } if (showShortcuts) { setShowShortcuts(false); return } if (notifDropdownOpen) { setNotifDropdownOpen(false); return } }
      if (isInput) return
      if (!(e.ctrlKey || e.metaKey)) return
      if (e.key === 'b') { e.preventDefault(); setSidebarOpen((prev) => !prev); return }
      if (e.key === 'k') { e.preventDefault(); setQuickSwitcherOpen((prev) => !prev); setQuickSearch(''); return }
      if (e.key === 'd') { e.preventDefault(); toggleDarkMode(); return }
      if (e.key === '/') { e.preventDefault(); setShowShortcuts((prev) => !prev); return }
      if (e.key === 'r' && selectedModule !== 'dashboard' && selectedModule !== 'my-tickets' && !isRunning) { e.preventDefault(); const pc = tests.filter((t) => t.status === 'pending').length; if (pc > 0) { runTests(false); setActiveTab('live-execution') }; return }
      if (selectedModule !== 'dashboard' && selectedModule !== 'my-tickets') { const tabMap: Record<string, string> = { '1': 'operations', '2': 'test-runner', '3': 'live-execution', '4': 'results', '5': 'screenshots', '6': 'schedule' }; const tabId = tabMap[e.key]; if (tabId) { e.preventDefault(); setActiveTab(tabId) } }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [quickSwitcherOpen, showShortcuts, notifDropdownOpen, selectedModule, isRunning, tests, toggleDarkMode, runTests])

  const passedCount = tests.filter((t) => t.status === 'passed').length
  const failedCount = tests.filter((t) => t.status === 'failed').length

  const getModulePath = useCallback(() => {
    for (const mod of sidebarModules) {
      if (mod.id === selectedModule) return { parent: null, name: mod.label, badge: mod.badge }
      if (mod.children) { for (const child of mod.children) { if (child.id === selectedModule) return { parent: mod.label, name: child.label, badge: child.badge } } }
    }
    return { parent: null, name: selectedModule, badge: undefined }
  }, [selectedModule])
  const modulePath = getModulePath()

  const handleViewResults = useCallback(() => { setCompletionModalOpen(false); setActiveTab('results') }, [])
  const handleCompletionRerunFailed = useCallback(() => {
    setCompletionModalOpen(false)
    const failedIds = tests.filter((t) => t.status === 'failed').map((t) => t.id)
    if (failedIds.length > 0) { rerunTestIds(failedIds); runTests(true, failedIds); setActiveTab('live-execution') }
  }, [tests, rerunTestIds, runTests])
  const handleNewRun = useCallback(() => { setCompletionModalOpen(false); setTests(initialTests); setTestChecks(new Set()); setActiveTab('test-runner') }, [])
  const handleReportTest = useCallback((test: TestItem) => { const error = getTestError(test.id); setReportingTest({ id: test.id, name: test.name, error }); setReportDialogOpen(true) }, [getTestError])

  // AI Feature handlers — temporarily disabled
  // const handleAiTriage = useCallback((test: TestItem) => { const error = getTestError(test.id); setAiTriageTest({ id: test.id, name: test.name, error }); setAiBugTriageOpen(true) }, [getTestError])
  // const handleAiFailureAnalysis = useCallback((test: TestItem) => { const error = getTestError(test.id); setAiAnalysisTest({ id: test.id, name: test.name, error }); setAiFailureAnalysisOpen(true) }, [getTestError])
  // const handleAiNlApply = useCallback((testIds: string[], _runType: string) => { setTestChecks(new Set(testIds)); setActiveTab('test-runner'); toast.success(`${testIds.length} tests selected by AI`) }, [])

  // ─── Dashboard Render Function ────────────────────────────
  const renderDashboard = () => {
    const stats = dashboardStats as Record<string, any> | null
    const totalTests = (stats?.totalTests as number) ?? 0
    const totalPassed = (stats?.totalPassed as number) ?? 0
    const totalFailed = (stats?.totalFailed as number) ?? 0
    const passRate = (stats?.passRate as number) ?? 0
    const totalBugs = (stats?.totalBugs as number) ?? 0
    const openBugs = (stats?.openBugs as number) ?? 0
    const inProgressBugs = (stats?.inProgressBugs as number) ?? 0
    const fixedBugs = (stats?.fixedBugs as number) ?? 0
    const highPriorityBugs = (stats?.highPriorityBugs as number) ?? 0
    const totalRuns = (stats?.totalRuns as number) ?? 0
    const completedRuns = (stats?.completedRuns as number) ?? 0
    const failedRuns = (stats?.failedRuns as number) ?? 0
    const activeUsers = (stats?.activeUsers as number) ?? 0
    const activeModules = (stats?.activeModules as number) ?? 0
    const activeEnvs = (stats?.activeEnvs as number) ?? 0
    const recentRuns = (stats?.recentRuns as Array<Record<string, any>>) ?? []
    const recentBugs = (stats?.recentBugs as Array<Record<string, any>>) ?? []
    const bugTrend = (stats?.bugTrend as Array<{ date: string; count: number }>) ?? []
    const runTrend = (stats?.runTrend as Array<Record<string, any>>) ?? []
    const apiModuleHealth = (stats?.moduleHealth as Array<Record<string, any>>) ?? []
    const bugByPriority = (stats?.bugByPriority as Record<string, number>) ?? {}
    const bugByStatus = (stats?.bugByStatus as Record<string, number>) ?? {}
    const apiRunHistory: RunSnapshot[] = runTrend.map((r) => ({ id: r.id ?? '', date: r.startedAt ?? '', moduleId: r.moduleName ?? '', results: [], passed: r.passed ?? 0, failed: r.failed ?? 0, total: r.total ?? 0, duration: r.duration ?? '—', rate: r.passRate ?? 0 }))
    const apiModuleHealthData: ModuleHealth[] = apiModuleHealth.map((m) => ({ moduleId: m.moduleName ?? '', moduleName: m.moduleName ?? '', passRate: m.passRate ?? 0, totalTests: m.total ?? 0, passedTests: m.passed ?? 0, failedTests: m.failed ?? 0, lastRun: '' }))
    const chartRunHistory = apiRunHistory.length > 0 ? apiRunHistory : runHistory
    const chartModuleHealth = apiModuleHealthData.length > 0 ? apiModuleHealthData : moduleHealth
    const bugTrendData = bugTrend.map((b) => b.count)
    const runTrendData = runTrend.map((r) => r.passRate ?? 0)

    return (
      <div data-tour="dashboard" className="flex-1 min-h-0 overflow-auto">
        <div className="p-5 space-y-5">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-[18px] font-semibold text-[#333333] dark:text-gray-100 font-['Poppins']">Dashboard</h2>
              <p className="text-[13px] text-[#666666] dark:text-gray-400 mt-0.5 font-['Manrope']">Overview of all RhythmERP automation modules</p>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" onClick={loadDashboardStats} disabled={dashboardLoading} className="h-8 px-3 text-[12px] text-[#666666] dark:text-gray-400 hover:text-[#3F51B5] dark:hover:text-indigo-400">
                <RefreshCw className={`size-3.5 mr-1 ${dashboardLoading ? 'animate-spin' : ''}`} />Refresh
              </Button>
              <ExportMenu runHistory={runHistory} moduleHealth={moduleHealth} />
            </div>
          </div>
          {dashboardLoading && !dashboardStats && (
            <div className="flex items-center justify-center py-20"><div className="flex flex-col items-center gap-3"><Loader2 className="size-8 text-[#3F51B5] animate-spin" /><span className="text-[13px] text-[#888888] dark:text-gray-400 font-['Manrope']">Loading dashboard stats...</span></div></div>
          )}
          {/* Stat Cards Row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
              <div className="flex items-center justify-between mb-2"><div className="flex items-center gap-2"><div className="w-8 h-8 rounded-lg bg-[#E8F5E9] dark:bg-green-900/30 flex items-center justify-center"><CheckCircle2 className="size-4 text-[#4CAF50]" /></div><span className="text-[11px] text-[#888888] dark:text-gray-400 font-medium uppercase tracking-wider font-['Poppins']">Total Tests</span></div>{runTrendData.length >= 2 && <Sparkline data={runTrendData} width={56} height={18} strokeColor={runTrendData[runTrendData.length - 1] >= runTrendData[runTrendData.length - 2] ? '#22c55e' : '#ef4444'} fillColor={runTrendData[runTrendData.length - 1] >= runTrendData[runTrendData.length - 2] ? '#22c55e' : '#ef4444'} strokeWidth={1.5} />}</div>
              <div className="text-xl font-bold text-[#333333] dark:text-gray-100 font-['Poppins']">{totalTests.toLocaleString()}</div>
              <div className="flex items-center gap-2 mt-1"><span className="text-[11px] text-[#4CAF50] dark:text-green-400 font-medium font-['Manrope']">{totalPassed.toLocaleString()} passed</span><span className="text-[11px] text-[#888888] dark:text-gray-500">•</span><span className="text-[11px] text-[#F44336] dark:text-red-400 font-medium font-['Manrope']">{totalFailed.toLocaleString()} failed</span></div>
              <div className="mt-2"><Progress value={passRate} className="h-1.5 bg-gray-100 dark:bg-gray-700" /><span className="text-[10px] text-[#3F51B5] dark:text-indigo-400 font-medium font-['Manrope']">{passRate.toFixed(1)}% pass rate</span></div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
              <div className="flex items-center justify-between mb-2"><div className="flex items-center gap-2"><div className="w-8 h-8 rounded-lg bg-[#FFEBEE] dark:bg-red-900/30 flex items-center justify-center"><Bug className="size-4 text-[#F44336]" /></div><span className="text-[11px] text-[#888888] dark:text-gray-400 font-medium uppercase tracking-wider font-['Poppins']">Total Bugs</span></div>{bugTrendData.length >= 2 && <Sparkline data={bugTrendData} width={56} height={18} strokeColor="#F44336" fillColor="#F44336" strokeWidth={1.5} />}</div>
              <div className="text-xl font-bold text-[#333333] dark:text-gray-100 font-['Poppins']">{totalBugs.toLocaleString()}</div>
              <div className="flex items-center gap-2 mt-1"><span className="text-[11px] text-[#F44336] dark:text-red-400 font-medium font-['Manrope']">{openBugs} open</span><span className="text-[11px] text-[#888888] dark:text-gray-500">•</span><span className="text-[11px] text-[#FF9800] dark:text-orange-400 font-medium font-['Manrope']">{inProgressBugs} in progress</span></div>
              {highPriorityBugs > 0 && <div className="flex items-center gap-1 mt-1.5"><AlertTriangle className="size-3 text-[#FF9800]" /><span className="text-[10px] text-[#FF9800] dark:text-orange-400 font-medium font-['Manrope']">{highPriorityBugs} high priority</span></div>}
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
              <div className="flex items-center gap-2 mb-2"><div className="w-8 h-8 rounded-lg bg-[#DFE9FB] dark:bg-indigo-900/30 flex items-center justify-center"><Play className="size-4 text-[#3F51B5]" /></div><span className="text-[11px] text-[#888888] dark:text-gray-400 font-medium uppercase tracking-wider font-['Poppins']">Total Runs</span></div>
              <div className="text-xl font-bold text-[#333333] dark:text-gray-100 font-['Poppins']">{totalRuns.toLocaleString()}</div>
              <div className="flex items-center gap-2 mt-1"><span className="text-[11px] text-[#4CAF50] dark:text-green-400 font-medium font-['Manrope']">{completedRuns} completed</span><span className="text-[11px] text-[#888888] dark:text-gray-500">•</span><span className="text-[11px] text-[#F44336] dark:text-red-400 font-medium font-['Manrope']">{failedRuns} failed</span></div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
              <div className="flex items-center gap-2 mb-2"><div className="w-8 h-8 rounded-lg bg-[#FFF3E0] dark:bg-orange-900/30 flex items-center justify-center"><LayoutDashboard className="size-4 text-[#FF9800]" /></div><span className="text-[11px] text-[#888888] dark:text-gray-400 font-medium uppercase tracking-wider font-['Poppins']">Active Modules</span></div>
              <div className="text-xl font-bold text-[#333333] dark:text-gray-100 font-['Poppins']">{activeModules}</div>
              <div className="flex items-center gap-2 mt-1"><span className="text-[11px] text-[#888888] dark:text-gray-400 font-['Manrope']">{activeUsers} users</span><span className="text-[11px] text-[#888888] dark:text-gray-500">•</span><span className="text-[11px] text-[#888888] dark:text-gray-400 font-['Manrope']">{activeEnvs} envs</span></div>
            </div>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700"><h3 className="text-[13px] font-semibold text-[#333333] dark:text-gray-100 mb-3 flex items-center gap-2 font-['Poppins']"><LayoutDashboard className="size-4 text-[#3F51B5]" />Pass Rate Trend</h3><PassRateTrendChart runHistory={chartRunHistory} /></div>
            <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700"><h3 className="text-[13px] font-semibold text-[#333333] dark:text-gray-100 mb-3 flex items-center gap-2 font-['Poppins']"><AlertTriangle className="size-4 text-[#F44336]" />Bug Distribution</h3><BugDistributionPie moduleHealth={chartModuleHealth} /></div>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700"><h3 className="text-[13px] font-semibold text-[#333333] dark:text-gray-100 mb-3 flex items-center gap-2 font-['Poppins']"><BarChart3 className="size-4 text-[#3F51B5]" />Module Health Overview</h3><ModuleHealthBarChart moduleHealth={chartModuleHealth} /></div>
            <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
              <h3 className="text-[13px] font-semibold text-[#333333] dark:text-gray-100 mb-3 flex items-center gap-2 font-['Poppins']"><Activity className="size-4 text-[#3F51B5]" />Bug Status &amp; Priority</h3>
              <div className="grid grid-cols-2 gap-4">
                <div><div className="text-[11px] text-[#888888] dark:text-gray-400 font-medium uppercase tracking-wider mb-2 font-['Poppins']">By Status</div><div className="space-y-2">{Object.entries(bugByStatus).map(([status, count]) => { const statusColors: Record<string, string> = { open: 'bg-[#F44336] text-white', in_progress: 'bg-[#FF9800] text-white', fixed: 'bg-[#4CAF50] text-white', closed: 'bg-[#888888] text-white', rejected: 'bg-gray-400 text-white' }; const statusLabels: Record<string, string> = { open: 'Open', in_progress: 'In Progress', fixed: 'Fixed', closed: 'Closed', rejected: 'Rejected' }; return (<div key={status} className="flex items-center justify-between"><div className="flex items-center gap-1.5"><span className={`w-2 h-2 rounded-full ${statusColors[status]?.split(' ')[0] ?? 'bg-gray-400'}`} /><span className="text-[12px] text-[#333333] dark:text-gray-200 font-['Manrope']">{statusLabels[status] ?? status}</span></div><span className="text-[12px] font-semibold text-[#333333] dark:text-gray-100 font-['Poppins']">{count as number}</span></div>) })}</div></div>
                <div><div className="text-[11px] text-[#888888] dark:text-gray-400 font-medium uppercase tracking-wider mb-2 font-['Poppins']">By Priority</div><div className="space-y-2">{Object.entries(bugByPriority).map(([priority, count]) => { const priorityColors: Record<string, string> = { high: 'bg-[#F44336]', medium: 'bg-[#FF9800]', low: 'bg-[#4CAF50]' }; const priorityLabels: Record<string, string> = { high: 'High', medium: 'Medium', low: 'Low' }; return (<div key={priority} className="flex items-center justify-between"><div className="flex items-center gap-1.5"><span className={`w-2 h-2 rounded-full ${priorityColors[priority] ?? 'bg-gray-400'}`} /><span className="text-[12px] text-[#333333] dark:text-gray-200 font-['Manrope']">{priorityLabels[priority] ?? priority}</span></div><span className="text-[12px] font-semibold text-[#333333] dark:text-gray-100 font-['Poppins']">{count as number}</span></div>) })}</div></div>
              </div>
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700"><h3 className="text-[13px] font-semibold text-[#333333] dark:text-gray-100 mb-3 flex items-center gap-2 font-['Poppins']"><Activity className="size-4 text-[#3F51B5]" />Execution Timeline</h3><TestExecutionTimeline runHistory={chartRunHistory} /></div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700"><h3 className="text-[13px] font-semibold text-[#333333] dark:text-gray-100 mb-3 flex items-center gap-2 font-['Poppins']"><Bug className="size-4 text-[#F44336]" />Recent Bugs</h3>{recentBugs.length === 0 ? <div className="text-center py-8"><CheckCircle2 className="size-8 text-[#4CAF50] mx-auto mb-2" /><p className="text-[12px] text-[#888888] dark:text-gray-400 font-['Manrope']">No bugs reported yet</p></div> : <div className="space-y-2 max-h-72 overflow-y-auto">{recentBugs.map((bug) => { const priorityColor: Record<string, string> = { high: 'bg-[#FFEBEE] text-[#C62828] dark:bg-red-900/30 dark:text-red-400', medium: 'bg-[#FFF3E0] text-[#E65100] dark:bg-orange-900/30 dark:text-orange-400', low: 'bg-[#E8F5E9] text-[#2E7D32] dark:bg-green-900/30 dark:text-green-400' }; const statusColor: Record<string, string> = { open: 'bg-[#F44336] text-white', in_progress: 'bg-[#FF9800] text-white', fixed: 'bg-[#4CAF50] text-white', closed: 'bg-[#888888] text-white', rejected: 'bg-gray-400 text-white' }; const statusLabel: Record<string, string> = { open: 'Open', in_progress: 'In Progress', fixed: 'Fixed', closed: 'Closed', rejected: 'Rejected' }; return (<div key={bug.id as string} className="flex items-start gap-2 p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"><div className="flex-1 min-w-0"><div className="flex items-center gap-1.5 mb-0.5"><span className="text-[12px] font-medium text-[#333333] dark:text-gray-100 truncate font-['Manrope']">{(bug.testDescription as string) || (bug.testId as string)}</span></div><div className="flex items-center gap-1.5">{(bug.moduleName as string) && <Badge variant="outline" className="text-[10px] h-4 px-1.5 font-['Manrope']">{bug.moduleName as string}</Badge>}<Badge className={`text-[10px] h-4 px-1.5 ${priorityColor[bug.priority as string] ?? 'bg-gray-100 text-gray-600'}`}>{bug.priority as string}</Badge><Badge className={`text-[10px] h-4 px-1.5 ${statusColor[bug.status as string] ?? 'bg-gray-100 text-gray-600'}`}>{statusLabel[bug.status as string] ?? (bug.status as string)}</Badge></div></div><span className="text-[10px] text-[#888888] dark:text-gray-500 shrink-0 font-['Manrope']">{bug.createdAt ? new Date(bug.createdAt as string).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }) : ''}</span></div>) })}</div>}</div>
            <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700"><h3 className="text-[13px] font-semibold text-[#333333] dark:text-gray-100 mb-3 flex items-center gap-2 font-['Poppins']"><Clock className="size-4 text-[#3F51B5]" />Recent Runs</h3>{recentRuns.length === 0 ? <div className="text-center py-8"><Play className="size-8 text-[#888888] mx-auto mb-2" /><p className="text-[12px] text-[#888888] dark:text-gray-400 font-['Manrope']">No runs recorded yet</p></div> : <div className="space-y-0 max-h-72 overflow-y-auto"><Table><TableHeader><TableRow className="hover:bg-transparent"><TableHead className="text-[10px] h-7 px-2 font-['Poppins']">Module</TableHead><TableHead className="text-[10px] h-7 px-2 font-['Poppins']">Status</TableHead><TableHead className="text-[10px] h-7 px-2 font-['Poppins'] text-right">Passed</TableHead><TableHead className="text-[10px] h-7 px-2 font-['Poppins'] text-right">Failed</TableHead><TableHead className="text-[10px] h-7 px-2 font-['Poppins'] text-right">Rate</TableHead><TableHead className="text-[10px] h-7 px-2 font-['Poppins'] text-right">Duration</TableHead></TableRow></TableHeader><TableBody>{recentRuns.map((run) => { const runStatus = run.status as string; const runRate = (run.rate as number) ?? 0; return (<TableRow key={run.id as string} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer" onClick={() => { if (run.moduleId as string) handleSelectModule(run.moduleId as string) }}><TableCell className="text-[12px] px-2 py-1.5 font-['Manrope'] text-[#333333] dark:text-gray-200 truncate max-w-[120px]">{(run.moduleName as string) || '—'}</TableCell><TableCell className="px-2 py-1.5"><Badge className={`text-[10px] h-4 px-1.5 ${runStatus === 'completed' ? 'bg-[#4CAF50] text-white' : runStatus === 'failed' ? 'bg-[#F44336] text-white' : 'bg-[#FF9800] text-white'}`}>{runStatus === 'completed' ? <CheckCircle2 className="size-2.5 mr-0.5" /> : runStatus === 'failed' ? <XCircle className="size-2.5 mr-0.5" /> : <Clock className="size-2.5 mr-0.5" />}{runStatus.charAt(0).toUpperCase() + runStatus.slice(1)}</Badge></TableCell><TableCell className="text-[12px] px-2 py-1.5 text-right text-[#4CAF50] dark:text-green-400 font-medium font-['Manrope']">{run.passed as number ?? 0}</TableCell><TableCell className="text-[12px] px-2 py-1.5 text-right text-[#F44336] dark:text-red-400 font-medium font-['Manrope']">{run.failed as number ?? 0}</TableCell><TableCell className="text-[12px] px-2 py-1.5 text-right font-medium font-['Manrope']"><span className={runRate >= 80 ? 'text-[#4CAF50] dark:text-green-400' : runRate >= 50 ? 'text-[#FF9800] dark:text-orange-400' : 'text-[#F44336] dark:text-red-400'}>{runRate.toFixed(1)}%</span></TableCell><TableCell className="text-[12px] px-2 py-1.5 text-right text-[#888888] dark:text-gray-400 font-['Manrope']">{(run.duration as string) || '—'}</TableCell></TableRow>) })}</TableBody></Table></div>}</div>
          </div>
          <DashboardTab onSelectModule={handleSelectModule} moduleHealth={moduleHealth} onRunModule={handleRunModule} runHistory={runHistory} />
        </div>
      </div>
    )
  }

  // Loading / Login screen
  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-[#F1F2F7] dark:bg-gray-900">
        <div className="flex flex-col items-center gap-3">
          <Image src="/agdi-logo-new.webp" alt="AgDi Automation" width={80} height={36} className="object-contain animate-pulse" />
          <Loader2 className="size-5 text-[#3F51B5] animate-spin" />
        </div>
      </div>
    )
  }

  if (!user) return <LoginPage onLogin={handleLogin} />

  const userInitials = user.name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)
  const isReadOnly = user?.role === 'viewer' || user?.role === 'client'
  const canRunTests = !isReadOnly
  const tabs = [
    { id: 'operations', label: '📋 Test Specifications' },
    ...(canRunTests ? [{ id: 'test-runner', label: '🧪 Test Runner' }] : []),
    ...(canRunTests ? [{ id: 'live-execution', label: '📺 Live Execution' }] : []),
    { id: 'results', label: '📈 Results' },
    { id: 'screenshots', label: '📸 Screenshots' },
    ...(canRunTests ? [{ id: 'schedule', label: '🗓️ Schedule' }] : []),
  ]

  return (
    <div className="h-screen flex flex-col bg-white dark:bg-gray-900 overflow-hidden">
      <AppTour selectedModule={selectedModule} activeTab={activeTab} />
      {/* Keyboard Shortcuts Cheat Sheet */}
      <Dialog open={showShortcuts} onOpenChange={setShowShortcuts}>
        <DialogContent className="sm:max-w-[440px]">
          <DialogHeader><DialogTitle className="flex items-center gap-2"><Zap className="size-4 text-green-600" />Keyboard Shortcuts</DialogTitle><DialogDescription>Quick actions to speed up your workflow</DialogDescription></DialogHeader>
          <div className="grid gap-1.5 py-2">
            {[{ keys: 'Ctrl + B', desc: 'Toggle sidebar' }, { keys: 'Ctrl + K', desc: 'Quick module search' }, { keys: 'Ctrl + D', desc: 'Toggle dark mode' }, { keys: 'Ctrl + R', desc: 'Run all pending tests' }, { keys: 'Ctrl + 1', desc: 'Test Specifications tab' }, { keys: 'Ctrl + 2', desc: 'Test Runner tab' }, { keys: 'Ctrl + 3', desc: 'Live Execution tab' }, { keys: 'Ctrl + 4', desc: 'Results tab' }, { keys: 'Ctrl + 5', desc: 'Screenshots tab' }, { keys: 'Ctrl + 6', desc: 'Schedule tab' }, { keys: 'Ctrl + /', desc: 'Show this cheat sheet' }, { keys: 'Escape', desc: 'Close dialog / panel' }].map((s) => (
              <div key={s.keys} className="flex items-center justify-between px-2 py-1.5 rounded-md hover:bg-gray-50 dark:hover:bg-gray-800/50"><span className="text-[13px] text-gray-600 dark:text-gray-400">{s.desc}</span><kbd className="px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-[11px] font-mono text-gray-700 dark:text-gray-300">{s.keys}</kbd></div>
            ))}
          </div>
          <DialogFooter><span className="text-[11px] text-gray-400">Press <kbd className="px-1 py-0.5 rounded bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-[10px] font-mono">Ctrl + /</kbd> to toggle</span></DialogFooter>
        </DialogContent>
      </Dialog>
      {/* HEADER */}
      <header className="h-[60px] bg-white dark:bg-gray-900 border-b border-[#e0e0e0] dark:border-gray-700 flex items-center px-4 shrink-0 z-10 shadow-[0_2px_8px_rgba(0,0,0,0.06)]">
        <div className="flex items-center gap-3 flex-1">
          <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(!sidebarOpen)} data-tour="sidebar-toggle" className={`size-8 cursor-pointer shrink-0 transition-all duration-200 ${sidebarOpen ? 'text-[#888888] hover:text-[#333333] hover:bg-gray-100 dark:hover:bg-gray-800' : 'text-[#3F51B5] hover:text-[#2D3FC7] hover:bg-[#E8F5E9] dark:hover:bg-indigo-900/20'}`} title="Toggle sidebar (Ctrl+B)"><Menu className={`size-[18px] transition-transform duration-200 ${sidebarOpen ? '' : 'rotate-90'}`} /></Button>
          <Separator orientation="vertical" className="h-5" />
          <div className="flex items-center gap-2"><Image src="/agdi-logo-new.webp" alt="AgDi Automation" width={70} height={28} className="object-contain" /><span className="text-[#888888] dark:text-gray-500 text-[13px]">Automation Runner</span></div>
          <div className="hidden md:flex items-center ml-4 bg-[#F5F5F5] dark:bg-gray-800 rounded-md px-3 py-1.5 gap-2 w-64"><Search className="size-3.5 text-[#888888] dark:text-gray-400" /><input type="text" placeholder="Search modules..." className="bg-transparent text-[13px] text-[#333333] dark:text-gray-200 placeholder:text-[#888888] dark:placeholder:text-gray-500 outline-none flex-1" onFocus={() => setQuickSwitcherOpen(true)} readOnly /></div>
        </div>
        <div className="flex items-center gap-1.5">
          <Button variant="ghost" size="icon" onClick={toggleDarkMode} data-tour="dark-mode" className="size-8 text-[#888888] dark:text-gray-400 hover:text-[#333333] dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer" title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}>{darkMode ? <Sun className="size-4" /> : <Moon className="size-4" />}</Button>
          <Button variant="ghost" size="icon" onClick={startAppTour} data-tour="help-btn" className="size-8 text-[#3F51B5] hover:text-[#2D3FC7] hover:bg-[#E8F5E9] dark:hover:bg-indigo-900/20 cursor-pointer" title="Take a tour of the app"><HelpCircle className="size-4" /></Button>
          <Button variant="ghost" size="icon" onClick={() => setShowShortcuts(true)} data-tour="keyboard-shortcuts" className="size-8 text-[#888888] dark:text-gray-400 hover:text-[#333333] dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer" title="Keyboard shortcuts (Ctrl+/)"><Zap className="size-4" /></Button>
          {/* WS Connection Indicator */}
          <div className="flex items-center" title={wsConnected ? 'Real-time connected' : 'Real-time disconnected — using polling'}>
            <div className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-yellow-400 animate-pulse'}`} />
          </div>
          {/* Notifications */}
          <div className="relative" data-tour="notifications">
            <Button variant="ghost" size="icon" onClick={() => { setNotifDropdownOpen((prev) => !prev); if (!notifDropdownOpen) handleMarkAllRead() }} className="size-8 text-[#888888] dark:text-gray-400 hover:text-[#333333] dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer relative" title="Notifications"><Bell className="size-4" />{unreadCount > 0 && <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-[#6777EF] text-white text-[9px] font-bold rounded-full flex items-center justify-center animate-pulse">{unreadCount > 9 ? '9+' : unreadCount}</span>}</Button>
            {notifDropdownOpen && (
              <div className="absolute right-0 top-10 w-96 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 z-50 overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between bg-gray-50/50 dark:bg-gray-800/50"><div className="flex items-center gap-2"><Bell className="size-4 text-[#3F51B5]" /><span className="text-[13px] font-semibold text-[#333333] dark:text-gray-100">Notifications</span>{unreadCount > 0 && <Badge className="bg-[#6777EF] text-white text-[10px] px-1.5 py-0 h-4">{unreadCount} new</Badge>}</div><button onClick={handleMarkAllRead} className="text-[11px] text-[#3F51B5] hover:text-[#2D3FC7] cursor-pointer font-medium">Mark all read</button></div>
                <div className="max-h-72 overflow-y-auto">{notifications.length === 0 ? <div className="p-8 text-center"><Bell className="size-8 text-gray-200 dark:text-gray-600 mx-auto mb-2" /><div className="text-[13px] text-gray-400 dark:text-gray-500">No notifications yet</div><div className="text-[11px] text-gray-300 dark:text-gray-600 mt-1">Notifications will appear here when tests complete or bugs are updated</div></div> : notifications.slice(0, 20).map((n) => { const getCategoryStyle = (type: string) => { switch (type) { case 'run_complete': return { icon: <CheckCircle2 className="size-3.5" />, color: 'text-green-500 bg-green-50 dark:bg-green-900/20' }; case 'status_change': return { icon: <RotateCcw className="size-3.5" />, color: 'text-blue-500 bg-blue-50 dark:bg-blue-900/20' }; case 'reply': return { icon: <MessageSquare className="size-3.5" />, color: 'text-purple-500 bg-purple-50 dark:bg-purple-900/20' }; case 'schedule': return { icon: <CalendarClock className="size-3.5" />, color: 'text-orange-500 bg-orange-50 dark:bg-orange-900/20' }; default: return { icon: <Bell className="size-3.5" />, color: 'text-gray-500 bg-gray-50 dark:bg-gray-700/50' } } }; const catStyle = getCategoryStyle(n.type); return (<div key={n.id} className={`px-4 py-2.5 border-b border-gray-50 dark:border-gray-700/50 flex gap-3 items-start hover:bg-gray-50/50 dark:hover:bg-gray-700/20 transition-colors ${!n.read ? 'bg-[#E8F5E9]/30 dark:bg-green-900/5' : ''}`}><div className={`shrink-0 w-7 h-7 rounded-full flex items-center justify-center ${catStyle.color}`}>{catStyle.icon}</div><div className="flex-1 min-w-0"><div className="text-[12px] font-medium text-[#333333] dark:text-gray-200 leading-tight">{n.title}</div><div className="text-[11px] text-[#666666] dark:text-gray-400 mt-0.5 leading-snug">{n.message}</div><div className="text-[10px] text-[#888888] dark:text-gray-500 mt-1">{new Date(n.createdAt).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}</div></div>{!n.read && <div className="shrink-0 w-2 h-2 rounded-full bg-[#6777EF] mt-1.5" />}</div>) })}</div>
                {notifications.length > 0 && <div className="px-4 py-2 border-t border-gray-100 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50 text-center"><span className="text-[11px] text-gray-400 dark:text-gray-500">{notifications.length} notification{notifications.length !== 1 ? 's' : ''}</span></div>}
              </div>
            )}
          </div>
          {(user.role === 'admin' || user.role === 'qa_lead') && <Link href="/admin" className="flex items-center gap-1.5 px-2.5 h-8 text-[12px] text-[#888888] dark:text-gray-400 hover:text-red-700 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md transition-colors" title="Admin Panel"><Shield className="size-3.5" /><span className="hidden sm:inline">Admin</span></Link>}
          <Separator orientation="vertical" className="h-5 mx-0.5" />
          <div className="flex items-center gap-2" data-tour="user-menu">
            <button onClick={() => setProfileDialogOpen(true)} className="flex items-center gap-2 hover:opacity-80 transition-opacity cursor-pointer"><Avatar className="size-7"><AvatarFallback className="bg-[#6777EF] text-white text-xs font-semibold">{userInitials}</AvatarFallback></Avatar><div className="hidden sm:flex flex-col"><span className="text-[12px] text-[#333333] dark:text-gray-200 font-medium max-w-[120px] truncate leading-tight">{user.name}</span><span className="text-[10px] text-[#888888] dark:text-gray-500 leading-tight">{user.role}</span></div></button>
            <Button variant="ghost" size="icon" onClick={handleLogout} data-tour="logout-btn" className="size-7 text-[#888888] hover:text-red-500 cursor-pointer" title="Sign out"><LogOut className="size-3.5" /></Button>
          </div>
        </div>
      </header>
      {/* BODY */}
      <div className="flex flex-1 overflow-hidden">
        {/* SIDEBAR */}
        <div className="shrink-0 overflow-hidden h-full" style={{ width: sidebarOpen ? sidebarWidth : 0 }}>
          <aside className="flex flex-col h-full font-['Poppins'] bg-gradient-to-b from-[#F7FBF8] via-[#EAF5EC] to-[#D6EDDC] dark:from-[#1e293b] dark:via-[#1e293b] dark:to-[#1e293b] shadow-[-1px_0px_0px_#D4E3D9] dark:shadow-[-1px_0px_0px_#334155]" style={{ width: sidebarWidth }}>
            <ScrollArea className="flex-1 min-h-0" data-tour="sidebar-modules">
              <div className="py-2 px-2">
                {sidebarModules.map((mod) => (<SidebarModuleItem key={mod.id} module={mod} activeId={selectedModule} onSelect={handleSelectModule} expandedIds={expandedIds} toggleExpand={toggleExpand} justExpandedId={justExpandedId} />))}
              </div>
            </ScrollArea>
            <div className="relative shrink-0 overflow-hidden" style={{ height: 99 }}><Image src="/agri2.png" alt="" fill className="object-cover" sizes="280px" style={{ objectPosition: 'center 25%' }} /></div>
          </aside>
        </div>
        {sidebarOpen && <div onMouseDown={handleResizeStart} className="w-1 cursor-col-resize bg-transparent hover:bg-[#3F51B5]/40 active:bg-[#3F51B5]/60 transition-colors shrink-0 relative z-10" />}
        {/* MAIN CONTENT */}
        <main className="flex-1 flex flex-col overflow-hidden bg-[#F1F2F7] dark:bg-gray-900 relative">
          {navToast && <NavToast key={navToast.key} label={navToast.label} parent={navToast.parent} />}
          {!sidebarOpen && selectedModule !== 'dashboard' && (
            <div className="flex items-center gap-1.5 px-4 py-2 border-b border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-900 shrink-0">
              <button onClick={handleGoHome} className="text-[12px] text-[#3F51B5] hover:text-[#2D3FC7] dark:hover:text-indigo-400 font-medium cursor-pointer transition-colors hover:underline">Dashboard</button>
              {modulePath.parent && <><ChevronRight className="size-3 text-gray-400 dark:text-gray-500" /><span className="text-[12px] text-gray-500 dark:text-gray-400">{modulePath.parent}</span></>}
              <ChevronRight className="size-3 text-gray-400 dark:text-gray-500" />
              <span className="text-[12px] text-gray-800 dark:text-gray-100 font-medium">{modulePath.name}</span>
              {modulePath.badge && <span className="text-[11px] text-orange-600 dark:text-orange-400 ml-1">{modulePath.badge}</span>}
              <div className="flex-1" />
              <span className="text-[11px] text-gray-400 dark:text-gray-500"><kbd className="px-1 py-0.5 rounded bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-[10px] font-mono">Ctrl+B</kbd> to toggle</span>
            </div>
          )}
          {selectedModule === 'dashboard' && renderDashboard()}
          {selectedModule === 'my-tickets' && user && <MyTicketsTab userEmail={user.email} userName={user.name} />}
          {selectedModule !== 'dashboard' && selectedModule !== 'my-tickets' && (
            <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
              <div className="border-b border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/30 shrink-0" data-tour="tab-bar">
                <div className="flex items-center h-10 px-4 gap-0">
                  {tabs.map((tab) => (<button key={tab.id} onClick={() => setActiveTab(tab.id)} className={`px-4 h-full text-[13px] font-medium transition-colors border-b-2 cursor-pointer ${activeTab === tab.id ? 'border-[#3F51B5] text-[#3F51B5] dark:text-indigo-400 bg-white dark:bg-gray-900' : 'border-transparent text-[#888888] dark:text-gray-400 hover:text-[#333333] dark:hover:text-gray-200 hover:bg-gray-100/50 dark:hover:bg-gray-800/30'}`}>{tab.label}</button>))}
                  <div className="flex-1" />
                  <span className="text-[12px] text-gray-400 dark:text-gray-500">Module: <span className="text-gray-600 dark:text-gray-300 font-medium">{modulePath.name}</span>{modulePath.badge && <span className="ml-2 text-orange-600 dark:text-orange-400">{modulePath.badge}</span>}</span>
                </div>
              </div>
              <div className="flex-1 overflow-hidden min-h-0">
                {activeTab === 'operations' && <div data-tour="operations" className="h-full"><OperationsTab testGroups={currentTestGroups} testCasesModule={allTestCases[selectedModule?.toLowerCase().replace(' ', '_').replace('-', '_')]} /></div>}
                {activeTab === 'test-runner' && <div data-tour="test-runner" className="h-full"><TestRunnerTab tests={tests} testChecks={testChecks} toggleTestCheck={toggleTestCheck} isRunning={isRunning} totalFailed={failedCount} onRun={(selectedOnly) => { runTests(selectedOnly); setActiveTab('live-execution') }} onRunByPriority={runByPriority} onRerunFailed={() => { const failedIds = tests.filter((t) => t.status === 'failed').map((t) => t.id); if (failedIds.length > 0) { rerunTestIds(failedIds); runTests(true, failedIds); setActiveTab('live-execution') } }} /></div>}
                {activeTab === 'live-execution' && <div data-tour="live-execution" className="h-full"><LiveExecutionTab tests={tests} testGroups={currentTestGroups} isRunning={isRunning} runningProgress={runningProgress} onStop={async () => { const runId = currentRunIdRef.current; if (runId) { try { await stopRun(runId); toast.success('Run stopped') } catch (err) { toast.error('Failed to stop run', { description: err instanceof Error ? err.message : 'Unknown error' }) } } setIsRunning(false) }} onBack={() => setActiveTab('test-runner')} onRerunFailed={() => { const failedIds = tests.filter((t) => t.status === 'failed').map((t) => t.id); if (failedIds.length > 0) { rerunTestIds(failedIds); runTests(true, failedIds) } }} onScreenshotCaptured={(entry) => { setScreenshotEntries((prev) => { if (prev.length >= 50) return [entry, ...prev.slice(0, 49)]; return [entry, ...prev] }) }} /></div>}
                {activeTab === 'results' && <div data-tour="results" className="h-full"><ResultsTab tests={tests} passedCount={passedCount} failedCount={failedCount} totalCount={tests.length} runHistory={runHistory} onReportTest={handleReportTest} bugReportsList={bugReportsList} onRunDetail={(run) => { setSelectedRunForDetail(run); setRunDetailDialogOpen(true) }} onCompareRuns={() => setRunComparisonOpen(true)} testGroups={currentTestGroups} moduleHealth={moduleHealth} moduleName={modulePath.name} /></div>}
                {activeTab === 'screenshots' && (
                  <div data-tour="screenshots" className="flex flex-col h-full min-h-0">
                    <div className="p-4 shrink-0">
                      <div className="flex items-center justify-between mb-3">
                        <div><h3 className="text-[14px] font-semibold text-gray-800 dark:text-gray-100">Screenshot Gallery</h3><p className="text-[12px] text-gray-500 dark:text-gray-400 mt-0.5">Screenshots captured during test execution</p></div>
                        <div className="flex items-center gap-2">
                          {screenshotEntries.length >= 2 && <Button variant="outline" size="sm" onClick={() => { setCompareScreenshots([screenshotEntries[0] || null, screenshotEntries[1] || null]); setScreenshotCompareOpen(true) }} className="h-7 text-[12px] gap-1.5 cursor-pointer"><GitCompare className="size-3" />Compare</Button>}
                          <Button variant="outline" size="sm" onClick={async () => { try { const data = await fetchScreenshot(); if (data.active && data.screenshot) { const newEntry: ScreenshotEntry = { id: `ss-${Date.now()}`, src: `data:image/png;base64,${data.screenshot}`, testName: 'Live Capture', timestamp: new Date().toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit' }), status: 'running' }; setScreenshotEntries((prev) => [newEntry, ...prev]); toast.success('Screenshot captured') } else { toast.info('No active screenshot available') } } catch { toast.error('Failed to capture screenshot') } }} className="h-7 text-[12px] gap-1.5 cursor-pointer"><Monitor className="size-3" />Capture Now</Button>
                        </div>
                      </div>
                    </div>
                    <div className="flex-1 overflow-auto px-4 pb-4"><ScreenshotGallery screenshots={screenshotEntries} onRefresh={async () => { try { const data = await fetchScreenshot(); if (data.active && data.screenshot) { const newEntry: ScreenshotEntry = { id: `ss-${Date.now()}`, src: `data:image/png;base64,${data.screenshot}`, testName: 'Live Capture', timestamp: new Date().toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit' }), status: 'running' }; setScreenshotEntries((prev) => [newEntry, ...prev]) } } catch {} }} /></div>
                  </div>
                )}
                {activeTab === 'schedule' && user && <div data-tour="schedule-runs" className="h-full"><ScheduleRunsTab userName={user.name} sidebarModules={sidebarModules} /></div>}
              </div>
            </div>
          )}
        </main>
      </div>
      {/* Console Panel */}
      {consoleOpen && (
        <div className="shrink-0 border-t border-gray-700 bg-[#1a1a2e] flex flex-col" style={{ height: '200px' }}>
          <div className="flex items-center justify-between px-4 py-1.5 bg-[#16162a] border-b border-gray-700"><div className="flex items-center gap-2"><Terminal className="size-3.5 text-green-400" /><span className="text-[12px] text-gray-300 font-medium">Console Output</span></div><div className="flex items-center gap-2"><span className="text-[11px] text-gray-500">{consoleLogs.length} entries</span><Button variant="ghost" size="icon" className="size-5 text-gray-400 hover:text-gray-200" onClick={() => setConsoleOpen(false)}><X className="size-3" /></Button></div></div>
          <ScrollArea className="flex-1 px-4 py-2"><div className="space-y-0.5">{consoleLogs.map((log, i) => (<div key={i} className={`text-[12px] font-mono leading-5 ${log.includes('PASSED') ? 'text-green-400' : log.includes('FAILED') ? 'text-red-400' : log.includes('Navigating') || log.includes('Clicking') || log.includes('Filling') || log.includes('Selecting') || log.includes('Setting') ? 'text-yellow-300' : 'text-gray-300'}`}>{log}</div>))}</div></ScrollArea>
        </div>
      )}
      {activeTab === 'live-execution' && !isRunning && passedCount + failedCount > 0 && (
        <button onClick={() => setActiveTab('test-runner')} className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 bg-[#3F51B5] hover:bg-[#2D3FC7] text-white transition-all duration-200 rounded-xl px-5 py-2.5 flex items-center gap-2 cursor-pointer hover:-translate-y-0.5"><RotateCcwIcon className="size-4" /><span className="text-[13px] font-medium">New Test Run</span></button>
      )}
      {/* Quick Switcher */}
      {quickSwitcherOpen && (
        <><div className="fixed inset-0 z-[100] bg-black/40 backdrop-blur-sm" onClick={() => setQuickSwitcherOpen(false)} /><div className="fixed top-[20%] left-1/2 -translate-x-1/2 z-[101] w-full max-w-lg"><div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden"><div className="flex items-center gap-3 px-4 py-3 border-b border-gray-100 dark:border-gray-700"><Search className="size-4 text-gray-400 shrink-0" /><input type="text" value={quickSearch} onChange={(e) => setQuickSearch(e.target.value)} placeholder="Search modules... (e.g. tax, uom, crop)" className="flex-1 text-[14px] text-gray-800 dark:text-gray-100 placeholder:text-gray-400 outline-none bg-transparent" autoFocus onKeyDown={(e) => { if (e.key === 'Escape') setQuickSwitcherOpen(false) }} /><kbd className="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 text-[10px] font-mono text-gray-400 shrink-0">ESC</kbd></div><div className="max-h-[300px] overflow-auto py-2">{(() => { const q = quickSearch.toLowerCase(); const flatModules: { id: string; label: string; parent?: string; badge?: string }[] = []; for (const mod of sidebarModules) { if (mod.children) { for (const child of mod.children) { flatModules.push({ id: child.id, label: child.label, parent: mod.label, badge: child.badge }) } } else { flatModules.push({ id: mod.id, label: mod.label, badge: mod.badge }) } } const filtered = q ? flatModules.filter((m) => m.label.toLowerCase().includes(q) || m.id.toLowerCase().includes(q) || (m.parent && m.parent.toLowerCase().includes(q))) : flatModules; if (filtered.length === 0) return <div className="px-4 py-6 text-center text-[13px] text-gray-400 dark:text-gray-500">No modules found</div>; return filtered.map((mod) => { const isActive = mod.id === selectedModule; return (<button key={mod.id} onClick={() => { setSelectedModule(mod.id); setActiveTab('operations'); setQuickSwitcherOpen(false); setSidebarOpen(true) }} className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors cursor-pointer ${isActive ? 'bg-[#E8F5E9] dark:bg-[#1B4332]/20 text-[#1B4332] dark:text-green-400' : 'text-[#333333] dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700/50'}`}>{mod.parent && <span className="text-[11px] text-gray-400 dark:text-gray-500 truncate max-w-[100px]">{mod.parent}</span>}{mod.parent && <ChevronRight className="size-3 text-gray-300 dark:text-gray-600 shrink-0" />}<span className={`text-[13px] flex-1 truncate ${isActive ? 'font-medium' : ''}`}>{mod.label}</span>{mod.badge && <span className="text-[11px] text-gray-500 dark:text-gray-400 shrink-0">{mod.badge}</span>}{isActive && <CheckCircle2 className="size-3.5 text-[#3F51B5] shrink-0" />}</button>) }) })()}</div><div className="flex items-center gap-4 px-4 py-2 border-t border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 text-[11px] text-gray-400"><span><kbd className="px-1 py-0.5 rounded bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 text-[10px] font-mono">↑↓</kbd> navigate</span><span><kbd className="px-1 py-0.5 rounded bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 text-[10px] font-mono">Enter</kbd> select</span><span><kbd className="px-1 py-0.5 rounded bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 text-[10px] font-mono">Esc</kbd> close</span></div></div></div></>
      )}
      {/* Console toggle buttons */}
      {!consoleOpen && <button onClick={() => setConsoleOpen(true)} className="fixed bottom-4 right-4 z-50 bg-[#1a1a2e] text-green-400 hover:bg-[#252540] transition-colors rounded-lg px-3 py-2 flex items-center gap-2 shadow-lg border border-gray-700 cursor-pointer"><Terminal className="size-3.5" /><span className="text-[12px] font-medium">Console</span><span className="bg-green-500/20 text-green-400 text-[10px] px-1.5 py-0.5 rounded-full">{consoleLogs.length}</span></button>}
      {consoleOpen && <button onClick={() => setConsoleOpen(false)} className="fixed bottom-[208px] right-4 z-50 bg-[#1a1a2e] text-gray-400 hover:text-gray-200 transition-colors rounded-t-lg px-3 py-1 flex items-center gap-1.5 shadow-lg border border-b-0 border-gray-700 cursor-pointer"><Minimize2 className="size-3" /><span className="text-[11px]">Hide</span></button>}
      {/* Completion Summary Modal */}
      <CompletionSummaryModal open={completionModalOpen} onClose={() => setCompletionModalOpen(false)} passedCount={completionStats.passed} failedCount={completionStats.failed} totalDuration={completionStats.duration} onViewResults={handleViewResults} onRerunFailed={handleCompletionRerunFailed} onNewRun={handleNewRun} />
      {/* Bug Report Dialog */}
      <ReportToAdminDialog open={reportDialogOpen} onClose={() => setReportDialogOpen(false)} testId={reportingTest?.id || ''} testDescription={reportingTest?.name || ''} error={reportingTest?.error} moduleName={modulePath.name} userName={user?.name || ''} userEmail={user?.email || ''} />
      {/* User Profile Dialog */}
      {user && <UserProfileDialog open={profileDialogOpen} onClose={() => setProfileDialogOpen(false)} user={user} />}
      {/* Run Detail Dialog */}
      <RunDetailDialog open={runDetailDialogOpen} onClose={() => { setRunDetailDialogOpen(false); setSelectedRunForDetail(null) }} run={selectedRunForDetail} />

      {/* AI Features — temporarily disabled (can be re-enabled later) */}
      {/* <AiBugTriage open={aiBugTriageOpen} onClose={() => { setAiBugTriageOpen(false); setAiTriageTest(null) }} testId={aiTriageTest?.id || ''} testDescription={aiTriageTest?.name || ''} error={aiTriageTest?.error} moduleName={modulePath.name} userName={user?.name || ''} />
      <AiFailureAnalysis open={aiFailureAnalysisOpen} onClose={() => { setAiFailureAnalysisOpen(false); setAiAnalysisTest(null) }} testId={aiAnalysisTest?.id || ''} testName={aiAnalysisTest?.name || ''} error={aiAnalysisTest?.error} moduleName={modulePath.name} />
      {selectedModule !== 'dashboard' && selectedModule !== 'my-tickets' && (
        <>
          <AiNlRunBar availableModules={sidebarModules.filter(m => m.id !== 'dashboard' && m.id !== 'my-tickets').map(m => m.label)} availableTests={tests.map(t => ({ id: t.id, name: t.name, module: modulePath.name }))} onApplySelection={handleAiNlApply} />
          <AiTestSuggestions failedTests={tests.filter(t => t.status === 'failed').map(t => ({ id: t.id, name: t.name, error: getTestError(t.id), module: modulePath.name }))} currentModule={modulePath.name} />
        </>
      )} */}
      {/* Run Comparison Dialog */}
      <RunComparisonDialog open={runComparisonOpen} onClose={() => setRunComparisonOpen(false)} runHistory={runHistory} />
      {/* Screenshot Lightbox */}
      {lightboxOpen && <ScreenshotLightbox open={lightboxOpen} onClose={() => setLightboxOpen(false)} screenshots={screenshotEntries} initialIndex={lightboxIndex} />}
      {/* Screenshot Compare */}
      {screenshotCompareOpen && <ScreenshotCompare left={compareScreenshots[0]} right={compareScreenshots[1]} onClose={() => setScreenshotCompareOpen(false)} />}
      {/* FOOTER */}
      <footer className="shrink-0 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-4 py-1.5 flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-[10px] text-gray-400 dark:text-gray-500"><Copyright className="size-3" /><span>2026 AgDi Solutions Pvt. Ltd. All rights reserved.</span></div>
        <div className="flex items-center gap-3 text-[10px] text-gray-400 dark:text-gray-500"><span className="flex items-center gap-1">Version 1.0.0</span><a href="https://rhythmerp.algorhythms.in" target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 hover:text-[#3F51B5] dark:hover:text-indigo-400 transition-colors cursor-pointer"><HelpCircle className="size-3" />Help<ExternalLink className="size-2.5" /></a></div>
      </footer>
    </div>
  )
}
