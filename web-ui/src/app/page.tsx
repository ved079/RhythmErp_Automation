'use client'

import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import Link from 'next/link'
import { toast } from 'sonner'
import { fetchModules, folderToSidebarId, type ApiModule, type ApiSubModule } from '@/lib/api'
import {
  addBugReport,
  getBugReports,
  addReplyToReport,
  markReportReadByUser,
  getNotifications,
  markAllNotificationsRead,
  getUnreadNotificationCount,
  getScheduledRuns,
  addScheduledRun,
  deleteScheduledRun,
  updateScheduledRun,
  getSLAStatus,
  type BugReport,
  type Notification as NotifType,
  type ScheduledRun,
} from '@/lib/bug-reports'
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
  RefreshCw,
  MoreVertical,
  Eye,
  Pencil,
  ClipboardList,
  Clock,
  ChevronRight,
  ChevronLeft,
  ChevronDown,
  Play,
  Square,
  Terminal,
  X,
  Minimize2,
  CheckCircle2,
  XCircle,
  Circle,
  AlertTriangle,
  Loader2,
  User,
  Lock,
  LogOut,
  FileSpreadsheet,
  Globe,
  MoreHorizontal,
  ArrowLeft,
  RotateCcw,
  Menu,
  Sun,
  Moon,
  LayoutDashboard,
  GitCompare,
  Flame,
  ShieldCheck,
  Activity,
  TrendingUp,
  BarChart3,
  Zap,
  Shield,
  MessageSquare,
  Send,
  Bell,
  CalendarClock,
  Timer,
  Ticket,
} from 'lucide-react'

// ─── Types ───────────────────────────────────────────────
type TestPriority = 'smoke' | 'regression' | 'sanity'

interface SidebarModule {
  id: string
  label: string
  badge?: string
  badgeType?: 'success' | 'warning' | 'wip' | 'none'
  children?: SidebarModule[]
  defaultExpanded?: boolean
}

interface TestItem {
  id: string
  name: string
  status: 'passed' | 'failed' | 'pending' | 'running'
  duration: string
  priority?: TestPriority
}

interface TestSpecItem {
  id: string
  description: string
  status: 'passed' | 'failed' | 'not-run'
  duration: string
  steps: string
  expected: string
  error?: string
  priority?: TestPriority
}

interface TestClassGroup {
  className: string
  tests: TestSpecItem[]
}

interface AuthUser {
  id: string
  email: string
  name: string
  role: string
}

interface RunSnapshot {
  id: number
  date: string
  moduleId: string
  results: { testId: string; status: 'passed' | 'failed' }[]
  passed: number
  failed: number
  total: number
  duration: string
  rate: number
}

interface ModuleHealth {
  moduleId: string
  moduleName: string
  parentGroup?: string
  passRate: number
  totalTests: number
  passedTests: number
  failedTests: number
  lastRun: string
}

// ─── Helper: get priority ────────────────────────────────
function getPriority(id: string): TestPriority {
  if (['T01', 'T02', 'T10'].includes(id)) return 'smoke'
  if (['T03', 'T04', 'T05', 'T06', 'T09', 'T11'].includes(id)) return 'regression'
  return 'sanity'
}

function getStepsForTest(testId: string): string[] {
  for (const g of testSpecGroups) {
    const t = g.tests.find((x) => x.id === testId)
    if (t) return t.steps.split(' → ').map((s) => s.trim())
  }
  return []
}

// ─── Module Data (fetched from API) ────────────────────

// Full list of ALL sidebar modules (with or without tests).
// API data enriches these with real test counts.
const ALL_SIDEBAR_MODULES: SidebarModule[] = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'customer', label: 'Customer' },
  { id: 'farmer', label: 'Farmer' },
  { id: 'company-onboarding', label: 'Company Onboarding' },
  {
    id: 'common-settings',
    label: 'Common Settings',
    defaultExpanded: true,
    children: [
      { id: 'uom', label: 'UOM', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'uom-conversion', label: 'UOM Conversion', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'designation', label: 'Designation', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'bank', label: 'Bank', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'seasons', label: 'Seasons', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'hsn-sac', label: 'HSN SAC', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'error-code-master', label: 'Error Code Master', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'vehicle-master', label: 'Vehicle Master', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'tax-authority', label: 'Tax Authority', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'tax-rate', label: 'Tax Rate', badge: '📝 No tests', badgeType: 'none' as const },
    ],
  },
  {
    id: 'commodity-settings',
    label: 'Commodity Settings',
    children: [
      { id: 'crop-master', label: 'Crop Master', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'commodity-quality-param', label: 'Commodity Quality Param', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'quality-parameter-def', label: 'Quality Parameter Def', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'commodity-base-rate', label: 'Commodity Base Rate', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'commodity-master', label: 'Commodity Master', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'item-master', label: 'Item Master', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'services-master', label: 'Services Master', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'item-category', label: 'Item Category', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'item-group', label: 'Item Group', badge: '📝 No tests', badgeType: 'none' as const },
    ],
  },
  { id: 'finance-settings', label: 'Finance Settings' },
  { id: 'access', label: 'Access' },
  { id: 'my-tickets', label: 'My Tickets' },
]

/**
 * Build sidebar by merging real API test counts into the full module list.
 * Modules without tests keep the "📝 No tests" badge.
 */
function buildSidebarModules(apiModules: ApiModule[]): SidebarModule[] {
  // Deep clone the master list
  const sidebar: SidebarModule[] = JSON.parse(JSON.stringify(ALL_SIDEBAR_MODULES))

  // Build a lookup: sidebarId → test count from API
  const testCounts: Record<string, number> = {}
  for (const apiMod of apiModules) {
    for (const sub of apiMod.sub_modules) {
      const sid = folderToSidebarId(sub.name)
      testCounts[sid] = sub.tests.length
    }
    // Standalone modules
    if (apiMod.sub_modules.length === 0) {
      const sid = folderToSidebarId(apiMod.name)
      testCounts[sid] = 0
    }
  }

  // Update badges with real counts
  for (const mod of sidebar) {
    if (mod.children) {
      for (const child of mod.children) {
        const count = testCounts[child.id]
        if (count !== undefined) {
          if (count > 0) {
            child.badge = `${count} tests`
            child.badgeType = 'success'
          }
          // else keep "📝 No tests"
        }
      }
    }
  }

  return sidebar
}

const testSpecGroups: TestClassGroup[] = [
  {
    className: 'TestCreate',
    tests: [
      {
        id: 'T01',
        description: 'Create with all valid fields',
        status: 'passed',
        duration: '2:11',
        priority: 'smoke',
        steps: 'Click Add → Fill Name, Tax Type, Tax Authority → Select From/To Date, Revision Status → Submit',
        expected: 'Record created successfully, SweetAlert2 success toast',
      },
      {
        id: 'T02',
        description: 'Create with minimum fields',
        status: 'passed',
        duration: '1:45',
        priority: 'smoke',
        steps: 'Click Add → Fill Tax Rate Name → Submit',
        expected: 'Record created with default values',
      },
    ],
  },
  {
    className: 'TestEdit',
    tests: [
      {
        id: 'T04',
        description: 'Update existing record name',
        status: 'passed',
        duration: '1:30',
        priority: 'regression',
        steps: 'Search record → Click Edit → Change Name → Update',
        expected: 'Name updated, success alert',
      },
      {
        id: 'T05',
        description: 'Update with blank name',
        status: 'passed',
        duration: '0:55',
        priority: 'regression',
        steps: 'Search record → Click Edit → Clear Name → Update',
        expected: 'Validation error shown',
      },
      {
        id: 'T06',
        description: 'Update non-existent record',
        status: 'passed',
        duration: '0:32',
        priority: 'regression',
        steps: 'Search for non-existent name → Verify not in table',
        expected: 'Record not found',
      },
    ],
  },
  {
    className: 'TestSubTable',
    tests: [
      {
        id: 'T03',
        description: 'Add HSN row in sub-table',
        status: 'failed',
        duration: '—',
        priority: 'regression',
        steps: 'Click Add → Fill fields → Go to "Define Tax Rate Details" tab → Click Add → Select HSN Number → Enter Tax Rate → Submit',
        expected: 'Sub-table row added, record created',
        error: 'SubTableAddButton not found in DOM',
      },
      {
        id: 'T09',
        description: 'Submit with empty sub-table',
        status: 'failed',
        duration: '—',
        priority: 'regression',
        steps: 'Click Add → Fill header fields → Submit WITHOUT adding sub-table row',
        expected: 'Form should reject empty sub-table',
        error: 'Server accepts empty sub-table as success (wrong assertion)',
      },
    ],
  },
  {
    className: 'TestSearch',
    tests: [
      {
        id: 'T10',
        description: 'Search existing record',
        status: 'passed',
        duration: '1:15',
        priority: 'smoke',
        steps: 'Enter record name in search field → Verify record appears in table',
        expected: 'Matching record displayed in results',
      },
      {
        id: 'T11',
        description: 'Search non-existent record',
        status: 'passed',
        duration: '0:42',
        priority: 'regression',
        steps: 'Enter non-existent name → Verify "No records found" message',
        expected: 'No records displayed, empty state shown',
      },
    ],
  },
  {
    className: 'TestPagination',
    tests: [
      {
        id: 'T24',
        description: 'Verify pagination controls',
        status: 'passed',
        duration: '0:28',
        priority: 'sanity',
        steps: 'Navigate through page controls → Verify First, Prev, Next, Last buttons',
        expected: 'Pagination works correctly, correct records per page',
      },
    ],
  },
  {
    className: 'TestHistory',
    tests: [
      {
        id: 'T17',
        description: 'View history of existing record',
        status: 'passed',
        duration: '1:50',
        priority: 'sanity',
        steps: 'Click History icon → Verify popup opens with record history',
        expected: 'History popup displays with correct entries',
      },
      {
        id: 'T18',
        description: 'Search within history popup',
        status: 'passed',
        duration: '1:22',
        priority: 'sanity',
        steps: 'Open History popup → Enter search term → Verify filtered results',
        expected: 'History entries filtered correctly',
      },
    ],
  },
]

const initialTests: TestItem[] = testSpecGroups.flatMap((g) =>
  g.tests.map((t) => ({
    id: t.id,
    name: t.description,
    status: t.status === 'not-run' ? ('pending' as const) : (t.status as 'passed' | 'failed'),
    duration: t.duration === '—' ? '—' : t.duration,
    priority: t.priority,
  }))
)

const consoleLogs = [
  '[10:23:14] Navigating to Tax Rate page...',
  '[10:23:16] Page loaded. Found 3 records in table.',
  '[10:23:16] Clicking ADD button...',
  '[10:23:17] Form popup opened.',
  '[10:23:18] Filling Tax Rate Name: "Auto_Test_Demo"',
  '[10:23:19] Selecting Tax Type: "GST"',
  '[10:23:20] Selecting Tax Authority: "GST"',
  '[10:23:21] Setting From Date: "14/05/2026"',
  '[10:23:22] Setting To Date: "30/12/2099"',
  '[10:23:23] Selecting Revision Status: "Effective"',
  '[10:23:24] Clicking Submit button...',
  '[10:23:25] Success notification detected.',
  '[10:23:26] Verifying record in table...',
  '[10:23:27] Record "Auto_Test_Demo" found. Test PASSED.',
]

const recentRuns = [
  { date: '16 May 2026, 10:23 AM', duration: '4:32', passed: 17, failed: 3, rate: '85%' },
  { date: '15 May 2026, 03:45 PM', duration: '5:01', passed: 15, failed: 5, rate: '75%' },
  { date: '14 May 2026, 11:20 AM', duration: '4:10', passed: 18, failed: 2, rate: '90%' },
  { date: '13 May 2026, 09:15 AM', duration: '3:55', passed: 16, failed: 4, rate: '80%' },
  { date: '12 May 2026, 02:30 PM', duration: '6:22', passed: 20, failed: 0, rate: '100%' },
]

const bugRegistry = [
  { id: 'TR-001', desc: 'Edit button disabled for all rows', status: 'Known', tests: 'T08' },
  { id: 'TR-002', desc: 'SubTableAddButton not found', status: 'Open', tests: 'T03' },
  { id: 'TR-003', desc: 'Date fields have name=null', status: 'Known', tests: 'T16' },
  { id: 'TR-004', desc: 'Empty sub-table accepted on submit', status: 'Open', tests: 'T09' },
  { id: 'TR-005', desc: 'No success SweetAlert2 on form close', status: 'Known', tests: 'T01' },
]

// ─── Module Health Data (Feature 3) ─────────────────────
const moduleHealthData: ModuleHealth[] = [
  { moduleId: 'customer', moduleName: 'Customer', parentGroup: 'Standalone', passRate: 100, totalTests: 15, passedTests: 15, failedTests: 0, lastRun: '16 May 2026, 09:30 AM' },
  { moduleId: 'farmer', moduleName: 'Farmer', parentGroup: 'Standalone', passRate: 92, totalTests: 24, passedTests: 22, failedTests: 2, lastRun: '16 May 2026, 09:15 AM' },
  { moduleId: 'company-onboarding', moduleName: 'Company Onboarding', parentGroup: 'Standalone', passRate: 88, totalTests: 18, passedTests: 16, failedTests: 2, lastRun: '15 May 2026, 04:20 PM' },
  { moduleId: 'uom', moduleName: 'UOM', parentGroup: 'Common Settings', passRate: 100, totalTests: 8, passedTests: 8, failedTests: 0, lastRun: '16 May 2026, 08:45 AM' },
  { moduleId: 'uom-conversion', moduleName: 'UOM Conversion', parentGroup: 'Common Settings', passRate: 100, totalTests: 6, passedTests: 6, failedTests: 0, lastRun: '16 May 2026, 08:46 AM' },
  { moduleId: 'designation', moduleName: 'Designation', parentGroup: 'Common Settings', passRate: 100, totalTests: 5, passedTests: 5, failedTests: 0, lastRun: '15 May 2026, 03:10 PM' },
  { moduleId: 'bank', moduleName: 'Bank', parentGroup: 'Common Settings', passRate: 83, totalTests: 12, passedTests: 10, failedTests: 2, lastRun: '16 May 2026, 08:50 AM' },
  { moduleId: 'seasons', moduleName: 'Seasons', parentGroup: 'Common Settings', passRate: 100, totalTests: 7, passedTests: 7, failedTests: 0, lastRun: '14 May 2026, 10:00 AM' },
  { moduleId: 'hsn-sac', moduleName: 'HSN SAC', parentGroup: 'Common Settings', passRate: 100, totalTests: 12, passedTests: 12, failedTests: 0, lastRun: '16 May 2026, 08:30 AM' },
  { moduleId: 'error-code-master', moduleName: 'Error Code Master', parentGroup: 'Common Settings', passRate: 0, totalTests: 0, passedTests: 0, failedTests: 0, lastRun: '—' },
  { moduleId: 'vehicle-master', moduleName: 'Vehicle Master', parentGroup: 'Common Settings', passRate: 0, totalTests: 0, passedTests: 0, failedTests: 0, lastRun: '—' },
  { moduleId: 'tax-authority', moduleName: 'Tax Authority', parentGroup: 'Common Settings', passRate: 83, totalTests: 18, passedTests: 15, failedTests: 3, lastRun: '16 May 2026, 09:00 AM' },
  { moduleId: 'tax-rate', moduleName: 'Tax Rate', parentGroup: 'Common Settings', passRate: 85, totalTests: 20, passedTests: 17, failedTests: 3, lastRun: '16 May 2026, 10:23 AM' },
  { moduleId: 'crop-master', moduleName: 'Crop Master', parentGroup: 'Commodity Settings', passRate: 95, totalTests: 20, passedTests: 19, failedTests: 1, lastRun: '16 May 2026, 07:45 AM' },
  { moduleId: 'commodity-quality-param', moduleName: 'Commodity Quality Param', parentGroup: 'Commodity Settings', passRate: 78, totalTests: 9, passedTests: 7, failedTests: 2, lastRun: '15 May 2026, 02:00 PM' },
  { moduleId: 'quality-parameter-def', moduleName: 'Quality Parameter Def', parentGroup: 'Commodity Settings', passRate: 100, totalTests: 11, passedTests: 11, failedTests: 0, lastRun: '16 May 2026, 07:50 AM' },
  { moduleId: 'commodity-base-rate', moduleName: 'Commodity Base Rate', parentGroup: 'Commodity Settings', passRate: 88, totalTests: 8, passedTests: 7, failedTests: 1, lastRun: '15 May 2026, 11:30 AM' },
  { moduleId: 'commodity-master', moduleName: 'Commodity Master', parentGroup: 'Commodity Settings', passRate: 91, totalTests: 22, passedTests: 20, failedTests: 2, lastRun: '16 May 2026, 08:00 AM' },
  { moduleId: 'item-master', moduleName: 'Item Master', parentGroup: 'Commodity Settings', passRate: 100, totalTests: 16, passedTests: 16, failedTests: 0, lastRun: '16 May 2026, 08:10 AM' },
  { moduleId: 'services-master', moduleName: 'Services Master', parentGroup: 'Commodity Settings', passRate: 100, totalTests: 10, passedTests: 10, failedTests: 0, lastRun: '14 May 2026, 09:00 AM' },
  { moduleId: 'item-category', moduleName: 'Item Category', parentGroup: 'Commodity Settings', passRate: 100, totalTests: 8, passedTests: 8, failedTests: 0, lastRun: '14 May 2026, 09:05 AM' },
  { moduleId: 'item-group', moduleName: 'Item Group', parentGroup: 'Commodity Settings', passRate: 100, totalTests: 7, passedTests: 7, failedTests: 0, lastRun: '14 May 2026, 09:10 AM' },
  { moduleId: 'finance-settings', moduleName: 'Finance Settings', parentGroup: 'Standalone', passRate: 70, totalTests: 30, passedTests: 21, failedTests: 9, lastRun: '15 May 2026, 01:00 PM' },
  { moduleId: 'access', moduleName: 'Access', parentGroup: 'Standalone', passRate: 0, totalTests: 0, passedTests: 0, failedTests: 0, lastRun: '—' },
]

// ─── Initial Run History (Feature 5) ────────────────────
const initialRunHistory: RunSnapshot[] = [
  {
    id: 5,
    date: '12 May 2026, 02:30 PM',
    moduleId: 'tax-rate',
    results: [
      { testId: 'T01', status: 'passed' }, { testId: 'T02', status: 'passed' },
      { testId: 'T03', status: 'passed' }, { testId: 'T04', status: 'passed' },
      { testId: 'T05', status: 'passed' }, { testId: 'T06', status: 'passed' },
      { testId: 'T09', status: 'passed' }, { testId: 'T10', status: 'passed' },
      { testId: 'T11', status: 'passed' }, { testId: 'T17', status: 'passed' },
      { testId: 'T18', status: 'passed' }, { testId: 'T24', status: 'passed' },
    ],
    passed: 20, failed: 0, total: 20, duration: '6:22', rate: 100,
  },
  {
    id: 4,
    date: '13 May 2026, 09:15 AM',
    moduleId: 'tax-rate',
    results: [
      { testId: 'T01', status: 'passed' }, { testId: 'T02', status: 'passed' },
      { testId: 'T03', status: 'failed' }, { testId: 'T04', status: 'passed' },
      { testId: 'T05', status: 'failed' }, { testId: 'T06', status: 'passed' },
      { testId: 'T09', status: 'failed' }, { testId: 'T10', status: 'passed' },
      { testId: 'T11', status: 'passed' }, { testId: 'T17', status: 'passed' },
      { testId: 'T18', status: 'passed' }, { testId: 'T24', status: 'passed' },
    ],
    passed: 16, failed: 4, total: 20, duration: '3:55', rate: 80,
  },
  {
    id: 3,
    date: '14 May 2026, 11:20 AM',
    moduleId: 'tax-rate',
    results: [
      { testId: 'T01', status: 'passed' }, { testId: 'T02', status: 'passed' },
      { testId: 'T03', status: 'failed' }, { testId: 'T04', status: 'passed' },
      { testId: 'T05', status: 'passed' }, { testId: 'T06', status: 'passed' },
      { testId: 'T09', status: 'failed' }, { testId: 'T10', status: 'passed' },
      { testId: 'T11', status: 'passed' }, { testId: 'T17', status: 'passed' },
      { testId: 'T18', status: 'passed' }, { testId: 'T24', status: 'passed' },
    ],
    passed: 18, failed: 2, total: 20, duration: '4:10', rate: 90,
  },
  {
    id: 2,
    date: '15 May 2026, 03:45 PM',
    moduleId: 'tax-rate',
    results: [
      { testId: 'T01', status: 'passed' }, { testId: 'T02', status: 'failed' },
      { testId: 'T03', status: 'failed' }, { testId: 'T04', status: 'passed' },
      { testId: 'T05', status: 'passed' }, { testId: 'T06', status: 'passed' },
      { testId: 'T09', status: 'failed' }, { testId: 'T10', status: 'passed' },
      { testId: 'T11', status: 'failed' }, { testId: 'T17', status: 'passed' },
      { testId: 'T18', status: 'passed' }, { testId: 'T24', status: 'passed' },
    ],
    passed: 15, failed: 5, total: 20, duration: '5:01', rate: 75,
  },
  {
    id: 1,
    date: '16 May 2026, 10:23 AM',
    moduleId: 'tax-rate',
    results: [
      { testId: 'T01', status: 'passed' }, { testId: 'T02', status: 'passed' },
      { testId: 'T03', status: 'failed' }, { testId: 'T04', status: 'passed' },
      { testId: 'T05', status: 'passed' }, { testId: 'T06', status: 'passed' },
      { testId: 'T09', status: 'failed' }, { testId: 'T10', status: 'passed' },
      { testId: 'T11', status: 'passed' }, { testId: 'T17', status: 'passed' },
      { testId: 'T18', status: 'passed' }, { testId: 'T24', status: 'passed' },
    ],
    passed: 17, failed: 3, total: 20, duration: '4:32', rate: 85,
  },
]

// ─── Priority Config ────────────────────────────────────
const priorityConfig = {
  smoke: { icon: <Flame className="size-3" />, label: '🔥 Smoke', color: 'text-orange-700 bg-orange-100 dark:text-orange-300 dark:bg-orange-900/40', dot: 'bg-orange-500' },
  regression: { icon: <Activity className="size-3" />, label: '🔄 Regression', color: 'text-blue-700 bg-blue-100 dark:text-blue-300 dark:bg-blue-900/40', dot: 'bg-blue-500' },
  sanity: { icon: <ShieldCheck className="size-3" />, label: '🛡️ Sanity', color: 'text-purple-700 bg-purple-100 dark:text-purple-300 dark:bg-purple-900/40', dot: 'bg-purple-500' },
} as const

function PriorityBadge({ priority }: { priority?: TestPriority }) {
  if (!priority) return null
  const cfg = priorityConfig[priority]
  return (
    <span className={`inline-flex items-center gap-0.5 text-[10px] font-medium px-1.5 py-0.5 rounded-full ${cfg.color}`}>
      {cfg.label}
    </span>
  )
}

// ─── Sidebar Module Component ────────────────────────────
function SidebarModuleItem({
  module,
  depth = 0,
  activeId,
  onSelect,
  expandedIds,
  toggleExpand,
}: {
  module: SidebarModule
  depth?: number
  activeId: string | null
  onSelect: (id: string) => void
  expandedIds: Set<string>
  toggleExpand: (id: string) => void
}) {
  const hasChildren = module.children && module.children.length > 0
  const isExpanded = expandedIds.has(module.id)
  const isActive = activeId === module.id
  const isParentActive = activeId && hasChildren && module.children!.some((c) => c.id === activeId)

  return (
    <div>
      <button
        onClick={() => {
          if (hasChildren) toggleExpand(module.id)
          else onSelect(module.id)
        }}
        className={`w-full flex items-center gap-1.5 px-3 py-[7px] text-[13px] rounded-md transition-colors cursor-pointer text-left ${
          isActive
            ? 'bg-[#c8e6c9] dark:bg-[#2d4a2d] text-gray-900 dark:text-gray-100 font-medium shadow-sm'
            : isParentActive
              ? 'bg-[#c8e6c9]/50 dark:bg-[#2d4a2d]/50 text-gray-800 dark:text-gray-200 font-medium'
              : 'text-gray-700 dark:text-gray-300 hover:bg-[#c8e6c9]/40 dark:hover:bg-[#2d4a2d]/30'
        }`}
        style={{ paddingLeft: `${depth * 16 + 12}px` }}
      >
        {hasChildren ? (
          <ChevronDown
            className={`size-3.5 shrink-0 transition-transform duration-200 ${
              !isExpanded ? '-rotate-90' : ''
            }`}
          />
        ) : (
          <span className="w-3.5 shrink-0" />
        )}
        <span className="truncate flex-1">{module.label}</span>
        {module.badge && (
          <span
            className={`text-[11px] ml-auto shrink-0 ${
              module.badgeType === 'success'
                ? 'text-green-700 dark:text-green-400'
                : module.badgeType === 'warning'
                  ? 'text-orange-700 dark:text-orange-400'
                  : module.badgeType === 'wip'
                    ? 'text-blue-600 dark:text-blue-400'
                    : 'text-gray-500 dark:text-gray-400'
            }`}
          >
            {module.badge}
          </span>
        )}
      </button>
      {hasChildren && isExpanded && (
        <div className="mt-0.5">
          {module.children!.map((child) => (
            <SidebarModuleItem
              key={child.id}
              module={child}
              depth={depth + 1}
              activeId={activeId}
              onSelect={onSelect}
              expandedIds={expandedIds}
              toggleExpand={toggleExpand}
            />
          ))}
        </div>
      )}
    </div>
  )
}

// ─── Test Status Icon ────────────────────────────────────
function TestStatusIcon({ status, size = 4 }: { status: string; size?: number }) {
  const cls = `size-${size} shrink-0`
  switch (status) {
    case 'passed':
      return <CheckCircle2 className={`${cls} text-green-500`} />
    case 'failed':
      return <XCircle className={`${cls} text-red-500`} />
    case 'running':
      return <Loader2 className={`${cls} text-blue-500 animate-spin`} />
    default:
      return <Circle className={`size-${Math.max(size - 0.5, 3)} text-gray-300 dark:text-gray-600`} />
  }
}

// ─── LOGIN PAGE ──────────────────────────────────────────
function LoginPage({ onLogin }: { onLogin: (user: AuthUser) => void }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault()
      setError('')
      setLoading(true)

      try {
        const res = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        })

        const data = await res.json()

        if (!res.ok) {
          setError(data.error || 'Login failed')
          return
        }

        onLogin(data.user)
      } catch {
        setError('Network error. Please try again.')
      } finally {
        setLoading(false)
      }
    },
    [email, password, onLogin]
  )

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-950 flex items-center justify-center p-4">
      <div className="w-full max-w-[400px]">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-green-600 flex items-center justify-center mb-4 shadow-lg shadow-green-600/20">
            <span className="text-white text-2xl font-bold">R</span>
          </div>
          <h1 className="text-[22px] font-semibold text-gray-800 dark:text-gray-100">Welcome Back !</h1>
          <p className="text-[13px] text-gray-500 dark:text-gray-400 mt-1">Sign in to RhythmERP Automation Runner</p>
        </div>

        {/* Login Card */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg shadow-gray-200/50 dark:shadow-gray-900/50 border border-gray-100 dark:border-gray-700 p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email */}
            <div className="space-y-1.5">
              <Label className="text-[13px] text-gray-700 dark:text-gray-300 font-medium">Email / Username</Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-gray-400" />
                <Input
                  type="email"
                  placeholder="admin@rhythmerp.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="h-10 pl-9 text-[13px] bg-gray-50/50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600 focus:bg-white dark:focus:bg-gray-700 text-gray-800 dark:text-gray-100"
                  required
                  autoFocus
                />
              </div>
            </div>

            {/* Password */}
            <div className="space-y-1.5">
              <Label className="text-[13px] text-gray-700 dark:text-gray-300 font-medium">Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-gray-400" />
                <Input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="h-10 pl-9 pr-10 text-[13px] bg-gray-50/50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600 focus:bg-white dark:focus:bg-gray-700 text-gray-800 dark:text-gray-100"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors cursor-pointer"
                >
                  <Eye className="size-4" />
                </button>
              </div>
            </div>

            {/* Remember Me */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Checkbox
                  id="remember"
                  checked={rememberMe}
                  onCheckedChange={(v) => setRememberMe(v === true)}
                  className="size-4"
                />
                <label htmlFor="remember" className="text-[12px] text-gray-600 dark:text-gray-400 cursor-pointer select-none">
                  Remember me
                </label>
              </div>
              <button type="button" className="text-[12px] text-green-600 hover:text-green-700 font-medium cursor-pointer">
                Forgot password?
              </button>
            </div>

            {/* Error */}
            {error && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-[12px] px-3 py-2 rounded-lg flex items-center gap-2">
                <XCircle className="size-3.5 shrink-0" />
                {error}
              </div>
            )}

            {/* Submit */}
            <Button
              type="submit"
              disabled={loading}
              className="w-full h-10 bg-green-600 hover:bg-green-700 text-white text-[14px] font-medium gap-2 rounded-lg cursor-pointer"
            >
              {loading ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                'Sign In'
              )}
            </Button>
          </form>
        </div>

        {/* Footer */}
        <p className="text-center text-[11px] text-gray-400 dark:text-gray-500 mt-6">
          RhythmERP Automation Runner v1.0 — Internal QA Tool
        </p>
      </div>
    </div>
  )
}

// ─── DASHBOARD TAB (Feature 3) ───────────────────────────
function DashboardTab({
  onSelectModule,
}: {
  onSelectModule: (moduleId: string) => void
}) {
  // Group modules by parentGroup, preserving order
  const grouped = useMemo(() => {
    const order = ['Standalone', 'Common Settings', 'Commodity Settings']
    const groups: { name: string; icon: string; modules: ModuleHealth[] }[] = []
    const groupMap = new Map<string, ModuleHealth[]>()

    for (const mod of moduleHealthData) {
      const g = mod.parentGroup || 'Other'
      if (!groupMap.has(g)) groupMap.set(g, [])
      groupMap.get(g)!.push(mod)
    }

    for (const name of order) {
      const mods = groupMap.get(name)
      if (mods) groups.push({ name, icon: name === 'Common Settings' ? '⚙️' : name === 'Commodity Settings' ? '📦' : '📁', modules: mods })
    }
    // catch any remaining
    for (const [name, mods] of groupMap) {
      if (!order.includes(name)) groups.push({ name, icon: '📁', modules: mods })
    }
    return groups
  }, [])

  const quickStats = useMemo(() => {
    const total = moduleHealthData.length
    const fullyPassing = moduleHealthData.filter((m) => m.totalTests > 0 && m.passRate === 100).length
    const partiallyPassing = moduleHealthData.filter((m) => m.totalTests > 0 && m.passRate > 0 && m.passRate < 100).length
    const notStarted = moduleHealthData.filter((m) => m.totalTests === 0).length
    const totalPassed = moduleHealthData.reduce((s, m) => s + m.passedTests, 0)
    const totalFailed = moduleHealthData.reduce((s, m) => s + m.failedTests, 0)
    const totalTests = moduleHealthData.reduce((s, m) => s + m.totalTests, 0)
    return { total, fullyPassing, partiallyPassing, notStarted, totalPassed, totalFailed, totalTests }
  }, [])

  const getHealthColor = useCallback((rate: number, total: number) => {
    if (total === 0) return { bg: 'bg-gray-100 dark:bg-gray-800', text: 'text-gray-400 dark:text-gray-500', indicator: 'bg-gray-400', label: 'Not Started' }
    if (rate === 100) return { bg: 'bg-green-50 dark:bg-green-900/20', text: 'text-green-700 dark:text-green-400', indicator: 'bg-green-500', label: 'Healthy' }
    if (rate >= 75) return { bg: 'bg-orange-50 dark:bg-orange-900/20', text: 'text-orange-700 dark:text-orange-400', indicator: 'bg-orange-500', label: 'Partial' }
    return { bg: 'bg-red-50 dark:bg-red-900/20', text: 'text-red-700 dark:text-red-400', indicator: 'bg-red-500', label: 'Critical' }
  }, [])

  return (
    <div className="flex flex-col h-full overflow-auto">
      <div className="p-5 space-y-5">
        {/* Page Header */}
        <div>
          <h2 className="text-[18px] font-semibold text-gray-800 dark:text-gray-100">Dashboard</h2>
          <p className="text-[13px] text-gray-500 dark:text-gray-400 mt-0.5">Overview of all RhythmERP automation modules</p>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3.5 border border-gray-100 dark:border-gray-700">
            <div className="text-[11px] text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wider">Total Modules</div>
            <div className="text-xl font-bold text-gray-800 dark:text-gray-100 mt-1">{quickStats.total}</div>
          </div>
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3.5 border border-green-100 dark:border-green-800/50">
            <div className="text-[11px] text-green-600 dark:text-green-400 font-medium uppercase tracking-wider">Fully Passing</div>
            <div className="text-xl font-bold text-green-700 dark:text-green-400 mt-1">{quickStats.fullyPassing}</div>
          </div>
          <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-3.5 border border-orange-100 dark:border-orange-800/50">
            <div className="text-[11px] text-orange-600 dark:text-orange-400 font-medium uppercase tracking-wider">Partial / Critical</div>
            <div className="text-xl font-bold text-orange-700 dark:text-orange-400 mt-1">{quickStats.partiallyPassing}</div>
          </div>
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3.5 border border-blue-100 dark:border-blue-800/50">
            <div className="text-[11px] text-blue-600 dark:text-blue-400 font-medium uppercase tracking-wider">Overall Pass Rate</div>
            <div className="text-xl font-bold text-blue-700 dark:text-blue-400 mt-1">
              {quickStats.totalTests > 0 ? Math.round((quickStats.totalPassed / quickStats.totalTests) * 100) : 0}%
            </div>
            <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5">
              {quickStats.totalPassed} / {quickStats.totalTests} tests passed
            </div>
          </div>
        </div>

        {/* Module Groups */}
        {grouped.map((group) => {
          const groupTotal = group.modules.reduce((s, m) => s + m.totalTests, 0)
          const groupPassed = group.modules.reduce((s, m) => s + m.passedTests, 0)
          const groupFailed = group.modules.reduce((s, m) => s + m.failedTests, 0)
          const groupRate = groupTotal > 0 ? Math.round((groupPassed / groupTotal) * 100) : 0
          const groupHealth = getHealthColor(groupRate, groupTotal)

          return (
            <div key={group.name}>
              {/* Group Header */}
              <div className="flex items-center gap-2 mb-2.5">
                <span className="text-[14px]">{group.icon}</span>
                <h3 className="text-[14px] font-semibold text-gray-800 dark:text-gray-100">{group.name}</h3>
                <span className="text-[12px] text-gray-500 dark:text-gray-400 ml-1">
                  {group.modules.length} modules
                </span>
                {groupTotal > 0 && (
                  <>
                    <div className="flex-1" />
                    <span className={`text-[12px] font-medium ${groupHealth.text}`}>
                      {groupRate}%
                    </span>
                    <span className="text-[11px] text-gray-400 dark:text-gray-500">
                      ({groupPassed}/{groupTotal})
                    </span>
                  </>
                )}
              </div>

              {/* Module Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2.5">
                {group.modules.map((mod) => {
                  const health = getHealthColor(mod.passRate, mod.totalTests)
                  return (
                    <button
                      key={mod.moduleId}
                      onClick={() => onSelectModule(mod.moduleId)}
                      className={`text-left p-3 rounded-lg border transition-all hover:shadow-md hover:-translate-y-0.5 cursor-pointer ${health.bg} border-gray-100 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600`}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <div className={`w-2.5 h-2.5 rounded-full shrink-0 ${health.indicator}`} />
                        <span className="text-[13px] font-medium text-gray-800 dark:text-gray-100 truncate">{mod.moduleName}</span>
                      </div>
                      <div className="flex items-center gap-3 text-[11px]">
                        {mod.totalTests > 0 ? (
                          <>
                            <span className={`font-medium ${health.text}`}>{mod.passRate}%</span>
                            <span className="text-gray-400 dark:text-gray-500">
                              {mod.passedTests}/{mod.totalTests}
                            </span>
                            <Progress value={mod.passRate} className="h-1.5 flex-1 bg-gray-200 dark:bg-gray-700" />
                          </>
                        ) : (
                          <span className="text-gray-400 dark:text-gray-500">No tests yet</span>
                        )}
                      </div>
                      {mod.totalTests > 0 && (
                        <div className="text-[10px] text-gray-400 dark:text-gray-500 mt-1.5 flex items-center gap-1">
                          <Clock className="size-2.5" />
                          {mod.lastRun}
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
    </div>
  )
}

// ─── OPERATIONS TAB (Test Specification View) ────────────
function OperationsTab() {
  const [searchVal, setSearchVal] = useState('')
  const [filter, setFilter] = useState<'all' | 'passed' | 'failed' | 'not-run'>('all')
  const [priorityFilter, setPriorityFilter] = useState<'all' | TestPriority>('all')
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(
    new Set(testSpecGroups.map((g) => g.className))
  )
  const [expandedTests, setExpandedTests] = useState<Set<string>>(new Set())

  const toggleGroup = useCallback((name: string) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev)
      if (next.has(name)) next.delete(name)
      else next.add(name)
      return next
    })
  }, [])

  const toggleTest = useCallback((id: string) => {
    setExpandedTests((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  // Filter groups based on search and filter
  const filteredGroups = useMemo(() =>
    testSpecGroups
      .map((group) => {
        const filteredTests = group.tests.filter((test) => {
          const matchSearch =
            searchVal === '' ||
            test.id.toLowerCase().includes(searchVal.toLowerCase()) ||
            test.description.toLowerCase().includes(searchVal.toLowerCase()) ||
            test.steps.toLowerCase().includes(searchVal.toLowerCase()) ||
            test.expected.toLowerCase().includes(searchVal.toLowerCase())
          const matchFilter =
            filter === 'all' ||
            (filter === 'passed' && test.status === 'passed') ||
            (filter === 'failed' && test.status === 'failed') ||
            (filter === 'not-run' && test.status === 'not-run')
          const matchPriority =
            priorityFilter === 'all' ||
            test.priority === priorityFilter
          return matchSearch && matchFilter && matchPriority
        })
        return { ...group, tests: filteredTests, filteredTestCount: filteredTests.length }
      })
      .filter((g) => g.filteredTestCount > 0),
  [searchVal, filter, priorityFilter])

  const totalTests = testSpecGroups.reduce((acc, g) => acc + g.tests.length, 0)
  const totalPassed = testSpecGroups.reduce(
    (acc, g) => acc + g.tests.filter((t) => t.status === 'passed').length,
    0
  )
  const totalFailed = testSpecGroups.reduce(
    (acc, g) => acc + g.tests.filter((t) => t.status === 'failed').length,
    0
  )

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-100 dark:border-gray-700 shrink-0">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-gray-400" />
          <Input
            placeholder="Search tests..."
            value={searchVal}
            onChange={(e) => setSearchVal(e.target.value)}
            className="h-8 pl-8 text-[13px] bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-600 text-gray-800 dark:text-gray-100"
          />
        </div>
        <Button variant="outline" className="h-8 text-[13px] gap-1.5 border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300">
          <FileSpreadsheet className="size-3.5" />
          Export to Excel
        </Button>
        <Select
          value={filter}
          onValueChange={(v) => setFilter(v as typeof filter)}
        >
          <SelectTrigger className="h-8 w-28 text-[13px] bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-600">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="passed">Passed</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
            <SelectItem value="not-run">Not Run</SelectItem>
          </SelectContent>
        </Select>
        <div className="flex-1" />
        {/* Priority filter pills */}
        <div className="flex items-center gap-1">
          <button
            onClick={() => setPriorityFilter('all')}
            className={`px-2 py-1 rounded-md text-[11px] font-medium transition-colors cursor-pointer ${
              priorityFilter === 'all' ? 'bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-100' : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
          >All</button>
          <button
            onClick={() => setPriorityFilter('smoke')}
            className={`px-2 py-1 rounded-md text-[11px] font-medium transition-colors cursor-pointer ${
              priorityFilter === 'smoke' ? 'bg-orange-100 dark:bg-orange-900/40 text-orange-700 dark:text-orange-300' : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
          >🔥 Smoke</button>
          <button
            onClick={() => setPriorityFilter('regression')}
            className={`px-2 py-1 rounded-md text-[11px] font-medium transition-colors cursor-pointer ${
              priorityFilter === 'regression' ? 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300' : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
          >🔄 Regression</button>
          <button
            onClick={() => setPriorityFilter('sanity')}
            className={`px-2 py-1 rounded-md text-[11px] font-medium transition-colors cursor-pointer ${
              priorityFilter === 'sanity' ? 'bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300' : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
          >🛡️ Sanity</button>
        </div>
        <Separator orientation="vertical" className="h-5 mx-1" />
        <div className="flex items-center gap-3 text-[12px]">
          <span className="text-gray-500 dark:text-gray-400">{totalTests} tests</span>
          <span className="text-green-600 dark:text-green-400 font-medium">{totalPassed} passed</span>
          <span className="text-red-500 dark:text-red-400 font-medium">{totalFailed} failed</span>
        </div>
      </div>

      {/* Test Groups */}
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-2">
          {filteredGroups.map((group) => {
            const passed = group.tests.filter((t) => t.status === 'passed').length
            const failed = group.tests.filter((t) => t.status === 'failed').length
            const notRun = group.tests.filter((t) => t.status === 'not-run').length
            const allPassed = passed === group.tests.length && group.tests.length > 0
            const hasFailed = failed > 0

            const groupBorderColor = allPassed
              ? 'border-green-200 dark:border-green-800'
              : hasFailed
                ? 'border-red-200 dark:border-red-800'
                : 'border-gray-200 dark:border-gray-700'

            const groupBgColor = allPassed
              ? 'bg-green-50/30 dark:bg-green-900/10'
              : hasFailed
                ? 'bg-red-50/30 dark:bg-red-900/10'
                : 'bg-white dark:bg-gray-800/30'

            return (
              <div
                key={group.className}
                className={`border rounded-lg overflow-hidden ${groupBorderColor} ${groupBgColor}`}
              >
                {/* Group Header */}
                <button
                  onClick={() => toggleGroup(group.className)}
                  className="w-full flex items-center gap-3 px-4 py-3 hover:bg-black/[0.02] dark:hover:bg-white/[0.02] transition-colors cursor-pointer"
                >
                  <ChevronRight
                    className={`size-4 text-gray-400 dark:text-gray-500 shrink-0 transition-transform duration-200 ${
                      expandedGroups.has(group.className) ? 'rotate-90' : ''
                    }`}
                  />
                  <span className="text-[13px] font-semibold text-gray-800 dark:text-gray-100 flex-1 text-left">
                    {group.className}
                  </span>
                  <span className="text-[12px] text-gray-500 dark:text-gray-400">
                    {group.tests.length} test{group.tests.length !== 1 ? 's' : ''}
                  </span>
                  <div className="flex items-center gap-1.5">
                    {passed > 0 && (
                      <span className="inline-flex items-center gap-0.5 text-[11px] text-green-700 dark:text-green-400 bg-green-100 dark:bg-green-900/30 px-1.5 py-0.5 rounded-full font-medium">
                        ✅ {passed}
                      </span>
                    )}
                    {failed > 0 && (
                      <span className="inline-flex items-center gap-0.5 text-[11px] text-red-700 dark:text-red-400 bg-red-100 dark:bg-red-900/30 px-1.5 py-0.5 rounded-full font-medium">
                        ❌ {failed}
                      </span>
                    )}
                    {notRun > 0 && (
                      <span className="inline-flex items-center gap-0.5 text-[11px] text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded-full font-medium">
                        — {notRun}
                      </span>
                    )}
                  </div>
                </button>

                {/* Expanded Tests */}
                {expandedGroups.has(group.className) && (
                  <div className="border-t border-gray-100 dark:border-gray-700">
                    {group.tests.map((test, idx) => {
                      const isLast = idx === group.tests.length - 1
                      const isExpanded = expandedTests.has(test.id)
                      const statusIcon =
                        test.status === 'passed' ? (
                          <span className="text-green-500 text-sm">✅</span>
                        ) : test.status === 'failed' ? (
                          <span className="text-red-500 text-sm">❌</span>
                        ) : (
                          <span className="text-gray-300 dark:text-gray-600 text-sm">—</span>
                        )

                      return (
                        <div key={test.id}>
                          <button
                            onClick={() => toggleTest(test.id)}
                            className={`w-full flex items-center gap-3 px-4 py-2.5 pl-10 hover:bg-black/[0.02] dark:hover:bg-white/[0.02] transition-colors cursor-pointer ${
                              !isLast ? 'border-b border-gray-50 dark:border-gray-800' : ''
                            }`}
                          >
                            {isExpanded ? (
                              <ChevronDown className="size-3 text-gray-400 dark:text-gray-500 shrink-0" />
                            ) : (
                              <ChevronRight className="size-3 text-gray-400 dark:text-gray-500 shrink-0" />
                            )}
                            <span className="text-[11px] text-gray-400 dark:text-gray-500 font-mono w-7 text-left shrink-0">
                              {test.id}
                            </span>
                            <span className="text-[12px] text-gray-700 dark:text-gray-200 flex-1 text-left">
                              {test.description}
                            </span>
                            <PriorityBadge priority={test.priority} />
                            {statusIcon}
                            <span
                              className={`text-[11px] font-mono w-10 text-right shrink-0 ${
                                test.status === 'passed'
                                  ? 'text-green-600 dark:text-green-400'
                                  : test.status === 'failed'
                                    ? 'text-red-500 dark:text-red-400'
                                    : 'text-gray-400 dark:text-gray-500'
                              }`}
                            >
                              {test.duration}
                            </span>
                          </button>

                          {/* Expanded Test Details */}
                          {isExpanded && (
                            <div className="px-10 pb-3 pl-[72px] pr-4 border-b border-gray-50 dark:border-gray-800 bg-gray-50/30 dark:bg-gray-800/20">
                              <div className="space-y-2 py-2">
                                <div>
                                  <span className="text-[11px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                    Steps:
                                  </span>
                                  <p className="text-[12px] text-gray-600 dark:text-gray-300 mt-0.5 leading-5">
                                    {test.steps}
                                  </p>
                                </div>
                                <div>
                                  <span className="text-[11px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                    Expected:
                                  </span>
                                  <p className="text-[12px] text-gray-600 dark:text-gray-300 mt-0.5 leading-5">
                                    {test.expected}
                                  </p>
                                </div>
                                {test.error && (
                                  <div>
                                    <span className="text-[11px] font-semibold text-red-500 dark:text-red-400 uppercase tracking-wider">
                                      Error:
                                    </span>
                                    <p className="text-[12px] text-red-600 dark:text-red-400 mt-0.5 leading-5 bg-red-50 dark:bg-red-900/20 px-2 py-1 rounded">
                                      {test.error}
                                    </p>
                                  </div>
                                )}
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
          })}

          {filteredGroups.length === 0 && (
            <div className="text-center py-12 text-gray-400 dark:text-gray-500">
              <Search className="size-8 mx-auto mb-2 opacity-50" />
              <p className="text-[13px]">No tests match your search criteria</p>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  )
}

// ─── TEST RUNNER TAB (Setup — checkboxes + Run) ──────────
function TestRunnerTab({
  tests,
  testChecks,
  toggleTestCheck,
  isRunning,
  onRun,
  onRunByPriority,
  totalFailed,
  onRerunFailed,
}: {
  tests: TestItem[]
  testChecks: Set<string>
  toggleTestCheck: (id: string) => void
  isRunning: boolean
  onRun: (selectedOnly: boolean) => void
  onRunByPriority: (priority: TestPriority) => void
  totalFailed: number
  onRerunFailed: () => void
}) {
  const [selectAll, setSelectAll] = useState(false)

  const handleSelectAll = useCallback(() => {
    if (selectAll) {
      testChecks.forEach((id) => toggleTestCheck(id))
    } else {
      tests.filter((t) => t.status === 'pending' || t.status === 'running').forEach((t) => {
        if (!testChecks.has(t.id)) toggleTestCheck(t.id)
      })
    }
    setSelectAll(!selectAll)
  }, [selectAll, tests, testChecks, toggleTestCheck])

  const passedCount = tests.filter((t) => t.status === 'passed').length
  const failedCount = tests.filter((t) => t.status === 'failed').length
  const pendingCount = tests.filter((t) => t.status === 'pending').length
  const selectedRunnable = tests.filter((t) => t.status === 'pending' && testChecks.has(t.id)).length
  const smokeCount = tests.filter((t) => t.priority === 'smoke' && (t.status === 'pending' || t.status === 'running')).length
  const regressionCount = tests.filter((t) => t.priority === 'regression' && (t.status === 'pending' || t.status === 'running')).length

  // Group tests by class
  const testGroups: { name: string; tests: TestItem[] }[] = []
  let currentGroup = ''
  for (const t of tests) {
    const cls = t.id.replace(/\d+$/, '').replace(/T/, 'Test')
    if (cls !== currentGroup) {
      currentGroup = cls
      testGroups.push({ name: cls, tests: [] })
    }
    testGroups[testGroups.length - 1].tests.push(t)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Action Bar */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-100 dark:border-gray-700 shrink-0 flex-wrap">
        <Button
          onClick={() => onRun(false)}
          disabled={isRunning || pendingCount === 0}
          className="bg-green-600 hover:bg-green-700 text-white h-9 text-[13px] gap-2 px-5 cursor-pointer"
        >
          <Play className="size-4" />
          Run All ({pendingCount})
        </Button>
        <Button
          onClick={() => onRun(true)}
          disabled={isRunning || selectedRunnable === 0}
          className="bg-[#1976d2] hover:bg-[#1565c0] text-white h-9 text-[13px] gap-2 px-5 cursor-pointer"
        >
          <Play className="size-4" />
          Run Selected ({selectedRunnable})
        </Button>
        <Button
          onClick={() => onRunByPriority('smoke')}
          disabled={isRunning || smokeCount === 0}
          className="bg-orange-500 hover:bg-orange-600 text-white h-9 text-[13px] gap-2 px-4 cursor-pointer"
        >
          <Flame className="size-3.5" />
          Run Smoke ({smokeCount})
        </Button>
        <Button
          onClick={() => onRunByPriority('regression')}
          disabled={isRunning || regressionCount === 0}
          className="bg-blue-500 hover:bg-blue-600 text-white h-9 text-[13px] gap-2 px-4 cursor-pointer"
        >
          <Activity className="size-3.5" />
          Run Regression ({regressionCount})
        </Button>
        {totalFailed > 0 && (
          <Button
            onClick={onRerunFailed}
            disabled={isRunning}
            variant="outline"
            className="border-orange-300 dark:border-orange-700 text-orange-600 dark:text-orange-400 hover:bg-orange-50 dark:hover:bg-orange-900/20 hover:text-orange-700 h-9 text-[13px] gap-2 px-4 cursor-pointer"
          >
            <RotateCcw className="size-3.5" />
            Rerun Failed ({totalFailed})
          </Button>
        )}
        <div className="flex-1" />
        <div className="flex items-center gap-4 text-[12px]">
          <span className="flex items-center gap-1 text-green-600 dark:text-green-400">
            <CheckCircle2 className="size-3.5" /> {passedCount} passed
          </span>
          <span className="flex items-center gap-1 text-red-500 dark:text-red-400">
            <XCircle className="size-3.5" /> {failedCount} failed
          </span>
          <span className="flex items-center gap-1 text-gray-400 dark:text-gray-500">
            <Circle className="size-3" /> {pendingCount} pending
          </span>
        </div>
      </div>

      {/* Priority filter pills */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-gray-100 dark:border-gray-700 shrink-0 bg-gray-50/30 dark:bg-gray-800/20">
        <span className="text-[11px] text-gray-500 dark:text-gray-400 font-medium">Priority:</span>
        <span className={`inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full ${priorityConfig.smoke.color}`}>
          <Flame className="size-2.5" /> Smoke: {tests.filter(t => t.priority === 'smoke').length}
        </span>
        <span className={`inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full ${priorityConfig.regression.color}`}>
          <Activity className="size-2.5" /> Regression: {tests.filter(t => t.priority === 'regression').length}
        </span>
        <span className={`inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full ${priorityConfig.sanity.color}`}>
          <ShieldCheck className="size-2.5" /> Sanity: {tests.filter(t => t.priority === 'sanity').length}
        </span>
      </div>

      {/* Test List by Groups */}
      <ScrollArea className="flex-1">
        <div className="px-4 py-3 space-y-3">
          {testGroups.map((group) => {
            const groupPassed = group.tests.filter((t) => t.status === 'passed').length
            const groupFailed = group.tests.filter((t) => t.status === 'failed').length
            const groupPending = group.tests.filter((t) => t.status === 'pending').length
            const allSelected = group.tests.every((t) => testChecks.has(t.id) || t.status !== 'pending')
            const someSelected = group.tests.some((t) => testChecks.has(t.id))

            return (
              <div key={group.name} className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                {/* Group Header */}
                <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700">
                  <Checkbox
                    checked={allSelected}
                    ref={(el) => { if (el) (el as unknown as HTMLInputElement).indeterminate = someSelected && !allSelected }}
                    onCheckedChange={() => {
                      group.tests.forEach((t) => {
                        if (t.status === 'pending') {
                          if (!testChecks.has(t.id)) toggleTestCheck(t.id)
                        }
                      })
                    }}
                    disabled={isRunning}
                    className="size-3.5"
                  />
                  <span className="text-[13px] font-semibold text-gray-700 dark:text-gray-200 flex-1">{group.name}</span>
                  <span className="text-[11px] text-gray-500 dark:text-gray-400">({group.tests.length})</span>
                  {groupPassed > 0 && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">{groupPassed} ✅</span>
                  )}
                  {groupFailed > 0 && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400">{groupFailed} ❌</span>
                  )}
                  {groupPending > 0 && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400">{groupPending} pending</span>
                  )}
                </div>
                {/* Test Rows */}
                <div className="divide-y divide-gray-100 dark:divide-gray-800">
                  {group.tests.map((test) => (
                    <div
                      key={test.id}
                      className={`flex items-center gap-2.5 px-4 py-2 hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors ${
                        test.status === 'running' ? 'bg-blue-50 dark:bg-blue-900/20' : ''
                      }`}
                    >
                      <Checkbox
                        checked={testChecks.has(test.id) || test.status === 'passed' || test.status === 'failed'}
                        disabled={isRunning || test.status !== 'pending'}
                        onCheckedChange={() => { if (test.status === 'pending') toggleTestCheck(test.id) }}
                        className="size-3.5"
                      />
                      <span className="text-[11px] text-gray-400 dark:text-gray-500 font-mono w-8 shrink-0">{test.id}</span>
                      <span className={`text-[13px] flex-1 truncate ${
                        test.status === 'running' ? 'text-blue-600 dark:text-blue-400 font-medium' :
                        test.status === 'failed' ? 'text-red-600 dark:text-red-400' :
                        test.status === 'passed' ? 'text-gray-500 dark:text-gray-400' :
                        'text-gray-800 dark:text-gray-100'
                      }`}>{test.name}</span>
                      <PriorityBadge priority={test.priority} />
                      <TestStatusIcon status={test.status} size={3.5} />
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </ScrollArea>
    </div>
  )
}

// ─── LIVE EXECUTION TAB (Browser view + Console) ────────
function LiveExecutionTab({
  tests,
  isRunning,
  runningProgress,
  onStop,
  onBack,
  onRerunFailed,
}: {
  tests: TestItem[]
  isRunning: boolean
  runningProgress: string
  onStop: () => void
  onBack: () => void
  onRerunFailed: () => void
}) {
  const consoleEndRef = useRef<HTMLDivElement>(null)
  const lastProgressRef = useRef<string>('')
  const [consoleLines, setConsoleLines] = useState<string[]>([
    '> Waiting for tests to start...',
    '> Select tests in Test Runner and click Run.',
  ])
  const [currentStepIndex, setCurrentStepIndex] = useState(-1)
  const prevRunningTestIdRef = useRef<string | null>(null)
  const stepTimerRef = useRef<NodeJS.Timeout | null>(null)

  // Get steps for running test
  const runningTest = tests.find((t) => t.status === 'running')
  const runningTestId = runningTest?.id || null
  const runningSteps = useMemo(() => (runningTestId ? getStepsForTest(runningTestId) : []), [runningTestId])

  // Step progress effect (Feature 2)
  useEffect(() => {
    // Clear previous timer
    if (stepTimerRef.current) {
      clearInterval(stepTimerRef.current)
      stepTimerRef.current = null
    }

    if (runningTestId && runningTestId !== prevRunningTestIdRef.current) {
      prevRunningTestIdRef.current = runningTestId
      if (runningSteps.length > 0) {
        setCurrentStepIndex(0)
        let idx = 0
        stepTimerRef.current = setInterval(() => {
          idx++
          if (idx < runningSteps.length) {
            setCurrentStepIndex(idx)
          } else {
            if (stepTimerRef.current) clearInterval(stepTimerRef.current)
            stepTimerRef.current = null
          }
        }, 150)
      } else {
        setCurrentStepIndex(-1)
      }
    } else if (!runningTestId) {
      setCurrentStepIndex(-1)
      prevRunningTestIdRef.current = null
    }

    return () => {
      if (stepTimerRef.current) {
        clearInterval(stepTimerRef.current)
        stepTimerRef.current = null
      }
    }
  }, [runningTestId, runningSteps.length])

  // Track console lines via ref + parent updates
  useEffect(() => {
    if (runningProgress && runningProgress !== lastProgressRef.current) {
      lastProgressRef.current = runningProgress
      setConsoleLines((prev) => [...prev, runningProgress])
    }
  }, [runningProgress])

  useEffect(() => {
    consoleEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [consoleLines.length])

  const passedCount = tests.filter((t) => t.status === 'passed').length
  const failedCount = tests.filter((t) => t.status === 'failed').length
  const completedCount = passedCount + failedCount
  const progressPercent = tests.length > 0 ? Math.round((completedCount / tests.length) * 100) : 0

  return (
    <div className="flex flex-col h-full">
      {/* Top Bar: Back + Progress + Stop */}
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-gray-100 dark:border-gray-700 shrink-0 bg-gray-50/50 dark:bg-gray-800/30">
        <Button
          variant="ghost"
          onClick={onBack}
          className="h-8 text-[13px] gap-1.5 text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-gray-100 cursor-pointer px-2"
        >
          <ArrowLeft className="size-3.5" />
          Test Runner
        </Button>
        <Separator orientation="vertical" className="h-5 mx-1" />
        {isRunning ? (
          <>
            <div className="flex items-center gap-2 flex-1 max-w-sm">
              <Progress value={progressPercent} className="h-2 flex-1" />
              <span className="text-[12px] text-blue-600 dark:text-blue-400 font-medium whitespace-nowrap">
                {completedCount}/{tests.length} ({progressPercent}%)
              </span>
            </div>
            <div className="flex-1" />
            <Button
              onClick={onStop}
              className="bg-red-500 hover:bg-red-600 text-white h-8 text-[13px] gap-1.5 cursor-pointer"
            >
              <Square className="size-3.5" />
              Stop
            </Button>
          </>
        ) : completedCount > 0 ? (
          <>
            <span className="text-[12px] text-gray-500 dark:text-gray-400">
              Run complete — <span className="text-green-600 dark:text-green-400 font-medium">{passedCount} passed</span>, <span className="text-red-500 dark:text-red-400 font-medium">{failedCount} failed</span>
            </span>
            <div className="flex-1" />
            {failedCount > 0 && (
              <Button
                onClick={onRerunFailed}
                className="bg-orange-500 hover:bg-orange-600 text-white h-8 text-[13px] gap-1.5 cursor-pointer mr-2"
              >
                <RotateCcw className="size-3.5" />
                Rerun Failed ({failedCount})
              </Button>
            )}
            <Button
              onClick={onBack}
              className="bg-[#1976d2] hover:bg-[#1565c0] text-white h-8 text-[13px] gap-1.5 cursor-pointer"
            >
              <RotateCcw className="size-3.5" />
              New Run
            </Button>
          </>
        ) : (
          <>
            <span className="text-[12px] text-gray-400 dark:text-gray-500">No test running</span>
            <div className="flex-1" />
          </>
        )}
        <div className="flex items-center gap-3 text-[12px] ml-2">
          <span className="flex items-center gap-1 text-green-600 dark:text-green-400"><CheckCircle2 className="size-3" /> {passedCount}</span>
          <span className="flex items-center gap-1 text-red-500 dark:text-red-400"><XCircle className="size-3" /> {failedCount}</span>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden flex flex-col">
        {/* Step Progress Panel + Browser View split */}
        <div className="flex-1 px-4 pt-3 pb-2 min-h-0 flex gap-3">
          {/* Step Progress Side Panel — only visible when a test is running with steps */}
          {isRunning && runningTest && runningSteps.length > 0 && (
            <div className="w-72 shrink-0 flex flex-col bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
              <div className="flex items-center justify-between px-4 py-2.5 border-b border-gray-100 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/80">
                <div className="flex items-center gap-2">
                  <ClipboardList className="size-3.5 text-blue-600 dark:text-blue-400" />
                  <span className="text-[12px] font-semibold text-gray-700 dark:text-gray-200">Test Steps</span>
                </div>
                <span className="text-[11px] text-blue-600 dark:text-blue-400 font-medium tabular-nums">
                  {Math.min(currentStepIndex + 1, runningSteps.length)} of {runningSteps.length}
                </span>
              </div>
              <div className="flex-1 overflow-auto p-2.5">
                <div className="space-y-1">
                  {runningSteps.map((step, idx) => {
                    const isCompleted = idx < currentStepIndex
                    const isCurrent = idx === currentStepIndex
                    return (
                      <div
                        key={idx}
                        className={`flex items-start gap-2 px-3 py-2 rounded-md text-[12px] transition-all ${
                          isCompleted
                            ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400'
                            : isCurrent
                              ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 font-medium ring-1 ring-blue-200 dark:ring-blue-800'
                              : 'text-gray-400 dark:text-gray-500'
                        }`}
                      >
                        {isCompleted ? (
                          <CheckCircle2 className="size-3.5 text-green-500 shrink-0 mt-0.5" />
                        ) : isCurrent ? (
                          <Loader2 className="size-3.5 text-blue-500 shrink-0 mt-0.5 animate-spin" />
                        ) : (
                          <Circle className="size-3.5 text-gray-300 dark:text-gray-600 shrink-0 mt-0.5" />
                        )}
                        <span className={`flex-1 leading-tight ${isCompleted ? 'line-through opacity-70' : ''}`}>{step}</span>
                        {isCurrent && (
                          <span className="text-[10px] text-blue-500 dark:text-blue-400 whitespace-nowrap shrink-0">Running</span>
                        )}
                        {isCompleted && (
                          <span className="text-[10px] text-green-500 dark:text-green-400 whitespace-nowrap shrink-0">Done</span>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
              <div className="px-4 py-2.5 border-t border-gray-100 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/80">
                <div className="flex items-center justify-between text-[11px] text-gray-500 dark:text-gray-400 mb-1.5">
                  <span>Progress</span>
                  <span className="font-medium text-gray-700 dark:text-gray-200 tabular-nums">
                    {Math.round(((currentStepIndex + 1) / runningSteps.length) * 100)}%
                  </span>
                </div>
                <Progress value={((currentStepIndex + 1) / runningSteps.length) * 100} className="h-1.5 bg-gray-200 dark:bg-gray-700" />
              </div>
            </div>
          )}

          {/* Live Browser View */}
          <div className="flex-1 min-w-0">
            <div className="h-full rounded-lg border-2 border-gray-700 dark:border-gray-600 overflow-hidden flex flex-col bg-white dark:bg-gray-900">
              {/* Chrome-like top bar */}
              <div className="bg-gray-200 dark:bg-gray-700 px-3 py-1.5 flex items-center gap-2 shrink-0">
                <div className="flex items-center gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-red-400" />
                  <div className="w-3 h-3 rounded-full bg-yellow-400" />
                  <div className="w-3 h-3 rounded-full bg-green-400" />
                </div>
                <div className="flex-1 flex items-center justify-center">
                  <div className="bg-white dark:bg-gray-800 rounded-md px-3 py-0.5 flex items-center gap-2 text-[11px] text-gray-500 dark:text-gray-400 border border-gray-300 dark:border-gray-600 min-w-[300px]">
                    <Globe className="size-3 text-gray-400 dark:text-gray-500" />
                    <span className="truncate">
                      {isRunning
                        ? `https://rhythmerp.com/common-settings/tax-rate — ${runningTest?.name || 'Running...'}`
                        : 'https://rhythmerp.com/common-settings/tax-rate'}
                    </span>
                  </div>
                </div>
                <MoreHorizontal className="size-4 text-gray-500 dark:text-gray-400" />
              </div>

              {/* Browser Content */}
              <div className="flex-1 bg-gray-100 dark:bg-gray-800 flex items-center justify-center min-h-0 overflow-auto">
                {isRunning && runningTest ? (
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-16 h-16 rounded-2xl bg-green-600/10 dark:bg-green-400/10 flex items-center justify-center">
                      <Loader2 className="size-7 text-green-600 dark:text-green-400 animate-spin" />
                    </div>
                    <div className="text-center">
                      <p className="text-[15px] font-semibold text-gray-700 dark:text-gray-200">
                        {runningTest.id}
                      </p>
                      <p className="text-[12px] text-gray-500 dark:text-gray-400 mt-0.5 max-w-xs">
                        {runningTest.name}
                      </p>
                    </div>
                    <span className="text-[11px] text-gray-400 dark:text-gray-500 flex items-center gap-1.5 bg-white dark:bg-gray-700 px-3 py-1 rounded-full border border-gray-200 dark:border-gray-600">
                      <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                      CDP Screencast — awaiting connection
                    </span>
                  </div>
                ) : completedCount > 0 ? (
                  <div className="flex flex-col items-center gap-2">
                    <CheckCircle2 className="size-12 text-green-500" />
                    <p className="text-[15px] font-medium text-gray-700 dark:text-gray-200">Run Complete</p>
                    <p className="text-[13px] text-gray-500 dark:text-gray-400">
                      {passedCount} passed, {failedCount} failed
                    </p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-20 h-20 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
                      <Play className="size-8 text-gray-400 dark:text-gray-500 ml-0.5" />
                    </div>
                    <p className="text-[14px] text-gray-500 dark:text-gray-400 font-medium">No test running</p>
                    <p className="text-[12px] text-gray-400 dark:text-gray-500">Go to Test Runner, select tests and click Run</p>
                  </div>
                )}
              </div>
            </div>

            {/* Currently running info */}
            {isRunning && runningTest && (
              <div className="flex items-center gap-3 mt-2 px-1">
                <span className="text-[12px] text-gray-500 dark:text-gray-400">
                  Currently: <span className="font-medium text-gray-700 dark:text-gray-200">{runningTest.id}</span> — {runningTest.name}
                </span>
                <Separator orientation="vertical" className="h-3" />
                <span className="text-[12px] text-blue-600 dark:text-blue-400 flex items-center gap-1">
                  <Loader2 className="size-3 animate-spin" />
                  Running...
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Console Output — Full Width */}
        <div className="shrink-0 border-t border-gray-700 flex flex-col" style={{ height: '220px' }}>
          <div className="flex items-center gap-2 px-3 py-1.5 bg-[#1e1e2e] border-b border-gray-700 shrink-0">
            <Terminal className="size-3.5 text-green-400" />
            <span className="text-[11px] font-medium text-gray-400">LIVE CONSOLE</span>
            <span className="text-[10px] text-gray-600 ml-auto font-mono">pytest • test_tax_rate_validation.py</span>
          </div>
          <div className="flex-1 bg-[#1a1a2e] overflow-auto p-2">
            <div className="space-y-0">
              {consoleLines.map((line, i) => (
                <div
                  key={i}
                  className={`text-[11px] font-mono leading-4 ${
                    line.includes('PASSED') || line.includes('✅')
                      ? 'text-green-400'
                      : line.includes('FAILED') || line.includes('❌') || line.includes('ERROR')
                        ? 'text-red-400'
                        : line.includes('Running') || line.includes('Navigating') || line.includes('Clicking')
                          ? 'text-yellow-300'
                          : line.startsWith('>')
                            ? 'text-blue-300'
                            : 'text-gray-400'
                  }`}
                >
                  {line}
                </div>
              ))}
              <div ref={consoleEndRef} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── REPORT TO ADMIN DIALOG ──────────────────────────────
// ─── MY TICKETS TAB (Feature 1 & 2 & 4) ─────────────────
function MyTicketsTab({ userName, userEmail }: { userName: string; userEmail: string }) {
  const [filter, setFilter] = useState<string>('all')
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [reports, setReports] = useState<BugReport[]>([])
  const [followUpText, setFollowUpText] = useState('')
  const [replyingTo, setReplyingTo] = useState<string | null>(null)

  useEffect(() => {
    const refresh = () => {
      const all = getBugReports().filter((r) => r.reporterEmail === userEmail)
      setReports(all)
      // Mark all as read by user
      all.forEach((r) => markReportReadByUser(r))
    }
    refresh()
    const interval = setInterval(refresh, 3000)
    return () => clearInterval(interval)
  }, [userEmail])

  const handleFollowUp = useCallback((reportId: string) => {
    if (!followUpText.trim()) return
    addReplyToReport(reportId, { authorName: userName, authorRole: 'user', message: followUpText.trim() })
    setFollowUpText('')
    setReplyingTo(null)
    const all = getBugReports().filter((r) => r.reporterEmail === userEmail)
    setReports(all)
    toast.success('Follow-up sent')
  }, [followUpText, userName, userEmail])

  const filtered = useMemo(() => {
    if (filter === 'all') return reports
    return reports.filter((r) => r.status === filter)
  }, [reports, filter])

  const openCount = reports.filter((r) => r.status === 'open').length
  const inProgressCount = reports.filter((r) => r.status === 'in-progress').length
  const fixedCount = reports.filter((r) => r.status === 'fixed').length

  const statusConfig: Record<string, { label: string; color: string; dot: string }> = {
    'open': { label: 'Open', color: 'text-orange-700 bg-orange-100 dark:text-orange-300 dark:bg-orange-900/40', dot: 'bg-orange-500' },
    'in-progress': { label: 'In Progress', color: 'text-blue-700 bg-blue-100 dark:text-blue-300 dark:bg-blue-900/40', dot: 'bg-blue-500' },
    'fixed': { label: 'Fixed', color: 'text-green-700 bg-green-100 dark:text-green-300 dark:bg-green-900/40', dot: 'bg-green-500' },
  }

  const priorityConfig: Record<string, { label: string; color: string; emoji: string }> = {
    'high': { label: 'High', color: 'text-red-700 bg-red-100 dark:text-red-300 dark:bg-red-900/40', emoji: '🔴' },
    'medium': { label: 'Medium', color: 'text-orange-700 bg-orange-100 dark:text-orange-300 dark:bg-orange-900/40', emoji: '🟡' },
    'low': { label: 'Low', color: 'text-green-700 bg-green-100 dark:text-green-300 dark:bg-green-900/40', emoji: '🟢' },
  }

  const formatDate = (iso: string) => {
    try {
      const d = new Date(iso)
      return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
    } catch { return iso }
  }

  return (
    <div className="flex flex-col h-full overflow-auto">
      <div className="p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-[18px] font-semibold text-gray-800 dark:text-gray-100 flex items-center gap-2">
              <Ticket className="size-5 text-green-600" />
              My Tickets
            </h2>
            <p className="text-[13px] text-gray-500 dark:text-gray-400 mt-0.5">Bug reports you have raised</p>
          </div>
          <span className="text-[12px] text-gray-500 dark:text-gray-400">{reports.length} total</span>
        </div>

        {/* Summary */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-3 border border-orange-100 dark:border-orange-800/50">
            <div className="text-[11px] text-orange-600 dark:text-orange-400 font-medium uppercase">Open</div>
            <div className="text-xl font-bold text-orange-700 dark:text-orange-400 mt-0.5">{openCount}</div>
          </div>
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 border border-blue-100 dark:border-blue-800/50">
            <div className="text-[11px] text-blue-600 dark:text-blue-400 font-medium uppercase">In Progress</div>
            <div className="text-xl font-bold text-blue-700 dark:text-blue-400 mt-0.5">{inProgressCount}</div>
          </div>
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 border border-green-100 dark:border-green-800/50">
            <div className="text-[11px] text-green-600 dark:text-green-400 font-medium uppercase">Fixed</div>
            <div className="text-xl font-bold text-green-700 dark:text-green-400 mt-0.5">{fixedCount}</div>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-1.5">
          {(['all', 'open', 'in-progress', 'fixed'] as const).map((f) => {
            const count = f === 'all' ? reports.length : f === 'open' ? openCount : f === 'in-progress' ? inProgressCount : fixedCount
            return (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1.5 rounded-md text-[12px] font-medium transition-colors cursor-pointer ${
                  filter === f
                    ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                    : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                }`}
              >
                {f === 'all' ? 'All' : f === 'in-progress' ? 'In Progress' : f.charAt(0).toUpperCase() + f.slice(1)} ({count})
              </button>
            )
          })}
        </div>

        {/* Ticket List */}
        {filtered.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-8 text-center">
            <Ticket className="size-10 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
            <p className="text-[14px] text-gray-500 dark:text-gray-400 font-medium">No tickets raised yet</p>
            <p className="text-[12px] text-gray-400 dark:text-gray-500 mt-1">
              Bug reports from test runs will appear here
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
                      ? 'border-orange-200 dark:border-orange-800/40 hover:border-orange-300'
                      : report.status === 'in-progress'
                        ? 'border-blue-200 dark:border-blue-800/40 hover:border-blue-300'
                        : 'border-green-200 dark:border-green-800/40 hover:border-green-300 opacity-70'
                  } ${isExpanded ? 'shadow-sm' : ''}`}
                  onClick={() => setExpandedId(isExpanded ? null : report.id)}
                >
                  <div className="flex items-center gap-3 px-4 py-3">
                    <div className={`w-2.5 h-2.5 rounded-full shrink-0 ${sCfg.dot} ${report.status === 'open' ? 'animate-pulse' : ''}`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-[12px] font-mono font-semibold text-gray-800 dark:text-gray-100">{report.id}</span>
                        <span className="text-[12px] text-gray-400">—</span>
                        <span className="text-[12px] text-gray-700 dark:text-gray-200 truncate">{report.testDescription}</span>
                      </div>
                      <div className="flex items-center gap-2 mt-0.5 text-[11px] text-gray-500 dark:text-gray-400">
                        <span className="font-mono">{report.testId}</span>
                        <span>in</span>
                        <span>{report.moduleName}</span>
                      </div>
                    </div>
                    {/* SLA Badge */}
                    <span className={`inline-flex items-center text-[10px] font-medium px-1.5 py-0.5 rounded-full shrink-0 ${sla.color}`}>
                      {sla.label === 'Overdue' ? '⚠️' : sla.label === 'At Risk' ? '⏰' : '✅'} {sla.remaining}
                    </span>
                    <span className={`inline-flex items-center text-[10px] font-medium px-1.5 py-0.5 rounded-full shrink-0 ${pCfg.color}`}>
                      {pCfg.emoji} {pCfg.label}
                    </span>
                    <Badge variant="outline" className={`text-[10px] px-1.5 py-0 border-0 shrink-0 ${sCfg.color}`}>
                      {sCfg.label}
                    </Badge>
                    {(report.replies?.length ?? 0) > 0 && (
                      <span className="text-[10px] text-gray-400 shrink-0 flex items-center gap-0.5">
                        <MessageSquare className="size-3" /> {report.replies.length}
                      </span>
                    )}
                    <span className="text-[10px] text-gray-400 shrink-0 w-28 text-right">{formatDate(report.createdAt)}</span>
                    <ChevronDown className={`size-4 text-gray-400 shrink-0 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                  </div>

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
                          <div className="text-[11px] text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wider mb-1">Your Note</div>
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
                                  : 'bg-green-50 dark:bg-green-900/10 border-green-100 dark:border-green-800/30'
                              }`}>
                                <div className="flex items-center gap-2 mb-1">
                                  <span className={`text-[11px] font-semibold ${reply.authorRole === 'admin' ? 'text-red-700 dark:text-red-400' : 'text-green-700 dark:text-green-400'}`}>
                                    {reply.authorRole === 'admin' ? '👤 Admin' : '🧑 You'}
                                  </span>
                                  <span className="text-[10px] text-gray-400">{formatDate(reply.createdAt)}</span>
                                </div>
                                <div className="text-[12px] text-gray-700 dark:text-gray-200">{reply.message}</div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Follow Up */}
                      <div>
                        {replyingTo === report.id ? (
                          <div className="flex items-end gap-2">
                            <textarea
                              value={followUpText}
                              onChange={(e) => setFollowUpText(e.target.value)}
                              placeholder="Add a follow-up message..."
                              rows={2}
                              className="flex-1 px-3 py-2 text-[12px] rounded-md border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/50 text-gray-800 dark:text-gray-100 resize-none focus:outline-none focus:ring-2 focus:ring-green-500/20 focus:border-green-500"
                            />
                            <Button
                              size="sm"
                              onClick={() => handleFollowUp(report.id)}
                              disabled={!followUpText.trim()}
                              className="bg-green-600 hover:bg-green-700 text-white text-[12px] cursor-pointer shrink-0"
                            >
                              <Send className="size-3 mr-1" /> Send
                            </Button>
                          </div>
                        ) : (
                          <button
                            onClick={() => { setReplyingTo(report.id); setFollowUpText('') }}
                            className="text-[12px] text-green-600 hover:text-green-700 font-medium cursor-pointer flex items-center gap-1"
                          >
                            <MessageSquare className="size-3.5" /> Follow Up
                          </button>
                        )}
                      </div>

                      {/* Meta */}
                      <div className="text-[11px] text-gray-400 dark:text-gray-500">
                        Reported: {formatDate(report.createdAt)} • Updated: {formatDate(report.updatedAt)}
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

// ─── SCHEDULE RUNS TAB (Feature 5) ────────────────────────
function ScheduleRunsTab({ userName, sidebarModules }: { userName: string; sidebarModules: SidebarModule[] }) {
  const [runs, setRuns] = useState<ScheduledRun[]>([])
  const [showForm, setShowForm] = useState(false)
  const [moduleId, setModuleId] = useState('tax-rate')
  const [frequency, setFrequency] = useState<'one-time' | 'daily' | 'weekly'>('one-time')
  const [scheduledDate, setScheduledDate] = useState('')
  const [scheduledTime, setScheduledTime] = useState('')
  const [weeklyDay, setWeeklyDay] = useState('1')
  const [testSelection, setTestSelection] = useState<'all' | 'priority' | 'selected'>('all')
  const [countdown, setCountdown] = useState<Record<string, string>>({})

  // Load runs
  useEffect(() => {
    const loadRuns = () => setRuns(getScheduledRuns())
    loadRuns()
  }, [])

  // Countdown timer
  useEffect(() => {
    const tick = () => {
      const now = new Date()
      const newCountdown: Record<string, string> = {}
      for (const run of runs) {
        if (!run.enabled) continue
        const target = new Date(run.scheduledTime)
        const diff = target.getTime() - now.getTime()
        if (diff <= 0) {
          newCountdown[run.id] = 'Due now!'
          // Trigger mock execution for demo
          if (diff > -2000) {
            updateScheduledRun(run.id, { lastRunAt: new Date().toISOString(), enabled: false })
            addNotification({ type: 'run_complete', title: 'Scheduled run completed', message: `Scheduled run for ${run.moduleName} completed (mock)` })
            setRuns(getScheduledRuns())
            toast.success(`Scheduled run for ${run.moduleName} completed!`)
          }
        } else {
          const h = Math.floor(diff / 3600000)
          const m = Math.floor((diff % 3600000) / 60000)
          const s = Math.floor((diff % 60000) / 1000)
          newCountdown[run.id] = h > 0 ? `${h}h ${m}m ${s}s` : m > 0 ? `${m}m ${s}s` : `${s}s`
        }
      }
      setCountdown(newCountdown)
    }
    tick()
    const interval = setInterval(tick, 1000)
    return () => clearInterval(interval)
  }, [runs])

  const handleAddRun = useCallback(() => {
    let scheduledTimeStr = ''
    if (frequency === 'one-time' && scheduledDate && scheduledTime) {
      scheduledTimeStr = new Date(`${scheduledDate}T${scheduledTime}`).toISOString()
    } else if (frequency === 'daily' && scheduledTime) {
      const tomorrow = new Date()
      tomorrow.setDate(tomorrow.getDate() + 1)
      scheduledTimeStr = new Date(`${tomorrow.toISOString().split('T')[0]}T${scheduledTime}`).toISOString()
    } else if (frequency === 'weekly' && scheduledTime) {
      const now = new Date()
      const dayNum = parseInt(weeklyDay)
      const daysUntil = ((dayNum - now.getDay() + 7) % 7) || 7
      const target = new Date(now)
      target.setDate(target.getDate() + daysUntil)
      scheduledTimeStr = new Date(`${target.toISOString().split('T')[0]}T${scheduledTime}`).toISOString()
    } else {
      // Quick test: 10 seconds from now
      scheduledTimeStr = new Date(Date.now() + 10000).toISOString()
    }

    if (!scheduledTimeStr) return

    const mod = sidebarModules.find((m) => m.id === moduleId) || sidebarModules.find((m) => m.children?.some((c) => c.id === moduleId))
    const modName = mod?.label || moduleId

    addScheduledRun({
      moduleId,
      moduleName: modName,
      frequency,
      scheduledTime: scheduledTimeStr,
      testSelection,
      enabled: true,
      createdBy: userName,
    })
    setRuns(getScheduledRuns())
    setShowForm(false)
    toast.success(`Scheduled run created for ${modName}`)
  }, [moduleId, frequency, scheduledDate, scheduledTime, weeklyDay, testSelection, userName])

  const handleDelete = useCallback((id: string) => {
    deleteScheduledRun(id)
    setRuns(getScheduledRuns())
    toast.success('Schedule deleted')
  }, [])

  const handleToggle = useCallback((id: string, enabled: boolean) => {
    updateScheduledRun(id, { enabled: !enabled })
    setRuns(getScheduledRuns())
  }, [])

  const formatDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
    } catch { return iso }
  }

  const allModuleOptions = useMemo(() => {
    const opts: { id: string; label: string }[] = []
    for (const mod of sidebarModules) {
      if (mod.children) {
        for (const child of mod.children) {
          opts.push({ id: child.id, label: `${mod.label} > ${child.label}` })
        }
      } else {
        opts.push({ id: mod.id, label: mod.label })
      }
    }
    return opts
  }, [])

  return (
    <div className="flex flex-col h-full overflow-auto">
      <div className="p-4 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-[14px] font-semibold text-gray-800 dark:text-gray-100 flex items-center gap-2">
              <CalendarClock className="size-4 text-green-600" />
              Run Scheduling
            </h3>
            <p className="text-[12px] text-gray-500 dark:text-gray-400 mt-0.5">Schedule future test runs</p>
          </div>
          <Button
            size="sm"
            onClick={() => setShowForm(!showForm)}
            className="bg-green-600 hover:bg-green-700 text-white text-[12px] cursor-pointer"
          >
            <Plus className="size-3.5 mr-1" /> New Schedule
          </Button>
        </div>

        {/* Create Form */}
        {showForm && (
          <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700 p-4 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label className="text-[12px]">Module</Label>
                <Select value={moduleId} onValueChange={setModuleId}>
                  <SelectTrigger className="h-9 text-[12px]"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {allModuleOptions.map((opt) => (
                      <SelectItem key={opt.id} value={opt.id}>{opt.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label className="text-[12px]">Frequency</Label>
                <Select value={frequency} onValueChange={(v) => setFrequency(v as 'one-time' | 'daily' | 'weekly')}>
                  <SelectTrigger className="h-9 text-[12px]"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="one-time">One-time</SelectItem>
                    <SelectItem value="daily">Daily</SelectItem>
                    <SelectItem value="weekly">Weekly</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {frequency === 'one-time' && (
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label className="text-[12px]">Date</Label>
                  <Input type="date" value={scheduledDate} onChange={(e) => setScheduledDate(e.target.value)} className="h-9 text-[12px]" />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-[12px]">Time</Label>
                  <Input type="time" value={scheduledTime} onChange={(e) => setScheduledTime(e.target.value)} className="h-9 text-[12px]" />
                </div>
              </div>
            )}

            {frequency === 'daily' && (
              <div className="space-y-1.5">
                <Label className="text-[12px]">Time</Label>
                <Input type="time" value={scheduledTime} onChange={(e) => setScheduledTime(e.target.value)} className="h-9 text-[12px] w-48" />
              </div>
            )}

            {frequency === 'weekly' && (
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label className="text-[12px]">Day of Week</Label>
                  <Select value={weeklyDay} onValueChange={setWeeklyDay}>
                    <SelectTrigger className="h-9 text-[12px]"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">Monday</SelectItem>
                      <SelectItem value="2">Tuesday</SelectItem>
                      <SelectItem value="3">Wednesday</SelectItem>
                      <SelectItem value="4">Thursday</SelectItem>
                      <SelectItem value="5">Friday</SelectItem>
                      <SelectItem value="6">Saturday</SelectItem>
                      <SelectItem value="0">Sunday</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label className="text-[12px]">Time</Label>
                  <Input type="time" value={scheduledTime} onChange={(e) => setScheduledTime(e.target.value)} className="h-9 text-[12px]" />
                </div>
              </div>
            )}

            <div className="space-y-1.5">
              <Label className="text-[12px]">Tests to Run</Label>
              <Select value={testSelection} onValueChange={(v) => setTestSelection(v as 'all' | 'priority' | 'selected')}>
                <SelectTrigger className="h-9 text-[12px]"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Tests</SelectItem>
                  <SelectItem value="priority">Priority Only (Smoke + Regression)</SelectItem>
                  <SelectItem value="selected">Selected Tests</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-2 pt-1">
              <Button size="sm" onClick={handleAddRun} className="bg-green-600 hover:bg-green-700 text-white text-[12px] cursor-pointer">
                <CalendarClock className="size-3.5 mr-1" /> Create Schedule
              </Button>
              <Button size="sm" variant="outline" onClick={() => { setShowForm(false); setFrequency('one-time'); setScheduledDate(''); setScheduledTime('') }} className="text-[12px] cursor-pointer">
                Cancel
              </Button>
              <span className="text-[11px] text-gray-400 ml-auto">
                💡 Leave date/time empty for a 10-second quick test
              </span>
            </div>
          </div>
        )}

        {/* Upcoming Runs */}
        <div>
          <h4 className="text-[13px] font-semibold text-gray-700 dark:text-gray-200 mb-2">Upcoming Scheduled Runs</h4>
          {runs.length === 0 ? (
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 text-center">
              <CalendarClock className="size-8 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
              <p className="text-[13px] text-gray-500 dark:text-gray-400">No scheduled runs</p>
              <p className="text-[11px] text-gray-400 mt-1">Create a schedule to automate test runs</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {runs.map((run) => (
                <div key={run.id} className={`bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-3 flex items-center gap-3 ${!run.enabled ? 'opacity-50' : ''}`}>
                  <div className={`w-2.5 h-2.5 rounded-full shrink-0 ${run.enabled ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
                  <div className="flex-1 min-w-0">
                    <div className="text-[12px] font-medium text-gray-800 dark:text-gray-100 truncate">{run.moduleName}</div>
                    <div className="text-[11px] text-gray-500 dark:text-gray-400 flex items-center gap-2 mt-0.5">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                        run.frequency === 'one-time' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400'
                          : run.frequency === 'daily' ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400'
                            : 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400'
                      }`}>{run.frequency}</span>
                      <span>{formatDate(run.scheduledTime)}</span>
                      <span>•</span>
                      <span>{run.testSelection} tests</span>
                    </div>
                  </div>
                  {run.enabled && countdown[run.id] && (
                    <div className="text-[11px] font-mono text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-900/20 px-2 py-1 rounded flex items-center gap-1">
                      <Timer className="size-3" />
                      {countdown[run.id]}
                    </div>
                  )}
                  {run.lastRunAt && (
                    <span className="text-[10px] text-gray-400">Last: {formatDate(run.lastRunAt)}</span>
                  )}
                  <button onClick={() => handleToggle(run.id, run.enabled)} className="text-[11px] text-gray-500 hover:text-gray-700 cursor-pointer px-2 py-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700">
                    {run.enabled ? 'Disable' : 'Enable'}
                  </button>
                  <button onClick={() => handleDelete(run.id)} className="text-[11px] text-red-500 hover:text-red-700 cursor-pointer px-2 py-1 rounded hover:bg-red-50 dark:hover:bg-red-900/20">
                    Delete
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ─── REPORT TO ADMIN DIALOG ──────────────────────────────
function ReportToAdminDialog({
  open,
  onClose,
  testId,
  testDescription,
  error,
  moduleName,
  userName,
  userEmail,
}: {
  open: boolean
  onClose: () => void
  testId: string
  testDescription: string
  error?: string
  moduleName: string
  userName: string
  userEmail: string
}) {
  const [note, setNote] = useState('')
  const [priority, setPriority] = useState<'low' | 'medium' | 'high'>('medium')
  const [sending, setSending] = useState(false)

  const handleSend = useCallback(() => {
    setSending(true)
    setTimeout(() => {
      addBugReport({
        testId,
        testDescription,
        moduleName,
        error: error || 'Unknown error',
        userNote: note,
        priority,
        reporterName: userName,
        reporterEmail: userEmail,
      })
      setSending(false)
      setNote('')
      setPriority('medium')
      onClose()
      toast.success(`Bug report sent to admin`, {
        description: `${testId} — ${testDescription}`,
        duration: 4000,
      })
    }, 500)
  }, [testId, testDescription, moduleName, error, note, priority, userName, userEmail, onClose])

  useEffect(() => {
    const reset = () => { setNote(''); setPriority('medium') }
    if (open) reset()
  }, [open])

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-[480px] dark:bg-gray-800 dark:border-gray-700">
        <DialogHeader>
          <DialogTitle className="text-[16px] flex items-center gap-2">
            <MessageSquare className="size-5 text-orange-500" />
            Report Issue to Admin
          </DialogTitle>
          <DialogDescription>
            Send a bug report about this test failure to the automation team.
          </DialogDescription>
        </DialogHeader>

        {/* Pre-filled error info */}
        <div className="bg-red-50 dark:bg-red-900/15 rounded-lg p-3 border border-red-100 dark:border-red-800/40 space-y-1.5">
          <div className="flex items-center gap-2 text-[12px]">
            <span className="text-gray-500 dark:text-gray-400 w-16 shrink-0">Test ID</span>
            <span className="font-mono font-semibold text-gray-800 dark:text-gray-100">{testId}</span>
            <span className="text-gray-400 dark:text-gray-500">—</span>
            <span className="text-gray-700 dark:text-gray-200">{testDescription}</span>
          </div>
          <div className="flex items-center gap-2 text-[12px]">
            <span className="text-gray-500 dark:text-gray-400 w-16 shrink-0">Module</span>
            <span className="text-gray-700 dark:text-gray-200">{moduleName}</span>
          </div>
          {error && (
            <div className="flex items-start gap-2 text-[12px]">
              <span className="text-gray-500 dark:text-gray-400 w-16 shrink-0">Error</span>
              <span className="text-red-600 dark:text-red-400 break-all">{error}</span>
            </div>
          )}
        </div>

        {/* User note */}
        <div className="space-y-1.5">
          <Label className="text-[12px] text-gray-700 dark:text-gray-300 font-medium">
            Additional Notes <span className="text-gray-400 font-normal">(optional)</span>
          </Label>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            rows={3}
            className="w-full px-3 py-2 text-[12px] rounded-md border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/50 text-gray-800 dark:text-gray-100 resize-none focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 placeholder:text-gray-400 dark:placeholder:text-gray-500"
            placeholder="Describe what happened or any context that might help..."
          />
        </div>

        {/* Priority */}
        <div className="space-y-1.5">
          <Label className="text-[12px] text-gray-700 dark:text-gray-300 font-medium">Priority</Label>
          <div className="flex gap-2">
            {(['low', 'medium', 'high'] as const).map((p) => (
              <button
                key={p}
                onClick={() => setPriority(p)}
                className={`flex-1 px-3 py-2 rounded-md text-[12px] font-medium transition-all cursor-pointer border ${
                  priority === p
                    ? p === 'high'
                      ? 'bg-red-100 dark:bg-red-900/30 border-red-300 dark:border-red-700 text-red-700 dark:text-red-400 ring-1 ring-red-200 dark:ring-red-800'
                      : p === 'medium'
                        ? 'bg-orange-100 dark:bg-orange-900/30 border-orange-300 dark:border-orange-700 text-orange-700 dark:text-orange-400 ring-1 ring-orange-200 dark:ring-orange-800'
                        : 'bg-green-100 dark:bg-green-900/30 border-green-300 dark:border-green-700 text-green-700 dark:text-green-400 ring-1 ring-green-200 dark:ring-green-800'
                    : 'border-gray-200 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'
                }`}
              >
                {p === 'high' ? '🔴 High' : p === 'medium' ? '🟡 Medium' : '🟢 Low'}
              </button>
            ))}
          </div>
        </div>

        <DialogFooter className="gap-2 pt-1">
          <Button variant="outline" onClick={onClose} className="cursor-pointer text-[12px]">Cancel</Button>
          <Button onClick={handleSend} disabled={sending} className="bg-orange-500 hover:bg-orange-600 text-white cursor-pointer text-[12px] gap-1.5">
            {sending ? <Loader2 className="size-3.5 animate-spin" /> : <Send className="size-3.5" />}
            {sending ? 'Sending...' : 'Send Report'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─── COMPLETION SUMMARY MODAL (Feature 1) ───────────────
function CompletionSummaryModal({
  open,
  onClose,
  passedCount,
  failedCount,
  totalDuration,
  onViewResults,
  onRerunFailed,
  onNewRun,
}: {
  open: boolean
  onClose: () => void
  passedCount: number
  failedCount: number
  totalDuration: string
  onViewResults: () => void
  onRerunFailed: () => void
  onNewRun: () => void
}) {
  const total = passedCount + failedCount
  const passRate = total > 0 ? Math.round((passedCount / total) * 100) : 0
  const allPassed = failedCount === 0

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-[460px] dark:bg-gray-800 dark:border-gray-700">
        <DialogHeader>
          <DialogTitle className="sr-only">Run Complete</DialogTitle>
          <DialogDescription className="sr-only">Test run completion summary</DialogDescription>
        </DialogHeader>

        {/* Header */}
        <div className={`rounded-lg p-4 text-center ${allPassed ? 'bg-green-50 dark:bg-green-900/20' : 'bg-orange-50 dark:bg-orange-900/20'}`}>
          <div className="flex justify-center mb-2">
            {allPassed ? (
              <div className="w-14 h-14 rounded-full bg-green-100 dark:bg-green-900/40 flex items-center justify-center">
                <CheckCircle2 className="size-8 text-green-600 dark:text-green-400" />
              </div>
            ) : (
              <div className="w-14 h-14 rounded-full bg-orange-100 dark:bg-orange-900/40 flex items-center justify-center">
                <AlertTriangle className="size-8 text-orange-600 dark:text-orange-400" />
              </div>
            )}
          </div>
          <h3 className={`text-[18px] font-bold ${allPassed ? 'text-green-700 dark:text-green-400' : 'text-orange-700 dark:text-orange-400'}`}>
            {allPassed ? 'All Tests Passed!' : 'Tests Completed with Failures'}
          </h3>
          <p className="text-[13px] text-gray-500 dark:text-gray-400 mt-1">
            {allPassed ? 'Congratulations! Every test in this run passed successfully.' : `${failedCount} test${failedCount !== 1 ? 's' : ''} failed. Review results for details.`}
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 text-center border border-green-100 dark:border-green-800/50">
            <div className="text-[11px] text-green-600 dark:text-green-400 font-medium uppercase">Passed</div>
            <div className="text-2xl font-bold text-green-700 dark:text-green-400 mt-1">{passedCount}</div>
          </div>
          <div className={`rounded-lg p-3 text-center border ${failedCount > 0 ? 'bg-red-50 dark:bg-red-900/20 border-red-100 dark:border-red-800/50' : 'bg-gray-50 dark:bg-gray-800 border-gray-100 dark:border-gray-700'}`}>
            <div className={`text-[11px] font-medium uppercase ${failedCount > 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-500 dark:text-gray-400'}`}>Failed</div>
            <div className={`text-2xl font-bold mt-1 ${failedCount > 0 ? 'text-red-700 dark:text-red-400' : 'text-gray-500 dark:text-gray-400'}`}>{failedCount}</div>
          </div>
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 text-center border border-gray-100 dark:border-gray-700">
            <div className="text-[11px] text-gray-500 dark:text-gray-400 font-medium uppercase">Duration</div>
            <div className="text-lg font-bold text-gray-800 dark:text-gray-100 mt-1">{totalDuration}</div>
          </div>
        </div>

        {/* Pass Rate */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-[12px]">
            <span className="text-gray-600 dark:text-gray-300 font-medium">Pass Rate</span>
            <span className={`font-bold ${passRate === 100 ? 'text-green-600 dark:text-green-400' : passRate >= 75 ? 'text-orange-600 dark:text-orange-400' : 'text-red-600 dark:text-red-400'}`}>
              {passRate}%
            </span>
          </div>
          <Progress value={passRate} className="h-2.5" />
        </div>

        {/* Actions */}
        <DialogFooter className="flex-col sm:flex-row gap-2 pt-2">
          <Button onClick={onViewResults} variant="outline" className="flex-1 h-9 text-[13px] gap-2 border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 cursor-pointer">
            <ClipboardList className="size-4" />
            View Results
          </Button>
          {failedCount > 0 && (
            <Button onClick={onRerunFailed} className="flex-1 h-9 text-[13px] gap-2 bg-orange-500 hover:bg-orange-600 text-white cursor-pointer">
              <RotateCcw className="size-4" />
              Rerun Failed
            </Button>
          )}
          <Button onClick={onNewRun} className="flex-1 h-9 text-[13px] gap-2 bg-[#1976d2] hover:bg-[#1565c0] text-white cursor-pointer">
            <RotateCcw className="size-4" />
            New Run
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─── RESULTS TAB ─────────────────────────────────────────
function ResultsTab({
  tests,
  passedCount,
  failedCount,
  totalCount,
  runHistory,
  onReportTest,
}: {
  tests: TestItem[]
  passedCount: number
  failedCount: number
  totalCount: number
  runHistory: RunSnapshot[]
  onReportTest: (test: TestItem) => void
}) {
  const passRate = Math.round((passedCount / totalCount) * 100)
  const [resultFilter, setResultFilter] = useState<'all' | 'passed' | 'failed'>('all')
  const [compareRun1, setCompareRun1] = useState<string>('')
  const [compareRun2, setCompareRun2] = useState<string>('')

  const filteredTests = tests.filter((t) => {
    if (resultFilter === 'all') return true
    return resultFilter === 'passed' ? t.status === 'passed' : t.status === 'failed'
  })

  // Get error info from testSpecGroups
  const getTestError = (id: string): string | undefined => {
    for (const g of testSpecGroups) {
      const t = g.tests.find((x) => x.id === id)
      if (t) return t.error
    }
    return undefined
  }

  // Comparison logic (Feature 5)
  const comparisonData = useMemo(() => {
    if (!compareRun1 || !compareRun2) return null
    const run1 = runHistory.find((r) => String(r.id) === compareRun1)
    const run2 = runHistory.find((r) => String(r.id) === compareRun2)
    if (!run1 || !run2) return null

    const allTestIds = new Set([...run1.results.map((r) => r.testId), ...run2.results.map((r) => r.testId)])
    const rows: {
      testId: string
      testName: string
      run1Status: 'passed' | 'failed' | 'skipped'
      run2Status: 'passed' | 'failed' | 'skipped'
      change: 'fixed' | 'regressed' | 'unchanged'
    }[] = []

    let improved = 0
    let regressed = 0
    let unchanged = 0

    for (const id of allTestIds) {
      const r1 = run1.results.find((r) => r.testId === id)
      const r2 = run2.results.find((r) => r.testId === id)
      const s1 = r1?.status || 'skipped' as const
      const s2 = r2?.status || 'skipped' as const
      let change: 'fixed' | 'regressed' | 'unchanged' = 'unchanged'
      if (s1 === 'failed' && s2 === 'passed') { change = 'fixed'; improved++ }
      else if (s1 === 'passed' && s2 === 'failed') { change = 'regressed'; regressed++ }
      else { unchanged++ }

      // Find test name
      let testName = id
      for (const g of testSpecGroups) {
        const t = g.tests.find((x) => x.id === id)
        if (t) { testName = t.description; break }
      }

      rows.push({ testId: id, testName, run1Status: s1, run2Status: s2, change })
    }

    return { rows, improved, regressed, unchanged, run1Label: run1.date, run2Label: run2.date }
  }, [compareRun1, compareRun2, runHistory])

  return (
    <div className="flex flex-col h-full overflow-auto">
      {/* Summary Cards */}
      <div className="px-4 pt-4 pb-3 shrink-0">
        <h3 className="text-[14px] font-semibold text-gray-800 dark:text-gray-100 mb-3">Test Results Summary</h3>
        <div className="grid grid-cols-4 gap-3">
          <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4 border border-gray-100 dark:border-gray-700">
            <div className="text-[12px] text-gray-500 dark:text-gray-400 font-medium mb-1">Total Tests</div>
            <div className="text-2xl font-bold text-gray-800 dark:text-gray-100">{totalCount}</div>
          </div>
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 border border-green-100 dark:border-green-800/50">
            <div className="text-[12px] text-green-600 dark:text-green-400 font-medium mb-1">Passed</div>
            <div className="text-2xl font-bold text-green-700 dark:text-green-400">{passedCount}</div>
          </div>
          <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4 border border-red-100 dark:border-red-800/50">
            <div className="text-[12px] text-red-600 dark:text-red-400 font-medium mb-1">Failed</div>
            <div className="text-2xl font-bold text-red-700 dark:text-red-400">{failedCount}</div>
          </div>
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-100 dark:border-blue-800/50">
            <div className="text-[12px] text-blue-600 dark:text-blue-400 font-medium mb-1">Pass Rate</div>
            <div className="text-2xl font-bold text-blue-700 dark:text-blue-400">{passRate}%</div>
            <Progress value={passRate} className="h-1.5 mt-2 bg-blue-100 dark:bg-blue-800" />
          </div>
        </div>
      </div>

      <Separator className="mx-4" />

      {/* Run Results Drill-Down */}
      <div className="px-4 pt-3 pb-3 shrink-0">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-[14px] font-semibold text-gray-800 dark:text-gray-100">Run Results</h3>
          <div className="flex items-center gap-1">
            {(['all', 'passed', 'failed'] as const).map((f) => (
              <button
                key={f}
                onClick={() => setResultFilter(f)}
                className={`px-2.5 py-1 rounded-md text-[12px] font-medium transition-colors cursor-pointer ${
                  resultFilter === f
                    ? f === 'failed'
                      ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                      : f === 'passed'
                        ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200'
                    : 'text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
                }`}
              >
                {f === 'all' ? `All (${totalCount})` : f === 'passed' ? `Passed (${passedCount})` : `Failed (${failedCount})`}
              </button>
            ))}
          </div>
        </div>
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                <TableHead className="text-[12px] font-semibold text-gray-600 dark:text-gray-300 w-12">Status</TableHead>
                <TableHead className="text-[12px] font-semibold text-gray-600 dark:text-gray-300 w-14">ID</TableHead>
                <TableHead className="text-[12px] font-semibold text-gray-600 dark:text-gray-300">Test</TableHead>
                <TableHead className="text-[12px] font-semibold text-gray-600 dark:text-gray-300 w-16 text-center">Duration</TableHead>
                <TableHead className="text-[12px] font-semibold text-gray-600 dark:text-gray-300">Error</TableHead>
                <TableHead className="text-[12px] font-semibold text-gray-600 dark:text-gray-300 w-24 text-center">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredTests.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-[13px] text-gray-400 dark:text-gray-500 py-6">
                    No {resultFilter} tests
                  </TableCell>
                </TableRow>
              ) : (
                filteredTests.map((test) => {
                  const error = getTestError(test.id)
                  return (
                    <TableRow key={test.id} className={`dark:border-gray-700 ${test.status === 'failed' ? 'bg-red-50/30 dark:bg-red-900/10' : ''}`}>
                      <TableCell>
                        <TestStatusIcon status={test.status} size={3.5} />
                      </TableCell>
                      <TableCell className="text-[12px] font-mono text-gray-500 dark:text-gray-400">{test.id}</TableCell>
                      <TableCell className={`text-[13px] ${test.status === 'failed' ? 'text-red-700 dark:text-red-400 font-medium' : 'text-gray-700 dark:text-gray-200'}`}>
                        {test.name}
                      </TableCell>
                      <TableCell className="text-center text-[12px] font-mono text-gray-500 dark:text-gray-400">{test.duration}</TableCell>
                      <TableCell className="text-[12px] text-red-500 dark:text-red-400 max-w-[250px] truncate">
                        {error || '—'}
                      </TableCell>
                      <TableCell className="text-center">
                        {test.status === 'failed' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => onReportTest(test)}
                            className="h-7 text-[11px] gap-1 text-orange-600 hover:text-orange-700 hover:bg-orange-50 dark:text-orange-400 dark:hover:bg-orange-900/20 cursor-pointer"
                          >
                            <MessageSquare className="size-3" />
                            Report
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  )
                })
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      <Separator className="mx-4" />

      {/* Compare Runs Section (Feature 5) */}
      <div className="px-4 pt-3 pb-3 shrink-0">
        <h3 className="text-[14px] font-semibold text-gray-800 dark:text-gray-100 mb-3 flex items-center gap-2">
          <GitCompare className="size-4 text-gray-500 dark:text-gray-400" />
          Compare Runs
        </h3>
        <div className="flex items-center gap-3 mb-3 flex-wrap">
          <div className="flex items-center gap-2">
            <span className="text-[12px] text-gray-500 dark:text-gray-400 font-medium">Run 1:</span>
            <Select value={compareRun1} onValueChange={setCompareRun1}>
              <SelectTrigger className="h-8 w-56 text-[12px] bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-600">
                <SelectValue placeholder="Select a run..." />
              </SelectTrigger>
              <SelectContent>
                {runHistory.map((r) => (
                  <SelectItem key={r.id} value={String(r.id)}>
                    {r.date} ({r.rate}%)
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <span className="text-gray-400 dark:text-gray-500 text-lg">vs</span>
          <div className="flex items-center gap-2">
            <span className="text-[12px] text-gray-500 dark:text-gray-400 font-medium">Run 2:</span>
            <Select value={compareRun2} onValueChange={setCompareRun2}>
              <SelectTrigger className="h-8 w-56 text-[12px] bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-600">
                <SelectValue placeholder="Select a run..." />
              </SelectTrigger>
              <SelectContent>
                {runHistory.map((r) => (
                  <SelectItem key={r.id} value={String(r.id)}>
                    {r.date} ({r.rate}%)
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {comparisonData ? (
          <>
            {/* Summary */}
            <div className="flex items-center gap-4 mb-3">
              <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                ✅ {comparisonData.improved} Fixed
              </span>
              <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400">
                ❌ {comparisonData.regressed} Regressed
              </span>
              <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">
                ➡️ {comparisonData.unchanged} Unchanged
              </span>
            </div>

            {/* Comparison Table */}
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                    <TableHead className="text-[12px] font-semibold text-gray-600 dark:text-gray-300 w-14">Test ID</TableHead>
                    <TableHead className="text-[12px] font-semibold text-gray-600 dark:text-gray-300">Test Name</TableHead>
                    <TableHead className="text-[12px] font-semibold text-gray-600 dark:text-gray-300 text-center">{comparisonData.run1Label}</TableHead>
                    <TableHead className="text-[12px] font-semibold text-gray-600 dark:text-gray-300 text-center">{comparisonData.run2Label}</TableHead>
                    <TableHead className="text-[12px] font-semibold text-gray-600 dark:text-gray-300 text-center">Change</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {comparisonData.rows.map((row) => (
                    <TableRow key={row.testId} className="dark:border-gray-700">
                      <TableCell className="text-[12px] font-mono text-gray-500 dark:text-gray-400">{row.testId}</TableCell>
                      <TableCell className="text-[13px] text-gray-700 dark:text-gray-200">{row.testName}</TableCell>
                      <TableCell className="text-center">
                        <TestStatusIcon status={row.run1Status} size={3.5} />
                      </TableCell>
                      <TableCell className="text-center">
                        <TestStatusIcon status={row.run2Status} size={3.5} />
                      </TableCell>
                      <TableCell className="text-center">
                        <span className={`text-[12px] font-medium ${
                          row.change === 'fixed' ? 'text-green-600 dark:text-green-400' :
                          row.change === 'regressed' ? 'text-red-600 dark:text-red-400' :
                          'text-gray-500 dark:text-gray-400'
                        }`}>
                          {row.change === 'fixed' ? '✅ Fixed' : row.change === 'regressed' ? '❌ Regressed' : '➡️ Unchanged'}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </>
        ) : (
          <div className="text-center py-6 text-gray-400 dark:text-gray-500">
            <GitCompare className="size-8 mx-auto mb-2 opacity-50" />
            <p className="text-[13px]">Select two runs above to compare</p>
          </div>
        )}
      </div>

      <Separator className="mx-4" />

      {/* Recent Runs */}
      <div className="px-4 pt-3 pb-3 shrink-0">
        <h3 className="text-[14px] font-semibold text-gray-800 dark:text-gray-100 mb-3">Recent Runs</h3>
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                <TableHead className="text-[12px] font-semibold text-gray-600 dark:text-gray-300">Date</TableHead>
                <TableHead className="text-[12px] font-semibold text-gray-600 dark:text-gray-300">Duration</TableHead>
                <TableHead className="text-[12px] font-semibold text-gray-600 dark:text-gray-300 text-center">Passed</TableHead>
                <TableHead className="text-[12px] font-semibold text-gray-600 dark:text-gray-300 text-center">Failed</TableHead>
                <TableHead className="text-[12px] font-semibold text-gray-600 dark:text-gray-300 text-center">Rate</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {runHistory.slice(0, 5).map((run) => (
                <TableRow key={run.id} className="dark:border-gray-700">
                  <TableCell className="text-[13px] text-gray-700 dark:text-gray-200">{run.date}</TableCell>
                  <TableCell className="text-[13px] text-gray-600 dark:text-gray-400 font-mono">{run.duration}</TableCell>
                  <TableCell className="text-center">
                    <span className="text-green-600 dark:text-green-400 font-medium text-[13px]">{run.passed}</span>
                  </TableCell>
                  <TableCell className="text-center">
                    <span className={`font-medium text-[13px] ${run.failed > 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-400 dark:text-gray-500'}`}>
                      {run.failed}
                    </span>
                  </TableCell>
                  <TableCell className="text-center">
                    <span
                      className={`text-[12px] font-medium px-2 py-0.5 rounded-full ${
                        run.rate >= 90
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                          : run.rate >= 75
                            ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
                            : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                      }`}
                    >
                      {run.rate}%
                    </span>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>

      <Separator className="mx-4" />

      {/* Bug Registry */}
      <div className="px-4 pt-3 pb-4">
        <h3 className="text-[14px] font-semibold text-gray-800 dark:text-gray-100 mb-3">Bug Registry</h3>
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                <TableHead className="text-[12px] font-semibold text-gray-600 dark:text-gray-300">Bug ID</TableHead>
                <TableHead className="text-[12px] font-semibold text-gray-600 dark:text-gray-300">Description</TableHead>
                <TableHead className="text-[12px] font-semibold text-gray-600 dark:text-gray-300 text-center">Status</TableHead>
                <TableHead className="text-[12px] font-semibold text-gray-600 dark:text-gray-300">Related Tests</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {bugRegistry.map((bug) => (
                <TableRow key={bug.id} className="dark:border-gray-700">
                  <TableCell className="text-[13px] font-mono text-gray-600 dark:text-gray-400">{bug.id}</TableCell>
                  <TableCell className="text-[13px] text-gray-700 dark:text-gray-200">{bug.desc}</TableCell>
                  <TableCell className="text-center">
                    <span
                      className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${
                        bug.status === 'Open' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                      }`}
                    >
                      {bug.status}
                    </span>
                  </TableCell>
                  <TableCell className="text-[13px] text-gray-500 dark:text-gray-400">{bug.tests}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  )
}

// ─── MAIN PAGE COMPONENT ─────────────────────────────────
export default function Home() {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)
  const [sidebarModules, setSidebarModules] = useState<SidebarModule[]>(ALL_SIDEBAR_MODULES)
  const [apiModules, setApiModules] = useState<ApiModule[]>([])
  const [selectedModule, setSelectedModule] = useState<string>('dashboard')
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set(['common-settings']))
  const [activeTab, setActiveTab] = useState('operations')
  const [consoleOpen, setConsoleOpen] = useState(false)
  const [testChecks, setTestChecks] = useState<Set<string>>(new Set())
  const [tests, setTests] = useState<TestItem[]>(initialTests)
  const [isRunning, setIsRunning] = useState(false)
  const [runningProgress, setRunningProgress] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(true)
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

  // Poll notifications every 2s
  useEffect(() => {
    const poll = () => {
      setUnreadCount(getUnreadNotificationCount())
      setNotifications(getNotifications())
    }
    poll()
    const interval = setInterval(poll, 2000)
    return () => clearInterval(interval)
  }, [])

  // ─── Fetch real modules from API ──────────────────────
  useEffect(() => {
    fetchModules()
      .then((mods) => {
        setApiModules(mods)
        setSidebarModules(buildSidebarModules(mods))
      })
      .catch((err) => {
        console.warn('API modules fetch failed, using defaults:', err)
        // Keep ALL_SIDEBAR_MODULES on failure
      })
  }, [])

  const handleMarkAllRead = useCallback(() => {
    markAllNotificationsRead()
    setUnreadCount(0)
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))
  }, [])

  // Feature 5: Run history
  const [runHistory, setRunHistory] = useState<RunSnapshot[]>(initialRunHistory)
  const runIdCounterRef = useRef(initialRunHistory.length + 1)

  // Feature 6: Dark mode
  const [darkMode, setDarkMode] = useState(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('rhythmerp-dark-mode')
      if (stored !== null) return stored === 'true'
      return window.matchMedia('(prefers-color-scheme: dark)').matches
    }
    return false
  })

  // Persist dark mode & toggle class
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
    localStorage.setItem('rhythmerp-dark-mode', String(darkMode))
  }, [darkMode])

  const toggleDarkMode = useCallback(() => {
    setDarkMode((prev) => !prev)
  }, [])

  // Keyboard shortcut: Ctrl+B to toggle sidebar, Cmd+K / Ctrl+K for quick switcher
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
        e.preventDefault()
        setSidebarOpen((prev) => !prev)
      }
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        setQuickSwitcherOpen((prev) => !prev)
        setQuickSearch('')
      }
      if (e.key === 'Escape' && quickSwitcherOpen) {
        setQuickSwitcherOpen(false)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [quickSwitcherOpen])

  // Auto-hide sidebar on Live Execution, show on other tabs
  useEffect(() => {
    if (activeTab === 'live-execution') {
      setSidebarOpen(false)
    } else if (activeTab === 'operations' || activeTab === 'test-runner' || activeTab === 'results') {
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
        // Calculate total duration
        const durations = tests
          .filter((t) => t.duration && t.duration !== '—' && t.duration !== '...' && t.duration !== '')
          .map((t) => {
            const parts = t.duration.split(':')
            return parseInt(parts[0]) * 60 + parseInt(parts[1])
          })
        const totalSecs = durations.reduce((a, b) => a + b, 0)
        const mins = Math.floor(totalSecs / 60)
        const secs = totalSecs % 60
        setCompletionStats({
          passed,
          failed,
          duration: `${mins}:${String(secs).padStart(2, '0')}`,
        })
        setCompletionModalOpen(true)
      }
    }
    prevIsRunningRef.current = isRunning
  }, [isRunning, tests])

  // Check session on mount & seed admin
  useEffect(() => {
    const init = async () => {
      try {
        // Seed admin user (idempotent)
        await fetch('/api/auth/seed')
        // Check session
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
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  const handleSelectModule = useCallback((id: string) => {
    setSelectedModule(id)
    setActiveTab('operations')
  }, [])

  const handleGoHome = useCallback(() => {
    setSelectedModule('dashboard')
    setActiveTab('operations')
    setSidebarOpen(true)
  }, [])

  const toggleTestCheck = useCallback((id: string) => {
    setTestChecks((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  // Helper: reset test to pending for rerun
  const rerunTestIds = useCallback((ids: string[]) => {
    setTests((prev) =>
      prev.map((t) => (ids.includes(t.id) ? { ...t, status: 'pending' as const, duration: '' } : t))
    )
    setTestChecks(new Set(ids))
  }, [])

  // Helper: get error for test ID
  const getTestError = useCallback((id: string): string | undefined => {
    for (const g of testSpecGroups) {
      const t = g.tests.find((x) => x.id === id)
      if (t) return t.error
    }
    return undefined
  }, [])

  // Mock run animation
  const mockRunTests = useCallback(
    (selectedOnly: boolean, forceIds?: string[]) => {
      if (isRunning) return
      setIsRunning(true)

      let testsToRun: TestItem[]
      if (forceIds) {
        testsToRun = tests.filter((t) => forceIds.includes(t.id))
      } else if (selectedOnly) {
        testsToRun = tests.filter((t) => testChecks.has(t.id))
      } else {
        testsToRun = tests.filter((t) => t.status === 'pending')
      }

      if (testsToRun.length === 0) {
        setIsRunning(false)
        return
      }

      // Reset all to-be-run tests to pending first
      setTests((prev) =>
        prev.map((t) =>
          testsToRun.some((r) => r.id === t.id) ? { ...t, status: 'pending' as const, duration: '' } : t
        )
      )

      let i = 0
      const interval = setInterval(() => {
        if (i >= testsToRun.length) {
          setIsRunning(false)
          setRunningProgress('')
          clearInterval(interval)
          // Save run to history (Feature 5)
          setTests((currentTests) => {
            const completedTests = currentTests.filter((t) =>
              testsToRun.some((r) => r.id === t.id)
            )
            const passed = completedTests.filter((t) => t.status === 'passed').length
            const failed = completedTests.filter((t) => t.status === 'failed').length
            const results = completedTests.map((t) => ({
              testId: t.id,
              status: t.status as 'passed' | 'failed',
            }))
            const runSnapshot: RunSnapshot = {
              id: runIdCounterRef.current++,
              date: new Date().toLocaleDateString('en-GB', {
                day: 'numeric', month: 'short', year: 'numeric',
              }) + ', ' + new Date().toLocaleTimeString('en-US', {
                hour: 'numeric', minute: '2-digit', hour12: true,
              }),
              moduleId: selectedModule,
              results,
              passed,
              failed,
              total: completedTests.length,
              duration: `${Math.floor(Math.random() * 5) + 2}:${String(Math.floor(Math.random() * 59)).padStart(2, '0')}`,
              rate: completedTests.length > 0 ? Math.round((passed / completedTests.length) * 100) : 0,
            }
            setRunHistory((prev) => [runSnapshot, ...prev])
            return currentTests
          })
          return
        }

        const test = testsToRun[i]
        const willFail = test.id === 'T03' || test.id === 'T09' || test.id === 'T16'

        setTests((prev) =>
          prev.map((t) =>
            t.id === test.id ? { ...t, status: 'running' as const, duration: '...' } : t
          )
        )
        setRunningProgress(`Running ${i + 1}/${testsToRun.length} tests...`)

        setTimeout(() => {
          setTests((prev) =>
            prev.map((t) =>
              t.id === test.id
                ? {
                    ...t,
                    status: willFail ? ('failed' as const) : ('passed' as const),
                    duration: willFail
                      ? '--'
                      : `${Math.floor(Math.random() * 3) + 1}:${String(Math.floor(Math.random() * 59)).padStart(2, '0')}`,
                  }
                : t
            )
          )
          // Fire failure toast
          if (willFail) {
            const error = getTestError(test.id)
            toast.error(`${test.id} failed`, {
              description: error || test.name,
              duration: 6000,
            })
          }
        }, 600)

        i++
      }, 1200)
    },
    [isRunning, tests, testChecks, getTestError, selectedModule]
  )

  // Feature 4: Run by priority
  const runByPriority = useCallback(
    (priority: TestPriority) => {
      if (isRunning) return
      const priorityIds = tests.filter((t) => t.priority === priority).map((t) => t.id)
      if (priorityIds.length === 0) return
      rerunTestIds(priorityIds)
      mockRunTests(true, priorityIds)
      setActiveTab('live-execution')
    },
    [isRunning, tests, rerunTestIds, mockRunTests]
  )

  const passedCount = tests.filter((t) => t.status === 'passed').length
  const failedCount = tests.filter((t) => t.status === 'failed').length

  // Get module display path for breadcrumb
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

  // Feature 1: Completion modal handlers
  const handleViewResults = useCallback(() => {
    setCompletionModalOpen(false)
    setActiveTab('results')
  }, [])

  const handleCompletionRerunFailed = useCallback(() => {
    setCompletionModalOpen(false)
    const failedIds = tests.filter((t) => t.status === 'failed').map((t) => t.id)
    if (failedIds.length > 0) {
      rerunTestIds(failedIds)
      mockRunTests(true, failedIds)
      setActiveTab('live-execution')
    }
  }, [tests, rerunTestIds, mockRunTests])

  const handleNewRun = useCallback(() => {
    setCompletionModalOpen(false)
    // Reset all tests
    setTests(initialTests)
    setTestChecks(new Set())
    setActiveTab('test-runner')
  }, [])

  // Bug report handler
  const handleReportTest = useCallback((test: TestItem) => {
    const error = getTestError(test.id)
    setReportingTest({ id: test.id, name: test.name, error })
    setReportDialogOpen(true)
  }, [getTestError])

  // Loading / Login screen
  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-white dark:bg-gray-900">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-green-600 flex items-center justify-center animate-pulse">
            <span className="text-white text-lg font-bold">R</span>
          </div>
          <Loader2 className="size-5 text-green-600 animate-spin" />
        </div>
      </div>
    )
  }

  if (!user) {
    return <LoginPage onLogin={handleLogin} />
  }

  // Dashboard
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
    { id: 'schedule', label: '🗓️ Schedule' },
  ]

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
              sidebarOpen
                ? 'text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800'
                : 'text-green-600 hover:text-green-700 hover:bg-green-50 dark:hover:bg-green-900/20'
            }`}
            title="Toggle sidebar (Ctrl+B)"
          >
            <Menu className={`size-[18px] transition-transform duration-200 ${sidebarOpen ? '' : 'rotate-90'}`} />
          </Button>
          <Separator orientation="vertical" className="h-5" />
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-md bg-green-600 flex items-center justify-center">
              <span className="text-white text-xs font-bold">R</span>
            </div>
            <span className="text-[15px] font-semibold text-gray-800 dark:text-gray-100 tracking-tight">
              Rhythm<span className="text-green-600">ERP</span>
              <span className="text-gray-400 dark:text-gray-500 font-normal ml-1.5 text-[13px]">Automation Runner</span>
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" className="size-8 text-gray-500 dark:text-gray-400">
            <Search className="size-4" />
          </Button>
          {/* Feature 6: Dark mode toggle */}
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleDarkMode}
            className="size-8 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer"
            title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {darkMode ? <Sun className="size-4" /> : <Moon className="size-4" />}
          </Button>
          {/* Bell Notification */}
          <div className="relative">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => {
                setNotifDropdownOpen((prev) => !prev)
                if (!notifDropdownOpen) handleMarkAllRead()
              }}
              className="size-8 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer relative"
              title="Notifications"
            >
              <Bell className="size-4" />
              {unreadCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-orange-500 text-white text-[9px] font-bold rounded-full flex items-center justify-center">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </Button>
            {notifDropdownOpen && (
              <div className="absolute right-0 top-10 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50">
                <div className="px-3 py-2 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
                  <span className="text-[13px] font-semibold text-gray-800 dark:text-gray-100">Notifications</span>
                  <button onClick={handleMarkAllRead} className="text-[11px] text-green-600 hover:text-green-700 cursor-pointer">Mark all read</button>
                </div>
                <div className="max-h-64 overflow-y-auto">
                  {notifications.length === 0 ? (
                    <div className="p-6 text-center text-[12px] text-gray-400">No notifications yet</div>
                  ) : (
                    notifications.slice(0, 15).map((n) => (
                      <div key={n.id} className={`px-3 py-2 border-b border-gray-50 dark:border-gray-700/50 ${!n.read ? 'bg-green-50/50 dark:bg-green-900/10' : ''}`}>
                        <div className="text-[12px] font-medium text-gray-700 dark:text-gray-200">{n.title}</div>
                        <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5">{n.message}</div>
                        <div className="text-[10px] text-gray-400 mt-0.5">{new Date(n.createdAt).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}</div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
          {(user.role === 'admin' || user.role === 'qa_lead') && (
            <Link href="/admin" className="flex items-center gap-1.5 px-2.5 h-8 text-[12px] text-gray-500 dark:text-gray-400 hover:text-red-700 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md transition-colors" title="Admin Panel">
              <Shield className="size-3.5" />
              <span className="hidden sm:inline">Admin</span>
            </Link>
          )}
          <Separator orientation="vertical" className="h-5 mx-1" />
          <div className="flex items-center gap-2">
            <Avatar className="size-7">
              <AvatarFallback className="bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs font-semibold">
                {userInitials}
              </AvatarFallback>
            </Avatar>
            <span className="text-[12px] text-gray-600 dark:text-gray-300 font-medium max-w-[120px] truncate">
              {user.name}
            </span>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleLogout}
              className="size-8 text-gray-400 hover:text-red-500 cursor-pointer"
              title="Sign out"
            >
              <LogOut className="size-4" />
            </Button>
          </div>
        </div>
      </header>

      {/* ─── BODY ───────────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">
        {/* ─── SIDEBAR ──────────────────────────────────── */}
        <div
          className={`shrink-0 transition-all duration-200 ease-in-out overflow-hidden ${
            sidebarOpen ? 'w-60' : 'w-0'
          }`}
        >
        <aside className="w-60 bg-[#e8f5e9] dark:bg-[#1a2e1a] border-r border-[#c8e6c9] dark:border-[#2d4a2d] flex flex-col h-full">
          <div className="px-3 py-2.5 border-b border-[#c8e6c9] dark:border-[#2d4a2d] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Search className="size-3.5 text-gray-500 dark:text-gray-400" />
              <span className="text-[13px] font-medium text-gray-600 dark:text-gray-300">Module Navigator</span>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors cursor-pointer p-0.5 rounded hover:bg-[#c8e6c9]/50 dark:hover:bg-[#2d4a2d]/50"
              title="Collapse sidebar (Ctrl+B)"
            >
              <ChevronLeft className="size-4" />
            </button>
          </div>
          <ScrollArea className="flex-1">
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
          <div className="px-3 py-2 border-t border-[#c8e6c9] dark:border-[#2d4a2d]">
            <div className="flex items-center gap-2 text-[11px] text-gray-500 dark:text-gray-400">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              Connected to RhythmERP
            </div>
          </div>
        </aside>
        </div>

        {/* ─── MAIN CONTENT ─────────────────────────────── */}
        <main className="flex-1 flex flex-col overflow-hidden bg-white dark:bg-gray-900">
          {/* Breadcrumb (when sidebar collapsed + not on Dashboard) */}
          {!sidebarOpen && selectedModule !== 'dashboard' && (
            <div className="flex items-center gap-1.5 px-4 py-2 border-b border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-900 shrink-0">
              <button
                onClick={handleGoHome}
                className="text-[12px] text-green-600 hover:text-green-700 dark:hover:text-green-400 font-medium cursor-pointer transition-colors hover:underline"
              >
                Dashboard
              </button>
              {modulePath.parent && (
                <>
                  <ChevronRight className="size-3 text-gray-400 dark:text-gray-500" />
                  <span className="text-[12px] text-gray-500 dark:text-gray-400">{modulePath.parent}</span>
                </>
              )}
              <ChevronRight className="size-3 text-gray-400 dark:text-gray-500" />
              <span className="text-[12px] text-gray-800 dark:text-gray-100 font-medium">{modulePath.name}</span>
              {modulePath.badge && (
                <span className="text-[11px] text-orange-600 dark:text-orange-400 ml-1">{modulePath.badge}</span>
              )}
              <div className="flex-1" />
              <span className="text-[11px] text-gray-400 dark:text-gray-500">
                <kbd className="px-1 py-0.5 rounded bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-[10px] font-mono">Ctrl+B</kbd>{' '}
                to toggle
              </span>
            </div>
          )}

          {/* ── DASHBOARD VIEW ── */}
          {selectedModule === 'dashboard' && (
            <DashboardTab onSelectModule={handleSelectModule} />
          )}

          {/* ── MY TICKETS VIEW ── */}
          {selectedModule === 'my-tickets' && user && (
            <MyTicketsTab userName={user.name} userEmail={user.email} />
          )}

          {/* ── MODULE VIEW (module selected — tabs + content) ── */}
          {selectedModule !== 'dashboard' && selectedModule !== 'my-tickets' && (
            <>
              {/* Tab bar */}
              <div className="border-b border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/30 shrink-0">
                <div className="flex items-center h-10 px-4 gap-0">
                  {tabs.map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`px-4 h-full text-[13px] font-medium transition-colors border-b-2 cursor-pointer ${
                        activeTab === tab.id
                          ? 'border-green-600 text-green-700 dark:text-green-400 bg-white dark:bg-gray-900'
                          : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100/50 dark:hover:bg-gray-800/30'
                      }`}
                    >
                      {tab.label}
                    </button>
                  ))}
                  <div className="flex-1" />
                  <span className="text-[12px] text-gray-400 dark:text-gray-500">
                    Module: <span className="text-gray-600 dark:text-gray-300 font-medium">{modulePath.name}</span>
                    {modulePath.badge && (
                      <span className="ml-2 text-orange-600 dark:text-orange-400">{modulePath.badge}</span>
                    )}
                  </span>
                </div>
              </div>

              {/* Tab Content */}
              <div className="flex-1 overflow-hidden">
                {activeTab === 'operations' && <OperationsTab />}
            {activeTab === 'test-runner' && (
              <TestRunnerTab
                tests={tests}
                testChecks={testChecks}
                toggleTestCheck={toggleTestCheck}
                isRunning={isRunning}
                totalFailed={failedCount}
                onRun={(selectedOnly) => {
                  mockRunTests(selectedOnly)
                  setActiveTab('live-execution')
                }}
                onRunByPriority={runByPriority}
                onRerunFailed={() => {
                  const failedIds = tests.filter((t) => t.status === 'failed').map((t) => t.id)
                  if (failedIds.length > 0) {
                    rerunTestIds(failedIds)
                    mockRunTests(true, failedIds)
                    setActiveTab('live-execution')
                  }
                }}
              />
            )}
            {activeTab === 'live-execution' && (
              <LiveExecutionTab
                tests={tests}
                isRunning={isRunning}
                runningProgress={runningProgress}
                onStop={() => setIsRunning(false)}
                onBack={() => setActiveTab('test-runner')}
                onRerunFailed={() => {
                  const failedIds = tests.filter((t) => t.status === 'failed').map((t) => t.id)
                  if (failedIds.length > 0) {
                    rerunTestIds(failedIds)
                    mockRunTests(true, failedIds)
                  }
                }}
              />
            )}
            {activeTab === 'results' && (
              <ResultsTab
                tests={tests}
                passedCount={passedCount}
                failedCount={failedCount}
                totalCount={tests.length}
                runHistory={runHistory}
                onReportTest={handleReportTest}
              />
            )}
            {activeTab === 'schedule' && user && (
              <ScheduleRunsTab userName={user.name} sidebarModules={sidebarModules} />
            )}
          </div>
            </>
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
              <Button
                variant="ghost"
                size="icon"
                className="size-5 text-gray-400 hover:text-gray-200"
                onClick={() => setConsoleOpen(false)}
              >
                <X className="size-3" />
              </Button>
            </div>
          </div>
          <ScrollArea className="flex-1 px-4 py-2">
            <div className="space-y-0.5">
              {consoleLogs.map((log, i) => (
                <div
                  key={i}
                  className={`text-[12px] font-mono leading-5 ${
                    log.includes('PASSED')
                      ? 'text-green-400'
                      : log.includes('FAILED')
                        ? 'text-red-400'
                        : log.includes('Navigating') || log.includes('Clicking') || log.includes('Filling') || log.includes('Selecting') || log.includes('Setting')
                          ? 'text-yellow-300'
                          : 'text-gray-300'
                  }`}
                >
                  {log}
                </div>
              ))}
            </div>
          </ScrollArea>
        </div>
      )}

      {/* Floating "New Test Run" button on Live Execution */}
      {activeTab === 'live-execution' && !isRunning && passedCount + failedCount > 0 && (
        <button
          onClick={() => setActiveTab('test-runner')}
          className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 bg-green-600 hover:bg-green-700 text-white transition-all duration-200 rounded-xl px-5 py-2.5 flex items-center gap-2 shadow-lg shadow-green-600/20 cursor-pointer hover:shadow-xl hover:shadow-green-600/30 hover:-translate-y-0.5"
        >
          <RotateCcw className="size-4" />
          <span className="text-[13px] font-medium">New Test Run</span>
        </button>
      )}

      {/* ─── QUICK SWITCHER (Cmd+K) ────────────────────── */}
      {quickSwitcherOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-[100] bg-black/40 backdrop-blur-sm"
            onClick={() => setQuickSwitcherOpen(false)}
          />
          {/* Dialog */}
          <div className="fixed top-[20%] left-1/2 -translate-x-1/2 z-[101] w-full max-w-lg">
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
              {/* Search input */}
              <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-100 dark:border-gray-700">
                <Search className="size-4 text-gray-400 shrink-0" />
                <input
                  type="text"
                  value={quickSearch}
                  onChange={(e) => setQuickSearch(e.target.value)}
                  placeholder="Search modules... (e.g. tax, uom, crop)"
                  className="flex-1 text-[14px] text-gray-800 dark:text-gray-100 placeholder:text-gray-400 outline-none bg-transparent"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Escape') setQuickSwitcherOpen(false)
                  }}
                />
                <kbd className="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 text-[10px] font-mono text-gray-400 shrink-0">
                  ESC
                </kbd>
              </div>
              {/* Results */}
              <div className="max-h-[300px] overflow-auto py-2">
                {(() => {
                  const q = quickSearch.toLowerCase()
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
                    ? flatModules.filter(
                        (m) =>
                          m.label.toLowerCase().includes(q) ||
                          m.id.toLowerCase().includes(q) ||
                          (m.parent && m.parent.toLowerCase().includes(q))
                      )
                    : flatModules

                  if (filtered.length === 0) {
                    return (
                      <div className="px-4 py-6 text-center text-[13px] text-gray-400 dark:text-gray-500">
                        No modules found
                      </div>
                    )
                  }

                  return filtered.map((mod) => {
                    const isActive = mod.id === selectedModule
                    return (
                      <button
                        key={mod.id}
                        onClick={() => {
                          setSelectedModule(mod.id)
                          setActiveTab('operations')
                          setQuickSwitcherOpen(false)
                          setSidebarOpen(true)
                        }}
                        className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors cursor-pointer ${
                          isActive
                            ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400'
                            : 'text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                        }`}
                      >
                        {mod.parent && (
                          <span className="text-[11px] text-gray-400 dark:text-gray-500 truncate max-w-[100px]">{mod.parent}</span>
                        )}
                        {mod.parent && <ChevronRight className="size-3 text-gray-300 dark:text-gray-600 shrink-0" />}
                        <span className={`text-[13px] flex-1 truncate ${isActive ? 'font-medium' : ''}`}>
                          {mod.label}
                        </span>
                        {mod.badge && (
                          <span className="text-[11px] text-gray-500 dark:text-gray-400 shrink-0">{mod.badge}</span>
                        )}
                        {isActive && <CheckCircle2 className="size-3.5 text-green-500 shrink-0" />}
                      </button>
                    )
                  })
                })()}
              </div>
              {/* Footer hint */}
              <div className="flex items-center gap-4 px-4 py-2 border-t border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 text-[11px] text-gray-400">
                <span>
                  <kbd className="px-1 py-0.5 rounded bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 text-[10px] font-mono">↑↓</kbd> navigate
                </span>
                <span>
                  <kbd className="px-1 py-0.5 rounded bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 text-[10px] font-mono">Enter</kbd> select
                </span>
                <span>
                  <kbd className="px-1 py-0.5 rounded bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 text-[10px] font-mono">Esc</kbd> close
                </span>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Console toggle button */}
      {!consoleOpen && (
        <button
          onClick={() => setConsoleOpen(true)}
          className="fixed bottom-4 right-4 z-50 bg-[#1a1a2e] text-green-400 hover:bg-[#252540] transition-colors rounded-lg px-3 py-2 flex items-center gap-2 shadow-lg border border-gray-700 cursor-pointer"
        >
          <Terminal className="size-3.5" />
          <span className="text-[12px] font-medium">Console</span>
          <span className="bg-green-500/20 text-green-400 text-[10px] px-1.5 py-0.5 rounded-full">
            {consoleLogs.length}
          </span>
        </button>
      )}

      {/* Console minimize button (when console is open) */}
      {consoleOpen && (
        <button
          onClick={() => setConsoleOpen(false)}
          className="fixed bottom-[208px] right-4 z-50 bg-[#1a1a2e] text-gray-400 hover:text-gray-200 transition-colors rounded-t-lg px-3 py-1 flex items-center gap-1.5 shadow-lg border border-b-0 border-gray-700 cursor-pointer"
        >
          <Minimize2 className="size-3" />
          <span className="text-[11px]">Hide</span>
        </button>
      )}

      {/* ─── Feature 1: Completion Summary Modal ────────── */}
      <CompletionSummaryModal
        open={completionModalOpen}
        onClose={() => setCompletionModalOpen(false)}
        passedCount={completionStats.passed}
        failedCount={completionStats.failed}
        totalDuration={completionStats.duration}
        onViewResults={handleViewResults}
        onRerunFailed={handleCompletionRerunFailed}
        onNewRun={handleNewRun}
      />

      {/* ─── Bug Report Dialog ────────────────────────────── */}
      <ReportToAdminDialog
        open={reportDialogOpen}
        onClose={() => setReportDialogOpen(false)}
        testId={reportingTest?.id || ''}
        testDescription={reportingTest?.name || ''}
        error={reportingTest?.error}
        moduleName={modulePath.name}
        userName={user?.name || ''}
        userEmail={user?.email || ''}
      />
    </div>
  )
}
