'use client'

import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { useTheme } from 'next-themes'
import { toast } from 'sonner'
import { fetchModules, fetchRunDetail, sidebarToFolderMapping, startRun, stopRun, fetchTestCases, type ApiModule } from '@/lib/api'
import {
  getBugReports,
  markAllNotificationsRead,
  getUnreadNotificationCount,
  getNotifications,
  getSLAStatus,
  type Notification as NotifType,
  type BugReport,
} from '@/lib/bug-reports'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog'
import {
  Search,
  RefreshCw,
  ChevronRight,
  Play,
  RotateCcw,
  Terminal,
  X,
  Minimize2,
  CheckCircle2,
  XCircle,
  Circle,
  Loader2,
  LogOut,
  Menu,
  Sun,
  Moon,
  Zap,
  Shield,
  MessageSquare,
  Bell,
  CalendarClock,
  HelpCircle,
  Copyright,
  ExternalLink,
} from 'lucide-react'
import { AppTour, startAppTour } from '@/components/tour/AppTour'
import RunComparisonDialog from '@/components/comparison/RunComparisonDialog'
import { ScreenshotGallery, ScreenshotLightbox, ScreenshotCompare } from '@/components/screenshot/ScreenshotGallery'
import type { ScreenshotEntry } from '@/components/screenshot/ScreenshotGallery'

// ─── Extracted types & constants ──────────────────────────
import type { TestPriority, SidebarModule, TestItem, TestSpecItem, TestClassGroup, AuthUser, RunSnapshot, ModuleHealth } from '@/lib/types'
import { ALL_SIDEBAR_MODULES, testSpecGroups, initialTests, getTestsForSidebarModule, buildSidebarModules } from '@/lib/constants'

// ─── Extracted components ─────────────────────────────────
import { LoginPage } from '@/components/home/LoginPage'
import { NavToast } from '@/components/home/NavToast'
import { DashboardTab } from '@/components/home/DashboardTab'
import { OperationsTab } from '@/components/home/OperationsTab'
import { TestRunnerTab } from '@/components/home/TestRunnerTab'
import { LiveExecutionTab } from '@/components/home/LiveExecutionTab'
import { ScheduleRunsTab } from '@/components/home/ScheduleRunsTab'
import { MyTicketsTab } from '@/components/home/MyTicketsTab'
import { ResultsTab } from '@/components/home/ResultsTab'
import { ReportToAdminDialog } from '@/components/home/ReportToAdminDialog'
import { CompletionSummaryModal } from '@/components/home/CompletionSummaryModal'
import { UserProfileDialog } from '@/components/home/UserProfileDialog'
import { RunDetailDialog } from '@/components/home/RunDetailDialog'
import { SidebarModuleItem } from '@/components/home/SidebarModuleItem'

// ─── MAIN PAGE COMPONENT ─────────────────────────────────
export default function Home() {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)
  const [sidebarModules, setSidebarModules] = useState<SidebarModule[]>(ALL_SIDEBAR_MODULES)
  const [apiModules, setApiModules] = useState<ApiModule[]>([])
  const [selectedModule, setSelectedModule] = useState<string>('dashboard')
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())
  const [activeTab, setActiveTab] = useState('operations')
  const [consoleOpen, setConsoleOpen] = useState(false)
  const [hashReady, setHashReady] = useState(false)
  const [testChecks, setTestChecks] = useState<Set<string>>(new Set())
  const [tests, setTests] = useState<TestItem[]>(initialTests)
  const [currentTestGroups, setCurrentTestGroups] = useState<TestClassGroup[]>(testSpecGroups)
  const [allTestCases, setAllTestCases] = useState<Record<string, any>>({})
  const [isRunning, setIsRunning] = useState(false)
  const [runningProgress, setRunningProgress] = useState('')
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

  // Phase 4: Run Comparison Dialog
  const [runComparisonOpen, setRunComparisonOpen] = useState(false)

  // Phase 4: Screenshot Gallery state
  const [screenshotEntries, setScreenshotEntries] = useState<ScreenshotEntry[]>([])
  const [lightboxOpen, setLightboxOpen] = useState(false)
  const [lightboxIndex, setLightboxIndex] = useState(0)
  const [screenshotCompareOpen, setScreenshotCompareOpen] = useState(false)
  const [compareScreenshots, setCompareScreenshots] = useState<[ScreenshotEntry | null, ScreenshotEntry | null]>([null, null])

  // Poll notifications every 2s
  useEffect(() => {
    const poll = async () => {
      setUnreadCount(await getUnreadNotificationCount())
      setNotifications(await getNotifications())
    }
    poll()
    const interval = setInterval(poll, 2000)
    return () => clearInterval(interval)
  }, [])

  // ─── Fetch real modules from API ──────────────────────
  useEffect(() => {
    if (!user) return
    fetchModules()
      .then((mods) => {
        setApiModules(mods)
        setSidebarModules(buildSidebarModules(mods))
      })
      .catch((err) => {
        console.warn('API modules fetch failed, using defaults:', err)
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
      .catch(() => {
        // Backend not running — this is expected when FastAPI isn't available
      })
  }, [user])

  const handleMarkAllRead = useCallback(async () => {
    await markAllNotificationsRead()
    setUnreadCount(0)
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))
  }, [])

  // Feature 5: Run history (loaded from Prisma DB)
  const [runHistory, setRunHistory] = useState<RunSnapshot[]>([])

  // Track the current backend run ID for stop functionality
  const currentRunIdRef = useRef<string | null>(null)

  // Real console log lines from SSE events
  const [consoleLogs, setConsoleLogs] = useState<string[]>(['> Waiting for tests to start...', '> Select tests in Test Runner and click Run.'])

  // Real bug reports from Prisma
  const [bugReportsList, setBugReportsList] = useState<{ id: string; testId: string; desc: string; status: string }[]>([])

  // Load run history from Prisma
  const loadRunHistory = useCallback(async () => {
    try {
      const res = await fetch('/api/runs?limit=50')
      if (res.ok) {
        const data = await res.json()
        const mapped: RunSnapshot[] = (data as Array<{
          id: string
          moduleId: string
          moduleName: string
          passed: number
          failed: number
          total: number
          duration: string
          rate: number
          results: { testId: string; status: string }[] | null
          startedAt: string
          completedAt: string | null
          status: string
        }>).map((r) => ({
          id: r.id,
          date: r.startedAt ? new Date(r.startedAt).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—',
          moduleId: r.moduleId,
          results: Array.isArray(r.results) ? r.results.map((x: { testId: string; status: string }) => ({
            testId: x.testId,
            status: x.status === 'passed' ? 'passed' as const : 'failed' as const,
          })) : [],
          passed: r.passed || 0,
          failed: r.failed || 0,
          total: r.total || 0,
          duration: r.duration || '—',
          rate: r.rate || 0,
        }))
        setRunHistory(mapped)
      }
    } catch {
      // Silently fail — runs will show as empty
    }
  }, [])

  // Load bug reports from Prisma
  const loadBugReports = useCallback(async () => {
    try {
      const reports = await getBugReports()
      setBugReportsList(reports.map((r) => ({
        id: r.id,
        testId: r.testId,
        desc: r.error || r.testDescription,
        status: r.status === 'open' ? 'Open' : r.status === 'in_progress' ? 'In Progress' : 'Fixed',
      })))
    } catch {
      // Silently fail
    }
  }, [])

  // Load run history and bug reports after auth
  useEffect(() => {
    if (!user) return
    loadRunHistory()
    loadBugReports()
  }, [user, loadRunHistory, loadBugReports])

  // Compute module health from real run history
  const moduleHealth = useMemo(() => {
    const moduleInfo = new Map<string, { name: string; parentGroup: string }>()
    function collectModules(items: SidebarModule[], parent?: string) {
      for (const item of items) {
        if (item.id !== 'dashboard' && item.id !== 'my-tickets') {
          const group = parent || (item.children ? item.label : undefined) || 'Standalone'
          moduleInfo.set(item.id, { name: item.label, parentGroup: group })
          if (item.children) {
            collectModules(item.children, item.label)
          }
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
        health.push({
          moduleId: modId,
          moduleName: info.name,
          parentGroup: info.parentGroup,
          passRate: 0,
          totalTests: 0,
          passedTests: 0,
          failedTests: 0,
          lastRun: '—',
        })
      } else {
        const latestRun = runs[0]
        const passedTests = latestRun.passed
        const failedTests = latestRun.failed
        const totalTests = latestRun.total
        const passRate = totalTests > 0 ? Math.round((passedTests / totalTests) * 100) : 0
        const sortedRuns = [...runs].reverse().slice(-7)
        const trend = sortedRuns.map((r) => r.total > 0 ? Math.round((r.passed / r.total) * 100) : 0)
        health.push({
          moduleId: modId,
          moduleName: info.name,
          parentGroup: info.parentGroup,
          passRate,
          totalTests,
          passedTests,
          failedTests,
          lastRun: latestRun.date,
          trend,
        })
      }
    }
    return health
  }, [runHistory, sidebarModules])

  // Dark mode via next-themes
  const [navToast, setNavToast] = useState<{ key: number; label: string; parent?: string | null } | null>(null)
  const { theme, setTheme } = useTheme()
  const darkMode = theme === 'dark'
  const toggleDarkMode = useCallback(() => {
    setTheme(darkMode ? 'light' : 'dark')
  }, [darkMode, setTheme])

  // Auto-hide sidebar on Live Execution
  useEffect(() => {
    if (activeTab === 'live-execution') {
      setSidebarOpen(false)
    } else {
      setSidebarOpen(true)
    }
  }, [activeTab])

  // Feature 1: Detect run completion
  useEffect(() => {
    if (prevIsRunningRef.current && !isRunning) {
      const passed = tests.filter((t) => t.status === 'passed').length
      const failed = tests.filter((t) => t.status === 'failed').length
      const total = passed + failed
      if (total > 0) {
        const durations = tests
          .filter((t) => t.duration && t.duration !== '—' && t.duration !== '...' && t.duration !== '')
          .map((t) => {
            const parts = t.duration.split(':')
            return parseInt(parts[0]) * 60 + parseInt(parts[1])
          })
        const totalSecs = durations.reduce((a, b) => a + b, 0)
        const mins = Math.floor(totalSecs / 60)
        const secs = totalSecs % 60
        const durationStr = `${mins}:${String(secs).padStart(2, '0')}`
        setCompletionStats({ passed, failed, duration: durationStr })
        setCompletionModalOpen(true)

        const runId = currentRunIdRef.current
        const moduleName = (() => {
          for (const mod of sidebarModules) {
            if (mod.id === selectedModule) return mod.label
            if (mod.children) {
              const child = mod.children.find(c => c.id === selectedModule)
              if (child) return child.label
            }
          }
          return selectedModule
        })()
        fetch('/api/runs', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            moduleId: selectedModule,
            moduleName,
            passed,
            failed,
            total,
            duration: durationStr,
            rate: total > 0 ? Math.round((passed / total) * 100) : 0,
            results: tests.filter(t => t.status === 'passed' || t.status === 'failed').map(t => ({
              testId: t.id,
              status: t.status,
            })),
            status: 'completed',
            startedAt: new Date().toISOString(),
            completedAt: new Date().toISOString(),
          }),
        }).then(() => {
          loadRunHistory()
        }).catch(() => {})
        currentRunIdRef.current = null
      }
    }
    prevIsRunningRef.current = isRunning
  }, [isRunning, tests, selectedModule, sidebarModules, loadRunHistory])

  // Check session on mount & seed admin
  useEffect(() => {
    const init = async () => {
      try {
        await fetch('/api/auth/seed')
        const res = await fetch('/api/auth/me')
        if (res.ok) {
          const data = await res.json()
          setUser(data.user)
        }
      } catch {
        // Silently fail
      } finally {
        setLoading(false)
      }
    }
    init()
  }, [])

  const handleLogin = useCallback((u: AuthUser) => {
    setUser(u)
  }, [])

  const handleLogout = useCallback(async () => {
    await fetch('/api/auth/logout', { method: 'POST' })
    setUser(null)
  }, [])

  const toggleExpand = useCallback((id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        const isTopLevel = ALL_SIDEBAR_MODULES.some(m => m.id === id)
        if (isTopLevel) {
          ALL_SIDEBAR_MODULES.forEach(m => next.delete(m.id))
        } else {
          const findSiblings = (modules: SidebarModule[]): string[] => {
            for (const mod of modules) {
              if (mod.id === id) return []
              if (mod.children) {
                const childIds = mod.children.map(c => c.id)
                if (childIds.includes(id)) {
                  return mod.children.filter(c => c.children && c.children.length > 0).map(c => c.id)
                }
                const deeper = findSiblings(mod.children)
                if (deeper.length > 0) return deeper
              }
            }
            return []
          }
          const siblings = findSiblings(ALL_SIDEBAR_MODULES)
          siblings.forEach(s => next.delete(s))
        }
        next.add(id)
      }
      return next
    })
  }, [])

  // Hash routing: init from URL hash
  useEffect(() => {
    const readHash = () => {
      const h = window.location.hash.slice(1)
      if (h) {
        const [mod, tab] = h.split('/')
        if (mod && mod !== 'dashboard') setSelectedModule(mod)
        if (tab) setActiveTab(tab)
      }
      setHashReady(true)
    }
    readHash()
    window.addEventListener('hashchange', readHash)
    return () => window.removeEventListener('hashchange', readHash)
  }, [])

  // Write hash on module/tab change
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
        for (const child of mod.children ?? []) {
          if (child.id === id) return { label: child.label, parent: mod.label }
          for (const grand of child.children ?? []) {
            if (grand.id === id) return { label: grand.label, parent: child.label }
          }
        }
      }
      return { label: id, parent: null }
    })()
    setNavToast({ key: Date.now(), label: found.label, parent: found.parent })
    setActiveTab('operations')
    setTestChecks(new Set())

    const moduleKey = id.toLowerCase().replace(" ", "_").replace("-", "_")
    if (allTestCases[moduleKey]) {
      const moduleData = allTestCases[moduleKey]
      const mapTestCaseStatus = (s: string): TestSpecItem['status'] => {
        const upper = s.toUpperCase().trim()
        if (upper === 'PASSED' || upper === 'PASS') return 'passed'
        if (upper === 'BUG') return 'bug'
        if (upper === 'TODO') return 'todo'
        if (upper === 'FAILED' || upper === 'FAIL') return 'failed'
        return 'not-run'
      }
      const specGroups: TestClassGroup[] = [{
        className: moduleData.label,
        tests: moduleData.tests.map((t: any) => ({
          id: t.id,
          screenName: t.screenName,
          description: t.description,
          status: mapTestCaseStatus(t.status),
          duration: '',
          steps: t.steps,
          expected: t.expected,
          actual: t.actual || '',
          bugDetails: t.status === 'BUG' ? t.actual : undefined,
          priority: undefined,
          date: t.date || undefined,
        })),
      }]
      setCurrentTestGroups(specGroups)
      const mapToTestItemStatus = (s: string): 'passed' | 'failed' | 'pending' => {
        const upper = s.toUpperCase().trim()
        if (upper === 'PASSED' || upper === 'PASS') return 'passed'
        if (upper === 'BUG' || upper === 'FAILED' || upper === 'FAIL') return 'failed'
        return 'pending'
      }
      const items: TestItem[] = moduleData.tests.map((t: any) => ({
        id: t.id,
        name: t.description,
        status: mapToTestItemStatus(t.status),
        duration: '',
      }))
      setTests(items)
    } else {
      const { groups, items } = getTestsForSidebarModule(id, apiModules)
      if (groups.length > 0) {
        setCurrentTestGroups(groups)
        setTests(items)
      } else {
        setCurrentTestGroups([])
        setTests([])
      }
    }
  }, [apiModules, allTestCases])

  // Re-load current module tests when data changes
  useEffect(() => {
    if (selectedModule === 'dashboard' || selectedModule === 'my-tickets') return
    const moduleKey = selectedModule.toLowerCase().replace(" ", "_").replace("-", "_")
    if (allTestCases[moduleKey]) {
      const moduleData = allTestCases[moduleKey]
      const mapTestCaseStatus = (s: string): TestSpecItem['status'] => {
        const upper = s.toUpperCase().trim()
        if (upper === 'PASSED' || upper === 'PASS') return 'passed'
        if (upper === 'BUG') return 'bug'
        if (upper === 'TODO') return 'todo'
        if (upper === 'FAILED' || upper === 'FAIL') return 'failed'
        return 'not-run'
      }
      const specGroups: TestClassGroup[] = [{
        className: moduleData.label,
        tests: moduleData.tests.map((t: any) => ({
          id: t.id,
          screenName: t.screenName,
          description: t.description,
          status: mapTestCaseStatus(t.status),
          duration: '',
          steps: t.steps,
          expected: t.expected,
          actual: t.actual || '',
          bugDetails: t.status === 'BUG' ? t.actual : undefined,
          priority: undefined,
          date: t.date || undefined,
        })),
      }]
      setCurrentTestGroups(specGroups)
      const mapToTestItemStatus = (s: string): 'passed' | 'failed' | 'pending' => {
        const upper = s.toUpperCase().trim()
        if (upper === 'PASSED' || upper === 'PASS') return 'passed'
        if (upper === 'BUG' || upper === 'FAILED' || upper === 'FAIL') return 'failed'
        return 'pending'
      }
      const items: TestItem[] = moduleData.tests.map((t: any) => ({
        id: t.id,
        name: t.description,
        status: mapToTestItemStatus(t.status),
        duration: '',
      }))
      setTests(items)
    } else {
      const { groups, items } = getTestsForSidebarModule(selectedModule, apiModules)
      if (groups.length > 0) {
        setCurrentTestGroups(groups)
        setTests(items)
      }
    }
  }, [allTestCases, apiModules, selectedModule])

  const handleGoHome = useCallback(() => {
    setSelectedModule('dashboard')
    setActiveTab('operations')
    setSidebarOpen(true)
  }, [])

  const handleRunModule = useCallback((moduleId: string) => {
    handleSelectModule(moduleId)
    setTimeout(() => {
      setActiveTab('test-runner')
    }, 100)
  }, [handleSelectModule])

  const toggleTestCheck = useCallback((id: string) => {
    setTestChecks((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  const rerunTestIds = useCallback((ids: string[]) => {
    setTests((prev) =>
      prev.map((t) => (ids.includes(t.id) ? { ...t, status: 'pending' as const, duration: '' } : t))
    )
    setTestChecks(new Set(ids))
  }, [])

  const getTestError = useCallback((id: string): string | undefined => {
    for (const g of testSpecGroups) {
      const t = g.tests.find((x) => x.id === id)
      if (t) return t.bugDetails || (t.status === 'bug' ? t.actual : undefined)
    }
    for (const g of currentTestGroups) {
      const t = g.tests.find((x) => x.id === id)
      if (t) return t.bugDetails || (t.status === 'bug' ? t.actual : undefined)
    }
    return undefined
  }, [currentTestGroups])

  // Mock run animation
  const runTests = useCallback(
    (selectedOnly: boolean, forceIds?: string[]) => {
      if (isRunning) return

      let testsToRun: TestItem[]
      if (forceIds) {
        testsToRun = tests.filter((t) => forceIds.includes(t.id))
      } else if (selectedOnly) {
        testsToRun = tests.filter((t) => testChecks.has(t.id))
      } else {
        testsToRun = tests.filter((t) => t.status === 'pending' || t.status === 'failed')
      }

      if (testsToRun.length === 0) {
        toast.info('No tests to run')
        return
      }

      const mapping = sidebarToFolderMapping(selectedModule)
      if (!mapping) {
        toast.error('Cannot determine module path for: ' + selectedModule)
        return
      }

      setTests((prev) =>
        prev.map((t) =>
          testsToRun.some((r) => r.id === t.id) ? { ...t, status: (t.id === testsToRun[0].id ? 'running' as const : 'pending' as const), duration: '' } : t
        )
      )
      setIsRunning(true)
      setRunningProgress('Starting tests...')
      setActiveTab('live-execution')
      setConsoleLogs([])

      const testNames = testsToRun.map((t) => t.id)
      const runOnlyTests = selectedOnly || forceIds ? testNames : null

      startRun(
        mapping.module,
        mapping.subModule,
        runOnlyTests,
        (event) => {
          if (!currentRunIdRef.current && (event as Record<string, unknown>).run_id) {
            currentRunIdRef.current = (event as Record<string, unknown>).run_id as string
          }
          if (event.type === 'log') {
            setRunningProgress(event.message)
            setConsoleLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${event.message}`])
          } else if (event.type === 'test_end') {
            const statusLabel = event.status === 'passed' ? 'PASSED' : event.status === 'failed' ? 'FAILED' : 'SKIPPED'
            setConsoleLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${event.test_name} — ${statusLabel}${event.message ? ': ' + event.message : ''}`])
            if (event.test_name && event.status) {
              const testId = testsToRun.find((t) => t.id.endsWith('::' + event.test_name))?.id
                || testsToRun.find((t) => t.id.includes(event.test_name || ''))?.id
              if (testId) {
                setTests((prev) =>
                  prev.map((t) =>
                    t.id === testId
                      ? {
                          ...t,
                          status: event.status === 'passed' ? ('passed' as const)
                            : event.status === 'failed' ? ('failed' as const)
                            : ('pending' as const),
                          duration: event.duration ? `${(event.duration / 1000).toFixed(1)}s` : '--',
                        }
                      : t
                  )
                )
                if (event.status === 'failed') {
                  toast.error(`Failed: ${event.test_name}`, {
                    description: event.message || '',
                    duration: 8000,
                  })
                }
              }
            }
          } else if (event.type === 'run_end') {
            setRunningProgress('Run complete!')
            setConsoleLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] Run complete!`])
          } else if (event.type === 'error') {
            toast.error('Run error', { description: event.message, duration: 8000 })
            setConsoleLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ERROR: ${event.message}`])
          }
        },
        () => {
          setIsRunning(false)
          setRunningProgress('')
          toast.success('Test run finished!')
        },
        (err) => {
          setIsRunning(false)
          setRunningProgress('')
          toast.error('Connection failed', { description: err.message, duration: 8000 })
        }
      )
    },
    [isRunning, tests, testChecks, selectedModule]
  )

  // Run by priority
  const runByPriority = useCallback(
    (priority: TestPriority) => {
      if (isRunning) return
      const priorityIds = tests.filter((t) => t.priority === priority).map((t) => t.id)
      if (priorityIds.length === 0) return
      rerunTestIds(priorityIds)
      runTests(true, priorityIds)
      setActiveTab('live-execution')
    },
    [isRunning, tests, rerunTestIds, runTests]
  )

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement
      const isInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable

      if (e.key === 'Escape') {
        if (quickSwitcherOpen) { setQuickSwitcherOpen(false); return }
        if (showShortcuts) { setShowShortcuts(false); return }
        if (notifDropdownOpen) { setNotifDropdownOpen(false); return }
      }

      if (isInput) return
      if (!(e.ctrlKey || e.metaKey)) return

      if (e.key === 'b') { e.preventDefault(); setSidebarOpen((prev) => !prev); return }
      if (e.key === 'k') { e.preventDefault(); setQuickSwitcherOpen((prev) => !prev); setQuickSearch(''); return }
      if (e.key === 'd') { e.preventDefault(); toggleDarkMode(); return }
      if (e.key === '/') { e.preventDefault(); setShowShortcuts((prev) => !prev); return }

      if (e.key === 'r' && selectedModule !== 'dashboard' && selectedModule !== 'my-tickets' && !isRunning) {
        e.preventDefault()
        const pendingCount = tests.filter((t) => t.status === 'pending').length
        if (pendingCount > 0) { runTests(false); setActiveTab('live-execution') }
        return
      }

      if (selectedModule !== 'dashboard' && selectedModule !== 'my-tickets') {
        const tabMap: Record<string, string> = { '1': 'operations', '2': 'test-runner', '3': 'live-execution', '4': 'results', '5': 'screenshots', '6': 'schedule' }
        const tabId = tabMap[e.key]
        if (tabId) { e.preventDefault(); setActiveTab(tabId); return }
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [quickSwitcherOpen, showShortcuts, notifDropdownOpen, selectedModule, isRunning, tests, toggleDarkMode, runTests])

  const passedCount = tests.filter((t) => t.status === 'passed').length
  const failedCount = tests.filter((t) => t.status === 'failed').length

  const getModulePath = useCallback(() => {
    for (const mod of sidebarModules) {
      if (mod.id === selectedModule) return { parent: null, name: mod.label, badge: mod.badge }
      if (mod.children) {
        for (const child of mod.children) {
          if (child.id === selectedModule) return { parent: mod.label, name: child.label, badge: child.badge }
        }
      }
    }
    return { parent: null, name: selectedModule, badge: undefined }
  }, [selectedModule])

  const modulePath = getModulePath()

  const handleViewResults = useCallback(() => {
    setCompletionModalOpen(false)
    setActiveTab('results')
  }, [])

  const handleCompletionRerunFailed = useCallback(() => {
    setCompletionModalOpen(false)
    const failedIds = tests.filter((t) => t.status === 'failed').map((t) => t.id)
    if (failedIds.length > 0) {
      rerunTestIds(failedIds)
      runTests(true, failedIds)
      setActiveTab('live-execution')
    }
  }, [tests, rerunTestIds, runTests])

  const handleNewRun = useCallback(() => {
    setCompletionModalOpen(false)
    setTests(initialTests)
    setTestChecks(new Set())
    setActiveTab('test-runner')
  }, [])

  const handleReportTest = useCallback((test: TestItem) => {
    const error = getTestError(test.id)
    setReportingTest({ id: test.id, name: test.name, error })
    setReportDialogOpen(true)
  }, [getTestError])

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

  if (!user) {
    return <LoginPage onLogin={handleLogin} />
  }

  const userInitials = user.name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)

  const tabs = [
    { id: 'operations', label: '📋 Test Specifications' },
    { id: 'test-runner', label: '🧪 Test Runner' },
    { id: 'live-execution', label: '📺 Live Execution' },
    { id: 'results', label: '📈 Results' },
    { id: 'screenshots', label: '📸 Screenshots' },
    { id: 'schedule', label: '🗓️ Schedule' },
  ]

  return (
    <div className="h-screen flex flex-col bg-white dark:bg-gray-900 overflow-hidden">
      <AppTour selectedModule={selectedModule} activeTab={activeTab} />

      {/* ─── KEYBOARD SHORTCUTS CHEAT SHEET ──────────────── */}
      <Dialog open={showShortcuts} onOpenChange={setShowShortcuts}>
        <DialogContent className="sm:max-w-[440px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Zap className="size-4 text-green-600" />
              Keyboard Shortcuts
            </DialogTitle>
            <DialogDescription>
              Quick actions to speed up your workflow
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-1.5 py-2">
            {[
              { keys: 'Ctrl + B', desc: 'Toggle sidebar' },
              { keys: 'Ctrl + K', desc: 'Quick module search' },
              { keys: 'Ctrl + D', desc: 'Toggle dark mode' },
              { keys: 'Ctrl + R', desc: 'Run all pending tests' },
              { keys: 'Ctrl + 1', desc: 'Test Specifications tab' },
              { keys: 'Ctrl + 2', desc: 'Test Runner tab' },
              { keys: 'Ctrl + 3', desc: 'Live Execution tab' },
              { keys: 'Ctrl + 4', desc: 'Results tab' },
              { keys: 'Ctrl + 5', desc: 'Screenshots tab' },
              { keys: 'Ctrl + 6', desc: 'Schedule tab' },
              { keys: 'Ctrl + /', desc: 'Show this cheat sheet' },
              { keys: 'Escape', desc: 'Close dialog / panel' },
            ].map((s) => (
              <div key={s.keys} className="flex items-center justify-between px-2 py-1.5 rounded-md hover:bg-gray-50 dark:hover:bg-gray-800/50">
                <span className="text-[13px] text-gray-600 dark:text-gray-400">{s.desc}</span>
                <kbd className="px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-[11px] font-mono text-gray-700 dark:text-gray-300">
                  {s.keys}
                </kbd>
              </div>
            ))}
          </div>
          <DialogFooter>
            <span className="text-[11px] text-gray-400">Press <kbd className="px-1 py-0.5 rounded bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-[10px] font-mono">Ctrl + /</kbd> to toggle</span>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ─── HEADER ─────────────────────────────────────── */}
      <header className="h-[60px] bg-white dark:bg-gray-900 border-b border-[#e0e0e0] dark:border-gray-700 flex items-center px-4 shrink-0 z-10 shadow-[0_2px_8px_rgba(0,0,0,0.06)]">
        <div className="flex items-center gap-3 flex-1">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            data-tour="sidebar-toggle"
            className={`size-8 cursor-pointer shrink-0 transition-all duration-200 ${
              sidebarOpen
                ? 'text-[#888888] hover:text-[#333333] hover:bg-gray-100 dark:hover:bg-gray-800'
                : 'text-[#3F51B5] hover:text-[#2D3FC7] hover:bg-[#E8F5E9] dark:hover:bg-indigo-900/20'
            }`}
            title="Toggle sidebar (Ctrl+B)"
          >
            <Menu className={`size-[18px] transition-transform duration-200 ${sidebarOpen ? '' : 'rotate-90'}`} />
          </Button>
          <Separator orientation="vertical" className="h-5" />
          <div className="flex items-center gap-2">
            <Image src="/agdi-logo-new.webp" alt="AgDi Automation" width={70} height={28} className="object-contain" />
            <span className="text-[#888888] dark:text-gray-500 text-[13px]">Automation Runner</span>
          </div>
          <div className="hidden md:flex items-center ml-4 bg-[#F5F5F5] dark:bg-gray-800 rounded-md px-3 py-1.5 gap-2 w-64">
            <Search className="size-3.5 text-[#888888] dark:text-gray-400" />
            <input
              type="text"
              placeholder="Search modules..."
              className="bg-transparent text-[13px] text-[#333333] dark:text-gray-200 placeholder:text-[#888888] dark:placeholder:text-gray-500 outline-none flex-1"
              onFocus={() => setQuickSwitcherOpen(true)}
              readOnly
            />
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <Button variant="ghost" size="icon" onClick={toggleDarkMode} data-tour="dark-mode" className="size-8 text-[#888888] dark:text-gray-400 hover:text-[#333333] dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer" title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}>
            {darkMode ? <Sun className="size-4" /> : <Moon className="size-4" />}
          </Button>
          <Button variant="ghost" size="icon" onClick={startAppTour} data-tour="help-btn" className="size-8 text-[#3F51B5] hover:text-[#2D3FC7] hover:bg-[#E8F5E9] dark:hover:bg-indigo-900/20 cursor-pointer" title="Take a tour of the app">
            <HelpCircle className="size-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={() => setShowShortcuts(true)} data-tour="keyboard-shortcuts" className="size-8 text-[#888888] dark:text-gray-400 hover:text-[#333333] dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer" title="Keyboard shortcuts (Ctrl+/)">
            <Zap className="size-4" />
          </Button>
          {/* Bell Notification */}
          <div className="relative" data-tour="notifications">
            <Button variant="ghost" size="icon" onClick={() => { setNotifDropdownOpen((prev) => !prev); if (!notifDropdownOpen) handleMarkAllRead() }} className="size-8 text-[#888888] dark:text-gray-400 hover:text-[#333333] dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer relative" title="Notifications">
              <Bell className="size-4" />
              {unreadCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-[#6777EF] text-white text-[9px] font-bold rounded-full flex items-center justify-center animate-pulse">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </Button>
            {notifDropdownOpen && (
              <div className="absolute right-0 top-10 w-96 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 z-50 overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between bg-gray-50/50 dark:bg-gray-800/50">
                  <div className="flex items-center gap-2">
                    <Bell className="size-4 text-[#3F51B5]" />
                    <span className="text-[13px] font-semibold text-[#333333] dark:text-gray-100">Notifications</span>
                    {unreadCount > 0 && (
                      <Badge className="bg-[#6777EF] text-white text-[10px] px-1.5 py-0 h-4">{unreadCount} new</Badge>
                    )}
                  </div>
                  <button onClick={handleMarkAllRead} className="text-[11px] text-[#3F51B5] hover:text-[#2D3FC7] cursor-pointer font-medium">Mark all read</button>
                </div>
                <div className="max-h-72 overflow-y-auto">
                  {notifications.length === 0 ? (
                    <div className="p-8 text-center">
                      <Bell className="size-8 text-gray-200 dark:text-gray-600 mx-auto mb-2" />
                      <div className="text-[13px] text-gray-400 dark:text-gray-500">No notifications yet</div>
                      <div className="text-[11px] text-gray-300 dark:text-gray-600 mt-1">Notifications will appear here when tests complete or bugs are updated</div>
                    </div>
                  ) : (
                    notifications.slice(0, 20).map((n) => {
                      const getCategoryStyle = (type: string) => {
                        switch (type) {
                          case 'run_complete': return { icon: <CheckCircle2 className="size-3.5" />, color: 'text-green-500 bg-green-50 dark:bg-green-900/20' }
                          case 'status_change': return { icon: <RotateCcw className="size-3.5" />, color: 'text-blue-500 bg-blue-50 dark:bg-blue-900/20' }
                          case 'reply': return { icon: <MessageSquare className="size-3.5" />, color: 'text-purple-500 bg-purple-50 dark:bg-purple-900/20' }
                          case 'schedule': return { icon: <CalendarClock className="size-3.5" />, color: 'text-orange-500 bg-orange-50 dark:bg-orange-900/20' }
                          default: return { icon: <Bell className="size-3.5" />, color: 'text-gray-500 bg-gray-50 dark:bg-gray-700/50' }
                        }
                      }
                      const catStyle = getCategoryStyle(n.type)
                      return (
                        <div key={n.id} className={`px-4 py-2.5 border-b border-gray-50 dark:border-gray-700/50 flex gap-3 items-start hover:bg-gray-50/50 dark:hover:bg-gray-700/20 transition-colors ${!n.read ? 'bg-[#E8F5E9]/30 dark:bg-green-900/5' : ''}`}>
                          <div className={`shrink-0 w-7 h-7 rounded-full flex items-center justify-center ${catStyle.color}`}>
                            {catStyle.icon}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="text-[12px] font-medium text-[#333333] dark:text-gray-200 leading-tight">{n.title}</div>
                            <div className="text-[11px] text-[#666666] dark:text-gray-400 mt-0.5 leading-snug">{n.message}</div>
                            <div className="text-[10px] text-[#888888] dark:text-gray-500 mt-1">{new Date(n.createdAt).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}</div>
                          </div>
                          {!n.read && <div className="shrink-0 w-2 h-2 rounded-full bg-[#6777EF] mt-1.5" />}
                        </div>
                      )
                    })
                  )}
                </div>
                {notifications.length > 0 && (
                  <div className="px-4 py-2 border-t border-gray-100 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50 text-center">
                    <span className="text-[11px] text-gray-400 dark:text-gray-500">{notifications.length} notification{notifications.length !== 1 ? 's' : ''}</span>
                  </div>
                )}
              </div>
            )}
          </div>
          {(user.role === 'admin' || user.role === 'qa_lead') && (
            <Link href="/admin" className="flex items-center gap-1.5 px-2.5 h-8 text-[12px] text-[#888888] dark:text-gray-400 hover:text-red-700 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md transition-colors" title="Admin Panel">
              <Shield className="size-3.5" />
              <span className="hidden sm:inline">Admin</span>
            </Link>
          )}
          <Separator orientation="vertical" className="h-5 mx-0.5" />
          <div className="flex items-center gap-2" data-tour="user-menu">
            <button onClick={() => setProfileDialogOpen(true)} className="flex items-center gap-2 hover:opacity-80 transition-opacity cursor-pointer">
              <Avatar className="size-7">
                <AvatarFallback className="bg-[#6777EF] text-white text-xs font-semibold">
                  {userInitials}
                </AvatarFallback>
              </Avatar>
              <div className="hidden sm:flex flex-col">
                <span className="text-[12px] text-[#333333] dark:text-gray-200 font-medium max-w-[120px] truncate leading-tight">{user.name}</span>
                <span className="text-[10px] text-[#888888] dark:text-gray-500 leading-tight">{user.role}</span>
              </div>
            </button>
            <Button variant="ghost" size="icon" onClick={handleLogout} data-tour="logout-btn" className="size-7 text-[#888888] hover:text-red-500 cursor-pointer" title="Sign out">
              <LogOut className="size-3.5" />
            </Button>
          </div>
        </div>
      </header>

      {/* ─── BODY ───────────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">
        {/* ─── SIDEBAR ──────────────────────────────────── */}
        <div className="shrink-0 overflow-hidden h-full" style={{ width: sidebarOpen ? sidebarWidth : 0 }}>
          <aside className="flex flex-col h-full font-['Poppins'] bg-gradient-to-b from-[#F7FBF8] via-[#EAF5EC] to-[#D6EDDC] dark:from-[#1e293b] dark:via-[#1e293b] dark:to-[#1e293b] shadow-[-1px_0px_0px_#D4E3D9] dark:shadow-[-1px_0px_0px_#334155]" style={{ width: sidebarWidth }}>
            <ScrollArea className="flex-1 min-h-0" data-tour="sidebar-modules">
              <div className="py-2 px-2">
                {sidebarModules.map((mod) => (
                  <SidebarModuleItem
                    key={mod.id}
                    module={mod}
                    activeId={selectedModule}
                    onSelect={handleSelectModule}
                    expandedIds={expandedIds}
                    toggleExpand={toggleExpand}
                  />
                ))}
              </div>
            </ScrollArea>
            <div className="px-3 py-2 border-t border-[#E2E8F0] dark:border-[#334155]">
              <div className="relative w-full h-16 mb-1.5 rounded-lg overflow-hidden opacity-70">
                <Image src="/agdi-landscape.png" alt="AgDi Landscape" fill className="object-cover" />
              </div>
              <div className="flex items-center gap-2 text-[11px] text-[#666666] dark:text-gray-400">
                <div className="w-2 h-2 rounded-full bg-[#4CAF50] animate-pulse" />
                Connected to RhythmERP
              </div>
              <div className="text-[9px] text-[#888888] dark:text-gray-500 mt-1">
                agDi v1.0 · Helpline: 18006043021
              </div>
            </div>
          </aside>
        </div>

        {/* ─── RESIZE HANDLE ────────────────────────────── */}
        {sidebarOpen && (
          <div onMouseDown={handleResizeStart} className="w-1 cursor-col-resize bg-transparent hover:bg-[#3F51B5]/40 active:bg-[#3F51B5]/60 transition-colors shrink-0 relative z-10" />
        )}

        {/* ─── MAIN CONTENT ─────────────────────────────── */}
        <main className="flex-1 flex flex-col overflow-hidden bg-[#F1F2F7] dark:bg-gray-900 relative">
          {navToast && <NavToast key={navToast.key} label={navToast.label} parent={navToast.parent} />}
          {/* Breadcrumb */}
          {!sidebarOpen && selectedModule !== 'dashboard' && (
            <div className="flex items-center gap-1.5 px-4 py-2 border-b border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-900 shrink-0">
              <button onClick={handleGoHome} className="text-[12px] text-[#3F51B5] hover:text-[#2D3FC7] dark:hover:text-indigo-400 font-medium cursor-pointer transition-colors hover:underline">Dashboard</button>
              {modulePath.parent && (<><ChevronRight className="size-3 text-gray-400 dark:text-gray-500" /><span className="text-[12px] text-gray-500 dark:text-gray-400">{modulePath.parent}</span></>)}
              <ChevronRight className="size-3 text-gray-400 dark:text-gray-500" />
              <span className="text-[12px] text-gray-800 dark:text-gray-100 font-medium">{modulePath.name}</span>
              {modulePath.badge && <span className="text-[11px] text-orange-600 dark:text-orange-400 ml-1">{modulePath.badge}</span>}
              <div className="flex-1" />
              <span className="text-[11px] text-gray-400 dark:text-gray-500"><kbd className="px-1 py-0.5 rounded bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-[10px] font-mono">Ctrl+B</kbd>{' '}to toggle</span>
            </div>
          )}

          {/* ── DASHBOARD VIEW ── */}
          {selectedModule === 'dashboard' && (
            <div data-tour="dashboard" className="flex-1 min-h-0 overflow-hidden">
              <DashboardTab onSelectModule={handleSelectModule} moduleHealth={moduleHealth} onRunModule={handleRunModule} runHistory={runHistory} />
            </div>
          )}

          {/* ── MY TICKETS VIEW ── */}
          {selectedModule === 'my-tickets' && user && (
            <MyTicketsTab userEmail={user.email} userName={user.name} />
          )}

          {/* ── MODULE VIEW (module selected — tabs + content) ── */}
          {selectedModule !== 'dashboard' && selectedModule !== 'my-tickets' && (
            <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
              {/* Tab bar */}
              <div className="border-b border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/30 shrink-0" data-tour="tab-bar">
                <div className="flex items-center h-10 px-4 gap-0">
                  {tabs.map((tab) => (
                    <button key={tab.id} onClick={() => setActiveTab(tab.id)} className={`px-4 h-full text-[13px] font-medium transition-colors border-b-2 cursor-pointer ${activeTab === tab.id ? 'border-[#3F51B5] text-[#3F51B5] dark:text-indigo-400 bg-white dark:bg-gray-900' : 'border-transparent text-[#888888] dark:text-gray-400 hover:text-[#333333] dark:hover:text-gray-200 hover:bg-gray-100/50 dark:hover:bg-gray-800/30'}`}>
                      {tab.label}
                    </button>
                  ))}
                  <div className="flex-1" />
                  <span className="text-[12px] text-gray-400 dark:text-gray-500">Module: <span className="text-gray-600 dark:text-gray-300 font-medium">{modulePath.name}</span>{modulePath.badge && <span className="ml-2 text-orange-600 dark:text-orange-400">{modulePath.badge}</span>}</span>
                </div>
              </div>

              {/* Tab Content */}
              <div className="flex-1 overflow-hidden min-h-0">
                {activeTab === 'operations' && (
                  <div data-tour="operations" className="h-full">
                    <OperationsTab testGroups={currentTestGroups} testCasesModule={allTestCases[selectedModule?.toLowerCase().replace(' ', '_').replace('-', '_')]} />
                  </div>
                )}
                {activeTab === 'test-runner' && (
                  <div data-tour="test-runner" className="h-full">
                    <TestRunnerTab tests={tests} testChecks={testChecks} toggleTestCheck={toggleTestCheck} isRunning={isRunning} totalFailed={failedCount}
                      onRun={(selectedOnly) => { runTests(selectedOnly); setActiveTab('live-execution') }}
                      onRunByPriority={runByPriority}
                      onRerunFailed={() => { const failedIds = tests.filter((t) => t.status === 'failed').map((t) => t.id); if (failedIds.length > 0) { rerunTestIds(failedIds); runTests(true, failedIds); setActiveTab('live-execution') } }}
                    />
                  </div>
                )}
                {activeTab === 'live-execution' && (
                  <div data-tour="live-execution" className="h-full">
                    <LiveExecutionTab tests={tests} testGroups={currentTestGroups} isRunning={isRunning} runningProgress={runningProgress}
                      onStop={async () => { const runId = currentRunIdRef.current; if (runId) { try { await stopRun(runId); toast.success('Run stopped') } catch (err) { toast.error('Failed to stop run', { description: err instanceof Error ? err.message : 'Unknown error' }) } } setIsRunning(false) }}
                      onBack={() => setActiveTab('test-runner')}
                      onRerunFailed={() => { const failedIds = tests.filter((t) => t.status === 'failed').map((t) => t.id); if (failedIds.length > 0) { rerunTestIds(failedIds); runTests(true, failedIds) } }}
                      onScreenshotCaptured={(entry) => { setScreenshotEntries((prev) => { if (prev.length >= 50) return [entry, ...prev.slice(0, 49)]; return [entry, ...prev] }) }}
                    />
                  </div>
                )}
                {activeTab === 'results' && (
                  <div data-tour="results" className="h-full">
                    <ResultsTab tests={tests} passedCount={passedCount} failedCount={failedCount} totalCount={tests.length} runHistory={runHistory} onReportTest={handleReportTest} bugReportsList={bugReportsList}
                      onRunDetail={(run) => { setSelectedRunForDetail(run); setRunDetailDialogOpen(true) }}
                      onCompareRuns={() => setRunComparisonOpen(true)}
                      testGroups={currentTestGroups} moduleHealth={moduleHealth} moduleName={modulePath.name}
                    />
                  </div>
                )}
                {activeTab === 'screenshots' && (
                  <div data-tour="screenshots" className="flex flex-col h-full min-h-0">
                    <div className="p-4 shrink-0">
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <h3 className="text-[14px] font-semibold text-gray-800 dark:text-gray-100">Screenshot Gallery</h3>
                          <p className="text-[12px] text-gray-500 dark:text-gray-400 mt-0.5">Screenshots captured during test execution</p>
                        </div>
                        <div className="flex items-center gap-2">
                          {screenshotEntries.length >= 2 && (
                            <Button variant="outline" size="sm" onClick={() => { setCompareScreenshots([screenshotEntries[0] || null, screenshotEntries[1] || null]); setScreenshotCompareOpen(true) }} className="h-7 text-[12px] gap-1.5 cursor-pointer">
                              <RefreshCw className="size-3" /> Compare
                            </Button>
                          )}
                          <Button variant="outline" size="sm" onClick={async () => { try { const data = await (await import('@/lib/api')).fetchScreenshot(); if (data.active && data.screenshot) { const newEntry: ScreenshotEntry = { id: `ss-${Date.now()}`, src: `data:image/png;base64,${data.screenshot}`, testName: 'Live Capture', timestamp: new Date().toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit' }), status: 'running' }; setScreenshotEntries((prev) => [newEntry, ...prev]); toast.success('Screenshot captured') } else { toast.info('No active screenshot available') } } catch { toast.error('Failed to capture screenshot') } }} className="h-7 text-[12px] gap-1.5 cursor-pointer">
                            <Play className="size-3" /> Capture Now
                          </Button>
                        </div>
                      </div>
                    </div>
                    <div className="flex-1 overflow-auto px-4 pb-4">
                      <ScreenshotGallery screenshots={screenshotEntries} onRefresh={async () => { try { const data = await (await import('@/lib/api')).fetchScreenshot(); if (data.active && data.screenshot) { const newEntry: ScreenshotEntry = { id: `ss-${Date.now()}`, src: `data:image/png;base64,${data.screenshot}`, testName: 'Live Capture', timestamp: new Date().toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit' }), status: 'running' }; setScreenshotEntries((prev) => [newEntry, ...prev]) } } catch {} }} />
                    </div>
                  </div>
                )}
                {activeTab === 'schedule' && user && (
                  <div data-tour="schedule-runs" className="h-full">
                    <ScheduleRunsTab userName={user.name} sidebarModules={sidebarModules} />
                  </div>
                )}
              </div>
            </div>
          )}
        </main>
      </div>

      {/* ─── CONSOLE PANEL ──────────────────────────────── */}
      {consoleOpen && (
        <div className="shrink-0 border-t border-gray-700 bg-[#1a1a2e] flex flex-col" style={{ height: '200px' }}>
          <div className="flex items-center justify-between px-4 py-1.5 bg-[#16162a] border-b border-gray-700">
            <div className="flex items-center gap-2">
              <Terminal className="size-3.5 text-green-400" />
              <span className="text-[12px] text-gray-300 font-medium">Console Output</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] text-gray-500">{consoleLogs.length} entries</span>
              <Button variant="ghost" size="icon" className="size-5 text-gray-400 hover:text-gray-200" onClick={() => setConsoleOpen(false)}>
                <X className="size-3" />
              </Button>
            </div>
          </div>
          <ScrollArea className="flex-1 px-4 py-2">
            <div className="space-y-0.5">
              {consoleLogs.map((log, i) => (
                <div key={i} className={`text-[12px] font-mono leading-5 ${log.includes('PASSED') ? 'text-green-400' : log.includes('FAILED') ? 'text-red-400' : log.includes('Navigating') || log.includes('Clicking') || log.includes('Filling') || log.includes('Selecting') || log.includes('Setting') ? 'text-yellow-300' : 'text-gray-300'}`}>
                  {log}
                </div>
              ))}
            </div>
          </ScrollArea>
        </div>
      )}

      {/* Floating "New Test Run" button on Live Execution */}
      {activeTab === 'live-execution' && !isRunning && passedCount + failedCount > 0 && (
        <button onClick={() => setActiveTab('test-runner')} className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 bg-[#3F51B5] hover:bg-[#2D3FC7] text-white transition-all duration-200 rounded-xl px-5 py-2.5 flex items-center gap-2 cursor-pointer hover:-translate-y-0.5">
          <RotateCcw className="size-4" />
          <span className="text-[13px] font-medium">New Test Run</span>
        </button>
      )}

      {/* ─── QUICK SWITCHER (Cmd+K) ────────────────────── */}
      {quickSwitcherOpen && (
        <>
          <div className="fixed inset-0 z-[100] bg-black/40 backdrop-blur-sm" onClick={() => setQuickSwitcherOpen(false)} />
          <div className="fixed top-[20%] left-1/2 -translate-x-1/2 z-[101] w-full max-w-lg">
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
              <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-100 dark:border-gray-700">
                <Search className="size-4 text-gray-400 shrink-0" />
                <input type="text" value={quickSearch} onChange={(e) => setQuickSearch(e.target.value)} placeholder="Search modules... (e.g. tax, uom, crop)" className="flex-1 text-[14px] text-gray-800 dark:text-gray-100 placeholder:text-gray-400 outline-none bg-transparent" autoFocus onKeyDown={(e) => { if (e.key === 'Escape') setQuickSwitcherOpen(false) }} />
                <kbd className="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 text-[10px] font-mono text-gray-400 shrink-0">ESC</kbd>
              </div>
              <div className="max-h-[300px] overflow-auto py-2">
                {(() => {
                  const q = quickSearch.toLowerCase()
                  const flatModules: { id: string; label: string; parent?: string; badge?: string }[] = []
                  for (const mod of sidebarModules) {
                    if (mod.children) { for (const child of mod.children) { flatModules.push({ id: child.id, label: child.label, parent: mod.label, badge: child.badge }) } }
                    else { flatModules.push({ id: mod.id, label: mod.label, badge: mod.badge }) }
                  }
                  const filtered = q ? flatModules.filter((m) => m.label.toLowerCase().includes(q) || m.id.toLowerCase().includes(q) || (m.parent && m.parent.toLowerCase().includes(q))) : flatModules
                  if (filtered.length === 0) { return <div className="px-4 py-6 text-center text-[13px] text-gray-400 dark:text-gray-500">No modules found</div> }
                  return filtered.map((mod) => {
                    const isActive = mod.id === selectedModule
                    return (
                      <button key={mod.id} onClick={() => { setSelectedModule(mod.id); setActiveTab('operations'); setQuickSwitcherOpen(false); setSidebarOpen(true) }} className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors cursor-pointer ${isActive ? 'bg-[#E8F5E9] dark:bg-[#1B4332]/20 text-[#1B4332] dark:text-green-400' : 'text-[#333333] dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700/50'}`}>
                        {mod.parent && <span className="text-[11px] text-gray-400 dark:text-gray-500 truncate max-w-[100px]">{mod.parent}</span>}
                        {mod.parent && <ChevronRight className="size-3 text-gray-300 dark:text-gray-600 shrink-0" />}
                        <span className={`text-[13px] flex-1 truncate ${isActive ? 'font-medium' : ''}`}>{mod.label}</span>
                        {mod.badge && <span className="text-[11px] text-gray-500 dark:text-gray-400 shrink-0">{mod.badge}</span>}
                        {isActive && <CheckCircle2 className="size-3.5 text-[#3F51B5] shrink-0" />}
                      </button>
                    )
                  })
                })()}
              </div>
              <div className="flex items-center gap-4 px-4 py-2 border-t border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 text-[11px] text-gray-400">
                <span><kbd className="px-1 py-0.5 rounded bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 text-[10px] font-mono">↑↓</kbd> navigate</span>
                <span><kbd className="px-1 py-0.5 rounded bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 text-[10px] font-mono">Enter</kbd> select</span>
                <span><kbd className="px-1 py-0.5 rounded bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 text-[10px] font-mono">Esc</kbd> close</span>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Console toggle button */}
      {!consoleOpen && (
        <button onClick={() => setConsoleOpen(true)} className="fixed bottom-4 right-4 z-50 bg-[#1a1a2e] text-green-400 hover:bg-[#252540] transition-colors rounded-lg px-3 py-2 flex items-center gap-2 shadow-lg border border-gray-700 cursor-pointer">
          <Terminal className="size-3.5" />
          <span className="text-[12px] font-medium">Console</span>
          <span className="bg-green-500/20 text-green-400 text-[10px] px-1.5 py-0.5 rounded-full">{consoleLogs.length}</span>
        </button>
      )}
      {consoleOpen && (
        <button onClick={() => setConsoleOpen(false)} className="fixed bottom-[208px] right-4 z-50 bg-[#1a1a2e] text-gray-400 hover:text-gray-200 transition-colors rounded-t-lg px-3 py-1 flex items-center gap-1.5 shadow-lg border border-b-0 border-gray-700 cursor-pointer">
          <Minimize2 className="size-3" /><span className="text-[11px]">Hide</span>
        </button>
      )}

      {/* ─── Feature 1: Completion Summary Modal ────────── */}
      <CompletionSummaryModal open={completionModalOpen} onClose={() => setCompletionModalOpen(false)} passedCount={completionStats.passed} failedCount={completionStats.failed} totalDuration={completionStats.duration} onViewResults={handleViewResults} onRerunFailed={handleCompletionRerunFailed} onNewRun={handleNewRun} />

      {/* ─── Bug Report Dialog ────────────────────────────── */}
      <ReportToAdminDialog open={reportDialogOpen} onClose={() => setReportDialogOpen(false)} testId={reportingTest?.id || ''} testDescription={reportingTest?.name || ''} error={reportingTest?.error} moduleName={modulePath.name} userName={user?.name || ''} userEmail={user?.email || ''} />

      {/* ─── Feature 2: User Profile Dialog ──────────────── */}
      {user && <UserProfileDialog open={profileDialogOpen} onClose={() => setProfileDialogOpen(false)} user={user} />}

      {/* ─── Feature 4: Run Detail Dialog ─────────────────── */}
      <RunDetailDialog open={runDetailDialogOpen} onClose={() => { setRunDetailDialogOpen(false); setSelectedRunForDetail(null) }} run={selectedRunForDetail} />

      {/* ─── Phase 4: Run Comparison Dialog ──────────────── */}
      <RunComparisonDialog open={runComparisonOpen} onClose={() => setRunComparisonOpen(false)} runHistory={runHistory} />

      {/* ─── Phase 4: Screenshot Lightbox ── */}
      {lightboxOpen && <ScreenshotLightbox open={lightboxOpen} onClose={() => setLightboxOpen(false)} screenshots={screenshotEntries} initialIndex={lightboxIndex} />}

      {/* ─── Phase 4: Screenshot Compare ─────────────────── */}
      {screenshotCompareOpen && <ScreenshotCompare left={compareScreenshots[0]} right={compareScreenshots[1]} onClose={() => setScreenshotCompareOpen(false)} />}

      {/* ─── FOOTER (ERP-style) ───────────────────────────── */}
      <footer className="shrink-0 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-4 py-1.5 flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-[10px] text-gray-400 dark:text-gray-500">
          <Copyright className="size-3" />
          <span>2026 AgDi Solutions Pvt. Ltd. All rights reserved.</span>
        </div>
        <div className="flex items-center gap-3 text-[10px] text-gray-400 dark:text-gray-500">
          <span className="flex items-center gap-1">Version 1.0.0</span>
          <a href="https://rhythmerp.algorhythms.in" target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 hover:text-[#3F51B5] dark:hover:text-indigo-400 transition-colors cursor-pointer">
            <HelpCircle className="size-3" /> Help <ExternalLink className="size-2.5" />
          </a>
        </div>
      </footer>
    </div>
  )
}
