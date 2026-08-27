'use client'

import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { useNotificationsSocket } from '@/hooks/use-notifications-socket'
import { useTheme } from 'next-themes'
import { toast } from 'sonner'
import { fetchModules, syncModulesToDB, fetchScreenshot, type ApiModule } from '@/lib/api'
import { ALL_SIDEBAR_MODULES } from '@/data/sidebarModules'
import { initialTests, type TestClassGroup, type TestPriority, type TestSpecItem } from '@/data/testSpecGroups'
import { buildSidebarModules, filterSidebarByAccess, getAllowedTabsForModule } from '@/lib/sidebar-helpers'
import { getTestsForSidebarModule } from '@/lib/test-helpers'
import NavToast from '@/components/nav-toast/NavToast'
import {
  getNotifications, markAllNotificationsRead, getUnreadNotificationCount,
  updateBugReportStatus, addNotification,
  type Notification as NotifType, type BugReport,
} from '@/lib/bug-reports'
import {
  getBrowserNotifyPreference, getBrowserNotifyPermission,
  requestBrowserNotifyPermission, setBrowserNotifyPreference,
} from '@/lib/browser-notify'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog'
import {
  Search, Play, RotateCcw, X, Minimize2, CheckCircle2,
  XCircle, AlertTriangle, Menu, Sun, Moon,
  Zap, Shield, MessageSquare, Bell, CalendarClock,
  Terminal, Monitor, HelpCircle, Copyright, ExternalLink,
  ChevronRight, LogOut, GitCompare, FlaskConical, BarChart2, Camera,
  Copy, Check, Package,
} from 'lucide-react'
import LoadingCard from '@/components/ui/LoadingCard'
import Spinner from '@/components/ui/Spinner'
import dynamic from 'next/dynamic'
import { startAppTour } from '@/components/tour/AppTour'
import { LoginPage } from '@/components/auth/LoginPage'
import type { AuthUser, ErpCred } from '@/lib/types'
import { SidebarModuleItem } from '@/components/sidebar/SidebarModuleItem'
import type { SidebarModule } from '@/components/sidebar/SidebarModuleItem'
import { getPanelPreference } from '@/components/PanelToggle'
import Link from 'next/link'
import Image from 'next/image'
import type { ScreenshotEntry } from '@/components/screenshot/ScreenshotGallery'
import { withCsrf } from '@/lib/csrf-client'
import { useTestRun } from '@/hooks/useTestRun'
import { useDialogs } from '@/hooks/useDialogs'
import { usePageData } from '@/hooks/usePageData'
import { useModuleHealth } from '@/hooks/useModuleHealth'
import { DashboardRenderer } from '@/components/dashboard/DashboardRenderer'
import { PersonalDashboardRenderer } from '@/components/dashboard/PersonalDashboardRenderer'

const TestRunnerTab = dynamic(() => import('@/components/test-runner/TestRunnerTab').then(m => ({ default: m.TestRunnerTab })), { ssr: false })
const LiveExecutionTab = dynamic(() => import('@/components/live-execution/LiveExecutionTab').then(m => ({ default: m.LiveExecutionTab })), { ssr: false })
const ScheduleRunsTab = dynamic(() => import('@/components/schedule/ScheduleRunsTab').then(m => ({ default: m.ScheduleRunsTab })), { ssr: false })
const PurchaseChainSection = dynamic(() => import('@/components/dialogs/PurchaseChainSection').then(m => ({ default: m.PurchaseChainSection })), { ssr: false })
const ResultsTab = dynamic(() => import('@/components/results/ResultsTab').then(m => ({ default: m.ResultsTab })), { ssr: false })
const MyTicketsTab = dynamic(() => import('@/components/tickets/MyTicketsTab').then(m => ({ default: m.MyTicketsTab })), { ssr: false })
const ReportToAdminDialog = dynamic(() => import('@/components/dialogs/ReportToAdminDialog').then(m => ({ default: m.ReportToAdminDialog })), { ssr: false })
const CompletionSummaryModal = dynamic(() => import('@/components/dialogs/CompletionSummaryModal').then(m => ({ default: m.CompletionSummaryModal })), { ssr: false })
const UserProfileDialog = dynamic(() => import('@/components/dialogs/UserProfileDialog').then(m => ({ default: m.UserProfileDialog })), { ssr: false })
const CredentialsScreen = dynamic(() => import('@/components/credentials/CredentialsScreen').then(m => ({ default: m.CredentialsScreen })), { ssr: false })
const RunDetailDialog = dynamic(() => import('@/components/dialogs/RunDetailDialog').then(m => ({ default: m.RunDetailDialog })), { ssr: false })
const AppTour = dynamic(() => import('@/components/tour/AppTour').then(m => ({ default: m.AppTour })), { ssr: false })
const ScreenshotGallery = dynamic(() => import('@/components/screenshot/ScreenshotGallery').then(m => ({ default: m.ScreenshotGallery })), { ssr: false })
const ScreenshotLightbox = dynamic(() => import('@/components/screenshot/ScreenshotGallery').then(m => ({ default: m.ScreenshotLightbox })), { ssr: false })
const ScreenshotCompare = dynamic(() => import('@/components/screenshot/ScreenshotGallery').then(m => ({ default: m.ScreenshotCompare })), { ssr: false })
const RunComparisonDialog = dynamic(() => import('@/components/comparison/RunComparisonDialog'), { ssr: false })
const RunHistoryDialog = dynamic(() => import('@/components/dialogs/RunHistoryDialog').then(m => ({ default: m.RunHistoryDialog })), { ssr: false })
const SetTokenDialog = dynamic(() => import('@/components/dialogs/SetTokenDialog').then(m => ({ default: m.SetTokenDialog })), { ssr: false })
const ConcurrencyTab = dynamic(() => import('@/components/concurrency/ConcurrencyTab').then(m => ({ default: m.ConcurrencyTab })), { ssr: false })
const DeploymentCheckTab = dynamic(() => import('@/components/deployment/DeploymentCheckTab').then(m => ({ default: m.DeploymentCheckTab })), { ssr: false })
import type { RunSnapshot, ModuleHealth } from '@/lib/types'

function RestartBackendButton() {
  const [state, setState] = React.useState<'idle'|'restarting'|'ok'|'err'>('idle')
  const handle = async () => {
    setState('restarting')
    try {
      await fetch('/api/proxy?path=restart', { method: 'POST', headers: { 'Content-Type': 'application/json' } })
      // poll health until back up (max 15s)
      const t0 = Date.now()
      while (Date.now() - t0 < 15000) {
        await new Promise(r => setTimeout(r, 800))
        try {
          const r = await fetch('/api/proxy?path=health')
          if (r.ok) { setState('ok'); setTimeout(() => setState('idle'), 2000); return }
        } catch {}
      }
      setState('err')
    } catch { setState('err') }
    setTimeout(() => setState('idle'), 3000)
  }
  return (
    <button onClick={handle} disabled={state === 'restarting'}
      title="Restart backend server"
      className="flex items-center gap-1.5 px-2 h-7 text-[11px] font-medium text-gray-400 dark:text-gray-500 hover:text-orange-600 dark:hover:text-orange-400 hover:bg-orange-50 dark:hover:bg-orange-900/20 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
      <RotateCcw className={`size-3.5 ${state === 'restarting' ? 'animate-spin' : ''}`} />
      <span className="hidden sm:inline">
        {state === 'restarting' ? 'Restarting…' : state === 'ok' ? 'Ready ✓' : state === 'err' ? 'Failed' : 'Restart'}
      </span>
    </button>
  )
}

export default function Home() {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)
  const [sidebarModules, setSidebarModules] = useState<SidebarModule[]>([])
  const [apiModules, setApiModules] = useState<ApiModule[]>([])
  const [selectedModule, setSelectedModule] = useState<string>('dashboard')
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())
  const [justExpandedId, setJustExpandedId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('test-runner')
  const [consoleOpen, setConsoleOpen] = useState(false)
  const [consoleCopied, setConsoleCopied] = useState(false)
  const [hashReady, setHashReady] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [sidebarWidth, setSidebarWidth] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('sidebar-width')
      return saved ? Number(saved) : 350
    }
    return 350
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
  const [showRawNames, setShowRawNames] = useState(() => typeof window !== 'undefined' && localStorage.getItem('showRawNames') === 'true')
  const [erpToken, setErpToken] = useState(() => typeof window !== 'undefined' ? localStorage.getItem('erp_token') ?? '' : '')
  const [erpTenantId, setErpTenantId] = useState(() => typeof window !== 'undefined' ? localStorage.getItem('erp_tenant_id') ?? '' : '')
  useEffect(() => { if (erpToken) localStorage.setItem('erp_token', erpToken); else localStorage.removeItem('erp_token') }, [erpToken])
  useEffect(() => { if (erpTenantId) localStorage.setItem('erp_tenant_id', erpTenantId); else localStorage.removeItem('erp_tenant_id') }, [erpTenantId])
  // ERP UI credentials (email/password for Selenium tests)
  const [erpCredentials, setErpCredentials] = useState<ErpCred[]>([])
  const [activeCredId, setActiveCredId] = useState<string | null>(null)
  const [credLoading, setCredLoading] = useState(false)
  const [credForm, setCredForm] = useState({ name: '', email: '', password: '', tenantUrl: 'https://rhythmerp.algorhythms.in', isDefault: false })
  const [credFormOpen, setCredFormOpen] = useState(false)
  const [credSaving, setCredSaving] = useState(false)
  const credPasswords = useRef<Record<string, string>>({})
  const [notifDropdownOpen, setNotifDropdownOpen] = useState(false)
  const [unreadCount, setUnreadCount] = useState(0)
  const [notifications, setNotifications] = useState<NotifType[]>([])
  const [desktopNotifEnabled, setDesktopNotifEnabled] = useState(false)
  const [desktopNotifGranted, setDesktopNotifGranted] = useState(false)

  useEffect(() => {
    setDesktopNotifEnabled(getBrowserNotifyPreference())
    setDesktopNotifGranted(getBrowserNotifyPermission() === 'granted')
  }, [])

  const handleDesktopNotifToggle = useCallback(async (enabled: boolean) => {
    if (enabled) {
      let permission = getBrowserNotifyPermission()
      if (permission !== 'granted') {
        permission = await requestBrowserNotifyPermission()
      }
      if (permission === 'granted') {
        setBrowserNotifyPreference(true)
        setDesktopNotifEnabled(true)
        setDesktopNotifGranted(true)
        toast.success('Desktop notifications enabled', { description: 'You will get a PC notification when tasks complete.' })
      } else if (permission === 'denied') {
        setDesktopNotifEnabled(false)
        setDesktopNotifGranted(false)
        toast.error('Notifications blocked', { description: 'Enable them in your browser site settings, then try again.' })
      } else {
        setBrowserNotifyPreference(true)
        setDesktopNotifEnabled(true)
        toast('Desktop notifications enabled once you allow permission', { description: 'Check your browser permission prompt.' })
      }
    } else {
      setBrowserNotifyPreference(false)
      setDesktopNotifEnabled(false)
    }
  }, [])
  const [navToast, setNavToast] = useState<{ key: number; label: string; parent?: string | null } | null>(null)
  const [verifyingTicket, setVerifyingTicket] = useState<BugReport | null>(null)
  const [verifyResult, setVerifyResult] = useState<{ ticketId: string; passed: boolean } | null>(null)

  const { connected: wsConnected, on: wsOn } = useNotificationsSocket(user?.id)
  const { theme, setTheme } = useTheme()
  const darkMode = theme === 'dark'
  const [themeVersion, setThemeVersion] = useState(0)
  const toggleDarkMode = useCallback(() => { setTheme(darkMode ? 'light' : 'dark'); setThemeVersion(v => v + 1) }, [darkMode, setTheme])

  const refreshNotifications = useCallback(async () => {
    setUnreadCount(await getUnreadNotificationCount())
    setNotifications(await getNotifications())
  }, [])

  const pd = usePageData({ user, selectedModule })
  const moduleHealth = useModuleHealth(pd.runHistory, sidebarModules)
  const activeCred = erpCredentials.find(c => c.id === activeCredId) ?? erpCredentials.find(c => c.isDefault) ?? null
  const tr = useTestRun({ user, selectedModule, apiModules, allTestCases: pd.allTestCases, visibilityData: pd.visibilityData, loadRunHistory: pd.loadRunHistory, loadDashboardStats: pd.loadDashboardStats, sidebarModules, loadBugReports: pd.loadBugReports, erpToken, erpTenantId, erpEmail: activeCred?.email, erpPassword: activeCred ? credPasswords.current[activeCred.id] : undefined })
  const d = useDialogs()
  const [tokenDialogOpen, setTokenDialogOpen] = useState(false)
  const onOpenCredentials = useCallback(() => setTokenDialogOpen(true), [])
  const onClearToken = useCallback(() => { setErpToken(''); setErpTenantId('') }, [])

  const loadCredentials = useCallback(async () => {
    if (!user) return
    setCredLoading(true)
    try {
      const res = await fetch('/api/credentials')
      if (res.ok) {
        const data = await res.json()
        const creds = data.credentials || []
        // store passwords in ref so they survive re-renders but aren't in state
        creds.forEach((c: any) => { if (c.password) credPasswords.current[c.id] = c.password })
        setErpCredentials(creds.map((c: any) => ({ ...c, password: undefined })))
        // auto-select default
        const def = creds.find((c: any) => c.isDefault)
        if (def) setActiveCredId(def.id)
      }
    } finally {
      setCredLoading(false)
    }
  }, [user])

  const saveCredential = useCallback(async () => {
    if (!credForm.name || !credForm.email || !credForm.password || !credForm.tenantUrl) return
    setCredSaving(true)
    try {
      const res = await fetch('/api/credentials', withCsrf({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credForm),
      }))
      if (res.ok) {
        const data = await res.json()
        credPasswords.current[data.credential.id] = credForm.password
        setErpCredentials(prev => {
          const updated = credForm.isDefault ? prev.map(c => ({ ...c, isDefault: false })) : prev
          return [...updated, data.credential]
        })
        if (credForm.isDefault || erpCredentials.length === 0) setActiveCredId(data.credential.id)
        setCredForm({ name: '', email: '', password: '', tenantUrl: 'https://rhythmerp.algorhythms.in', isDefault: false })
        setCredFormOpen(false)
        toast.success('Credential saved', { description: `"${credForm.name}" is ready to use for ERP connections.` })
      } else {
        toast.error('Save failed', { description: 'Could not save the credential. Please try again.' })
      }
    } catch {
      toast.error('Save failed', { description: 'A network error occurred. Please try again.' })
    } finally {
      setCredSaving(false)
    }
  }, [credForm, erpCredentials])

  const setDefaultCred = useCallback(async (id: string) => {
    const res = await fetch(`/api/credentials/${id}`, withCsrf({
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ isDefault: true }),
    }))
    if (res.ok) {
      setErpCredentials(prev => prev.map(c => ({ ...c, isDefault: c.id === id })))
      setActiveCredId(id)
    }
  }, [])

  const updateCredential = useCallback(async (id: string, data: { name?: string; email?: string; password?: string; tenantUrl?: string; isDefault?: boolean }) => {
    const res = await fetch(`/api/credentials/${id}`, withCsrf({
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }))
    if (res.ok) {
      if (data.password) credPasswords.current[id] = data.password
      if (data.isDefault) setErpCredentials(prev => prev.map(c => ({ ...c, isDefault: c.id === id, ...(c.id === id ? data : {}) })))
      else setErpCredentials(prev => prev.map(c => c.id === id ? { ...c, ...data } : c))
      toast.success('Credential updated', { description: 'Your changes have been saved.' })
    } else {
      toast.error('Update failed', { description: 'Could not update the credential. Please try again.' })
    }
  }, [])

  const deleteCred = useCallback(async (id: string) => {
    const res = await fetch(`/api/credentials/${id}`, withCsrf({ method: 'DELETE' }))
    if (res.ok) {
      setErpCredentials(prev => prev.filter(c => c.id !== id))
      if (activeCredId === id) setActiveCredId(null)
    }
  }, [activeCredId])

  // ─── Effects ─────────────────────────────────────────
  useEffect(() => {
    if (!user) return
    refreshNotifications()
    const interval = setInterval(refreshNotifications, 30000)
    return () => clearInterval(interval)
  }, [refreshNotifications, user])

  useEffect(() => { loadCredentials() }, [loadCredentials])

  useEffect(() => {
    if (!user) return
    // TODO Phase 5: migrate to useQuery
    fetchModules()
      .then((mods) => {
        setApiModules(mods)
        let sidebar = filterSidebarByAccess(buildSidebarModules(mods), user)
        fetch('/api/admin/modules').then(r => r.ok && r.json()).then(data => {
          const disabledNames = new Set((data?.modules || []).filter((m: Record<string, unknown>) => m.status === 'disabled').map((m: Record<string, unknown>) => m.name))
          if (disabledNames.size > 0) {
            const removeDisabled = (items: SidebarModule[]): SidebarModule[] => items.filter(m => {
              if (disabledNames.has(m.id.replace(/-/g, '_'))) return false
              if (m.children) m.children = removeDisabled(m.children)
              return true
            })
            setSidebarModules(removeDisabled(sidebar))
          }
        }).catch(() => {})
        setSidebarModules(sidebar)
        if (mods.length > 0) { syncModulesToDB(mods).catch(() => {}) }
      })
      .catch(async () => {
        try {
          const res = await fetch('/api/admin/modules')
          if (res.ok) {
            const data = await res.json()
            const dbMods = data.modules || []
            if (dbMods.length > 0) {
              const sidebarFromDb: SidebarModule[] = [{ id: 'dashboard', label: 'Dashboard' }]
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
            } else { setSidebarModules(filterSidebarByAccess(ALL_SIDEBAR_MODULES, user)) }
          } else { setSidebarModules(filterSidebarByAccess(ALL_SIDEBAR_MODULES, user)) }
        } catch { setSidebarModules(filterSidebarByAccess(ALL_SIDEBAR_MODULES, user)) }
      })
  }, [user])

  useEffect(() => {
    setSidebarModules(prev => prev.map(m =>
      m.id === 'my-tickets' ? { ...m, badge: pd.myTicketUnread > 0 ? `${pd.myTicketUnread}` : undefined, badgeType: pd.myTicketUnread > 0 ? 'warning' as const : 'none' as const } : m
    ))
  }, [pd.myTicketUnread])

  useEffect(() => {
    const unsubRunComplete = wsOn('run_complete', (data) => {
      toast.success(`Run complete: ${data.moduleName}`, { description: `${data.passed}/${data.total} passed (${data.rate}% pass rate)` })
      refreshNotifications()
      pd.loadRunHistory()
      if (selectedModule === 'dashboard') pd.loadDashboardStats()
    })
    const unsubBugReply = wsOn('bug_reply', (data) => {
      toast.info(`Reply on bug #${data.bugReportId}`, { description: `${data.replyAuthor}: ${data.message}` })
      refreshNotifications()
      pd.loadBugReports()
    })
    const unsubBugStatus = wsOn('bug_status_change', (data) => {
      toast.info(`Bug #${data.bugReportId} updated`, { description: `Status changed to ${data.newStatus} by ${data.changedBy}` })
      refreshNotifications()
      pd.loadBugReports()
    })
    const unsubNotif = wsOn('notification', (data) => {
      toast.info(data.title, { description: data.message })
      refreshNotifications()
    })
    return () => {
      unsubRunComplete(); unsubBugReply(); unsubBugStatus(); unsubNotif()
    }
  }, [wsOn, refreshNotifications, pd.loadRunHistory, pd.loadDashboardStats, pd.loadBugReports, selectedModule])

  // Auto-hide sidebar on Live Execution
  useEffect(() => {
    if (activeTab === 'live-execution') setSidebarOpen(false)
    else setSidebarOpen(true)
  }, [activeTab])

  // Auth check
  useEffect(() => {
    const init = async () => {
      try {
        if (typeof window !== 'undefined' && !sessionStorage.getItem('seed_called')) {
          sessionStorage.setItem('seed_called', '1')
          fetch('/api/auth/seed', withCsrf({ method: 'POST' })).catch(() => {})
        }
        const controller = new AbortController()
        const timeout = setTimeout(() => controller.abort(), 8000)
        try {
          const res = await fetch('/api/auth/me', { signal: controller.signal })
          clearTimeout(timeout)
          if (res.ok) {
            const data = await res.json()
            setUser(data.user)
            setSidebarModules(filterSidebarByAccess(ALL_SIDEBAR_MODULES, data.user))
          }
        } catch { clearTimeout(timeout) }
      } catch {} finally { setLoading(false) }
    }
    init()
  }, [])

  const handleLogin = useCallback((u: AuthUser) => {
    if (u.role === 'admin' && getPanelPreference() === 'admin') { window.location.href = '/admin'; return }
    setUser(u); setSidebarModules(filterSidebarByAccess(ALL_SIDEBAR_MODULES, u)); setSelectedModule('dashboard')
    setActiveTab('test-runner'); localStorage.removeItem('ai-nl-run')
    pd.loadVisibility()
  }, [pd.loadVisibility])

  const [logoutConfirmOpen, setLogoutConfirmOpen] = useState(false)
  const handleLogout = useCallback(async () => {
    await fetch('/api/auth/logout', withCsrf({ method: 'POST' })); setUser(null)
  }, [])

  const handleMarkAllRead = useCallback(async () => {
    await markAllNotificationsRead()
    await refreshNotifications()
  }, [refreshNotifications])

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
    const hash = selectedModule === 'dashboard' ? '' : activeTab === 'test-runner' ? selectedModule : selectedModule + '/' + activeTab
    window.location.hash = hash
  }, [selectedModule, activeTab, hashReady])

  const handleSelectModule = useCallback(async (id: string) => {
    setSelectedModule(id)
    const found = (() => {
      for (const mod of sidebarModules) {
        if (mod.id === id) return { label: mod.label, parent: null }
        for (const child of mod.children ?? []) { if (child.id === id) return { label: child.label, parent: mod.label }; for (const grand of child.children ?? []) { if (grand.id === id) return { label: grand.label, parent: child.label } } }
      }
      return { label: id, parent: null }
    })()
    setNavToast({ key: Date.now(), label: found.label, parent: found.parent })
    if (id === 'credentials') { loadCredentials(); return }
    setActiveTab('test-runner')
    tr.setTestChecks(new Set())
    const visData = await pd.loadVisibility() || pd.visibilityData
    const moduleKey = id.toLowerCase().replace(" ", "_").replace("-", "_")
    const overrides = visData?.overrides || {}
    const excludedSet = new Set(visData?.excludedTestNames || [])
    if (pd.allTestCases[moduleKey]) {
      const moduleData = pd.allTestCases[moduleKey]
      const filteredModuleTests = moduleData.tests.filter(t => !excludedSet.has(t.id))
      const mapTestCaseStatus = (s: string): TestSpecItem['status'] => { const upper = s.toUpperCase().trim(); if (upper === 'PASSED' || upper === 'PASS') return 'passed'; if (upper === 'BUG') return 'bug'; if (upper === 'TODO') return 'todo'; if (upper === 'FAILED' || upper === 'FAIL') return 'failed'; return 'not-run' }
      const getDisplayName = (t: { id: string; description: string }): string => overrides[t.id]?.displayName || t.description
      const specGroups: TestClassGroup[] = [{ className: moduleData.label, tests: filteredModuleTests.map((t) => ({ id: t.id, screenName: t.screenName, description: getDisplayName(t), status: mapTestCaseStatus(t.status), duration: '', steps: t.steps, expected: t.expected, actual: t.actual || '', bugDetails: t.status === 'BUG' ? t.actual : undefined, priority: undefined, date: t.date || undefined })) }]
      tr.setCurrentTestGroups(specGroups)
      const caseItems = filteredModuleTests.map((t) => ({ id: t.id, name: getDisplayName(t), description: getDisplayName(t), status: 'pending' as const, duration: '' }))
      const { items: apiItems } = getTestsForSidebarModule(id, apiModules, visData)
      tr.setTests([...caseItems, ...apiItems])
    } else {
      const { groups, items } = getTestsForSidebarModule(id, apiModules, visData)
      if (groups.length > 0) { tr.setCurrentTestGroups(groups); tr.setTests(items) }
      else { tr.setCurrentTestGroups([]); tr.setTests([]) }
    }
  }, [apiModules, pd.allTestCases, sidebarModules, pd.loadVisibility, pd.visibilityData])

  useEffect(() => {
    if (selectedModule === 'dashboard' || selectedModule === 'my-tickets' || selectedModule === 'deployment-check') return
    const moduleKey = selectedModule.toLowerCase().replace(" ", "_").replace("-", "_")
    const overrides = pd.visibilityData?.overrides || {}
    const excludedSet = new Set(pd.visibilityData?.excludedTestNames || [])
    if (pd.allTestCases[moduleKey]) {
      const moduleData = pd.allTestCases[moduleKey]
      const filteredModuleTests = moduleData.tests.filter(t => !excludedSet.has(t.id))
      const mapTestCaseStatus = (s: string): TestSpecItem['status'] => { const upper = s.toUpperCase().trim(); if (upper === 'PASSED' || upper === 'PASS') return 'passed'; if (upper === 'BUG') return 'bug'; if (upper === 'TODO') return 'todo'; if (upper === 'FAILED' || upper === 'FAIL') return 'failed'; return 'not-run' }
      const getDisplayName = (t: { id: string; description: string }): string => overrides[t.id]?.displayName || t.description
      const specGroups: TestClassGroup[] = [{ className: moduleData.label, tests: filteredModuleTests.map((t) => ({ id: t.id, screenName: t.screenName, description: getDisplayName(t), status: mapTestCaseStatus(t.status), duration: '', steps: t.steps, expected: t.expected, actual: t.actual || '', bugDetails: t.status === 'BUG' ? t.actual : undefined, priority: undefined, date: t.date || undefined })) }]
      tr.setCurrentTestGroups(specGroups)
      const caseItems = filteredModuleTests.map((t) => ({ id: t.id, name: getDisplayName(t), description: getDisplayName(t), status: 'pending' as const, duration: '' }))
      const { items: apiItems } = getTestsForSidebarModule(selectedModule, apiModules, pd.visibilityData)
      tr.setTests([...caseItems, ...apiItems])
    } else {
      const { groups, items } = getTestsForSidebarModule(selectedModule, apiModules, pd.visibilityData)
      if (groups.length > 0) { tr.setCurrentTestGroups(groups); tr.setTests(items) }
    }
  }, [pd.allTestCases, apiModules, selectedModule, pd.visibilityData])

  const handleGoHome = useCallback(() => { setSelectedModule('dashboard'); setActiveTab('test-runner'); setSidebarOpen(true) }, [])

  const handleRunModule = useCallback((moduleId: string) => {
    handleSelectModule(moduleId)
    setTimeout(() => { setActiveTab('test-runner') }, 100)
  }, [handleSelectModule])

  const toggleTestCheck = useCallback((id: string) => {
    tr.setTestChecks((prev) => { const next = new Set(prev); if (next.has(id)) next.delete(id); else next.add(id); return next })
  }, [])

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement
      const isInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable
      if (e.key === 'Escape') { if (d.quickSwitcherOpen) { d.setQuickSwitcherOpen(false); return } if (d.showShortcuts) { d.setShowShortcuts(false); return } if (d.notifDropdownOpen) { d.setNotifDropdownOpen(false); return } }
      if (isInput) return
      if (!(e.ctrlKey || e.metaKey)) return
      if (e.key === 'b') { e.preventDefault(); setSidebarOpen((prev) => !prev); return }
      if (e.key === 'k') { e.preventDefault(); d.setQuickSwitcherOpen((prev) => !prev); d.setQuickSearch(''); return }
      if (e.key === 'd') { e.preventDefault(); toggleDarkMode(); return }
      if (e.key === '/') { e.preventDefault(); d.setShowShortcuts((prev) => !prev); return }
      if (e.key === 'r' && selectedModule !== 'dashboard' && selectedModule !== 'my-tickets' && !tr.isRunning) { e.preventDefault(); const pc = tr.tests.filter((t) => t.status === 'pending').length; if (pc > 0) { tr.runTests(false); setActiveTab('live-execution') }; return }
      if (selectedModule !== 'dashboard' && selectedModule !== 'my-tickets') { const tabMap: Record<string, string> = { '1': 'test-runner', '2': 'live-execution', '3': 'results', '4': 'screenshots', '5': 'schedule' }; const tabId = tabMap[e.key]; if (tabId) { e.preventDefault(); setActiveTab(tabId) } }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [d.quickSwitcherOpen, d.showShortcuts, d.notifDropdownOpen, selectedModule, tr.isRunning, tr.tests, toggleDarkMode, tr.runTests])

  const passedCount = tr.tests.filter((t) => t.status === 'passed').length
  const failedCount = tr.tests.filter((t) => t.status === 'failed').length

  const getModulePath = useCallback(() => {
    for (const mod of sidebarModules) {
      if (mod.id === selectedModule) return { parent: null, name: mod.label, badge: mod.badge }
      if (mod.children) {
        for (const child of mod.children) {
          if (child.id === selectedModule) return { parent: mod.label, name: child.label, badge: child.badge }
          if (child.children) {
            for (const grand of child.children) {
              if (grand.id === selectedModule) return { parent: child.label, name: grand.label, badge: grand.badge }
            }
          }
        }
      }
    }
    return { parent: null, name: selectedModule, badge: undefined }
  }, [selectedModule])
  const modulePath = getModulePath()

  const handleViewResults = useCallback(() => { tr.setCompletionModalOpen(false); setActiveTab('results') }, [])
  const handleCompletionRerunFailed = useCallback(() => {
    tr.setCompletionModalOpen(false)
    const failedIds = tr.tests.filter((t) => t.status === 'failed').map((t) => t.id)
    if (failedIds.length > 0) { tr.rerunTestIds(failedIds); tr.runTests(true, failedIds); setActiveTab('live-execution') }
  }, [tr.tests, tr.rerunTestIds, tr.runTests])
  const handleNewRun = useCallback(() => { tr.setCompletionModalOpen(false); tr.setTests(initialTests); tr.setTestChecks(new Set()); setActiveTab('test-runner') }, [])
  const handleReportTest = useCallback((test: any) => { const error = tr.getTestError(test.id); d.setReportingTest({ id: test.id, name: test.name, error }); d.setReportDialogOpen(true) }, [tr.getTestError])
  const handleQuickReport = useCallback((testId: string, name: string, error: string) => {
    d.setReportingTest({ id: testId, name, error })
    d.setReportDialogOpen(true)
  }, [])

  const handleVerifyFix = useCallback((ticket: BugReport) => {
    setVerifyResult(null)
    setVerifyingTicket(ticket)
    // Find the test in the current module, or switch to its module
    const testInCurrentModule = tr.tests.find(t => t.id === ticket.testId || t.id.endsWith('::' + ticket.testId) || t.name === ticket.testDescription)
    if (testInCurrentModule) {
      tr.rerunTestIds([testInCurrentModule.id])
      tr.runTests(true, [testInCurrentModule.id])
      setActiveTab('live-execution')
    } else {
      // Test is in a different module — just run by ID directly if possible
      setVerifyingTicket(ticket)
      setActiveTab('live-execution')
    }
  }, [tr.tests, tr.rerunTestIds, tr.runTests])

  // After a verify-fix run completes, check if the watched test passed
  useEffect(() => {
    if (!verifyingTicket || tr.isRunning) return
    const test = tr.tests.find(t =>
      t.id === verifyingTicket.testId ||
      t.id.endsWith('::' + verifyingTicket.testId) ||
      t.name === verifyingTicket.testDescription
    )
    if (!test || test.status === 'pending') return
    const passed = test.status === 'passed'
    setVerifyResult({ ticketId: verifyingTicket.id, passed })
    if (passed) {
      updateBugReportStatus(verifyingTicket.id, 'closed').then(() => {
        addNotification({ type: 'status_change', title: 'Ticket closed', message: `"${verifyingTicket.testDescription}" verified and closed` }).catch(() => {})
      })
    }
    setVerifyingTicket(null)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tr.isRunning])

  if (loading) {
    return <LoadingCard />
  }

  if (!user) return <LoginPage onLogin={handleLogin} />

  const userInitials = user.name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)
  const isReadOnly = user?.role === 'viewer' || user?.role === 'client'
  const canRunTests = !isReadOnly
  const moduleTabs = user?.role === 'admin' ? null : getAllowedTabsForModule(user?.moduleAccess ?? [], selectedModule)
  const isBatchOnly = moduleTabs !== null && moduleTabs.length === 1 && moduleTabs[0] === 'batch'
  const tabs = [
    ...(canRunTests ? [{ id: 'test-runner',    label: 'Test Runner',    icon: FlaskConical }] : []),
    ...(!isBatchOnly && canRunTests ? [{ id: 'live-execution', label: 'Live Execution', icon: Monitor }] : []),
    ...(!isBatchOnly ? [{ id: 'results',       label: 'Results',        icon: BarChart2 }] : []),
    ...(!isBatchOnly ? [{ id: 'screenshots',   label: 'Screenshots',    icon: Camera }] : []),
    ...(!isBatchOnly && canRunTests ? [{ id: 'schedule',       label: 'Schedule',       icon: CalendarClock }] : []),
  ]

  return (
    <div key={themeVersion} className="h-screen flex flex-col bg-white dark:bg-gray-900 overflow-hidden" style={{ animation: 'panelFadeIn 0.3s ease-out' }}>
      <AppTour selectedModule={selectedModule} activeTab={activeTab} />
      {/* Keyboard Shortcuts Cheat Sheet */}
      <Dialog open={d.showShortcuts} onOpenChange={d.setShowShortcuts}>
        <DialogContent className="sm:max-w-[440px]">
          <DialogHeader><DialogTitle className="flex items-center gap-2"><Zap className="size-4 text-green-600" />Keyboard Shortcuts</DialogTitle><DialogDescription>Quick actions to speed up your workflow</DialogDescription></DialogHeader>
          <div className="grid gap-1.5 py-2">
            {[{ keys: 'Ctrl + B', desc: 'Toggle sidebar' }, { keys: 'Ctrl + K', desc: 'Quick module search' }, { keys: 'Ctrl + D', desc: 'Toggle dark mode' }, { keys: 'Ctrl + R', desc: 'Run all pending tests' }, { keys: 'Ctrl + 1', desc: 'Test Runner tab' }, { keys: 'Ctrl + 2', desc: 'Live Execution tab' }, { keys: 'Ctrl + 3', desc: 'Results tab' }, { keys: 'Ctrl + 4', desc: 'Screenshots tab' }, { keys: 'Ctrl + 5', desc: 'Schedule tab' }, { keys: 'Ctrl + /', desc: 'Show this cheat sheet' }, { keys: 'Escape', desc: 'Close dialog / panel' }].map((s) => (
              <div key={s.keys} className="flex items-center justify-between px-2 py-1.5 rounded-md hover:bg-gray-50 dark:hover:bg-gray-800/50"><span className="text-[13px] text-gray-600 dark:text-gray-400">{s.desc}</span><kbd className="px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-[11px] font-mono text-gray-700 dark:text-gray-300">{s.keys}</kbd></div>
            ))}
          </div>
          <DialogFooter><span className="text-[11px] text-gray-400">Press <kbd className="px-1 py-0.5 rounded bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-[10px] font-mono">Ctrl + /</kbd> to toggle</span></DialogFooter>
        </DialogContent>
      </Dialog>
      {/* HEADER */}
      <header className="h-[52px] bg-white dark:bg-gray-900 border-b border-gray-100 dark:border-gray-800 flex items-center px-3 shrink-0 z-10">
        {/* Left */}
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(!sidebarOpen)} data-tour="sidebar-toggle" className="size-7 cursor-pointer shrink-0 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 rounded" title="Toggle sidebar (Ctrl+B)">
            <Menu className="size-4" />
          </Button>
          <Image src="/agdi-logo-new.webp" alt="AgDi Automation" width={60} height={24} className="object-contain shrink-0" />
          {selectedModule !== 'dashboard' && (() => {
            let modLabel = ''
            for (const m of sidebarModules) {
              if (m.id === selectedModule) { modLabel = m.label; break }
              for (const c of m.children ?? []) {
                if (c.id === selectedModule) { modLabel = c.label; break }
                for (const g of c.children ?? []) { if (g.id === selectedModule) { modLabel = g.label; break } }
              }
            }
            const TAB_LABELS: Record<string, string> = { 'test-runner': 'UI Tests', 'live-execution': 'Live Execution', 'results': 'Results', 'screenshots': 'Screenshots', 'schedule': 'Schedule', 'batch-create': 'Batch Create', 'concurrency': 'Concurrency', 'api-tests': 'API Tests' }
            return (
              <div className="hidden md:flex items-center gap-1.5 min-w-0">
                <ChevronRight className="size-3.5 text-gray-300 dark:text-gray-600 shrink-0" />
                <span className="text-[12px] text-gray-400 dark:text-gray-500 truncate max-w-[160px]">{modLabel || selectedModule}</span>
                <ChevronRight className="size-3 text-gray-300 dark:text-gray-600 shrink-0" />
                <span className="text-[12px] font-semibold text-gray-700 dark:text-gray-200 truncate">{TAB_LABELS[activeTab] ?? activeTab}</span>
              </div>
            )
          })()}
        </div>
        {/* Centre search */}
        <button onClick={() => d.setQuickSwitcherOpen(true)} className="hidden md:flex items-center gap-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-3 h-8 w-56 text-[12px] text-gray-400 dark:text-gray-500 hover:border-gray-300 dark:hover:border-gray-600 transition-colors cursor-pointer shrink-0">
          <Search className="size-3.5 shrink-0" />
          <span className="flex-1 text-left">Search modules…</span>
          <kbd className="text-[10px] bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400 px-1 rounded">⌘K</kbd>
        </button>
        {/* Right */}
        <div className="flex items-center gap-1 ml-3">
          <div title={wsConnected ? 'Real-time connected' : 'Real-time disconnected — using polling'} className="flex items-center px-1">
            <div className={`w-1.5 h-1.5 rounded-full ${wsConnected ? 'bg-green-400' : 'bg-amber-400 animate-pulse'}`} />
          </div>
          <Button variant="ghost" size="icon" onClick={toggleDarkMode} data-tour="dark-mode" className="size-7 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer rounded" title={darkMode ? 'Light mode' : 'Dark mode'}>{darkMode ? <Sun className="size-3.5" /> : <Moon className="size-3.5" />}</Button>
          <Button variant="ghost" size="icon" onClick={() => d.setShowShortcuts(true)} data-tour="keyboard-shortcuts" className="size-7 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer rounded" title="Keyboard shortcuts"><Zap className="size-3.5" /></Button>
          <div className="relative" data-tour="notifications">
            <Button
              variant="ghost" size="icon"
              onClick={() => { d.setNotifDropdownOpen((prev) => !prev) }}
              className="size-7 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer relative rounded"
              title="Notifications"
            >
              <Bell className="size-3.5" />
              {unreadCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 w-[15px] h-[15px] bg-[#3F51B5] text-white text-[8px] font-bold rounded-full flex items-center justify-center">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </Button>
            {d.notifDropdownOpen && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => d.setNotifDropdownOpen(false)} />
                <div className="absolute right-0 top-10 w-[380px] bg-white dark:bg-[#1e2132] rounded-xl shadow-2xl border border-gray-200 dark:border-gray-600/50 z-50 overflow-hidden flex flex-col" style={{ maxHeight: '480px' }}>
                  {/* Header */}
                  <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-700/60 flex items-center justify-between bg-gradient-to-r from-[#3F51B5]/[0.06] to-[#3F51B5]/[0.02] shrink-0">
                    <div className="flex items-center gap-2">
                      <Bell className="size-3.5 text-[#3F51B5]" />
                      <span className="text-[13px] font-semibold text-[#333333] dark:text-gray-100">Notifications</span>
                      {unreadCount > 0 && (
                        <span className="bg-[#3F51B5] text-white text-[10px] font-semibold px-1.5 py-0.5 rounded-full leading-none">{unreadCount} new</span>
                      )}
                    </div>
                    {unreadCount > 0 && (
                      <button onClick={handleMarkAllRead} className="text-[11px] text-[#3F51B5] hover:text-[#3949AB] dark:text-[#7986CB] dark:hover:text-[#9FA8DA] cursor-pointer font-medium transition-colors">
                        Mark all read
                      </button>
                    )}
                  </div>
                  {/* Desktop notifications toggle */}
                  <div className="px-4 py-2.5 border-b border-gray-100 dark:border-gray-700/60 flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2 min-w-0">
                      <Monitor className="size-3.5 text-[#3F51B5] shrink-0" />
                      <div className="min-w-0">
                        <p className="text-[12px] font-medium text-[#333333] dark:text-gray-100 leading-tight">Desktop notifications</p>
                        <p className="text-[10px] text-gray-400 dark:text-gray-500 leading-tight truncate">
                          {desktopNotifEnabled
                            ? (desktopNotifGranted ? 'Ping your PC when tasks complete' : 'Pending permission')
                            : 'Get a PC notification when tasks complete'}
                        </p>
                      </div>
                    </div>
                    <Switch
                      checked={desktopNotifEnabled}
                      onCheckedChange={handleDesktopNotifToggle}
                      className="shrink-0 cursor-pointer"
                      data-tour="desktop-notif-toggle"
                    />
                  </div>
                  {/* List */}
                  <div className="overflow-y-auto flex-1">
                    {notifications.length === 0 ? (
                      <div className="py-12 px-6 text-center">
                        <div className="w-10 h-10 rounded-full bg-gray-100 dark:bg-gray-700/50 flex items-center justify-center mx-auto mb-3">
                          <Bell className="size-5 text-gray-300 dark:text-gray-500" />
                        </div>
                        <p className="text-[13px] font-medium text-gray-500 dark:text-gray-400">All caught up</p>
                        <p className="text-[11px] text-gray-400 dark:text-gray-500 mt-1">Notifications appear here when tests complete or bugs are updated</p>
                      </div>
                    ) : (
                      notifications.slice(0, 25).map((n) => {
                        const typeMap: Record<string, { icon: React.ReactNode; accent: string; bg: string }> = {
                          run_complete: { icon: <CheckCircle2 className="size-3.5" />, accent: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-50 dark:bg-emerald-900/20' },
                          status_change: { icon: <RotateCcw className="size-3.5" />, accent: 'text-[#3F51B5] dark:text-[#7986CB]', bg: 'bg-[#3F51B5]/10 dark:bg-[#3F51B5]/15' },
                          reply: { icon: <MessageSquare className="size-3.5" />, accent: 'text-violet-600 dark:text-violet-400', bg: 'bg-violet-50 dark:bg-violet-900/20' },
                          schedule: { icon: <CalendarClock className="size-3.5" />, accent: 'text-amber-600 dark:text-amber-400', bg: 'bg-amber-50 dark:bg-amber-900/20' },
                        }
                        const style = typeMap[n.type] ?? { icon: <Bell className="size-3.5" />, accent: 'text-gray-500 dark:text-gray-400', bg: 'bg-gray-100 dark:bg-gray-700/50' }
                        return (
                          <div key={n.id} className={`relative px-4 py-3 border-b border-gray-50 dark:border-gray-700/30 flex gap-3 items-start hover:bg-gray-50 dark:hover:bg-gray-700/20 transition-colors cursor-default ${!n.read ? 'bg-[#3F51B5]/[0.04] dark:bg-[#3F51B5]/[0.08]' : ''}`}>
                            {!n.read && <span className="absolute left-1.5 top-1/2 -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-[#3F51B5]" />}
                            <div className={`shrink-0 w-7 h-7 rounded-full flex items-center justify-center ${style.accent} ${style.bg}`}>
                              {style.icon}
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-[12px] font-semibold text-[#333333] dark:text-gray-100 leading-snug">{n.title}</p>
                              <p className="text-[11px] text-[#666666] dark:text-gray-400 mt-0.5 leading-snug line-clamp-2">{n.message}</p>
                              <p className="text-[10px] text-[#999] dark:text-gray-500 mt-1.5">
                                {new Date(n.createdAt).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
                              </p>
                            </div>
                          </div>
                        )
                      })
                    )}
                  </div>
                  {/* Footer */}
                  {notifications.length > 0 && (
                    <div className="px-4 py-2.5 border-t border-gray-100 dark:border-gray-700/60 bg-gray-50/60 dark:bg-gray-800/40 shrink-0 flex items-center justify-between">
                      <span className="text-[11px] text-gray-400 dark:text-gray-500">{notifications.length} total</span>
                      <button onClick={() => d.setNotifDropdownOpen(false)} className="text-[11px] text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 cursor-pointer transition-colors">Close</button>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
          {(user.role === 'admin' || user.role === 'qa_lead') && <>
            <Link href="/admin" className="flex items-center gap-1.5 px-2 h-7 text-[11px] font-medium text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors" title="Admin Panel"><Shield className="size-3.5" /><span className="hidden sm:inline">Admin</span></Link>
            <RestartBackendButton />
          </>}
          <Separator orientation="vertical" className="h-4 mx-1" />
          <div className="flex items-center gap-1.5" data-tour="user-menu">
            <button onClick={() => d.setProfileDialogOpen(true)} className="flex items-center gap-2 px-1.5 py-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors cursor-pointer">
              <Avatar className="size-6"><AvatarFallback className="bg-[#3F51B5] text-white text-[10px] font-bold">{userInitials}</AvatarFallback></Avatar>
              <div className="hidden sm:flex flex-col leading-none">
                <span className="text-[12px] text-gray-700 dark:text-gray-200 font-medium max-w-[100px] truncate">{user.name}</span>
                <span className="text-[10px] text-gray-400 dark:text-gray-500">{user.role}</span>
              </div>
            </button>
            <Button variant="ghost" size="icon" onClick={() => setLogoutConfirmOpen(true)} data-tour="logout-btn" className="size-7 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 cursor-pointer rounded" title="Sign out"><LogOut className="size-3.5" /></Button>
          </div>
        </div>
      </header>
      {/* BODY */}
      <div className="flex flex-1 overflow-hidden">
        <div className="shrink-0 overflow-hidden h-full" style={{ width: sidebarOpen ? sidebarWidth : 0 }}>
          <aside className="flex flex-col h-full font-['Poppins'] bg-gradient-to-b from-[#F7FBF8] via-[#EAF5EC] to-[#D6EDDC] dark:from-[#13151d] dark:via-[#13151d] dark:to-[#111318] shadow-[1px_0px_0px_#D4E3D9] dark:shadow-[1px_0px_0px_#1e2030]" style={{ width: sidebarWidth }}>
            <ScrollArea className="flex-1 min-h-0" data-tour="sidebar-modules">
              <div className="py-2 px-2">
                {sidebarModules.map((mod) => (<SidebarModuleItem key={mod.id} module={mod} activeId={selectedModule} onSelect={handleSelectModule} expandedIds={expandedIds} toggleExpand={toggleExpand} justExpandedId={justExpandedId} />))}
                {(user.role === 'admin' || user.role === 'qa_lead' || (user.moduleAccess ?? []).includes('concurrency-testing')) && (
                <button
                  onClick={() => { setActiveTab('concurrency'); setSelectedModule('dashboard') }}
                  className={`w-full flex items-center text-[14px] transition-all duration-200 cursor-pointer text-left font-['Poppins'] px-[15px] py-[7px] rounded-[5px] ${
                    activeTab === 'concurrency'
                      ? 'bg-gradient-to-r from-[#DFF3E3] via-[#C8E6C9] to-[#B7E4C7] dark:bg-[#1B4332]/25 text-[#1B4332] dark:text-green-300 font-semibold shadow-[rgba(34,197,94,0.25)_2px_0px_4px_inset,rgba(34,197,94,0.15)_0px_2px_6px]'
                      : 'text-[#545454] dark:text-gray-300 font-medium hover:text-[#6777EF] dark:hover:text-indigo-400 hover:bg-[rgba(82,183,136,0.08)] hover:shadow-[rgba(82,183,136,0.5)_2px_0px_inset]'
                  }`}
                >
                  <Zap className="size-[18px] shrink-0 mr-[10px] text-[#6b7280]" />
                  <span className="truncate flex-1">Concurrency Testing</span>
                </button>
                )}
              </div>
            </ScrollArea>
            <div className="relative shrink-0 overflow-hidden" style={{ height: 99 }}><Image src="/agri2.png" alt="" fill className="object-cover" sizes="280px" style={{ objectPosition: 'center 25%' }} /></div>
          </aside>
        </div>
        {sidebarOpen && <div onMouseDown={handleResizeStart} className="w-1 cursor-col-resize bg-transparent hover:bg-[#3F51B5]/40 active:bg-[#3F51B5]/60 transition-colors shrink-0 relative z-10" />}
        <main className="flex-1 flex flex-col overflow-hidden bg-[#F1F2F7] dark:bg-gray-900 relative p-3">
          {navToast && <NavToast key={navToast.key} label={navToast.label} parent={navToast.parent} />}
          {/* White card wrapper — scrolls internally, browser never moves */}
          <div className="flex flex-col flex-1 min-h-0 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm">
          {!sidebarOpen && selectedModule !== 'dashboard' && (
            <div className="flex items-center gap-1.5 px-4 py-2 border-b border-gray-200 dark:border-gray-600/40 bg-white dark:bg-gray-900 shrink-0">
              <button onClick={handleGoHome} className="text-[12px] text-[#3F51B5] hover:text-[#3949AB] dark:text-[#7986CB] font-medium cursor-pointer transition-colors hover:underline">Dashboard</button>
              {modulePath.parent && <><ChevronRight className="size-3 text-gray-400 dark:text-gray-500" /><span className="text-[12px] text-gray-500 dark:text-gray-400">{modulePath.parent}</span></>}
              <ChevronRight className="size-3 text-gray-400 dark:text-gray-500" />
              <span className="text-[12px] text-gray-800 dark:text-gray-100 font-medium">{modulePath.name}</span>
              {modulePath.badge && <span className="text-[11px] text-orange-600 dark:text-orange-400 ml-1">{modulePath.badge}</span>}
              <div className="flex-1" /><span className="text-[11px] text-gray-400 dark:text-gray-500"><kbd className="px-1 py-0.5 rounded bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-[10px] font-mono">Ctrl+B</kbd> to toggle</span>
            </div>
          )}
          {selectedModule === 'dashboard' && (user?.role === 'admin' ? (
            <DashboardRenderer
              dashboardStats={pd.dashboardStats}
              dashboardLoading={pd.dashboardLoading}
              runHistory={pd.runHistory}
              moduleHealth={moduleHealth}
              handleSelectModule={handleSelectModule}
              handleRunModule={handleRunModule}
              loadDashboardStats={pd.loadDashboardStats}
            />
          ) : (
            <PersonalDashboardRenderer
              user={user}
              dashboardStats={pd.dashboardStats}
              runHistory={pd.runHistory}
              selectedModule={selectedModule}
              sidebarModules={sidebarModules}
              handleSelectModule={handleSelectModule}
              setActiveTab={setActiveTab}
            />
          ))}
          {selectedModule === 'my-tickets' && user && <MyTicketsTab userEmail={user.email} userName={user.name} onVerifyFix={handleVerifyFix} verifyingTicketId={verifyingTicket?.id} verifyResult={verifyResult} />}
          {selectedModule === 'deployment-check' && (
            <DeploymentCheckTab erpToken={erpToken} erpTenantId={erpTenantId} credentials={erpCredentials} activeCredId={activeCredId} getPassword={(id) => credPasswords.current[id] || ''} />
          )}
          {(selectedModule === 'full-purchase-flow' || selectedModule === 'full-purchase-flow-jv') && (
            <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
              <div className="border-b border-gray-300 dark:border-gray-600 bg-gray-50/50 dark:bg-gray-800/30 shrink-0">
                <div className="flex items-center h-10 px-4 gap-0">
                  <div className="flex items-center gap-1.5 px-4 h-full text-[12px] font-medium border-b-2 border-[#3F51B5] text-[#3F51B5] dark:text-[#7986CB] bg-white dark:bg-gray-900">
                    <Package className="size-4 text-[#3F51B5]" />
                    <h3 className="text-[14px] font-semibold text-gray-800 dark:text-gray-100">
                      {selectedModule === 'full-purchase-flow-jv' ? 'Purchase Chain + JV Check' : 'Purchase Chain'}
                    </h3>
                  </div>
                  <button
                    type="button"
                    onClick={startAppTour}
                    data-tour="pc-help"
                    title="Guide: how this screen works"
                    className="ml-2 flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold text-[#3F51B5] hover:text-[#3949AB] hover:bg-[#3F51B5]/10 dark:hover:bg-[#3F51B5]/20 cursor-pointer"
                  >
                    <HelpCircle className="size-3.5" />
                    Need help?
                  </button>
                  <div className="flex-1" />
                  <span className="text-[12px] text-gray-400 dark:text-gray-500">Module: <span className="text-gray-600 dark:text-gray-300 font-medium">
                    {selectedModule === 'full-purchase-flow-jv' ? 'Full Purchase Flow + JV Check' : 'Full Purchase Flow'}
                  </span></span>
                </div>
              </div>
              <div className="flex-1 overflow-hidden min-h-0 p-4">
                <PurchaseChainSection
                  erpToken={erpToken}
                  erpTenantId={erpTenantId || '681'}
                  onNeedsToken={() => setTokenDialogOpen(true)}
                  onClearToken={onClearToken}
                  userId={user?.id}
                  showJVCheck={selectedModule === 'full-purchase-flow-jv'}
                />
              </div>
            </div>
          )}
          {selectedModule === 'credentials' && (
            <CredentialsScreen
              erpCredentials={erpCredentials}
              activeCredId={activeCredId}
              setActiveCredId={setActiveCredId}
              credLoading={credLoading}
              credFormOpen={credFormOpen}
              setCredFormOpen={setCredFormOpen}
              credForm={credForm}
              setCredForm={setCredForm}
              credSaving={credSaving}
              saveCredential={saveCredential}
              setDefaultCred={setDefaultCred}
              deleteCred={deleteCred}
              updateCredential={updateCredential}
              getPassword={(id) => credPasswords.current[id] || ''}
              erpToken={erpToken}
              setErpToken={setErpToken}
              erpTenantId={erpTenantId}
              setErpTenantId={setErpTenantId}
            />
          )}
          {activeTab === 'concurrency' && (
            <ConcurrencyTab modules={sidebarModules} />
          )}
          {selectedModule !== 'dashboard' && selectedModule !== 'my-tickets' && selectedModule !== 'deployment-check' && selectedModule !== 'full-purchase-flow' && selectedModule !== 'full-purchase-flow-jv' && selectedModule !== 'credentials' && activeTab !== 'concurrency' && (
            <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
              <div className="border-b border-gray-300 dark:border-gray-500/70 bg-gray-50/50 dark:bg-gray-800/30 shrink-0" data-tour="tab-bar">
                <div className="flex items-center h-10 px-4 gap-0">
                  {tabs.map((tab) => { const Icon = tab.icon; return (<button key={tab.id} onClick={() => setActiveTab(tab.id)} className={`flex items-center gap-1.5 px-4 h-full text-[12px] font-medium transition-colors border-b-2 cursor-pointer ${activeTab === tab.id ? 'border-[#3F51B5] text-[#3F51B5] dark:text-[#7986CB] bg-white dark:bg-gray-900' : 'border-transparent text-[#888888] dark:text-gray-400 hover:text-[#333333] dark:hover:text-gray-200 hover:bg-gray-100/50 dark:hover:bg-gray-800/30'}`}><Icon className="size-3.5 shrink-0" />{tab.label}</button>) })}
                  <div className="flex-1" />
                  <span className="text-[12px] text-gray-400 dark:text-gray-500">Module: <span className="text-gray-600 dark:text-gray-300 font-medium">{modulePath.name}</span>{modulePath.badge && <span className="ml-2 text-orange-600 dark:text-orange-400">{modulePath.badge}</span>}</span>
                </div>
              </div>
              <div className="flex-1 overflow-hidden min-h-0">
                {(activeTab === 'test-runner' || activeTab === 'api-tests' || activeTab === 'batch-create') && <div data-tour="test-runner" className="h-full"><TestRunnerTab tests={tr.tests} testChecks={tr.testChecks} toggleTestCheck={toggleTestCheck} isRunning={tr.isRunning} totalFailed={failedCount} onRun={(selectedOnly, testType) => { tr.runTests(selectedOnly, undefined, testType); setActiveTab('live-execution') }} onRunByPriority={tr.runByPriority} onRerunFailed={() => { const failedIds = tr.tests.filter((t) => t.status === 'failed').map((t) => t.id); if (failedIds.length > 0) { tr.rerunTestIds(failedIds); tr.runTests(true, failedIds); setActiveTab('live-execution') } }} erpToken={erpToken} erpTenantId={erpTenantId} currentModuleId={selectedModule} onOpenCredentials={onOpenCredentials} onClearToken={onClearToken} showRawNames={showRawNames} credentials={erpCredentials} activeCredId={activeCredId} onSelectCred={(id) => setActiveCredId(id)} onOpenCredentialsScreen={() => setSelectedModule('credentials')} allowedTabs={user?.role === 'admin' ? null : getAllowedTabsForModule(user?.moduleAccess ?? [], selectedModule)} onSubTabChange={(t) => setActiveTab(t === 'ui' ? 'test-runner' : t === 'api' ? 'api-tests' : 'batch-create')} initialSubTab={activeTab === 'api-tests' ? 'api' : activeTab === 'batch-create' ? 'batch' : 'ui'} /></div>}
                {activeTab === 'live-execution' && <div data-tour="live-execution" className="h-full"><LiveExecutionTab tests={tr.tests} testGroups={tr.currentTestGroups} isRunning={tr.isRunning} runningProgress={tr.runningProgress} consoleLogs={tr.consoleLogs} showRawNames={showRawNames} onStop={tr.handleStopRun} onBack={() => setActiveTab('test-runner')} onRerunFailed={() => { const failedIds = tr.tests.filter((t) => t.status === 'failed').map((t) => t.id); if (failedIds.length > 0) { tr.rerunTestIds(failedIds); tr.runTests(true, failedIds) } }} onScreenshotCaptured={(entry) => { tr.setScreenshotEntries((prev) => { if (prev.length >= 50) return [entry, ...prev.slice(0, 49)]; return [entry, ...prev] }) }} /></div>}
                {activeTab === 'results' && <div data-tour="results" className="h-full"><ResultsTab tests={tr.tests} passedCount={passedCount} failedCount={failedCount} totalCount={tr.tests.length} runHistory={pd.runHistory} bugReportsList={pd.bugReportsList} onRunDetail={(run) => { d.setSelectedRunForDetail(run); d.setRunDetailDialogOpen(true) }} onCompareRuns={() => d.setRunComparisonOpen(true)} onViewAllRuns={() => d.setRunHistoryOpen(true)} onReportTest={handleQuickReport} testGroups={tr.currentTestGroups} moduleHealth={moduleHealth} moduleName={modulePath.name} currentModuleId={selectedModule} isRunning={tr.isRunning} onRerunFailed={() => { const failedIds = tr.tests.filter((t) => t.status === 'failed').map((t) => t.id); if (failedIds.length > 0) { tr.rerunTestIds(failedIds); tr.runTests(true, failedIds); setActiveTab('live-execution') } }} /></div>}
                {activeTab === 'screenshots' && (
                  <div data-tour="screenshots" className="flex flex-col h-full min-h-0">
                    <div className="p-4 shrink-0">
                      <div className="flex items-center justify-between mb-3">
                        <div><h3 className="text-[14px] font-semibold text-gray-800 dark:text-gray-100">Screenshot Gallery</h3><p className="text-[12px] text-gray-500 dark:text-gray-400 mt-0.5">Screenshots captured during test execution</p></div>
                        <div className="flex items-center gap-2">
                          {tr.screenshotEntries.length >= 2 && <Button variant="outline" size="sm" onClick={() => { d.setCompareScreenshots([tr.screenshotEntries[0] || null, tr.screenshotEntries[1] || null]); d.setScreenshotCompareOpen(true) }} className="h-7 text-[12px] gap-1.5 cursor-pointer"><GitCompare className="size-3" />Compare</Button>}
                          <Button variant="outline" size="sm" onClick={async () => { try { const data = await fetchScreenshot(); if (data.active && data.screenshot) { const newEntry: ScreenshotEntry = { id: `ss-${Date.now()}`, src: `data:image/png;base64,${data.screenshot}`, testName: 'Live Capture', timestamp: new Date().toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit' }), status: 'running' }; tr.setScreenshotEntries((prev) => [newEntry, ...prev]); toast.success('Screenshot captured') } else { toast.info('No active screenshot available') } } catch { toast.error('Failed to capture screenshot') } }} className="h-7 text-[12px] gap-1.5 cursor-pointer"><Monitor className="size-3" />Capture Now</Button>
                        </div>
                      </div>
                    </div>
                    <div className="flex-1 overflow-auto px-4 pb-4"><ScreenshotGallery screenshots={tr.screenshotEntries} onRefresh={async () => { try { const data = await fetchScreenshot(); if (data.active && data.screenshot) { const newEntry: ScreenshotEntry = { id: `ss-${Date.now()}`, src: `data:image/png;base64,${data.screenshot}`, testName: 'Live Capture', timestamp: new Date().toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit' }), status: 'running' }; tr.setScreenshotEntries((prev) => [newEntry, ...prev]) } } catch {} }} /></div>
                  </div>
                )}
                {activeTab === 'schedule' && user && <div data-tour="schedule-runs" className="h-full"><ScheduleRunsTab userName={user.name} sidebarModules={sidebarModules} /></div>}
              </div>
            </div>
          )}
          </div>{/* end white card */}
        </main>
      </div>
      {/* Console Popup */}
      {consoleOpen && (
        <div className="fixed inset-0 z-[9998] flex items-end justify-center pb-6 px-6 pointer-events-none">
          <div className="absolute inset-0 bg-black/40 pointer-events-auto" onClick={() => setConsoleOpen(false)} />
          <div className="relative pointer-events-auto w-full max-w-4xl h-[60vh] min-h-[340px] flex flex-col rounded-2xl overflow-hidden border border-white/[0.1] shadow-2xl shadow-black/60" style={{ background: '#0d1117' }}>
            {/* Header */}
            <div className="flex items-center gap-3 px-4 py-2.5 border-b border-white/[0.07] shrink-0" style={{ background: '#10151c' }}>
              <Terminal className="size-4 text-[#7986CB] shrink-0" />
              <span className="text-[13px] font-semibold text-slate-200">Console</span>
              <span className="text-[11px] font-mono tabular-nums text-slate-600 bg-slate-800/80 px-1.5 py-0.5 rounded">{tr.consoleLogs.length} lines</span>
              <span className="text-[11px] font-mono text-slate-700 bg-slate-800/60 border border-white/[0.04] px-2 py-0.5 rounded-md ml-1">pytest</span>
              <div className="flex-1" />
              <button
                onClick={() => {
                  navigator.clipboard.writeText(tr.consoleLogs.join('\n')).then(() => {
                    setConsoleCopied(true)
                    setTimeout(() => setConsoleCopied(false), 2000)
                  })
                }}
                title="Copy all lines"
                className={`p-1.5 rounded-lg transition-colors cursor-pointer ${consoleCopied ? 'text-emerald-400 bg-emerald-500/10' : 'text-slate-500 hover:text-slate-200 hover:bg-white/[0.06]'}`}
              >
                {consoleCopied ? <Check className="size-4" /> : <Copy className="size-4" />}
              </button>
              <button onClick={() => setConsoleOpen(false)} className="p-1.5 rounded-lg text-slate-500 hover:text-slate-200 hover:bg-white/[0.06] transition-colors cursor-pointer ml-1"><X className="size-4" /></button>
            </div>
            {/* Output */}
            <div className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden font-mono text-[12.5px] leading-[1.7]" style={{ background: '#090c11' }}>
              {tr.consoleLogs.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full gap-3">
                  <Terminal className="size-8 text-slate-800" />
                  <p className="text-slate-600">No output yet — waiting for tests to run…</p>
                </div>
              ) : (
                <table className="w-full border-collapse">
                  <tbody>
                    {tr.consoleLogs.map((log, i) => {
                      const isPassed = /PASSED|\bpassed\b/.test(log)
                      const isFailed = /FAILED|ERROR|\bfailed\b/.test(log)
                      const isAction = !isPassed && !isFailed && /Navigating|Clicking|Filling|Selecting|Setting/.test(log)
                      return (
                        <tr key={i} className={`group border-b border-white/[0.02] ${isFailed ? 'bg-red-950/25 hover:bg-red-950/35' : isPassed ? 'bg-emerald-950/15 hover:bg-emerald-950/25' : 'hover:bg-white/[0.025]'}`}>
                          <td className="select-none text-right px-3 py-0 w-10 text-[11px] text-slate-700 group-hover:text-slate-500 tabular-nums align-top pt-[2px]">{i + 1}</td>
                          <td className={`px-3 py-0 select-text whitespace-pre-wrap break-all ${isPassed ? 'text-emerald-400' : isFailed ? 'text-red-300' : isAction ? 'text-amber-200' : 'text-slate-200'}`}>
                            {isPassed && <span className="text-emerald-500 mr-2 select-none">✓</span>}
                            {isFailed && <span className="text-red-400 mr-2 select-none">✗</span>}
                            {log}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      )}
      {activeTab === 'live-execution' && !tr.isRunning && passedCount + failedCount > 0 && (
        <button onClick={() => setActiveTab('test-runner')} className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 bg-[#3F51B5] hover:bg-[#3949AB] text-white transition-all duration-200 rounded-xl px-5 py-2.5 flex items-center gap-2 cursor-pointer hover:-translate-y-0.5"><RotateCcw className="size-4" /><span className="text-[13px] font-medium">New Test Run</span></button>
      )}
      {/* Quick Switcher */}
      {d.quickSwitcherOpen && (
        <>
          <div className="fixed inset-0 z-[100] bg-black/40 backdrop-blur-sm" onClick={() => d.setQuickSwitcherOpen(false)} />
          <div className="fixed top-[20%] left-1/2 -translate-x-1/2 z-[101] w-full max-w-lg">
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-300 dark:border-gray-500/70 overflow-hidden">
              <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-200 dark:border-gray-600/40">
                <Search className="size-4 text-gray-400 shrink-0" />
                <input type="text" value={d.quickSearch} onChange={(e) => d.setQuickSearch(e.target.value)} placeholder="Search modules... (e.g. tax, uom, crop)" className="flex-1 text-[14px] text-gray-800 dark:text-gray-100 placeholder:text-gray-400 outline-none bg-transparent" autoFocus onKeyDown={(e) => { if (e.key === 'Escape') d.setQuickSwitcherOpen(false) }} />
                <kbd className="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 text-[10px] font-mono text-gray-400 shrink-0">ESC</kbd>
              </div>
              <div className="max-h-[300px] overflow-auto py-2">{(() => {
                const q = d.quickSearch.toLowerCase()
                const flatModules: { id: string; label: string; parent?: string; badge?: string }[] = []
                for (const mod of sidebarModules) {
                  if (mod.children) {
                    for (const child of mod.children) {
                      flatModules.push({ id: child.id, label: child.label, parent: mod.label, badge: child.badge })
                    }
                  } else {
                    flatModules.push({ id: mod.id, label: mod.label, badge: mod.badge })
                  }
                }
                const filtered = q
                  ? flatModules.filter((m) =>
                      m.label.toLowerCase().includes(q) ||
                      m.id.toLowerCase().includes(q) ||
                      (m.parent && m.parent.toLowerCase().includes(q))
                    )
                  : flatModules
                if (filtered.length === 0) return <div className="px-4 py-6 text-center text-[13px] text-gray-400 dark:text-gray-500">No modules found</div>
                return filtered.map((mod) => {
                  const isActive = mod.id === selectedModule
                  return (
                    <button key={mod.id} onClick={() => { setSelectedModule(mod.id); setActiveTab('test-runner'); d.setQuickSwitcherOpen(false) }}
                      className={`w-full flex items-center gap-3 px-4 py-2 hover:bg-[#3F51B5]/[0.04] dark:hover:bg-[#3F51B5]/10 transition-colors text-left ${isActive ? 'bg-[#3F51B5]/[0.06] dark:bg-[#3F51B5]/15' : ''}`}
                    >
                      <div className={`w-2 h-2 rounded-full shrink-0 ${isActive ? 'bg-[#3F51B5]' : 'bg-gray-300 dark:bg-gray-600'}`} />
                      <div className="flex-1 min-w-0">
                        <div className="text-[13px] text-gray-800 dark:text-gray-200 font-medium truncate">{mod.label}</div>
                        {mod.parent && <div className="text-[11px] text-gray-400 dark:text-gray-500 truncate">{mod.parent}</div>}
                      </div>
                      {mod.badge && <Badge className="text-[10px] h-4 px-1.5 bg-[#3F51B5]/10 text-[#3F51B5] dark:bg-[#3F51B5]/20 dark:text-[#7986CB] border-0 shrink-0">{mod.badge}</Badge>}
                    </button>
                  )
                })
              })()}</div>
            </div>
          </div>
        </>
      )}
      <CompletionSummaryModal open={tr.completionModalOpen} onClose={() => tr.setCompletionModalOpen(false)} passedCount={tr.completionStats.passed} failedCount={tr.completionStats.failed} totalDuration={tr.completionStats.duration} moduleName={tr.completionStats.moduleName} subModuleName={tr.completionStats.subModuleName} failedTests={tr.completionStats.failedTests} onViewResults={handleViewResults} onRerunFailed={handleCompletionRerunFailed} onNewRun={handleNewRun} onReportTest={handleQuickReport} />
      <ReportToAdminDialog open={d.reportDialogOpen} onClose={() => d.setReportDialogOpen(false)} testId={d.reportingTest?.id || ''} testDescription={d.reportingTest?.name || ''} error={d.reportingTest?.error} moduleName={modulePath.name} userName={user?.name || ''} userEmail={user?.email || ''} />
      {user && <UserProfileDialog open={d.profileDialogOpen} onClose={() => d.setProfileDialogOpen(false)} user={user} />}
      <SetTokenDialog open={tokenDialogOpen} onClose={() => setTokenDialogOpen(false)} erpToken={erpToken} setErpToken={setErpToken} erpTenantId={erpTenantId} setErpTenantId={setErpTenantId} />
      <Dialog open={logoutConfirmOpen} onOpenChange={setLogoutConfirmOpen}>
        <DialogContent className="sm:max-w-[360px]">
          <DialogHeader>
            <DialogTitle className="font-['Poppins'] text-[#333] dark:text-gray-100 flex items-center gap-2"><LogOut className="size-4 text-red-500" />Sign out</DialogTitle>
            <DialogDescription className="font-['Poppins'] text-[#888]">Are you sure you want to sign out?</DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setLogoutConfirmOpen(false)} className="font-['Poppins'] text-xs">Cancel</Button>
            <Button onClick={() => { setLogoutConfirmOpen(false); handleLogout() }} className="font-['Poppins'] text-xs bg-red-500 hover:bg-red-600 text-white">Sign out</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <RunDetailDialog open={d.runDetailDialogOpen} onClose={() => { d.setRunDetailDialogOpen(false); d.setSelectedRunForDetail(null) }} run={d.selectedRunForDetail} visibilityData={pd.visibilityData} showRawNames={showRawNames} onReportTest={handleQuickReport} />
      <RunComparisonDialog open={d.runComparisonOpen} onClose={() => d.setRunComparisonOpen(false)} runHistory={pd.runHistory} currentModuleId={selectedModule} />
      <RunHistoryDialog open={d.runHistoryOpen} onClose={() => d.setRunHistoryOpen(false)} runHistory={pd.runHistory} sidebarModules={sidebarModules} currentModuleId={selectedModule} onRunDetail={(run) => { d.setSelectedRunForDetail(run); d.setRunDetailDialogOpen(true) }} />
      {d.lightboxOpen && <ScreenshotLightbox open={d.lightboxOpen} onClose={() => d.setLightboxOpen(false)} screenshots={tr.screenshotEntries} initialIndex={d.lightboxIndex} />}
      {d.screenshotCompareOpen && <ScreenshotCompare left={d.compareScreenshots[0]} right={d.compareScreenshots[1]} onClose={() => d.setScreenshotCompareOpen(false)} />}
      <footer className="shrink-0 border-t border-gray-300 dark:border-gray-500/70 bg-white dark:bg-gray-900 px-4 py-1.5 flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-[10px] text-gray-400 dark:text-gray-500"><Copyright className="size-3" /><span>2026 AgDi Solutions Pvt. Ltd. All rights reserved.</span></div>
        <button onClick={() => setConsoleOpen(o => !o)} className="flex items-center gap-1.5 text-[10px] text-gray-700 dark:text-gray-600 hover:text-gray-900 dark:hover:text-gray-300 transition-colors cursor-pointer"><Terminal className="size-3" /><span>Console</span>{tr.consoleLogs.length > 0 && <span className="bg-green-500/20 text-green-500 dark:text-green-400 text-[9px] px-1 py-0.5 rounded-full">{tr.consoleLogs.length}</span>}</button>
        <div className="flex items-center gap-3 text-[10px] text-gray-400 dark:text-gray-500"><span className="flex items-center gap-1">Version 1.0.0</span><a href="https://rhythmerp.algorhythms.in" target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 hover:text-[#3F51B5] dark:hover:text-[#7986CB] transition-colors cursor-pointer"><HelpCircle className="size-3" />Help<ExternalLink className="size-2.5" /></a></div>
      </footer>
    </div>
  )
}
