'use client'

import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { ErrorBoundary } from '@/components/error-boundary/ErrorBoundary'

import Link from 'next/link'
import { toast } from 'sonner'
import { fetchModules, folderToSidebarId, sidebarToFolderMapping, startRun, fetchTestCases, type ApiModule, type ApiSubModule, type TestCasesData } from '@/lib/api'
import { DashboardTab } from '@/components/dashboard/DashboardTab'
import { ResultsTab } from '@/components/results/ResultsTab'
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
  addNotification,
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
  Maximize2,
  Monitor,
} from 'lucide-react'

//  Types 
import type { TestPriority, SidebarModule, TestItem, TestSpecItem, TestClassGroup, AuthUser, RunSnapshot, ModuleHealth } from "../types/page"

import LoginPage from '@/components/auth/LoginPage'
import OperationsTab from '@/components/operations/OperationsTab'
import TestRunnerTab from '@/components/test-runner/TestRunnerTab'
import LiveScreencast from '@/components/dashboard/LiveScreencast'
import ReportToAdminDialog from '@/components/bug-tracker/ReportToAdminDialog'
import CompletionSummaryModal from '@/components/dashboard/CompletionSummaryModal'

import { SidebarModuleItem } from '@/components/shared/SidebarModuleItem'
import { LiveExecutionTab } from '@/components/dashboard/LiveExecutionTab'
import { ScheduleTab as ScheduleRunsTab } from '@/components/schedule/ScheduleTab'


//  Helper: get priority 
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

//  Module Data (fetched from API) 

// Full list of ALL sidebar modules (with or without tests).
// API data enriches these with real test counts.

/**
 * Given a sidebar module ID (e.g. "seasons") and the API modules data,
 * return { groups: TestClassGroup[], items: TestItem[] } from real test functions.
 * Returns empty arrays for modules without API tests.
 */
function getTestsForSidebarModule(
  sidebarId: string,
  apiModules: ApiModule[]
): { groups: TestClassGroup[]; items: TestItem[] } {
  const empty = { groups: [] as TestClassGroup[], items: [] as TestItem[] }
  const mapping = sidebarToFolderMapping(sidebarId)
  if (!mapping) return empty

  // Find the API module
  const apiMod = apiModules.find((m) => m.name === mapping.module)
  if (!apiMod) return empty

  let subModule: ApiSubModule | undefined
  if (mapping.subModule) {
    subModule = apiMod.sub_modules.find((s) => s.name === mapping.subModule)
    if (!subModule) return empty
  }

  // Get tests list
  const allApiTests = subModule ? subModule.tests : apiMod.sub_modules.flatMap((s) => s.tests)
  const apiTests = [...new Map(allApiTests.map(t => [t.name, t])).values()]
  if (apiTests.length === 0) return empty

  // Group tests by their test file name (extract class name from file)
  const testFileGroups: Record<string, { file: string; tests: ApiSubModule['tests'] }> = {}
  for (const test of apiTests) {
    const parts = test.name.split('::')
    const fileName = parts[0]?.split('/').pop() || 'tests'
    const className = parts.length >= 3 ? parts[1] : fileName.replace('.py', '')

    if (!testFileGroups[className]) {
      testFileGroups[className] = { file: fileName, tests: [] }
    }
    testFileGroups[className].tests.push(test)
  }

    // Group all tests under one group (API names don't include file paths)
  const groups: TestClassGroup[] = [{
    className: 'All Tests',
    tests: apiTests.map((t) => ({
      id: t.name,
      description: t.display_name || t.name.split('::').pop() || t.name,
      status: 'not-run' as const,
      duration: '—',
      steps: t.docstring || '',
      expected: t.docstring || '',
    })),
  }]

  // Convert to TestItem[]
  const items: TestItem[] = apiTests.map((t) => ({
    id: t.name,
    name: t.display_name || t.name.split('::').pop() || t.name,
    status: 'pending' as const,
    duration: '',
  }))

  return { groups, items }
}
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
      {
        id: 'commodity-attributes-group',
        label: 'Commodity Attributes',
        defaultExpanded: true,
        children: [
          { id: 'item-attribute', label: 'Item Attribute', badge: '📝 No tests', badgeType: 'none' as const },
        ],
      },
      { id: 'quality-parameter-def', label: 'Quality Parameter Master', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'commodity-quality-param', label: 'Commodity Quality Parameter', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'commodity-base-rate', label: 'Commodity Base Rate', badge: '📝 No tests', badgeType: 'none' as const },
      {
        id: 'commodity-master-group',
        label: 'Commodity Master',
        defaultExpanded: true,
        children: [
          { id: 'item-master', label: 'Item Master', badge: '📝 No tests', badgeType: 'none' as const },
          { id: 'crop-master', label: 'Crop Master', badge: '📝 No tests', badgeType: 'none' as const },
          { id: 'services-master', label: 'Services Master', badge: '📝 No tests', badgeType: 'none' as const },
          { id: 'item-category', label: 'Item Category', badge: '📝 No tests', badgeType: 'none' as const },
          { id: 'item-group', label: 'Item Group', badge: '📝 No tests', badgeType: 'none' as const },
        ],
      },
    ],
  },
    {
    id: 'access',
    label: 'Access',
    defaultExpanded: true,
    children: [
      { id: 'entity-group', label: 'Entity Group Definition', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'role-creation', label: 'Role Creation Screen', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'role-screen-link', label: 'Role Screen Link', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'user-creation', label: 'User Creation Screen', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'screen-api-link', label: 'Screen API Link', badge: '📝 No tests', badgeType: 'none' as const },
    ],
  },
  { id: 'my-tickets', label: 'My Tickets' },
]

/**
 * Build sidebar by merging real API test counts into the full module list.
 * Modules without tests keep the "📝 No tests" badge.
 */
function buildSidebarModules(apiModules: ApiModule[]): SidebarModule[] {
  // Deep clone the master list
  const sidebar: SidebarModule[] = JSON.parse(JSON.stringify(ALL_SIDEBAR_MODULES))

  // Build a lookup: sidebarId  test count from API
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

  // Update badges with real counts (recursive for nested groups)
  function updateBadges(items: SidebarModule[]) {
    for (const item of items) {
      const count = testCounts[item.id]
      if (count !== undefined && count > 0) {
        item.badge = `${count} tests`
        item.badgeType = 'success'
      }
      if (item.children) updateBadges(item.children)
    }
  }
  for (const mod of sidebar) {
    if (mod.children) updateBadges(mod.children)
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

//  Module Health Data (Feature 3) 
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

//  Initial Run History (Feature 5) 
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

//  Priority Config 
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

//  Sidebar Module Component 
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

//  LOGIN PAGE 
function NavToast({ label, parent }: { label: string; parent?: string | null }) {
  return (
    <div
      className="pointer-events-none absolute top-3 left-1/2 z-50 transition-all duration-300 ease-out opacity-100"
      style={{ transform: 'translateX(-50%) translateY(0px)' }}
    >
      <div className="flex items-center gap-2 bg-gray-900/90 dark:bg-gray-100/90 text-white dark:text-gray-900 text-[12px] font-medium px-3.5 py-1.5 rounded-full shadow-lg shadow-black/20 backdrop-blur-sm whitespace-nowrap">
        {parent && (
          <>
            <span className="opacity-50">{parent}</span>
            <span className="opacity-30 mx-0.5">›</span>
          </>
        )}
        <span>{label}</span>
      </div>
    </div>
  )
}

//  MAIN PAGE COMPONENT 
export default function Home() {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)
  const [sidebarModules, setSidebarModules] = useState<SidebarModule[]>(ALL_SIDEBAR_MODULES)
  const [apiModules, setApiModules] = useState<ApiModule[]>([])
  const [selectedModule, setSelectedModule] = useState<string>('dashboard')
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())
  const [activeTab, setActiveTab] = useState('operations')
  const [consoleOpen, setConsoleOpen] = useState(false)
  // Hash routing - read initial state from URL hash
  const [hashReady, setHashReady] = useState(false)
  const [testChecks, setTestChecks] = useState<Set<string>>(new Set())
  const [tests, setTests] = useState<TestItem[]>(initialTests)
  const [currentTestGroups, setCurrentTestGroups] = useState<TestClassGroup[]>(testSpecGroups)
  const [allTestCases, setAllTestCases] = useState<TestCasesData>({})
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

  //  Fetch real modules from API 
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
    // Fetch test cases from backend
  useEffect(() => {
    fetchTestCases()
      .then((data) => {
        setAllTestCases(data)
        if (typeof window !== 'undefined') {
          (window as any).__ALL_TEST_CASES__ = data
        }
      })
      .catch(() => console.error('Failed to fetch test cases'))
  }, [])

  const handleMarkAllRead = useCallback(async () => {
    await markAllNotificationsRead()
    setUnreadCount(0)
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))
  }, [])

  // Feature 5: Run history
  const [runHistory, setRunHistory] = useState<RunSnapshot[]>(initialRunHistory)
  const runIdCounterRef = useRef(initialRunHistory.length + 1)

  // Feature 6: Dark mode
  const [navToast, setNavToast] = useState<{ key: number; label: string; parent?: string | null } | null>(null)
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

  // --- Hash routing: init from URL hash ---
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

  // Load real tests from API data for this sub-module
        // Try real test cases from Excel data first
    const moduleKey = id.toLowerCase().replace(" ", "_").replace("-", "_")
    if (allTestCases[moduleKey]) {
      const moduleData = allTestCases[moduleKey]
      const specGroups: TestClassGroup[] = [{
        className: moduleData.label,
        tests: moduleData.tests.map((t) => ({
          id: t.id,
          description: t.description,
          status: 'not-run' as const,
          duration: '',
          steps: t.steps,
          expected: t.expected,
          error: t.status === 'BUG' ? t.actual : undefined,
          priority: undefined,
        })),
      }]
      setCurrentTestGroups(specGroups)
      const items: TestItem[] = moduleData.tests.map((t) => ({
        id: t.id,
        name: t.description,
        status: 'pending' as const,
        duration: '',
      }))
      setTests(items)
    } else {
      // Fall back to API test functions
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

      const testNames = testsToRun.map((t) => t.id)
      const runOnlyTests = selectedOnly || forceIds ? testNames : null

      startRun(
        mapping.module,
        mapping.subModule,
        runOnlyTests,
        (event) => {
          if (event.type === 'log') {
            setRunningProgress(event.message)
          } else if (event.type === 'test_end') {
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
          } else if (event.type === 'error') {
            toast.error('Run error', { description: event.message, duration: 8000 })
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
   

  // Feature 4: Run by priority
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
      runTests(true, failedIds)
      setActiveTab('live-execution')
    }
  }, [tests, rerunTestIds, runTests])

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
      {/*  HEADER  */}
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

      {/*  BODY  */}
      <div className="flex flex-1 overflow-hidden">
        {/*  SIDEBAR  */}
        <div
          className="shrink-0 overflow-hidden h-full"
          style={{ width: sidebarOpen ? sidebarWidth : 0 }}
        >
        <aside className="bg-[#e8f5e9] dark:bg-[#1a2e1a] border-r border-[#c8e6c9] dark:border-[#2d4a2d] flex flex-col h-full" style={{ width: sidebarWidth }}>
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
          <ScrollArea className="flex-1 min-h-0">
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

        {/*  RESIZE HANDLE  */}
        {sidebarOpen && (
          <div
            onMouseDown={handleResizeStart}
            className="w-1 cursor-col-resize bg-transparent hover:bg-green-400/40 active:bg-green-400/60 transition-colors shrink-0 relative z-10"
          />
        )}

        {/*  MAIN CONTENT  */}
        <main className="flex-1 flex flex-col overflow-hidden bg-white dark:bg-gray-900 relative">
          {navToast && (
            <NavToast key={navToast.key} label={navToast.label} parent={navToast.parent} />
          )}
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

          {/*  DASHBOARD VIEW  */}
          {selectedModule === 'dashboard' && (
            <DashboardTab onSelectModule={handleSelectModule} />
          )}

          {/*  MY TICKETS VIEW  */}
          {selectedModule === 'my-tickets' && user && (
            <div className='p-8 text-center text-gray-400 text-sm'>No tickets yet</div>
          )}

          {/*  MODULE VIEW (module selected  tabs + content)  */}
          {selectedModule !== 'dashboard' && selectedModule !== 'my-tickets' && (
              <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
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
              <div className="flex-1 overflow-hidden min-h-0">
                {activeTab === 'operations' && (
                  <ErrorBoundary name="OperationsTab">
                    <OperationsTab
                      testGroups={currentTestGroups}
                      testCasesModule={
                        allTestCases[selectedModule?.toLowerCase().replace(' ', '_').replace('-', '_')]
                      }
                    />
                  </ErrorBoundary>
                )}
                {activeTab === 'test-runner' && (
                  <ErrorBoundary name="TestRunnerTab">
                    <TestRunnerTab
                      tests={tests}
                      testChecks={testChecks}
                      toggleTestCheck={toggleTestCheck}
                      isRunning={isRunning}
                      totalFailed={failedCount}
                      onRun={(selectedOnly) => {
                        runTests(selectedOnly)
                        setActiveTab('live-execution')
                      }}
                      onRunByPriority={runByPriority}
                      onRerunFailed={() => {
                        const failedIds = tests.filter((t) => t.status === 'failed').map((t) => t.id)
                        if (failedIds.length > 0) {
                          rerunTestIds(failedIds)
                          runTests(true, failedIds)
                          setActiveTab('live-execution')
                        }
                      }}
                    />
                  </ErrorBoundary>
                )}
                {activeTab === 'live-execution' && (
                  <ErrorBoundary name="LiveExecutionTab">
                    <LiveExecutionTab
                      tests={tests}
                      testGroups={currentTestGroups}
                      isRunning={isRunning}
                      runningProgress={runningProgress}
                      onStop={() => setIsRunning(false)}
                      onBack={() => setActiveTab('test-runner')}
                      onRerunFailed={() => {
                        const failedIds = tests.filter((t) => t.status === 'failed').map((t) => t.id)
                        if (failedIds.length > 0) {
                          rerunTestIds(failedIds)
                          runTests(true, failedIds)
                        }
                      }}
                    />
                  </ErrorBoundary>
                )}
                {activeTab === 'results' && (
                  <ErrorBoundary name="ResultsTab">
                    <ResultsTab
                      tests={tests}
                      passedCount={passedCount}
                      failedCount={failedCount}
                      totalCount={tests.length}
                      runHistory={runHistory}
                      onReportTest={handleReportTest}
                    />
                  </ErrorBoundary>
                )}
                {activeTab === 'schedule' && user && (
                  <ErrorBoundary>
                    <ScheduleRunsTab userName={user.name} sidebarModules={sidebarModules} />
                  </ErrorBoundary>
                )}
              </div>
            </div>
          )}
        </main>
      </div>

      {/*  CONSOLE PANEL  */}
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

      {/*  QUICK SWITCHER (Cmd+K)  */}
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

      {/*  Feature 1: Completion Summary Modal  */}
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

      {/*  Bug Report Dialog  */}
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
