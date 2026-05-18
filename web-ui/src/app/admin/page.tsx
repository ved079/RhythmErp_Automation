'use client'

import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { getBugReports, updateBugReportStatus, addReplyToReport, markReportReadByAdmin, getSLAStatus, type BugReport } from '@/lib/bug-reports'
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog'
import {
  Search,
  Plus,
  Filter,
  MoreVertical,
  Eye,
  Pencil,
  Trash2,
  ClipboardList,
  Clock,
  ChevronRight,
  ChevronLeft,
  ChevronDown,
  Play,
  Square,
  Terminal,
  X,
  Loader2,
  User,
  Lock,
  LogOut,
  Globe,
  Settings,
  LayoutDashboard,
  Users,
  Shield,
  Server,
  Cpu,
  Activity,
  TrendingUp,
  BarChart3,
  Flame,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Circle,
  Menu,
  Sun,
  Moon,
  ArrowLeft,
  ArrowUp,
  ArrowDown,
  Zap,
  Monitor,
  Database,
  Key,
  Bell,
  Webhook,
  RotateCcw,
  Save,
  Link2,
  Home,
  FolderTree,
  Inbox,
  Send,
  Timer,
} from 'lucide-react'

// ─── Types ───────────────────────────────────────────────
type TestPriority = 'smoke' | 'regression' | 'sanity'

interface AuthUser {
  id: string
  email: string
  name: string
  role: string
}

interface AdminTest {
  id: string
  description: string
  className: string
  status: 'active' | 'draft' | 'disabled'
  priority: TestPriority
  steps: string
  expected: string
  moduleId: string
  moduleName: string
  error?: string
  lastResult?: 'passed' | 'failed' | 'not-run'
  lastRun?: string
}

interface AdminModule {
  id: string
  label: string
  parentId?: string
  parentLabel?: string
  badge?: string
  badgeType?: 'success' | 'warning' | 'wip' | 'none'
  testCount: number
  sortOrder: number
  status: 'active' | 'draft' | 'disabled'
}

interface Environment {
  id: string
  name: string
  baseUrl: string
  browser: string
  status: 'active' | 'inactive'
  lastUsed?: string
  color: string
}

interface AdminUser {
  id: string
  email: string
  name: string
  role: 'admin' | 'qa_lead' | 'tester' | 'viewer' | 'client'
  status: 'active' | 'inactive'
  lastLogin?: string
  moduleAccess: string[]
}

interface SystemSetting {
  id: string
  key: string
  label: string
  value: string
  type: 'text' | 'number' | 'boolean' | 'select'
  description: string
  category: string
}

// ─── Mock Data ───────────────────────────────────────────
const initialTests: AdminTest[] = [
  { id: 'T01', description: 'Create with all valid fields', className: 'TestCreate', status: 'active', priority: 'smoke', steps: 'Click Add → Fill Name, Tax Type, Tax Authority → Select From/To Date, Revision Status → Submit', expected: 'Record created successfully, SweetAlert2 success toast', moduleId: 'tax-rate', moduleName: 'Tax Rate', lastResult: 'passed', lastRun: '16 May 2026, 10:23 AM' },
  { id: 'T02', description: 'Create with minimum fields', className: 'TestCreate', status: 'active', priority: 'smoke', steps: 'Click Add → Fill Tax Rate Name → Submit', expected: 'Record created with default values', moduleId: 'tax-rate', moduleName: 'Tax Rate', lastResult: 'passed', lastRun: '16 May 2026, 10:23 AM' },
  { id: 'T03', description: 'Add HSN row in sub-table', className: 'TestSubTable', status: 'active', priority: 'regression', steps: 'Click Add → Fill fields → Go to "Define Tax Rate Details" tab → Click Add → Select HSN Number → Enter Tax Rate → Submit', expected: 'Sub-table row added, record created', moduleId: 'tax-rate', moduleName: 'Tax Rate', lastResult: 'failed', lastRun: '16 May 2026, 10:23 AM', error: 'SubTableAddButton not found in DOM' },
  { id: 'T04', description: 'Update existing record name', className: 'TestEdit', status: 'active', priority: 'regression', steps: 'Search record → Click Edit → Change Name → Update', expected: 'Name updated, success alert', moduleId: 'tax-rate', moduleName: 'Tax Rate', lastResult: 'passed', lastRun: '16 May 2026, 10:23 AM' },
  { id: 'T05', description: 'Update with blank name', className: 'TestEdit', status: 'active', priority: 'regression', steps: 'Search record → Click Edit → Clear Name → Update', expected: 'Validation error shown', moduleId: 'tax-rate', moduleName: 'Tax Rate', lastResult: 'passed', lastRun: '16 May 2026, 10:23 AM' },
  { id: 'T06', description: 'Update non-existent record', className: 'TestEdit', status: 'active', priority: 'regression', steps: 'Search for non-existent name → Verify not in table', expected: 'Record not found', moduleId: 'tax-rate', moduleName: 'Tax Rate', lastResult: 'passed', lastRun: '16 May 2026, 10:23 AM' },
  { id: 'T09', description: 'Submit with empty sub-table', className: 'TestSubTable', status: 'active', priority: 'regression', steps: 'Click Add → Fill header fields → Submit WITHOUT adding sub-table row', expected: 'Form should reject empty sub-table', moduleId: 'tax-rate', moduleName: 'Tax Rate', lastResult: 'failed', lastRun: '16 May 2026, 10:23 AM', error: 'Server accepts empty sub-table as success (wrong assertion)' },
  { id: 'T10', description: 'Search existing record', className: 'TestSearch', status: 'active', priority: 'smoke', steps: 'Enter record name in search field → Verify record appears in table', expected: 'Matching record displayed in results', moduleId: 'tax-rate', moduleName: 'Tax Rate', lastResult: 'passed', lastRun: '16 May 2026, 10:23 AM' },
  { id: 'T11', description: 'Search non-existent record', className: 'TestSearch', status: 'active', priority: 'regression', steps: 'Enter non-existent name → Verify "No records found" message', expected: 'No records displayed, empty state shown', moduleId: 'tax-rate', moduleName: 'Tax Rate', lastResult: 'passed', lastRun: '16 May 2026, 10:23 AM' },
  { id: 'T17', description: 'View history of existing record', className: 'TestHistory', status: 'active', priority: 'sanity', steps: 'Click History icon → Verify popup opens with record history', expected: 'History popup displays with correct entries', moduleId: 'tax-rate', moduleName: 'Tax Rate', lastResult: 'passed', lastRun: '16 May 2026, 10:23 AM' },
  { id: 'T18', description: 'Search within history popup', className: 'TestHistory', status: 'active', priority: 'sanity', steps: 'Open History popup → Enter search term → Verify filtered results', expected: 'History entries filtered correctly', moduleId: 'tax-rate', moduleName: 'Tax Rate', lastResult: 'passed', lastRun: '16 May 2026, 10:23 AM' },
  { id: 'T24', description: 'Verify pagination controls', className: 'TestPagination', status: 'active', priority: 'sanity', steps: 'Navigate through page controls → Verify First, Prev, Next, Last buttons', expected: 'Pagination works correctly, correct records per page', moduleId: 'tax-rate', moduleName: 'Tax Rate', lastResult: 'passed', lastRun: '16 May 2026, 10:23 AM' },
  { id: 'T31', description: 'Add new customer with valid fields', className: 'TestCreate', status: 'active', priority: 'smoke', steps: 'Click Add → Fill Customer Name, Contact, Email, Phone → Select Region → Submit', expected: 'Customer created successfully', moduleId: 'customer', moduleName: 'Customer', lastResult: 'passed', lastRun: '16 May 2026, 09:30 AM' },
  { id: 'T32', description: 'Search customer by name', className: 'TestSearch', status: 'active', priority: 'regression', steps: 'Enter customer name → Verify in table', expected: 'Customer displayed', moduleId: 'customer', moduleName: 'Customer', lastResult: 'passed', lastRun: '16 May 2026, 09:30 AM' },
  { id: 'T33', description: 'Delete existing customer', className: 'TestDelete', status: 'draft', priority: 'sanity', steps: 'Select customer → Click Delete → Confirm', expected: 'Customer removed', moduleId: 'customer', moduleName: 'Customer', lastResult: 'not-run', lastRun: '—' },
  { id: 'T41', description: 'Verify farmer profile creation', className: 'TestCreate', status: 'active', priority: 'regression', steps: 'Navigate to Farmer → Click Add → Fill all required fields → Submit', expected: 'Farmer profile created', moduleId: 'farmer', moduleName: 'Farmer', lastResult: 'failed', lastRun: '16 May 2026, 09:15 AM', error: 'Village dropdown not populating' },
  { id: 'T42', description: 'Upload farmer documents', className: 'TestUpload', status: 'draft', priority: 'sanity', steps: 'Open farmer profile → Go to Documents tab → Upload PDF', expected: 'Document uploaded successfully', moduleId: 'farmer', moduleName: 'Farmer', lastResult: 'not-run', lastRun: '—' },
]

const initialModules: AdminModule[] = [
  { id: 'dashboard', label: 'Dashboard', testCount: 0, sortOrder: 0, status: 'active' },
  { id: 'customer', label: 'Customer', testCount: 3, sortOrder: 1, status: 'active' },
  { id: 'farmer', label: 'Farmer', testCount: 2, sortOrder: 2, status: 'active' },
  { id: 'company-onboarding', label: 'Company Onboarding', testCount: 18, sortOrder: 3, status: 'active' },
  { id: 'common-settings', label: 'Common Settings', testCount: 108, sortOrder: 4, status: 'active' },
  { id: 'uom', label: 'UOM', parentId: 'common-settings', parentLabel: 'Common Settings', testCount: 8, sortOrder: 5, status: 'active' },
  { id: 'uom-conversion', label: 'UOM Conversion', parentId: 'common-settings', parentLabel: 'Common Settings', testCount: 6, sortOrder: 6, status: 'active' },
  { id: 'designation', label: 'Designation', parentId: 'common-settings', parentLabel: 'Common Settings', testCount: 5, sortOrder: 7, status: 'active' },
  { id: 'bank', label: 'Bank', parentId: 'common-settings', parentLabel: 'Common Settings', testCount: 12, sortOrder: 8, status: 'active' },
  { id: 'seasons', label: 'Seasons', parentId: 'common-settings', parentLabel: 'Common Settings', testCount: 7, sortOrder: 9, status: 'active' },
  { id: 'hsn-sac', label: 'HSN SAC', parentId: 'common-settings', parentLabel: 'Common Settings', badge: '✅ 12/12', badgeType: 'success', testCount: 12, sortOrder: 10, status: 'active' },
  { id: 'error-code-master', label: 'Error Code Master', parentId: 'common-settings', parentLabel: 'Common Settings', badge: '🔄 WIP', badgeType: 'wip', testCount: 0, sortOrder: 11, status: 'draft' },
  { id: 'vehicle-master', label: 'Vehicle Master', parentId: 'common-settings', parentLabel: 'Common Settings', badge: '—', badgeType: 'none', testCount: 0, sortOrder: 12, status: 'active' },
  { id: 'tax-authority', label: 'Tax Authority', parentId: 'common-settings', parentLabel: 'Common Settings', badge: '⚠️ 15/18', badgeType: 'warning', testCount: 18, sortOrder: 13, status: 'active' },
  { id: 'tax-rate', label: 'Tax Rate', parentId: 'common-settings', parentLabel: 'Common Settings', badge: '⚠️ 17/20', badgeType: 'warning', testCount: 12, sortOrder: 14, status: 'active' },
  { id: 'commodity-settings', label: 'Commodity Settings', testCount: 118, sortOrder: 15, status: 'active' },
  { id: 'crop-master', label: 'Crop Master', parentId: 'commodity-settings', parentLabel: 'Commodity Settings', testCount: 20, sortOrder: 16, status: 'active' },
  { id: 'commodity-quality-param', label: 'Commodity Quality Param', parentId: 'commodity-settings', parentLabel: 'Commodity Settings', testCount: 9, sortOrder: 17, status: 'active' },
  { id: 'quality-parameter-def', label: 'Quality Parameter Def', parentId: 'commodity-settings', parentLabel: 'Commodity Settings', testCount: 11, sortOrder: 18, status: 'active' },
  { id: 'commodity-base-rate', label: 'Commodity Base Rate', parentId: 'commodity-settings', parentLabel: 'Commodity Settings', testCount: 8, sortOrder: 19, status: 'active' },
  { id: 'commodity-master', label: 'Commodity Master', parentId: 'commodity-settings', parentLabel: 'Commodity Settings', testCount: 22, sortOrder: 20, status: 'active' },
  { id: 'item-master', label: 'Item Master', parentId: 'commodity-settings', parentLabel: 'Commodity Settings', testCount: 16, sortOrder: 21, status: 'active' },
  { id: 'services-master', label: 'Services Master', parentId: 'commodity-settings', parentLabel: 'Commodity Settings', testCount: 10, sortOrder: 22, status: 'active' },
  { id: 'item-category', label: 'Item Category', parentId: 'commodity-settings', parentLabel: 'Commodity Settings', testCount: 8, sortOrder: 23, status: 'active' },
  { id: 'item-group', label: 'Item Group', parentId: 'commodity-settings', parentLabel: 'Commodity Settings', testCount: 7, sortOrder: 24, status: 'active' },
  { id: 'finance-settings', label: 'Finance Settings', testCount: 30, sortOrder: 25, status: 'active' },
  { id: 'access', label: 'Access', testCount: 0, sortOrder: 26, status: 'active' },
]

const initialEnvironments: Environment[] = [
  { id: 'env-1', name: 'Staging', baseUrl: 'https://staging.rhythmerp.com', browser: 'Chrome', status: 'active', lastUsed: '16 May 2026, 10:23 AM', color: 'bg-green-500' },
  { id: 'env-2', name: 'QA', baseUrl: 'https://qa.rhythmerp.com', browser: 'Chrome', status: 'active', lastUsed: '15 May 2026, 03:45 PM', color: 'bg-blue-500' },
  { id: 'env-3', name: 'UAT', baseUrl: 'https://uat.rhythmerp.com', browser: 'Edge', status: 'active', lastUsed: '14 May 2026, 11:20 AM', color: 'bg-orange-500' },
  { id: 'env-4', name: 'Production', baseUrl: 'https://rhythmerp.com', browser: 'Chrome', status: 'inactive', color: 'bg-red-500' },
]

const initialUsers: AdminUser[] = [
  { id: 'usr-1', email: 'admin@rhythmerp.com', name: 'Admin', role: 'admin', status: 'active', lastLogin: '16 May 2026, 10:00 AM', moduleAccess: ['all'] },
  { id: 'usr-2', email: 'priya@rhythmerp.com', name: 'Priya Sharma', role: 'qa_lead', status: 'active', lastLogin: '16 May 2026, 09:15 AM', moduleAccess: ['all'] },
  { id: 'usr-3', email: 'rahul@rhythmerp.com', name: 'Rahul Verma', role: 'tester', status: 'active', lastLogin: '15 May 2026, 04:30 PM', moduleAccess: ['tax-rate', 'tax-authority', 'hsn-sac', 'bank'] },
  { id: 'usr-4', email: 'amit@rhythmerp.com', name: 'Amit Patel', role: 'tester', status: 'active', lastLogin: '16 May 2026, 08:45 AM', moduleAccess: ['customer', 'farmer', 'company-onboarding'] },
  { id: 'usr-5', email: 'sneha@rhythmerp.com', name: 'Sneha Gupta', role: 'tester', status: 'inactive', lastLogin: '10 May 2026, 02:00 PM', moduleAccess: ['commodity-settings'] },
  { id: 'usr-6', email: 'client@rhythmerp.com', name: 'Client Viewer', role: 'client', status: 'active', lastLogin: '16 May 2026, 10:30 AM', moduleAccess: ['dashboard'] },
]

const initialSettings: SystemSetting[] = [
  { id: 's1', key: 'selenium_grid_url', label: 'Selenium Grid URL', value: 'http://localhost:4444/wd/hub', type: 'text', description: 'URL of the Selenium Grid hub for remote WebDriver execution', category: 'Execution' },
  { id: 's2', key: 'cdp_target_url', label: 'CDP Target URL', value: 'http://localhost:9222', type: 'text', description: 'Chrome DevTools Protocol target for live browser screencast', category: 'Execution' },
  { id: 's3', key: 'default_timeout', label: 'Default Test Timeout (sec)', value: '30', type: 'number', description: 'Maximum time to wait for a single test step before failing', category: 'Execution' },
  { id: 's4', key: 'max_retries', label: 'Max Retries per Test', value: '2', type: 'number', description: 'Number of retry attempts for a failed test before marking as permanently failed', category: 'Execution' },
  { id: 's5', key: 'parallel_workers', label: 'Parallel Workers', value: '3', type: 'number', description: 'Maximum number of tests that can run in parallel', category: 'Execution' },
  { id: 's6', key: 'slack_webhook', label: 'Slack Webhook URL', value: '', type: 'text', description: 'Slack incoming webhook URL for run completion notifications', category: 'Notifications' },
  { id: 's7', key: 'teams_webhook', label: 'MS Teams Webhook URL', value: '', type: 'text', description: 'Microsoft Teams incoming webhook for run notifications', category: 'Notifications' },
  { id: 's8', key: 'notify_on_failure', label: 'Notify on Test Failure', value: 'true', type: 'boolean', description: 'Send a notification when any test fails during a run', category: 'Notifications' },
  { id: 's9', key: 'notify_on_complete', label: 'Notify on Run Complete', value: 'true', type: 'boolean', description: 'Send a summary notification when a full run completes', category: 'Notifications' },
  { id: 's10', key: 'auto_screenshot_fail', label: 'Auto-screenshot on Failure', value: 'true', type: 'boolean', description: 'Automatically capture a screenshot when a test fails', category: 'Execution' },
  { id: 's11', key: 'log_level', label: 'Log Level', value: 'info', type: 'select', description: 'Console log verbosity level', category: 'System' },
  { id: 's12', key: 'session_timeout', label: 'Session Timeout (hours)', value: '168', type: 'number', description: 'User session duration before automatic logout (default 168 = 7 days)', category: 'System' },
]

// ─── Priority Config ────────────────────────────────────
const priorityConfig = {
  smoke: { icon: <Flame className="size-3" />, label: 'Smoke', color: 'text-orange-700 bg-orange-100 dark:text-orange-300 dark:bg-orange-900/40' },
  regression: { icon: <Activity className="size-3" />, label: 'Regression', color: 'text-blue-700 bg-blue-100 dark:text-blue-300 dark:bg-blue-900/40' },
  sanity: { icon: <Shield className="size-3" />, label: 'Sanity', color: 'text-purple-700 bg-purple-100 dark:text-purple-300 dark:bg-purple-900/40' },
} as const

const roleConfig: Record<string, { label: string; color: string }> = {
  admin: { label: 'Admin', color: 'text-red-700 bg-red-100 dark:text-red-300 dark:bg-red-900/40' },
  qa_lead: { label: 'QA Lead', color: 'text-blue-700 bg-blue-100 dark:text-blue-300 dark:bg-blue-900/40' },
  tester: { label: 'Tester', color: 'text-green-700 bg-green-100 dark:text-green-300 dark:bg-green-900/40' },
  viewer: { label: 'Viewer', color: 'text-gray-700 bg-gray-100 dark:text-gray-300 dark:bg-gray-900/40' },
  client: { label: 'Client', color: 'text-amber-700 bg-amber-100 dark:text-amber-300 dark:bg-amber-900/40' },
}

// ─── ADMIN PAGE COMPONENT ────────────────────────────────
export default function AdminPage() {
  const router = useRouter()
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [activeSection, setActiveSection] = useState('overview')

  // Admin data state
  const [tests, setTests] = useState<AdminTest[]>(initialTests)
  const [modules, setModules] = useState<AdminModule[]>(initialModules)
  const [environments, setEnvironments] = useState<Environment[]>(initialEnvironments)
  const [users, setUsers] = useState<AdminUser[]>(initialUsers)
  const [settings, setSettings] = useState<SystemSetting[]>(initialSettings)

  // Dialogs
  const [testDialogOpen, setTestDialogOpen] = useState(false)
  const [editingTest, setEditingTest] = useState<AdminTest | null>(null)
  const [moduleDialogOpen, setModuleDialogOpen] = useState(false)
  const [editingModule, setEditingModule] = useState<AdminModule | null>(null)
  const [envDialogOpen, setEnvDialogOpen] = useState(false)
  const [editingEnv, setEditingEnv] = useState<Environment | null>(null)
  const [userDialogOpen, setUserDialogOpen] = useState(false)
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<{ type: string; id: string; label: string } | null>(null)

  // Bug reports
  const [bugReports, setBugReports] = useState<BugReport[]>([])
  const [bugReportsLoaded, setBugReportsLoaded] = useState(false)

  // Load bug reports from localStorage
  useEffect(() => {
    if (!bugReportsLoaded) {
      setBugReports(getBugReports())
      setBugReportsLoaded(true)
    }
  }, [bugReportsLoaded])

  // Refresh bug reports when section becomes active
  useEffect(() => {
    if (activeSection === 'bug-reports') {
      setBugReports(getBugReports())
    }
  }, [activeSection])

  // Search / filter
  const [testSearch, setTestSearch] = useState('')
  const [testStatusFilter, setTestStatusFilter] = useState<string>('all')
  const [testModuleFilter, setTestModuleFilter] = useState<string>('all')
  const [testPriorityFilter, setTestPriorityFilter] = useState<string>('all')

  // Dark mode
  const [darkMode, setDarkMode] = useState(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('rhythmerp-dark-mode')
      if (stored !== null) return stored === 'true'
      return window.matchMedia('(prefers-color-scheme: dark)').matches
    }
    return false
  })

  useEffect(() => {
    if (darkMode) document.documentElement.classList.add('dark')
    else document.documentElement.classList.remove('dark')
    localStorage.setItem('rhythmerp-dark-mode', String(darkMode))
  }, [darkMode])

  // Auth check
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const res = await fetch('/api/auth/me')
        if (!res.ok) {
          router.push('/')
          return
        }
        const data = await res.json()
        if (data.user.role !== 'admin' && data.user.role !== 'qa_lead') {
          router.push('/')
          return
        }
        setUser(data.user)
      } catch {
        router.push('/')
      } finally {
        setLoading(false)
      }
    }
    checkAuth()
  }, [router])

  const handleLogout = useCallback(async () => {
    await fetch('/api/auth/logout', { method: 'POST' })
    router.push('/')
  }, [router])

  // ─── Filtered tests ────────────────────────────────
  const filteredTests = useMemo(() => {
    return tests.filter((t) => {
      const matchSearch = testSearch === '' || t.id.toLowerCase().includes(testSearch.toLowerCase()) || t.description.toLowerCase().includes(testSearch.toLowerCase()) || t.className.toLowerCase().includes(testSearch.toLowerCase())
      const matchStatus = testStatusFilter === 'all' || t.status === testStatusFilter
      const matchModule = testModuleFilter === 'all' || t.moduleId === testModuleFilter
      const matchPriority = testPriorityFilter === 'all' || t.priority === testPriorityFilter
      return matchSearch && matchStatus && matchModule && matchPriority
    })
  }, [tests, testSearch, testStatusFilter, testModuleFilter, testPriorityFilter])

  const uniqueModules = useMemo(() => {
    const modMap = new Map<string, string>()
    for (const t of tests) {
      if (!modMap.has(t.moduleId)) modMap.set(t.moduleId, t.moduleName)
    }
    return Array.from(modMap.entries()).sort((a, b) => a[1].localeCompare(b[1]))
  }, [tests])

  // ─── CRUD handlers ─────────────────────────────────
  const handleSaveTest = useCallback((testData: Partial<AdminTest>) => {
    if (editingTest) {
      setTests((prev) => prev.map((t) => t.id === editingTest.id ? { ...t, ...testData } : t))
    } else {
      const newId = `T${String(tests.length + 50).padStart(2, '0')}`
      const mod = modules.find((m) => m.id === (testData.moduleId || 'tax-rate'))
      setTests((prev) => [...prev, { ...testData, id: newId, className: testData.className || 'TestNew', status: 'draft' as const, priority: testData.priority || 'sanity' as TestPriority, moduleId: testData.moduleId || 'tax-rate', moduleName: mod?.label || 'Unknown', lastResult: 'not-run' as const, lastRun: '—' } as AdminTest])
    }
    setTestDialogOpen(false)
    setEditingTest(null)
  }, [editingTest, tests.length, modules])

  const handleSaveModule = useCallback((modData: Partial<AdminModule>) => {
    if (editingModule) {
      setModules((prev) => prev.map((m) => m.id === editingModule.id ? { ...m, ...modData } : m))
    } else {
      const newId = modData.id || `mod-${Date.now()}`
      setModules((prev) => [...prev, { ...modData, id: newId, testCount: 0, sortOrder: prev.length } as AdminModule])
    }
    setModuleDialogOpen(false)
    setEditingModule(null)
  }, [editingModule])

  const handleSaveEnv = useCallback((envData: Partial<Environment>) => {
    if (editingEnv) {
      setEnvironments((prev) => prev.map((e) => e.id === editingEnv.id ? { ...e, ...envData } : e))
    } else {
      setEnvironments((prev) => [...prev, { ...envData, id: `env-${Date.now()}`, status: 'active' as const } as Environment])
    }
    setEnvDialogOpen(false)
    setEditingEnv(null)
  }, [editingEnv])

  const handleSaveUser = useCallback((userData: Partial<AdminUser>) => {
    if (editingUser) {
      setUsers((prev) => prev.map((u) => u.id === editingUser.id ? { ...u, ...userData } : u))
    } else {
      setUsers((prev) => [...prev, { ...userData, id: `usr-${Date.now()}`, status: 'active' as const, moduleAccess: userData.moduleAccess || [] } as AdminUser])
    }
    setUserDialogOpen(false)
    setEditingUser(null)
  }, [editingUser])

  const handleDelete = useCallback(() => {
    if (!deleteTarget) return
    if (deleteTarget.type === 'test') setTests((prev) => prev.filter((t) => t.id !== deleteTarget.id))
    else if (deleteTarget.type === 'module') setModules((prev) => prev.filter((m) => m.id !== deleteTarget.id))
    else if (deleteTarget.type === 'environment') setEnvironments((prev) => prev.filter((e) => e.id !== deleteTarget.id))
    else if (deleteTarget.type === 'user') setUsers((prev) => prev.filter((u) => u.id !== deleteTarget.id))
    setDeleteDialogOpen(false)
    setDeleteTarget(null)
  }, [deleteTarget])

  // ─── Sidebar items ─────────────────────────────────
  const sidebarItems = [
    { id: 'overview', icon: LayoutDashboard, label: 'Overview' },
    { id: 'tests', icon: ClipboardList, label: 'Test Management' },
    { id: 'modules', icon: FolderTree, label: 'Module Management' },
    { id: 'bug-reports', icon: Inbox, label: 'Bug Reports' },
    { id: 'environments', icon: Globe, label: 'Environments' },
    { id: 'users', icon: Users, label: 'Users' },
    { id: 'settings', icon: Settings, label: 'Settings' },
  ]

  // ─── Stats for overview ────────────────────────────
  const overviewStats = useMemo(() => {
    const activeTests = tests.filter((t) => t.status === 'active').length
    const totalModules = modules.filter((m) => !m.parentId).length
    const activeEnvs = environments.filter((e) => e.status === 'active').length
    const activeUsers = users.filter((u) => u.status === 'active').length
    const failedTests = tests.filter((t) => t.lastResult === 'failed').length
    const passRate = tests.filter((t) => t.lastResult !== 'not-run').length > 0
      ? Math.round((tests.filter((t) => t.lastResult === 'passed').length / tests.filter((t) => t.lastResult !== 'not-run').length) * 100)
      : 0
    const draftTests = tests.filter((t) => t.status === 'draft').length
    return { activeTests, totalModules, activeEnvs, activeUsers, failedTests, passRate, draftTests, totalTests: tests.length }
  }, [tests, modules, environments, users])

  // ─── Loading ────────────────────────────────────────
  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-white dark:bg-gray-900">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-red-600 flex items-center justify-center animate-pulse">
            <span className="text-white text-lg font-bold">R</span>
          </div>
          <Loader2 className="size-5 text-red-600 animate-spin" />
        </div>
      </div>
    )
  }

  if (!user) return null

  const userInitials = user.name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)

  return (
    <div className="h-screen flex flex-col bg-white dark:bg-gray-900 overflow-hidden">
      {/* ─── HEADER ─────────────────────────────────────── */}
      <header className="h-12 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 flex items-center px-4 shrink-0 z-10">
        <div className="flex items-center gap-3 flex-1">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className={`size-8 cursor-pointer shrink-0 transition-all duration-200 ${
              sidebarOpen ? 'text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800'
                : 'text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20'
            }`}
            title="Toggle sidebar"
          >
            <Menu className={`size-[18px] transition-transform duration-200 ${sidebarOpen ? '' : 'rotate-90'}`} />
          </Button>
          <Separator orientation="vertical" className="h-5" />
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-md bg-red-600 flex items-center justify-center">
              <span className="text-white text-xs font-bold">R</span>
            </div>
            <span className="text-[15px] font-semibold text-gray-800 dark:text-gray-100 tracking-tight">
              Rhythm<span className="text-red-600">ERP</span>
              <span className="text-gray-400 dark:text-gray-500 font-normal ml-1.5 text-[13px]">Admin Panel</span>
            </span>
          </div>
          <Badge className="bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400 text-[10px] font-semibold px-1.5 py-0 ml-1 border-0">
            ADMIN
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setDarkMode((prev) => !prev)}
            className="size-8 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer"
          >
            {darkMode ? <Sun className="size-4" /> : <Moon className="size-4" />}
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push('/')}
            className="size-8 text-gray-500 dark:text-gray-400 hover:text-green-700 dark:hover:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20 cursor-pointer"
            title="Back to User Panel"
          >
            <Home className="size-4" />
          </Button>
          <Separator orientation="vertical" className="h-5 mx-1" />
          <div className="flex items-center gap-2">
            <Avatar className="size-7">
              <AvatarFallback className="bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 text-xs font-semibold">
                {userInitials}
              </AvatarFallback>
            </Avatar>
            <span className="text-[12px] text-gray-600 dark:text-gray-300 font-medium max-w-[120px] truncate">{user.name}</span>
            <Button variant="ghost" size="icon" onClick={handleLogout} className="size-8 text-gray-400 hover:text-red-500 cursor-pointer" title="Sign out">
              <LogOut className="size-4" />
            </Button>
          </div>
        </div>
      </header>

      {/* ─── BODY ───────────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">
        {/* ─── SIDEBAR ──────────────────────────────────── */}
        <div className={`shrink-0 transition-all duration-200 ease-in-out overflow-hidden ${sidebarOpen ? 'w-60' : 'w-0'}`}>
          <aside className="w-60 bg-[#fef2f2] dark:bg-[#2a1a1a] border-r border-[#fecaca] dark:border-[#4a2a2a] flex flex-col h-full">
            <div className="px-3 py-2.5 border-b border-[#fecaca] dark:border-[#4a2a2a] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Shield className="size-3.5 text-red-500 dark:text-red-400" />
                <span className="text-[13px] font-medium text-gray-600 dark:text-gray-300">Admin Controls</span>
              </div>
              <button onClick={() => setSidebarOpen(false)} className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors cursor-pointer p-0.5 rounded hover:bg-[#fecaca]/50 dark:hover:bg-[#4a2a2a]/50">
                <ChevronLeft className="size-4" />
              </button>
            </div>
            <ScrollArea className="flex-1">
              <div className="py-2 px-2">
                {sidebarItems.map((item) => {
                  const Icon = item.icon
                  const isActive = activeSection === item.id
                  return (
                    <button
                      key={item.id}
                      onClick={() => setActiveSection(item.id)}
                      className={`w-full flex items-center gap-2.5 px-3 py-2 text-[13px] rounded-md transition-colors cursor-pointer text-left ${
                        isActive
                          ? 'bg-[#fecaca] dark:bg-[#4a2a2a] text-gray-900 dark:text-gray-100 font-medium shadow-sm'
                          : 'text-gray-600 dark:text-gray-400 hover:bg-[#fecaca]/40 dark:hover:bg-[#4a2a2a]/30'
                      }`}
                    >
                      <Icon className={`size-4 shrink-0 ${isActive ? 'text-red-600 dark:text-red-400' : ''}`} />
                      <span className="truncate">{item.label}</span>
                      {item.id === 'tests' && (
                        <span className="text-[10px] text-gray-500 dark:text-gray-400 ml-auto">{tests.length}</span>
                      )}
                      {item.id === 'modules' && (
                        <span className="text-[10px] text-gray-500 dark:text-gray-400 ml-auto">{modules.length}</span>
                      )}
                      {item.id === 'bug-reports' && bugReports.filter((r) => r.status === 'open').length > 0 && (
                        <span className="ml-auto text-[10px] font-bold text-white bg-orange-500 rounded-full w-5 h-5 flex items-center justify-center">
                          {bugReports.filter((r) => r.status === 'open').length}
                        </span>
                      )}
                    </button>
                  )
                })}
              </div>
            </ScrollArea>
            <div className="px-3 py-2 border-t border-[#fecaca] dark:border-[#4a2a2a]">
              <button
                onClick={() => router.push('/')}
                className="w-full flex items-center gap-2 px-3 py-2 text-[12px] text-gray-500 dark:text-gray-400 hover:text-green-700 dark:hover:text-green-400 rounded-md hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors cursor-pointer"
              >
                <ArrowLeft className="size-3.5" />
                User Panel
              </button>
            </div>
          </aside>
        </div>

        {/* ─── MAIN CONTENT ─────────────────────────────── */}
        <main className="flex-1 flex flex-col overflow-hidden bg-gray-50 dark:bg-gray-900">
          {/* Content */}
          <div className="flex-1 overflow-auto p-5">
            {activeSection === 'overview' && (
              <AdminOverview stats={overviewStats} tests={tests} environments={environments} />
            )}
            {activeSection === 'tests' && (
              <AdminTests
                tests={filteredTests}
                allTests={tests}
                testSearch={testSearch}
                testStatusFilter={testStatusFilter}
                testModuleFilter={testModuleFilter}
                testPriorityFilter={testPriorityFilter}
                uniqueModules={uniqueModules}
                onSearchChange={setTestSearch}
                onStatusFilterChange={setTestStatusFilter}
                onModuleFilterChange={setTestModuleFilter}
                onPriorityFilterChange={setTestPriorityFilter}
                onAddTest={() => { setEditingTest(null); setTestDialogOpen(true) }}
                onEditTest={(t) => { setEditingTest(t); setTestDialogOpen(true) }}
                onDeleteTest={(t) => { setDeleteTarget({ type: 'test', id: t.id, label: `${t.id} — ${t.description}` }); setDeleteDialogOpen(true) }}
              />
            )}
            {activeSection === 'modules' && (
              <AdminModules
                modules={modules}
                onAddModule={() => { setEditingModule(null); setModuleDialogOpen(true) }}
                onEditModule={(m) => { setEditingModule(m); setModuleDialogOpen(true) }}
                onDeleteModule={(m) => { setDeleteTarget({ type: 'module', id: m.id, label: m.label }); setDeleteDialogOpen(true) }}
                onMoveModule={(id, dir) => {
                  setModules((prev) => {
                    const idx = prev.findIndex((m) => m.id === id)
                    if (idx < 0) return prev
                    const newIdx = dir === 'up' ? idx - 1 : idx + 1
                    if (newIdx < 0 || newIdx >= prev.length) return prev
                    const arr = [...prev]
                    ;[arr[idx], arr[newIdx]] = [arr[newIdx], arr[idx]]
                    return arr.map((m, i) => ({ ...m, sortOrder: i }))
                  })
                }}
              />
            )}
            {activeSection === 'environments' && (
              <AdminEnvironments
                environments={environments}
                onAddEnv={() => { setEditingEnv(null); setEnvDialogOpen(true) }}
                onEditEnv={(e) => { setEditingEnv(e); setEnvDialogOpen(true) }}
                onDeleteEnv={(e) => { setDeleteTarget({ type: 'environment', id: e.id, label: e.name }); setDeleteDialogOpen(true) }}
                onToggleEnv={(id) => setEnvironments((prev) => prev.map((e) => e.id === id ? { ...e, status: e.status === 'active' ? 'inactive' as const : 'active' as const } : e))}
              />
            )}
            {activeSection === 'users' && (
              <AdminUsers
                users={users}
                modules={modules}
                onAddUser={() => { setEditingUser(null); setUserDialogOpen(true) }}
                onEditUser={(u) => { setEditingUser(u); setUserDialogOpen(true) }}
                onDeleteUser={(u) => { setDeleteTarget({ type: 'user', id: u.id, label: `${u.name} (${u.email})` }); setDeleteDialogOpen(true) }}
                onToggleUser={(id) => setUsers((prev) => prev.map((u) => u.id === id ? { ...u, status: u.status === 'active' ? 'inactive' as const : 'active' as const } : u))}
              />
            )}
            {activeSection === 'bug-reports' && (
              <AdminBugReports
                reports={bugReports}
                onUpdateStatus={(id, status) => {
                  updateBugReportStatus(id, status)
                  setBugReports(getBugReports())
                }}
              />
            )}
            {activeSection === 'settings' && (
              <AdminSettings
                settings={settings}
                onUpdateSetting={(id, value) => setSettings((prev) => prev.map((s) => s.id === id ? { ...s, value } : s))}
              />
            )}
          </div>
        </main>
      </div>

      {/* ─── DIALOGS ────────────────────────────────────── */}
      {/* Test Dialog */}
      <Dialog open={testDialogOpen} onOpenChange={setTestDialogOpen}>
        <DialogContent className="max-w-xl max-h-[85vh] overflow-auto">
          <DialogHeader>
            <DialogTitle>{editingTest ? 'Edit Test Case' : 'Add Test Case'}</DialogTitle>
            <DialogDescription>{editingTest ? `Editing ${editingTest.id}` : 'Create a new test case'}</DialogDescription>
          </DialogHeader>
          <TestForm test={editingTest} modules={uniqueModules} onSave={handleSaveTest} onCancel={() => { setTestDialogOpen(false); setEditingTest(null) }} />
        </DialogContent>
      </Dialog>

      {/* Module Dialog */}
      <Dialog open={moduleDialogOpen} onOpenChange={setModuleDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{editingModule ? 'Edit Module' : 'Add Module'}</DialogTitle>
            <DialogDescription>{editingModule ? `Editing ${editingModule.label}` : 'Add a new module to the sidebar'}</DialogDescription>
          </DialogHeader>
          <ModuleForm module={editingModule} onSave={handleSaveModule} onCancel={() => { setModuleDialogOpen(false); setEditingModule(null) }} />
        </DialogContent>
      </Dialog>

      {/* Environment Dialog */}
      <Dialog open={envDialogOpen} onOpenChange={setEnvDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{editingEnv ? 'Edit Environment' : 'Add Environment'}</DialogTitle>
          </DialogHeader>
          <EnvironmentForm env={editingEnv} onSave={handleSaveEnv} onCancel={() => { setEnvDialogOpen(false); setEditingEnv(null) }} />
        </DialogContent>
      </Dialog>

      {/* User Dialog */}
      <Dialog open={userDialogOpen} onOpenChange={setUserDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{editingUser ? 'Edit User' : 'Add User'}</DialogTitle>
          </DialogHeader>
          <UserForm user={editingUser} onSave={handleSaveUser} onCancel={() => { setUserDialogOpen(false); setEditingUser(null) }} />
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Delete Confirmation</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete <strong>{deleteTarget?.label}</strong>? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)} className="cursor-pointer">Cancel</Button>
            <Button variant="destructive" onClick={handleDelete} className="cursor-pointer bg-red-600 hover:bg-red-700">Delete</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

// ─── ADMIN OVERVIEW ──────────────────────────────────────
function AdminOverview({ stats, tests, environments }: { stats: ReturnType<typeof useMemo>; tests: AdminTest[]; environments: Environment[] }) {
  const recentFailures = tests.filter((t) => t.lastResult === 'failed').slice(0, 5)
  const draftTests = tests.filter((t) => t.status === 'draft')

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-[18px] font-semibold text-gray-800 dark:text-gray-100">Admin Overview</h2>
        <p className="text-[13px] text-gray-500 dark:text-gray-400 mt-0.5">System health and management summary</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard label="Active Tests" value={stats.activeTests} sub={`of ${stats.totalTests} total`} color="green" />
        <StatCard label="Modules" value={stats.totalModules} sub={`${modules_total_tests} tests`} color="blue" />
        <StatCard label="Environments" value={stats.activeEnvs} sub={`of ${environments.length} configured`} color="orange" />
        <StatCard label="Active Users" value={stats.activeUsers} sub="currently" color="purple" />
      </div>

      {/* Pass Rate */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-100 dark:border-gray-700">
          <div className="text-[12px] text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wider mb-3">Overall Pass Rate</div>
          <div className="flex items-center gap-4">
            <div className="relative w-20 h-20">
              <svg className="w-20 h-20 -rotate-90" viewBox="0 0 36 36">
                <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" className="text-gray-200 dark:text-gray-700" strokeWidth="3" />
                <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" className={stats.passRate >= 80 ? 'text-green-500' : stats.passRate >= 50 ? 'text-orange-500' : 'text-red-500'} strokeWidth="3" strokeDasharray={`${stats.passRate}, 100`} strokeLinecap="round" />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-[14px] font-bold text-gray-800 dark:text-gray-100">{stats.passRate}%</span>
              </div>
            </div>
            <div className="space-y-1.5">
              <div className="flex items-center gap-2 text-[12px]">
                <CheckCircle2 className="size-3.5 text-green-500" />
                <span className="text-gray-600 dark:text-gray-300">{tests.filter((t) => t.lastResult === 'passed').length} passed</span>
              </div>
              <div className="flex items-center gap-2 text-[12px]">
                <XCircle className="size-3.5 text-red-500" />
                <span className="text-gray-600 dark:text-gray-300">{stats.failedTests} failed</span>
              </div>
              <div className="flex items-center gap-2 text-[12px]">
                <Circle className="size-3.5 text-gray-400" />
                <span className="text-gray-600 dark:text-gray-300">{tests.filter((t) => t.lastResult === 'not-run').length} not run</span>
              </div>
              <div className="flex items-center gap-2 text-[12px]">
                <Pencil className="size-3.5 text-blue-500" />
                <span className="text-gray-600 dark:text-gray-300">{draftTests.length} drafts</span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-100 dark:border-gray-700">
          <div className="text-[12px] text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wider mb-3">Active Environments</div>
          <div className="space-y-2">
            {environments.map((env) => (
              <div key={env.id} className="flex items-center gap-3">
                <div className={`w-2.5 h-2.5 rounded-full shrink-0 ${env.color} ${env.status === 'active' ? 'animate-pulse' : 'opacity-40'}`} />
                <span className="text-[13px] text-gray-700 dark:text-gray-200 flex-1">{env.name}</span>
                <Badge variant="outline" className={`text-[10px] px-1.5 py-0 border-0 ${env.status === 'active' ? 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900/30' : 'text-gray-400 bg-gray-100 dark:text-gray-500 dark:bg-gray-800'}`}>
                  {env.status}
                </Badge>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Failures */}
      {recentFailures.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-red-100 dark:border-red-900/30">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="size-4 text-red-500" />
            <span className="text-[13px] font-semibold text-red-700 dark:text-red-400">Recent Test Failures</span>
            <span className="text-[11px] text-gray-500 dark:text-gray-400 ml-auto">{recentFailures.length} failing</span>
          </div>
          <div className="space-y-2">
            {recentFailures.map((t) => (
              <div key={t.id} className="flex items-start gap-3 px-3 py-2 rounded-md bg-red-50 dark:bg-red-900/10">
                <XCircle className="size-4 text-red-500 shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-[12px] font-semibold text-gray-800 dark:text-gray-100">{t.id}</span>
                    <span className="text-[12px] text-gray-500 dark:text-gray-400">in</span>
                    <span className="text-[12px] text-gray-600 dark:text-gray-300">{t.moduleName}</span>
                  </div>
                  <p className="text-[11px] text-gray-600 dark:text-gray-400 mt-0.5 truncate">{t.description}</p>
                  {t.error && <p className="text-[11px] text-red-600 dark:text-red-400 mt-0.5 truncate">{t.error}</p>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// Temp workaround for modules total tests
const modules_total_tests = 291

// ─── STAT CARD ───────────────────────────────────────────
function StatCard({ label, value, sub, color }: { label: string; value: number; sub: string; color: string }) {
  const colors: Record<string, string> = {
    green: 'bg-green-50 dark:bg-green-900/20 border-green-100 dark:border-green-800/50',
    blue: 'bg-blue-50 dark:bg-blue-900/20 border-blue-100 dark:border-blue-800/50',
    orange: 'bg-orange-50 dark:bg-orange-900/20 border-orange-100 dark:border-orange-800/50',
    purple: 'bg-purple-50 dark:bg-purple-900/20 border-purple-100 dark:border-purple-800/50',
    red: 'bg-red-50 dark:bg-red-900/20 border-red-100 dark:border-red-800/50',
  }
  const textColors: Record<string, string> = {
    green: 'text-green-700 dark:text-green-400',
    blue: 'text-blue-700 dark:text-blue-400',
    orange: 'text-orange-700 dark:text-orange-400',
    purple: 'text-purple-700 dark:text-purple-400',
    red: 'text-red-700 dark:text-red-400',
  }
  return (
    <div className={`${colors[color]} rounded-lg p-3.5 border`}>
      <div className="text-[11px] text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wider">{label}</div>
      <div className={`text-xl font-bold ${textColors[color]} mt-1`}>{value}</div>
      <div className="text-[11px] text-gray-400 dark:text-gray-500 mt-0.5">{sub}</div>
    </div>
  )
}

// ─── ADMIN TESTS VIEW ────────────────────────────────────
function AdminTests({
  tests, testSearch, testStatusFilter, testModuleFilter, testPriorityFilter,
  uniqueModules, onSearchChange, onStatusFilterChange, onModuleFilterChange,
  onPriorityFilterChange, onAddTest, onEditTest, onDeleteTest,
}: {
  tests: AdminTest[]
  allTests: AdminTest[]
  testSearch: string
  testStatusFilter: string
  testModuleFilter: string
  testPriorityFilter: string
  uniqueModules: [string, string][]
  onSearchChange: (v: string) => void
  onStatusFilterChange: (v: string) => void
  onModuleFilterChange: (v: string) => void
  onPriorityFilterChange: (v: string) => void
  onAddTest: () => void
  onEditTest: (t: AdminTest) => void
  onDeleteTest: (t: AdminTest) => void
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-[18px] font-semibold text-gray-800 dark:text-gray-100">Test Management</h2>
          <p className="text-[13px] text-gray-500 dark:text-gray-400 mt-0.5">{tests.length} test cases</p>
        </div>
        <Button onClick={onAddTest} className="bg-red-600 hover:bg-red-700 text-white text-[13px] gap-1.5 cursor-pointer">
          <Plus className="size-4" /> Add Test
        </Button>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700 flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-gray-400" />
          <Input placeholder="Search by ID, description, or class..." value={testSearch} onChange={(e) => onSearchChange(e.target.value)} className="h-8 pl-8 text-[12px] bg-gray-50 dark:bg-gray-700/50" />
        </div>
        <Select value={testStatusFilter} onValueChange={onStatusFilterChange}>
          <SelectTrigger className="w-[120px] h-8 text-[12px]"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="disabled">Disabled</SelectItem>
          </SelectContent>
        </Select>
        <Select value={testModuleFilter} onValueChange={onModuleFilterChange}>
          <SelectTrigger className="w-[150px] h-8 text-[12px]"><SelectValue placeholder="Module" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Modules</SelectItem>
            {uniqueModules.map(([id, label]) => (
              <SelectItem key={id} value={id}>{label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={testPriorityFilter} onValueChange={onPriorityFilterChange}>
          <SelectTrigger className="w-[130px] h-8 text-[12px]"><SelectValue placeholder="Priority" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Priority</SelectItem>
            <SelectItem value="smoke">Smoke</SelectItem>
            <SelectItem value="regression">Regression</SelectItem>
            <SelectItem value="sanity">Sanity</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-gray-50 dark:bg-gray-800/80">
              <TableHead className="text-[11px] font-semibold w-[70px]">ID</TableHead>
              <TableHead className="text-[11px] font-semibold">Description</TableHead>
              <TableHead className="text-[11px] font-semibold w-[100px]">Class</TableHead>
              <TableHead className="text-[11px] font-semibold w-[90px]">Module</TableHead>
              <TableHead className="text-[11px] font-semibold w-[80px]">Priority</TableHead>
              <TableHead className="text-[11px] font-semibold w-[70px]">Status</TableHead>
              <TableHead className="text-[11px] font-semibold w-[70px]">Last Run</TableHead>
              <TableHead className="text-[11px] font-semibold w-[60px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {tests.map((t) => (
              <TableRow key={t.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                <TableCell className="text-[12px] font-mono font-semibold text-gray-800 dark:text-gray-100">{t.id}</TableCell>
                <TableCell className="text-[12px] text-gray-700 dark:text-gray-200 max-w-[250px]">
                  <div className="truncate">{t.description}</div>
                  {t.error && <div className="text-[10px] text-red-500 dark:text-red-400 mt-0.5 truncate">{t.error}</div>}
                </TableCell>
                <TableCell className="text-[11px] text-gray-500 dark:text-gray-400 font-mono">{t.className}</TableCell>
                <TableCell className="text-[11px] text-gray-600 dark:text-gray-300">{t.moduleName}</TableCell>
                <TableCell>
                  <span className={`inline-flex items-center gap-0.5 text-[10px] font-medium px-1.5 py-0.5 rounded-full ${priorityConfig[t.priority].color}`}>
                    {priorityConfig[t.priority].label}
                  </span>
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className={`text-[10px] px-1.5 py-0 border-0 ${t.status === 'active' ? 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900/30' : t.status === 'draft' ? 'text-blue-600 bg-blue-100 dark:text-blue-400 dark:bg-blue-900/30' : 'text-gray-400 bg-gray-100 dark:text-gray-500 dark:bg-gray-800'}`}>
                    {t.status}
                  </Badge>
                </TableCell>
                <TableCell>
                  {t.lastResult === 'passed' && <CheckCircle2 className="size-4 text-green-500" />}
                  {t.lastResult === 'failed' && <XCircle className="size-4 text-red-500" />}
                  {t.lastResult === 'not-run' && <Circle className="size-4 text-gray-300 dark:text-gray-600" />}
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-1">
                    <Button variant="ghost" size="icon" className="size-7 text-gray-400 hover:text-blue-600 cursor-pointer" onClick={() => onEditTest(t)} title="Edit">
                      <Pencil className="size-3.5" />
                    </Button>
                    <Button variant="ghost" size="icon" className="size-7 text-gray-400 hover:text-red-600 cursor-pointer" onClick={() => onDeleteTest(t)} title="Delete">
                      <Trash2 className="size-3.5" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
            {tests.length === 0 && (
              <TableRow>
                <TableCell colSpan={8} className="text-center py-8 text-[13px] text-gray-400 dark:text-gray-500">No test cases found</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}

// ─── ADMIN MODULES VIEW ──────────────────────────────────
function AdminModules({
  modules, onAddModule, onEditModule, onDeleteModule, onMoveModule,
}: {
  modules: AdminModule[]
  onAddModule: () => void
  onEditModule: (m: AdminModule) => void
  onDeleteModule: (m: AdminModule) => void
  onMoveModule: (id: string, dir: 'up' | 'down') => void
}) {
  const parentModules = modules.filter((m) => !m.parentId)
  const childModules = modules.filter((m) => m.parentId)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-[18px] font-semibold text-gray-800 dark:text-gray-100">Module Management</h2>
          <p className="text-[13px] text-gray-500 dark:text-gray-400 mt-0.5">Configure sidebar navigation structure</p>
        </div>
        <Button onClick={onAddModule} className="bg-red-600 hover:bg-red-700 text-white text-[13px] gap-1.5 cursor-pointer">
          <Plus className="size-4" /> Add Module
        </Button>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-gray-50 dark:bg-gray-800/80">
              <TableHead className="text-[11px] font-semibold w-[40px]"></TableHead>
              <TableHead className="text-[11px] font-semibold">Module ID</TableHead>
              <TableHead className="text-[11px] font-semibold">Label</TableHead>
              <TableHead className="text-[11px] font-semibold w-[120px]">Parent</TableHead>
              <TableHead className="text-[11px] font-semibold w-[60px] text-center">Tests</TableHead>
              <TableHead className="text-[11px] font-semibold w-[60px] text-center">Badge</TableHead>
              <TableHead className="text-[11px] font-semibold w-[70px]">Status</TableHead>
              <TableHead className="text-[11px] font-semibold w-[90px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {[...parentModules, ...childModules].map((m, idx) => (
              <TableRow key={m.id} className={`${m.parentId ? 'bg-gray-50/50 dark:bg-gray-900/30' : ''} hover:bg-gray-50 dark:hover:bg-gray-800/50`}>
                <TableCell className="text-[12px] text-gray-400 font-mono pl-6">
                  {m.parentId && <span className="text-gray-300 dark:text-gray-600">└</span>}
                </TableCell>
                <TableCell className="text-[12px] font-mono text-gray-600 dark:text-gray-300">{m.id}</TableCell>
                <TableCell className="text-[12px] font-medium text-gray-800 dark:text-gray-100">{m.parentId && <span className="text-gray-400 mr-2">↳</span>}{m.label}</TableCell>
                <TableCell className="text-[11px] text-gray-500 dark:text-gray-400">{m.parentLabel || '—'}</TableCell>
                <TableCell className="text-[12px] text-center text-gray-600 dark:text-gray-300">{m.testCount}</TableCell>
                <TableCell className="text-center text-[11px]">{m.badge || '—'}</TableCell>
                <TableCell>
                  <Badge variant="outline" className={`text-[10px] px-1.5 py-0 border-0 ${m.status === 'active' ? 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900/30' : m.status === 'draft' ? 'text-blue-600 bg-blue-100 dark:text-blue-400 dark:bg-blue-900/30' : 'text-gray-400 bg-gray-100 dark:text-gray-500 dark:bg-gray-800'}`}>
                    {m.status}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-0.5">
                    <Button variant="ghost" size="icon" className="size-7 text-gray-400 hover:text-gray-600 cursor-pointer" onClick={() => onMoveModule(m.id, 'up')} disabled={idx === 0} title="Move up">
                      <ArrowUp className="size-3" />
                    </Button>
                    <Button variant="ghost" size="icon" className="size-7 text-gray-400 hover:text-gray-600 cursor-pointer" onClick={() => onMoveModule(m.id, 'down')} disabled={idx === modules.length - 1} title="Move down">
                      <ArrowDown className="size-3" />
                    </Button>
                    <Button variant="ghost" size="icon" className="size-7 text-gray-400 hover:text-blue-600 cursor-pointer" onClick={() => onEditModule(m)} title="Edit">
                      <Pencil className="size-3.5" />
                    </Button>
                    <Button variant="ghost" size="icon" className="size-7 text-gray-400 hover:text-red-600 cursor-pointer" onClick={() => onDeleteModule(m)} title="Delete">
                      <Trash2 className="size-3.5" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}

// ─── ADMIN ENVIRONMENTS VIEW ─────────────────────────────
function AdminEnvironments({
  environments, onAddEnv, onEditEnv, onDeleteEnv, onToggleEnv,
}: {
  environments: Environment[]
  onAddEnv: () => void
  onEditEnv: (e: Environment) => void
  onDeleteEnv: (e: Environment) => void
  onToggleEnv: (id: string) => void
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-[18px] font-semibold text-gray-800 dark:text-gray-100">Environments</h2>
          <p className="text-[13px] text-gray-500 dark:text-gray-400 mt-0.5">Configure test execution environments</p>
        </div>
        <Button onClick={onAddEnv} className="bg-red-600 hover:bg-red-700 text-white text-[13px] gap-1.5 cursor-pointer">
          <Plus className="size-4" /> Add Environment
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {environments.map((env) => (
          <div key={env.id} className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 hover:shadow-sm transition-shadow">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${env.color} ${env.status === 'active' ? 'animate-pulse' : 'opacity-40'}`} />
                <span className="text-[14px] font-semibold text-gray-800 dark:text-gray-100">{env.name}</span>
              </div>
              <Badge variant="outline" className={`text-[10px] px-1.5 py-0 border-0 ${env.status === 'active' ? 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900/30' : 'text-gray-400 bg-gray-100 dark:text-gray-500 dark:bg-gray-800'}`}>
                {env.status}
              </Badge>
            </div>
            <div className="space-y-1.5 text-[12px]">
              <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
                <Globe className="size-3" />
                <span className="truncate">{env.baseUrl}</span>
              </div>
              <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
                <Monitor className="size-3" />
                <span>{env.browser}</span>
              </div>
              {env.lastUsed && (
                <div className="flex items-center gap-2 text-gray-400 dark:text-gray-500">
                  <Clock className="size-3" />
                  <span>Last used: {env.lastUsed}</span>
                </div>
              )}
            </div>
            <div className="flex items-center gap-1 mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
              <Button variant="ghost" size="sm" onClick={() => onToggleEnv(env.id)} className="h-7 text-[11px] gap-1 cursor-pointer text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200">
                {env.status === 'active' ? 'Deactivate' : 'Activate'}
              </Button>
              <Button variant="ghost" size="sm" onClick={() => onEditEnv(env)} className="h-7 text-[11px] gap-1 cursor-pointer text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400">
                <Pencil className="size-3" /> Edit
              </Button>
              <Button variant="ghost" size="sm" onClick={() => onDeleteEnv(env)} className="h-7 text-[11px] gap-1 cursor-pointer text-gray-500 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400">
                <Trash2 className="size-3" /> Delete
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── ADMIN USERS VIEW ────────────────────────────────────
function AdminUsers({
  users, modules, onAddUser, onEditUser, onDeleteUser, onToggleUser,
}: {
  users: AdminUser[]
  modules: AdminModule[]
  onAddUser: () => void
  onEditUser: (u: AdminUser) => void
  onDeleteUser: (u: AdminUser) => void
  onToggleUser: (id: string) => void
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-[18px] font-semibold text-gray-800 dark:text-gray-100">User Management</h2>
          <p className="text-[13px] text-gray-500 dark:text-gray-400 mt-0.5">Manage users, roles, and permissions</p>
        </div>
        <Button onClick={onAddUser} className="bg-red-600 hover:bg-red-700 text-white text-[13px] gap-1.5 cursor-pointer">
          <Plus className="size-4" /> Add User
        </Button>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-gray-50 dark:bg-gray-800/80">
              <TableHead className="text-[11px] font-semibold">User</TableHead>
              <TableHead className="text-[11px] font-semibold w-[100px]">Role</TableHead>
              <TableHead className="text-[11px] font-semibold w-[80px]">Status</TableHead>
              <TableHead className="text-[11px] font-semibold">Module Access</TableHead>
              <TableHead className="text-[11px] font-semibold w-[150px]">Last Login</TableHead>
              <TableHead className="text-[11px] font-semibold w-[90px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {users.map((u) => (
              <TableRow key={u.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                <TableCell>
                  <div className="flex items-center gap-2">
                    <Avatar className="size-7">
                      <AvatarFallback className="text-[10px] bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                        {u.name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <div className="text-[12px] font-medium text-gray-800 dark:text-gray-100">{u.name}</div>
                      <div className="text-[11px] text-gray-500 dark:text-gray-400">{u.email}</div>
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <span className={`inline-flex items-center text-[10px] font-medium px-1.5 py-0.5 rounded-full ${roleConfig[u.role]?.color || 'text-gray-500 bg-gray-100'}`}>
                    {roleConfig[u.role]?.label || u.role}
                  </span>
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className={`text-[10px] px-1.5 py-0 border-0 ${u.status === 'active' ? 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900/30' : 'text-gray-400 bg-gray-100 dark:text-gray-500 dark:bg-gray-800'}`}>
                    {u.status}
                  </Badge>
                </TableCell>
                <TableCell className="text-[11px] text-gray-500 dark:text-gray-400">
                  {u.moduleAccess.includes('all') ? (
                    <span className="text-green-600 dark:text-green-400 font-medium">All Modules</span>
                  ) : (
                    <span className="truncate">{u.moduleAccess.length} module{u.moduleAccess.length !== 1 ? 's' : ''}</span>
                  )}
                </TableCell>
                <TableCell className="text-[11px] text-gray-500 dark:text-gray-400">{u.lastLogin || '—'}</TableCell>
                <TableCell>
                  <div className="flex items-center gap-1">
                    <Button variant="ghost" size="icon" className="size-7 text-gray-400 hover:text-gray-600 cursor-pointer" onClick={() => onToggleUser(u.id)} title={u.status === 'active' ? 'Deactivate' : 'Activate'}>
                      {u.status === 'active' ? <XCircle className="size-3.5" /> : <CheckCircle2 className="size-3.5" />}
                    </Button>
                    <Button variant="ghost" size="icon" className="size-7 text-gray-400 hover:text-blue-600 cursor-pointer" onClick={() => onEditUser(u)} title="Edit">
                      <Pencil className="size-3.5" />
                    </Button>
                    <Button variant="ghost" size="icon" className="size-7 text-gray-400 hover:text-red-600 cursor-pointer" onClick={() => onDeleteUser(u)} title="Delete">
                      <Trash2 className="size-3.5" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}

// ─── ADMIN SETTINGS VIEW ─────────────────────────────────
function AdminSettings({
  settings, onUpdateSetting,
}: {
  settings: SystemSetting[]
  onUpdateSetting: (id: string, value: string) => void
}) {
  const categories = useMemo(() => {
    const cats = new Map<string, SystemSetting[]>()
    for (const s of settings) {
      if (!cats.has(s.category)) cats.set(s.category, [])
      cats.get(s.category)!.push(s)
    }
    return Array.from(cats.entries())
  }, [settings])

  const categoryIcons: Record<string, React.ReactNode> = {
    Execution: <Cpu className="size-4" />,
    Notifications: <Bell className="size-4" />,
    System: <Database className="size-4" />,
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-[18px] font-semibold text-gray-800 dark:text-gray-100">Settings</h2>
        <p className="text-[13px] text-gray-500 dark:text-gray-400 mt-0.5">System configuration and integrations</p>
      </div>

      {categories.map(([category, cats]) => (
        <div key={category} className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-100 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/80">
            <span className="text-gray-500 dark:text-gray-400">{categoryIcons[category]}</span>
            <span className="text-[13px] font-semibold text-gray-700 dark:text-gray-200">{category}</span>
            <span className="text-[11px] text-gray-400 dark:text-gray-500 ml-auto">{cats.length} settings</span>
          </div>
          <div className="divide-y divide-gray-100 dark:divide-gray-700">
            {cats.map((setting) => (
              <div key={setting.id} className="flex items-center gap-4 px-4 py-3">
                <div className="flex-1 min-w-0">
                  <div className="text-[12px] font-medium text-gray-700 dark:text-gray-200">{setting.label}</div>
                  <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5">{setting.description}</div>
                  <div className="text-[10px] text-gray-400 dark:text-gray-500 font-mono mt-1">{setting.key}</div>
                </div>
                <div className="w-64 shrink-0">
                  {setting.type === 'boolean' ? (
                    <label className="flex items-center gap-2 cursor-pointer">
                      <Checkbox
                        checked={setting.value === 'true'}
                        onCheckedChange={(v) => onUpdateSetting(setting.id, v === true ? 'true' : 'false')}
                        className="size-4"
                      />
                      <span className="text-[11px] text-gray-600 dark:text-gray-300">{setting.value === 'true' ? 'Enabled' : 'Disabled'}</span>
                    </label>
                  ) : setting.type === 'select' ? (
                    <Select value={setting.value} onValueChange={(v) => onUpdateSetting(setting.id, v)}>
                      <SelectTrigger className="h-8 text-[12px]"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="debug">Debug</SelectItem>
                        <SelectItem value="info">Info</SelectItem>
                        <SelectItem value="warn">Warning</SelectItem>
                        <SelectItem value="error">Error</SelectItem>
                      </SelectContent>
                    </Select>
                  ) : (
                    <Input
                      value={setting.value}
                      onChange={(e) => onUpdateSetting(setting.id, e.target.value)}
                      type={setting.type === 'number' ? 'number' : 'text'}
                      className="h-8 text-[12px] bg-gray-50 dark:bg-gray-700/50"
                    />
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

// ─── ADMIN BUG REPORTS VIEW ──────────────────────────────
function AdminBugReports({
  reports,
  onUpdateStatus,
}: {
  reports: BugReport[]
  onUpdateStatus: (id: string, status: BugReport['status']) => void
}) {
  const [filter, setFilter] = useState<string>('all')
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [replyText, setReplyText] = useState('')
  const [replyingTo, setReplyingTo] = useState<string | null>(null)
  const [localReports, setLocalReports] = useState<BugReport[]>(reports)

  useEffect(() => {
    setLocalReports(reports)
  }, [reports])

  // Mark reports as read by admin when expanded
  useEffect(() => {
    if (expandedId) {
      markReportReadByAdmin(expandedId)
    }
  }, [expandedId])

  const handleSendReply = useCallback((reportId: string) => {
    if (!replyText.trim()) return
    const updated = addReplyToReport(reportId, { authorName: 'Admin', authorRole: 'admin', message: replyText.trim() })
    if (updated) {
      setLocalReports((prev) => prev.map((r) => r.id === reportId ? { ...r, replies: updated.replies, updatedAt: updated.updatedAt } : r))
    }
    setReplyText('')
    setReplyingTo(null)
  }, [replyText])

  const filtered = useMemo(() => {
    if (filter === 'all') return localReports
    return localReports.filter((r) => r.status === filter)
  }, [localReports, filter])

  const openCount = localReports.filter((r) => r.status === 'open').length
  const inProgressCount = localReports.filter((r) => r.status === 'in-progress').length
  const fixedCount = localReports.filter((r) => r.status === 'fixed').length

  const statusConfig: Record<string, { label: string; color: string; dot: string }> = {
    'open': { label: 'Open', color: 'text-orange-700 bg-orange-100 dark:text-orange-300 dark:bg-orange-900/40', dot: 'bg-orange-500' },
    'in-progress': { label: 'In Progress', color: 'text-blue-700 bg-blue-100 dark:text-blue-300 dark:bg-blue-900/40', dot: 'bg-blue-500' },
    'fixed': { label: 'Fixed', color: 'text-green-700 bg-green-100 dark:text-green-300 dark:bg-green-900/40', dot: 'bg-green-500' },
  }

  const priorityConfig: Record<string, { label: string; color: string }> = {
    'high': { label: 'High', color: 'text-red-700 bg-red-100 dark:text-red-300 dark:bg-red-900/40' },
    'medium': { label: 'Medium', color: 'text-orange-700 bg-orange-100 dark:text-orange-300 dark:bg-orange-900/40' },
    'low': { label: 'Low', color: 'text-green-700 bg-green-100 dark:text-green-300 dark:bg-green-900/40' },
  }

  const formatDate = (iso: string) => {
    try {
      const d = new Date(iso)
      return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
    } catch {
      return iso
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-[18px] font-semibold text-gray-800 dark:text-gray-100">Bug Reports</h2>
          <p className="text-[13px] text-gray-500 dark:text-gray-400 mt-0.5">Issues reported by users from test runs</p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-3">
        <StatCard label="Total Reports" value={localReports.length} sub="all time" color="blue" />
        <div className={`${openCount > 0 ? 'bg-orange-50 dark:bg-orange-900/20 border-orange-100 dark:border-orange-800/50' : 'bg-gray-50 dark:bg-gray-800 border-gray-100 dark:border-gray-700'} rounded-lg p-3.5 border`}>
          <div className="text-[11px] text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wider">Open</div>
          <div className={`text-xl font-bold mt-1 ${openCount > 0 ? 'text-orange-700 dark:text-orange-400' : 'text-gray-500 dark:text-gray-400'}`}>{openCount}</div>
        </div>
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3.5 border border-blue-100 dark:border-blue-800/50">
          <div className="text-[11px] text-blue-600 dark:text-blue-400 font-medium uppercase tracking-wider">In Progress</div>
          <div className="text-xl font-bold text-blue-700 dark:text-blue-400 mt-1">{inProgressCount}</div>
        </div>
        <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3.5 border border-green-100 dark:border-green-800/50">
          <div className="text-[11px] text-green-600 dark:text-green-400 font-medium uppercase tracking-wider">Fixed</div>
          <div className="text-xl font-bold text-green-700 dark:text-green-400 mt-1">{fixedCount}</div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-1.5">
        {(['all', 'open', 'in-progress', 'fixed'] as const).map((f) => {
          const count = f === 'all' ? localReports.length : f === 'open' ? openCount : f === 'in-progress' ? inProgressCount : fixedCount
          return (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-md text-[12px] font-medium transition-colors cursor-pointer ${
                filter === f
                  ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                  : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
              }`}
            >
              {f === 'all' ? 'All' : f === 'in-progress' ? 'In Progress' : f.charAt(0).toUpperCase() + f.slice(1)} ({count})
            </button>
          )
        })}
      </div>

      {/* Reports List */}
      {filtered.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-8 text-center">
          <Inbox className="size-10 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
          <p className="text-[14px] text-gray-500 dark:text-gray-400 font-medium">
            {localReports.length === 0 ? 'No bug reports yet' : 'No reports match this filter'}
          </p>
          <p className="text-[12px] text-gray-400 dark:text-gray-500 mt-1">
            {localReports.length === 0 ? 'Bug reports from users will appear here' : 'Try a different filter'}
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((report) => {
            const sCfg = statusConfig[report.status]
            const pCfg = priorityConfig[report.priority]
            const sla = getSLAStatus(report.priority, report.createdAt, report.status)
            const isExpanded = expandedId === report.id
            return (
              <div
                key={report.id}
                className={`bg-white dark:bg-gray-800 rounded-lg border transition-all cursor-pointer ${
                  report.status === 'open'
                    ? 'border-orange-200 dark:border-orange-800/40 hover:border-orange-300 dark:hover:border-orange-700/60'
                    : report.status === 'in-progress'
                      ? 'border-blue-200 dark:border-blue-800/40 hover:border-blue-300 dark:hover:border-blue-700/60'
                      : 'border-green-200 dark:border-green-800/40 hover:border-green-300 dark:hover:border-green-700/60 opacity-70'
                } ${isExpanded ? 'shadow-sm' : ''}`}
                onClick={() => setExpandedId(isExpanded ? null : report.id)}
              >
                <div className="flex items-center gap-3 px-4 py-3">
                  {/* Status dot */}
                  <div className={`w-2.5 h-2.5 rounded-full shrink-0 ${sCfg.dot} ${report.status === 'open' ? 'animate-pulse' : ''}`} />

                  {/* ID + Description */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-[12px] font-mono font-semibold text-gray-800 dark:text-gray-100">{report.id}</span>
                      <span className="text-[12px] text-gray-400 dark:text-gray-500">—</span>
                      <span className="text-[12px] text-gray-700 dark:text-gray-200 truncate">{report.testDescription}</span>
                    </div>
                    <div className="flex items-center gap-2 mt-0.5 text-[11px] text-gray-500 dark:text-gray-400">
                      <span className="font-mono">{report.testId}</span>
                      <span>in</span>
                      <span>{report.moduleName}</span>
                      <span>•</span>
                      <span>{report.reporterName}</span>
                    </div>
                  </div>

                  {/* SLA Badge */}
                  <span className={`inline-flex items-center text-[10px] font-medium px-1.5 py-0.5 rounded-full shrink-0 ${sla.color}`}>
                    {sla.label === 'Overdue' ? '⚠️' : sla.label === 'At Risk' ? '⏰' : '✅'} {sla.remaining}
                  </span>

                  {/* Priority badge */}
                  <span className={`inline-flex items-center text-[10px] font-medium px-1.5 py-0.5 rounded-full shrink-0 ${pCfg.color}`}>
                    {report.priority === 'high' ? '🔴' : report.priority === 'medium' ? '🟡' : '🟢'} {pCfg.label}
                  </span>

                  {/* Status badge */}
                  <Badge variant="outline" className={`text-[10px] px-1.5 py-0 border-0 shrink-0 ${sCfg.color}`}>
                    {sCfg.label}
                  </Badge>

                  {/* Replies count */}
                  {(report.replies?.length ?? 0) > 0 && (
                    <span className="text-[10px] text-gray-400 shrink-0 flex items-center gap-0.5">
                      💬 {report.replies.length}
                    </span>
                  )}

                  {/* Date */}
                  <span className="text-[10px] text-gray-400 dark:text-gray-500 shrink-0 w-28 text-right">
                    {formatDate(report.createdAt)}
                  </span>

                  {/* Chevron */}
                  <ChevronDown className={`size-4 text-gray-400 shrink-0 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                </div>

                {/* Expanded Detail */}
                {isExpanded && (
                  <div className="px-4 pb-4 border-t border-gray-100 dark:border-gray-700 pt-3 space-y-3" onClick={(e) => e.stopPropagation()}>
                    {/* Error */}
                    <div>
                      <div className="text-[11px] text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wider mb-1">Error Message</div>
                      <div className="bg-red-50 dark:bg-red-900/15 rounded-md p-2.5 text-[12px] text-red-600 dark:text-red-400 font-mono break-all border border-red-100 dark:border-red-800/30">
                        {report.error}
                      </div>
                    </div>

                    {/* User Note */}
                    {report.userNote && (
                      <div>
                        <div className="text-[11px] text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wider mb-1">Reporter&apos;s Note</div>
                        <div className="bg-gray-50 dark:bg-gray-900 rounded-md p-2.5 text-[12px] text-gray-700 dark:text-gray-200 border border-gray-100 dark:border-gray-700">
                          {report.userNote}
                        </div>
                      </div>
                    )}

                    {/* SLA Detail */}
                    <div className="flex items-center gap-3">
                      <div className={`inline-flex items-center text-[11px] font-medium px-2 py-1 rounded-full ${sla.color}`}>
                        {sla.label === 'Overdue' ? '⚠️' : sla.label === 'At Risk' ? '⏰' : '✅'} SLA: {sla.remaining}
                      </div>
                      <span className="text-[11px] text-gray-400">
                        Priority {report.priority}: {report.priority === 'high' ? '24h' : report.priority === 'medium' ? '48h' : '7 days'} resolution target
                      </span>
                    </div>

                    {/* Replies Thread */}
                    {(report.replies?.length ?? 0) > 0 && (
                      <div>
                        <div className="text-[11px] text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wider mb-2">Conversation ({report.replies.length})</div>
                        <div className="space-y-2 max-h-48 overflow-y-auto">
                          {report.replies.map((reply) => (
                            <div key={reply.id} className={`rounded-md p-2.5 border ${
                              reply.authorRole === 'admin'
                                ? 'bg-red-50 dark:bg-red-900/10 border-red-100 dark:border-red-800/30'
                                : 'bg-blue-50 dark:bg-blue-900/10 border-blue-100 dark:border-blue-800/30'
                            }`}>
                              <div className="flex items-center gap-2 mb-1">
                                <span className={`text-[11px] font-semibold ${reply.authorRole === 'admin' ? 'text-red-700 dark:text-red-400' : 'text-blue-700 dark:text-blue-400'}`}>
                                  {reply.authorRole === 'admin' ? '👤 Admin' : `🧑 ${reply.authorName}`}
                                </span>
                                <span className="text-[10px] text-gray-400">{formatDate(reply.createdAt)}</span>
                              </div>
                              <div className="text-[12px] text-gray-700 dark:text-gray-200">{reply.message}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Reply Box */}
                    <div>
                      {replyingTo === report.id ? (
                        <div className="flex items-end gap-2">
                          <textarea
                            value={replyText}
                            onChange={(e) => setReplyText(e.target.value)}
                            placeholder="Type your reply..."
                            rows={2}
                            className="flex-1 px-3 py-2 text-[12px] rounded-md border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/50 text-gray-800 dark:text-gray-100 resize-none focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500"
                          />
                          <Button
                            size="sm"
                            onClick={() => handleSendReply(report.id)}
                            disabled={!replyText.trim()}
                            className="bg-red-600 hover:bg-red-700 text-white text-[12px] cursor-pointer shrink-0"
                          >
                            <Send className="size-3 mr-1" /> Send Reply
                          </Button>
                        </div>
                      ) : (
                        <button
                          onClick={() => { setReplyingTo(report.id); setReplyText('') }}
                          className="text-[12px] text-red-600 hover:text-red-700 font-medium cursor-pointer flex items-center gap-1"
                        >
                          <Send className="size-3.5" /> Reply
                        </button>
                      )}
                    </div>

                    {/* Meta info */}
                    <div className="flex items-center gap-4 text-[11px] text-gray-400 dark:text-gray-500">
                      <span>Reported by <strong className="text-gray-600 dark:text-gray-300">{report.reporterName}</strong> ({report.reporterEmail})</span>
                      <span>Updated: {formatDate(report.updatedAt)}</span>
                    </div>

                    {/* Status Actions */}
                    <div className="flex items-center gap-2 pt-1">
                      <span className="text-[11px] text-gray-500 dark:text-gray-400 font-medium mr-1">Update Status:</span>
                      {(['open', 'in-progress', 'fixed'] as const).map((s) => (
                        <button
                          key={s}
                          onClick={(e) => { e.stopPropagation(); onUpdateStatus(report.id, s) }}
                          disabled={report.status === s}
                          className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-all cursor-pointer border ${
                            report.status === s
                              ? statusConfig[s].color + ' border-current/20'
                              : 'border-gray-200 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed'
                          }`}
                        >
                          {statusConfig[s].label}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

// ─── FORMS ───────────────────────────────────────────────

function TestForm({ test, modules, onSave, onCancel }: { test: AdminTest | null; modules: [string, string][]; onSave: (t: Partial<AdminTest>) => void; onCancel: () => void }) {
  const [id, setId] = useState(test?.id || '')
  const [description, setDescription] = useState(test?.description || '')
  const [className, setClassName] = useState(test?.className || '')
  const [priority, setPriority] = useState<string>(test?.priority || 'sanity')
  const [status, setStatus] = useState<string>(test?.status || 'draft')
  const [moduleId, setModuleId] = useState(test?.moduleId || 'tax-rate')
  const [steps, setSteps] = useState(test?.steps || '')
  const [expected, setExpected] = useState(test?.expected || '')
  const [error, setError] = useState(test?.error || '')

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label className="text-[12px]">Test ID</Label>
          <Input value={id} onChange={(e) => setId(e.target.value)} disabled={!!test} className="h-9 text-[12px] font-mono bg-gray-50 dark:bg-gray-700/50" placeholder="T01" />
        </div>
        <div className="space-y-1.5">
          <Label className="text-[12px]">Test Class</Label>
          <Input value={className} onChange={(e) => setClassName(e.target.value)} className="h-9 text-[12px] font-mono" placeholder="TestCreate" />
        </div>
      </div>
      <div className="space-y-1.5">
        <Label className="text-[12px]">Description</Label>
        <Input value={description} onChange={(e) => setDescription(e.target.value)} className="h-9 text-[12px]" placeholder="What does this test verify?" />
      </div>
      <div className="grid grid-cols-3 gap-3">
        <div className="space-y-1.5">
          <Label className="text-[12px]">Priority</Label>
          <Select value={priority} onValueChange={setPriority}>
            <SelectTrigger className="h-9 text-[12px]"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="smoke">Smoke</SelectItem>
              <SelectItem value="regression">Regression</SelectItem>
              <SelectItem value="sanity">Sanity</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1.5">
          <Label className="text-[12px]">Status</Label>
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger className="h-9 text-[12px]"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="draft">Draft</SelectItem>
              <SelectItem value="disabled">Disabled</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1.5">
          <Label className="text-[12px]">Module</Label>
          <Select value={moduleId} onValueChange={setModuleId}>
            <SelectTrigger className="h-9 text-[12px]"><SelectValue /></SelectTrigger>
            <SelectContent>
              {modules.map(([id, label]) => (
                <SelectItem key={id} value={id}>{label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
      <div className="space-y-1.5">
        <Label className="text-[12px]">Test Steps (separated by →)</Label>
        <textarea value={steps} onChange={(e) => setSteps(e.target.value)} rows={3} className="w-full px-3 py-2 text-[12px] rounded-md border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/50 text-gray-800 dark:text-gray-100 resize-none focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500" placeholder="Click Add → Fill fields → Submit" />
      </div>
      <div className="space-y-1.5">
        <Label className="text-[12px]">Expected Result</Label>
        <textarea value={expected} onChange={(e) => setExpected(e.target.value)} rows={2} className="w-full px-3 py-2 text-[12px] rounded-md border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/50 text-gray-800 dark:text-gray-100 resize-none focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500" placeholder="What should happen?" />
      </div>
      {test?.error && (
        <div className="space-y-1.5">
          <Label className="text-[12px]">Known Error (optional)</Label>
          <Input value={error} onChange={(e) => setError(e.target.value)} className="h-9 text-[12px]" placeholder="Error message if known" />
        </div>
      )}
      <DialogFooter>
        <Button variant="outline" onClick={onCancel} className="cursor-pointer text-[12px]">Cancel</Button>
        <Button onClick={() => onSave({ id, description, className, priority: priority as TestPriority, status: status as AdminTest['status'], moduleId, steps, expected, error: error || undefined })} className="bg-red-600 hover:bg-red-700 text-white cursor-pointer text-[12px]">
          <Save className="size-3.5 mr-1" /> {test ? 'Update' : 'Create'} Test
        </Button>
      </DialogFooter>
    </div>
  )
}

function ModuleForm({ module, onSave, onCancel }: { module: AdminModule | null; onSave: (m: Partial<AdminModule>) => void; onCancel: () => void }) {
  const [id, setId] = useState(module?.id || '')
  const [label, setLabel] = useState(module?.label || '')
  const [parentId, setParentId] = useState(module?.parentId || '')
  const [badge, setBadge] = useState(module?.badge || '')
  const [status, setStatus] = useState(module?.status || 'active')

  return (
    <div className="space-y-4">
      <div className="space-y-1.5">
        <Label className="text-[12px]">Module ID (unique identifier)</Label>
        <Input value={id} onChange={(e) => setId(e.target.value)} disabled={!!module} className="h-9 text-[12px] font-mono bg-gray-50 dark:bg-gray-700/50" placeholder="tax-rate" />
      </div>
      <div className="space-y-1.5">
        <Label className="text-[12px]">Display Label</Label>
        <Input value={label} onChange={(e) => setLabel(e.target.value)} className="h-9 text-[12px]" placeholder="Tax Rate" />
      </div>
      <div className="space-y-1.5">
        <Label className="text-[12px]">Parent Module (optional — leave empty for top-level)</Label>
        <Input value={parentId} onChange={(e) => setParentId(e.target.value)} className="h-9 text-[12px] font-mono" placeholder="common-settings" />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label className="text-[12px]">Badge Text (optional)</Label>
          <Input value={badge} onChange={(e) => setBadge(e.target.value)} className="h-9 text-[12px]" placeholder="✅ 12/12" />
        </div>
        <div className="space-y-1.5">
          <Label className="text-[12px]">Status</Label>
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger className="h-9 text-[12px]"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="draft">Draft</SelectItem>
              <SelectItem value="disabled">Disabled</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={onCancel} className="cursor-pointer text-[12px]">Cancel</Button>
        <Button onClick={() => onSave({ id, label, parentId: parentId || undefined, badge: badge || undefined, status: status as AdminModule['status'] })} className="bg-red-600 hover:bg-red-700 text-white cursor-pointer text-[12px]">
          <Save className="size-3.5 mr-1" /> {module ? 'Update' : 'Create'} Module
        </Button>
      </DialogFooter>
    </div>
  )
}

function EnvironmentForm({ env, onSave, onCancel }: { env: Environment | null; onSave: (e: Partial<Environment>) => void; onCancel: () => void }) {
  const [name, setName] = useState(env?.name || '')
  const [baseUrl, setBaseUrl] = useState(env?.baseUrl || '')
  const [browser, setBrowser] = useState(env?.browser || 'Chrome')

  return (
    <div className="space-y-4">
      <div className="space-y-1.5">
        <Label className="text-[12px]">Environment Name</Label>
        <Input value={name} onChange={(e) => setName(e.target.value)} className="h-9 text-[12px]" placeholder="Staging" />
      </div>
      <div className="space-y-1.5">
        <Label className="text-[12px]">Base URL</Label>
        <Input value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} className="h-9 text-[12px] font-mono" placeholder="https://staging.rhythmerp.com" />
      </div>
      <div className="space-y-1.5">
        <Label className="text-[12px]">Default Browser</Label>
        <Select value={browser} onValueChange={setBrowser}>
          <SelectTrigger className="h-9 text-[12px]"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="Chrome">Chrome</SelectItem>
            <SelectItem value="Edge">Edge</SelectItem>
            <SelectItem value="Firefox">Firefox</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={onCancel} className="cursor-pointer text-[12px]">Cancel</Button>
        <Button onClick={() => onSave({ name, baseUrl, browser })} className="bg-red-600 hover:bg-red-700 text-white cursor-pointer text-[12px]">
          <Save className="size-3.5 mr-1" /> {env ? 'Update' : 'Create'} Environment
        </Button>
      </DialogFooter>
    </div>
  )
}

function UserForm({ user, onSave, onCancel }: { user: AdminUser | null; onSave: (u: Partial<AdminUser>) => void; onCancel: () => void }) {
  const [name, setName] = useState(user?.name || '')
  const [email, setEmail] = useState(user?.email || '')
  const [role, setRole] = useState(user?.role || 'tester')

  return (
    <div className="space-y-4">
      <div className="space-y-1.5">
        <Label className="text-[12px]">Full Name</Label>
        <Input value={name} onChange={(e) => setName(e.target.value)} className="h-9 text-[12px]" placeholder="John Doe" />
      </div>
      <div className="space-y-1.5">
        <Label className="text-[12px]">Email</Label>
        <Input value={email} onChange={(e) => setEmail(e.target.value)} type="email" disabled={!!user} className="h-9 text-[12px] bg-gray-50 dark:bg-gray-700/50" placeholder="user@rhythmerp.com" />
      </div>
      <div className="space-y-1.5">
        <Label className="text-[12px]">Role</Label>
        <Select value={role} onValueChange={setRole}>
          <SelectTrigger className="h-9 text-[12px]"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="admin">Admin</SelectItem>
            <SelectItem value="qa_lead">QA Lead</SelectItem>
            <SelectItem value="tester">Tester</SelectItem>
            <SelectItem value="viewer">Viewer</SelectItem>
            <SelectItem value="client">Client</SelectItem>
          </SelectContent>
        </Select>
        <p className="text-[10px] text-gray-400 dark:text-gray-500 mt-1">Module access and advanced permissions can be configured after creation.</p>
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={onCancel} className="cursor-pointer text-[12px]">Cancel</Button>
        <Button onClick={() => onSave({ name, email, role: role as AdminUser['role'] })} className="bg-red-600 hover:bg-red-700 text-white cursor-pointer text-[12px]">
          <Save className="size-3.5 mr-1" /> {user ? 'Update' : 'Create'} User
        </Button>
      </DialogFooter>
    </div>
  )
}
