'use client'

import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { toast } from 'sonner'
import { fetchModules, folderToSidebarId, sidebarToFolderMapping, startRun, stopRun, fetchTestCases, fetchScreenshot, type ApiModule, type ApiSubModule, type TestCasesData } from '@/lib/api'
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
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
  ArrowUpDown,
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
  HelpCircle,
  Copyright,
  ExternalLink,
} from 'lucide-react'
import { AppTour, startAppTour } from '@/components/tour/AppTour'
import { Sparkline, getSparklineColor, TrendIndicator } from '@/components/ui/sparkline'

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
  screenName?: string
  description: string
  status: 'passed' | 'failed' | 'bug' | 'todo' | 'not-run'
  duration: string
  steps: string
  expected: string
  actual: string
  bugDetails?: string
  priority?: TestPriority
  date?: string
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
  id: string
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
  trend?: number[] // last 7 run pass rates for sparkline
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
      actual: '',
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
  {
    id: 'registration',
    label: 'Registration',
    defaultExpanded: true,
    children: [
      { id: 'farmer', label: 'Farmer', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'supplier', label: 'Supplier', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'customer', label: 'Customer', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'agent', label: 'Agent', badge: '📝 No tests', badgeType: 'none' as const },
    ],
  },
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
        actual: 'Record created successfully, SweetAlert2 success toast appeared',
        date: '2026-05-16',
      },
      {
        id: 'T02',
        description: 'Create with minimum fields',
        status: 'passed',
        duration: '1:45',
        priority: 'smoke',
        steps: 'Click Add → Fill Tax Rate Name → Submit',
        expected: 'Record created with default values',
        actual: 'Record created with default values, appeared in table',
        date: '2026-05-16',
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
        actual: 'Name updated successfully, success alert shown',
        date: '2026-05-16',
      },
      {
        id: 'T05',
        description: 'Update with blank name',
        status: 'passed',
        duration: '0:55',
        priority: 'regression',
        steps: 'Search record → Click Edit → Clear Name → Update',
        expected: 'Validation error shown',
        actual: 'Validation error displayed, name field highlighted',
        date: '2026-05-16',
      },
      {
        id: 'T06',
        description: 'Update non-existent record',
        status: 'passed',
        duration: '0:32',
        priority: 'regression',
        steps: 'Search for non-existent name → Verify not in table',
        expected: 'Record not found',
        actual: 'No matching record found in table',
        date: '2026-05-16',
      },
    ],
  },
  {
    className: 'TestSubTable',
    tests: [
      {
        id: 'T03',
        description: 'Add HSN row in sub-table',
        status: 'bug',
        duration: '—',
        priority: 'regression',
        steps: 'Click Add → Fill fields → Go to "Define Tax Rate Details" tab → Click Add → Select HSN Number → Enter Tax Rate → Submit',
        expected: 'Sub-table row added, record created',
        actual: 'SubTableAddButton not found in DOM',
        bugDetails: 'SubTableAddButton not found in DOM — button element missing from page',
        date: '2026-05-16',
      },
      {
        id: 'T09',
        description: 'Submit with empty sub-table',
        status: 'bug',
        duration: '—',
        priority: 'regression',
        steps: 'Click Add → Fill header fields → Submit WITHOUT adding sub-table row',
        expected: 'Form should reject empty sub-table',
        actual: 'Server accepts empty sub-table as success (wrong assertion)',
        bugDetails: 'Server accepts empty sub-table as success — no validation on sub-table rows',
        date: '2026-05-16',
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
        actual: 'Matching record displayed in search results',
        date: '2026-05-16',
      },
      {
        id: 'T11',
        description: 'Search non-existent record',
        status: 'passed',
        duration: '0:42',
        priority: 'regression',
        steps: 'Enter non-existent name → Verify "No records found" message',
        expected: 'No records displayed, empty state shown',
        actual: 'No records displayed, empty state shown correctly',
        date: '2026-05-16',
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
        actual: 'Pagination controls work correctly, correct records per page',
        date: '2026-05-16',
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
        actual: 'History popup displays with correct entries',
        date: '2026-05-16',
      },
      {
        id: 'T18',
        description: 'Search within history popup',
        status: 'passed',
        duration: '1:22',
        priority: 'sanity',
        steps: 'Open History popup → Enter search term → Verify filtered results',
        expected: 'History entries filtered correctly',
        actual: 'History entries filtered correctly',
        date: '2026-05-16',
      },
    ],
  },
]

const initialTests: TestItem[] = testSpecGroups.flatMap((g) =>
  g.tests.map((t) => ({
    id: t.id,
    name: t.description,
    status: (t.status === 'not-run' || t.status === 'todo' ? 'pending' : t.status === 'bug' ? 'failed' : t.status) as 'passed' | 'failed' | 'pending',
    duration: t.duration === '—' ? '—' : t.duration,
    priority: t.priority,
  }))
)

// consoleLogs, recentRuns, bugRegistry replaced with real data from backend
// moduleHealthData replaced with computed moduleHealth from real run history
// initialRunHistory replaced with loadRunHistory() from Prisma

// ─── Priority Config ────────────────────────────────────
const priorityConfig = {
  smoke: { icon: <Flame className="size-3" />, label: '🔥 Smoke', color: 'text-[#E65100] bg-[#FFF3E0] dark:text-orange-300 dark:bg-orange-900/40', dot: 'bg-[#FF9800]' },
  regression: { icon: <Activity className="size-3" />, label: '🔄 Regression', color: 'text-[#3F51B5] bg-[#DFE9FB] dark:text-indigo-300 dark:bg-indigo-900/40', dot: 'bg-[#3F51B5]' },
  sanity: { icon: <ShieldCheck className="size-3" />, label: '🛡️ Sanity', color: 'text-[#2E7D32] bg-[#E8F5E9] dark:text-green-300 dark:bg-green-900/40', dot: 'bg-[#4CAF50]' },
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
  isLast = true,
}: {
  module: SidebarModule
  depth?: number
  activeId: string | null
  onSelect: (id: string) => void
  expandedIds: Set<string>
  toggleExpand: (id: string) => void
  isLast?: boolean
}) {
  const hasChildren = module.children && module.children.length > 0
  const isExpanded = expandedIds.has(module.id)
  const isActive = activeId === module.id
  const isParentActive = activeId && hasChildren && module.children!.some((c) => c.id === activeId)
  const isChild = depth > 0

  // Exact ERP tree-line values: width 2.7px, color #c8ccd4
  const treeLineWidth = '2.7px'
  const treeLineColor = '#c8ccd4'

  return (
    <div className="relative">
      {isChild && (
        <>
          {/* L-shaped tree branch connector (border-left + border-bottom with rounded corner) */}
          <div
            className="absolute bg-transparent z-0"
            style={{
              left: isChild && depth === 1 ? '34px' : '74px',
              top: '6px',
              width: depth === 1 ? '22px' : '16px',
              height: '16px',
              borderLeft: `${treeLineWidth} solid ${treeLineColor}`,
              borderBottom: `${treeLineWidth} solid ${treeLineColor}`,
              borderRadius: isLast ? '0 0 0 15px' : '0 0 0 15px',
              // For last child, the vertical line stops here (L-shape)
              // For non-last, the vertical line continues down via the parent ml-menu::before
            }}
          />
          {/* Continuing vertical line for non-last items */}
          {!isLast && (
            <div
              className="absolute z-0 bg-transparent"
              style={{
                left: isChild && depth === 1 ? '34px' : '74px',
                top: '22px',
                bottom: '0',
                width: treeLineWidth,
                backgroundColor: treeLineColor,
                borderRadius: '10px',
              }}
            />
          )}
        </>
      )}
      <button
        data-module-id={module.id}
        ref={(el) => {
          if (el && isExpanded && hasChildren) {
            requestAnimationFrame(() => {
              el.scrollIntoView({ behavior: 'smooth', block: 'center' })
            })
          }
        }}
        onClick={() => {
          if (hasChildren) toggleExpand(module.id)
          else onSelect(module.id)
        }}
        className={`w-full flex items-center text-[14px] transition-all duration-200 cursor-pointer text-left font-['Poppins'] relative z-[1] ${
          isChild
            ? isActive
              ? 'text-[#1B4332] dark:text-green-300 font-semibold'
              : 'text-[#545454] dark:text-gray-300 font-medium hover:text-[#6777EF] dark:hover:text-indigo-400 hover:bg-[rgba(82,183,136,0.08)] hover:shadow-[rgba(82,183,136,0.5)_2px_0px_inset] hover:rounded-[5px]'
            : isActive
              ? 'bg-gradient-to-r from-[#DFF3E3] via-[#C8E6C9] to-[#B7E4C7] dark:bg-[#1B4332]/25 text-[#1B4332] dark:text-green-300 font-semibold shadow-[rgba(34,197,94,0.25)_2px_0px_4px_inset,rgba(34,197,94,0.15)_0px_2px_6px] rounded-[5px]'
              : isParentActive
                ? 'text-[#1B4332] dark:text-green-300 font-semibold'
                : 'text-[#545454] dark:text-gray-300 font-medium hover:text-[#6777EF] dark:hover:text-indigo-400 hover:bg-[rgba(82,183,136,0.08)] hover:shadow-[rgba(82,183,136,0.5)_2px_0px_inset] hover:rounded-[5px]'
        }`}
        style={{
          paddingLeft: isChild ? (depth === 1 ? '48px' : '80px') : '15px',
          paddingRight: '24px',
          paddingTop: '7px',
          paddingBottom: '7px',
        }}
      >
        {hasChildren ? (
          <ChevronDown
            className={`size-[18px] shrink-0 transition-transform duration-200 mr-1.5 ${
              !isExpanded ? '-rotate-90' : ''
            } ${isActive || isParentActive ? 'text-[#1B4332] dark:text-green-300' : 'text-[#495584] dark:text-gray-400'}`}
          />
        ) : isChild ? (
          <span
            className={`w-[7px] h-[7px] rounded-full shrink-0 mr-2 ${
              isActive
                ? 'bg-[#1A56DB] dark:bg-indigo-400'
                : 'border-[1.5px] border-[#777777] dark:border-gray-500'
            }`}
          />
        ) : (
          <span className="w-[18px] shrink-0 mr-1.5" />
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
        <div className="relative">
          {/* Vertical tree line running down the left side of all children */}
          <div
            className="absolute z-0"
            style={{
              left: '34px',
              top: '0',
              bottom: isLast ? '27px' : '0',
              width: treeLineWidth,
              backgroundColor: treeLineColor,
              borderRadius: '10px',
            }}
          />
          {module.children!.map((child, idx) => (
            <SidebarModuleItem
              key={child.id}
              module={child}
              depth={depth + 1}
              activeId={activeId}
              onSelect={onSelect}
              expandedIds={expandedIds}
              toggleExpand={toggleExpand}
              isLast={idx === module.children!.length - 1}
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
      return <Loader2 className={`${cls} text-indigo-500 animate-spin`} />
    default:
      return <Circle className={`size-${Math.max(size - 0.5, 3)} text-gray-300 dark:text-gray-600`} />
  }
}

// ─── Sort Arrow (ERP-style: 150ms rotation) ─────────────
function SortArrow({ col, sortCol, sortDir }: { col: string; sortCol: string; sortDir: 'asc' | 'desc' }) {
  const isActive = sortCol === col
  return (
    <ArrowUpDown
      className={`size-3 transition-transform duration-150 ${isActive ? 'opacity-100' : 'opacity-30'} ${isActive && sortDir === 'desc' ? 'rotate-180' : ''}`}
    />
  )
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
    <div className="min-h-screen bg-[#F1F2F7] dark:bg-gray-900 flex">
      {/* ─── LEFT: Login Form ─── */}
      <div className="w-full lg:w-[440px] xl:w-[480px] shrink-0 flex flex-col items-center justify-center px-8 py-12 bg-white dark:bg-gray-800 relative">
        {/* Logo */}
        <div className="flex flex-col items-center mb-10">
          <div className="flex items-center justify-center mb-5">
            <Image src="/agdi-logo.png" alt="AgDi" width={120} height={60} className="object-contain" />
          </div>
          <h1 className="text-[24px] font-bold text-gray-800 dark:text-gray-100">Welcome Back!</h1>
          <p className="text-[14px] text-gray-500 dark:text-gray-400 mt-1">Sign in to continue</p>
        </div>

        {/* Login Card */}
        <div className="w-full max-w-[340px]">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email */}
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-[#374151] dark:text-gray-400" />
              <Input
                type="email"
                placeholder="Username*"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="h-11 pl-9 text-[14px] bg-white dark:bg-gray-700/50 border-[#d1d5db] dark:border-gray-600 focus:border-[#3F51B5] focus:ring-[#3F51B5]/20 text-[#333333] dark:text-gray-100 rounded-md placeholder:text-[#9ca3af]"
                required
                autoFocus
              />
            </div>

            {/* Password */}
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-[#374151] dark:text-gray-400" />
              <Input
                type={showPassword ? 'text' : 'password'}
                placeholder="Password*"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="h-11 pl-9 pr-10 text-[14px] bg-white dark:bg-gray-700/50 border-[#d1d5db] dark:border-gray-600 focus:border-[#3F51B5] focus:ring-[#3F51B5]/20 text-[#333333] dark:text-gray-100 rounded-md placeholder:text-[#9ca3af]"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[#374151] hover:text-gray-600 dark:text-gray-400 dark:hover:text-gray-300 transition-colors cursor-pointer"
              >
                <Eye className="size-4" />
              </button>
            </div>

            {/* Remember Me / Forgot */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Checkbox
                  id="remember"
                  checked={rememberMe}
                  onCheckedChange={(v) => setRememberMe(v === true)}
                  className="size-4"
                />
                <label htmlFor="remember" className="text-[13px] text-gray-600 dark:text-gray-400 cursor-pointer select-none">
                  Remember me
                </label>
              </div>
              <button type="button" className="text-[13px] text-gray-600 dark:text-gray-400 hover:text-[#3F51B5] dark:hover:text-indigo-400 font-medium cursor-pointer">
                Forgot Password?
              </button>
            </div>

            {/* Error */}
            {error && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-[12px] px-3 py-2.5 rounded-lg flex items-center gap-2">
                <XCircle className="size-3.5 shrink-0" />
                {error}
              </div>
            )}

            {/* Submit */}
            <Button
              type="submit"
              disabled={loading}
              className="w-full h-11 bg-[#3F51B5] hover:bg-[#2D3FC7] text-white text-[15px] font-semibold gap-2 rounded-[4px] cursor-pointer transition-all duration-200 font-['Roboto']"
            >
              {loading ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                'Login'
              )}
            </Button>
          </form>
        </div>

        {/* Footer */}
        <div className="absolute bottom-6 left-0 right-0 text-center">
          <p className="text-[11px] text-gray-400 dark:text-gray-500">
            agDi Automation Runner v1.0 — Internal QA Tool
          </p>
        </div>
      </div>

      {/* ─── RIGHT: Hero Illustration ─── */}
      <div className="hidden lg:flex flex-1 relative overflow-hidden">
        <img
          src="/agdi-hero-illustration.png"
          alt="AgDi - Agricultural Digital Intelligence"
          className="w-full h-full object-cover"
        />
      </div>
    </div>
  )
}

// ─── DASHBOARD TAB (Feature 3) ───────────────────────────
function DashboardTab({
  onSelectModule,
  moduleHealth,
}: {
  onSelectModule: (moduleId: string) => void
  moduleHealth: ModuleHealth[]
}) {
  // Group modules by parentGroup, preserving order
  const grouped = useMemo(() => {
    const order = ['Registration', 'Standalone', 'Common Settings', 'Commodity Settings']
    const groups: { name: string; icon: string; modules: ModuleHealth[] }[] = []
    const groupMap = new Map<string, ModuleHealth[]>()

    for (const mod of moduleHealth) {
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
  }, [moduleHealth])

  const quickStats = useMemo(() => {
    const total = moduleHealth.length
    const fullyPassing = moduleHealth.filter((m) => m.totalTests > 0 && m.passRate === 100).length
    const partiallyPassing = moduleHealth.filter((m) => m.totalTests > 0 && m.passRate > 0 && m.passRate < 100).length
    const notStarted = moduleHealth.filter((m) => m.totalTests === 0).length
    const totalPassed = moduleHealth.reduce((s, m) => s + m.passedTests, 0)
    const totalFailed = moduleHealth.reduce((s, m) => s + m.failedTests, 0)
    const totalTests = moduleHealth.reduce((s, m) => s + m.totalTests, 0)
    return { total, fullyPassing, partiallyPassing, notStarted, totalPassed, totalFailed, totalTests }
  }, [moduleHealth])

  // Overall trend: average pass rate across last 7 runs (computed from module trends)
  const overallTrend = useMemo(() => {
    const modulesWithTrend = moduleHealth.filter((m) => m.trend && m.trend.length > 0)
    if (modulesWithTrend.length === 0) return [90, 91, 90, 92, 91, 92, 93]
    const maxLen = Math.max(...modulesWithTrend.map((m) => m.trend!.length))
    const avgByRun: number[] = []
    for (let i = 0; i < maxLen; i++) {
      const vals = modulesWithTrend.filter((m) => m.trend![i] !== undefined).map((m) => m.trend![i])
      avgByRun.push(Math.round(vals.reduce((s, v) => s + v, 0) / vals.length))
    }
    return avgByRun
  }, [moduleHealth])

  const getHealthColor = useCallback((rate: number, total: number) => {
    if (total === 0) return { bg: 'bg-gray-50 dark:bg-gray-800', text: 'text-[#888888] dark:text-gray-500', indicator: 'bg-[#888888]', label: 'Not Started' }
    if (rate === 100) return { bg: 'bg-[#E8F5E9] dark:bg-green-900/20', text: 'text-[#2E7D32] dark:text-green-400', indicator: 'bg-[#4CAF50]', label: 'Healthy' }
    if (rate >= 75) return { bg: 'bg-[#FFF3E0] dark:bg-orange-900/20', text: 'text-[#E65100] dark:text-orange-400', indicator: 'bg-[#FF9800]', label: 'Partial' }
    return { bg: 'bg-[#FFEBEE] dark:bg-red-900/20', text: 'text-[#C62828] dark:text-red-400', indicator: 'bg-[#F44336]', label: 'Critical' }
  }, [])

  return (
    <div className="flex flex-col h-full overflow-auto">
      <div className="p-5 space-y-5">
        {/* Page Header */}
        <div>
          <h2 className="text-[18px] font-semibold text-[#333333] dark:text-gray-100">Dashboard</h2>
          <p className="text-[13px] text-[#666666] dark:text-gray-400 mt-0.5">Overview of all RhythmERP automation modules</p>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-3.5 border border-gray-100 dark:border-gray-700 shadow-sm">
            <div className="text-[11px] text-[#888888] dark:text-gray-400 font-medium uppercase tracking-wider">Total Modules</div>
            <div className="text-xl font-bold text-[#333333] dark:text-gray-100 mt-1">{quickStats.total}</div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-3.5 border border-green-100 dark:border-green-800/50 shadow-sm">
            <div className="text-[11px] text-[#4CAF50] dark:text-green-400 font-medium uppercase tracking-wider">Fully Passing</div>
            <div className="text-xl font-bold text-[#2E7D32] dark:text-green-400 mt-1">{quickStats.fullyPassing}</div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-3.5 border border-orange-100 dark:border-orange-800/50 shadow-sm">
            <div className="text-[11px] text-[#FF9800] dark:text-orange-400 font-medium uppercase tracking-wider">Partial / Critical</div>
            <div className="text-xl font-bold text-[#E65100] dark:text-orange-400 mt-1">{quickStats.partiallyPassing}</div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-3.5 border border-indigo-100 dark:border-indigo-800/50 shadow-sm">
            <div className="text-[11px] text-[#3F51B5] dark:text-indigo-400 font-medium uppercase tracking-wider">Overall Pass Rate</div>
            <div className="flex items-center gap-2 mt-1">
              <div className="text-xl font-bold text-[#3F51B5] dark:text-indigo-400">
                {quickStats.totalTests > 0 ? Math.round((quickStats.totalPassed / quickStats.totalTests) * 100) : 0}%
              </div>
              <Sparkline
                data={overallTrend}
                width={72}
                height={22}
                strokeColor={overallTrend[overallTrend.length - 1] >= overallTrend[overallTrend.length - 2] ? '#22c55e' : '#ef4444'}
                fillColor={overallTrend[overallTrend.length - 1] >= overallTrend[overallTrend.length - 2] ? '#22c55e' : '#ef4444'}
                strokeWidth={1.5}
              />
            </div>
            <div className="text-[11px] text-[#888888] dark:text-gray-400 mt-0.5">
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

          // Group trend: average of module trends per run
          const groupTrend = (() => {
            const modulesWithTrend = group.modules.filter((m) => m.trend && m.trend.length > 0)
            if (modulesWithTrend.length === 0) return null
            const maxLen = Math.max(...modulesWithTrend.map((m) => m.trend!.length))
            const avgByRun: number[] = []
            for (let i = 0; i < maxLen; i++) {
              const vals = modulesWithTrend.filter((m) => m.trend![i] !== undefined).map((m) => m.trend![i])
              avgByRun.push(Math.round(vals.reduce((s, v) => s + v, 0) / vals.length))
            }
            return avgByRun
          })()

          return (
            <div key={group.name}>
              {/* Group Header */}
              <div className="flex items-center gap-2 mb-2.5">
                <span className="text-[14px]">{group.icon}</span>
                <h3 className="text-[14px] font-semibold text-[#333333] dark:text-gray-100">{group.name}</h3>
                <span className="text-[12px] text-[#888888] dark:text-gray-400 ml-1">
                  {group.modules.length} modules
                </span>
                {groupTotal > 0 && (
                  <>
                    <div className="flex-1" />
                    {groupTrend && groupTrend.length >= 2 && (
                      <Sparkline
                        data={groupTrend}
                        width={56}
                        height={16}
                        strokeColor={groupTrend[groupTrend.length - 1] >= groupTrend[groupTrend.length - 2] ? '#22c55e' : '#ef4444'}
                        fillColor={groupTrend[groupTrend.length - 1] >= groupTrend[groupTrend.length - 2] ? '#22c55e' : '#ef4444'}
                        strokeWidth={1.5}
                      />
                    )}
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
                  const sparkColor = mod.trend ? getSparklineColor(mod.passRate, mod.trend[mod.trend.length - 2]) : { stroke: 'currentColor', fill: 'currentColor' }
                  return (
                    <button
                      key={mod.moduleId}
                      onClick={() => onSelectModule(mod.moduleId)}
                      className={`text-left p-3.5 rounded-[14px] border transition-all hover:shadow-md hover:-translate-y-0.5 cursor-pointer bg-white dark:bg-gray-800 border-gray-100 dark:border-gray-700 hover:border-[#3F51B5]/30 dark:hover:border-indigo-600/30 shadow-[0_8px_22px_rgba(0,0,0,0.05)]`}
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
                            {mod.trend && mod.trend.length >= 2 && (
                              <Sparkline
                                data={mod.trend}
                                width={64}
                                height={20}
                                strokeColor={sparkColor.stroke}
                                fillColor={sparkColor.fill}
                                strokeWidth={1.5}
                                className="ml-auto"
                              />
                            )}
                            {!mod.trend && (
                              <Progress value={mod.passRate} className="h-1.5 flex-1 bg-gray-200 dark:bg-gray-700" />
                            )}
                          </>
                        ) : (
                          <span className="text-gray-400 dark:text-gray-500">No tests yet</span>
                        )}
                      </div>
                      {mod.totalTests > 0 && (
                        <div className="text-[10px] text-gray-400 dark:text-gray-500 mt-1.5 flex items-center justify-between">
                          <div className="flex items-center gap-1">
                            <Clock className="size-2.5" />
                            {mod.lastRun}
                          </div>
                          {mod.trend && <TrendIndicator data={mod.trend} />}
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
function OperationsTab({ testGroups, testCasesModule }: { testGroups: TestClassGroup[]; testCasesModule?: { label: string; tests: any[] } }) {
  const testSpecGroups = testGroups
  const [searchVal, setSearchVal] = useState('')
  const [filter, setFilter] = useState<'all' | 'passed' | 'bug' | 'todo' | 'not-run'>('all')
  const [expandedTests, setExpandedTests] = useState<Set<string>>(new Set())
  const [sortCol, setSortCol] = useState<string>('id')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')

  const toggleTest = useCallback((id: string) => {
    setExpandedTests((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  const handleSort = useCallback((col: string) => {
    if (sortCol === col) {
      setSortDir((d) => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortCol(col)
      setSortDir('asc')
    }
  }, [sortCol])

  // Flatten all tests from all groups into one list for the table
  const allTests = useMemo(() => {
    const flat: (TestSpecItem & { groupName: string })[] = []
    for (const g of testSpecGroups) {
      for (const t of g.tests) {
        flat.push({ ...t, groupName: g.className })
      }
    }
    return flat
  }, [testSpecGroups])

  // Filter + sort
  const filteredTests = useMemo(() => {
    let result = allTests.filter((test) => {
      const matchSearch =
        searchVal === '' ||
        test.id.toLowerCase().includes(searchVal.toLowerCase()) ||
        test.description.toLowerCase().includes(searchVal.toLowerCase()) ||
        test.steps.toLowerCase().includes(searchVal.toLowerCase()) ||
        test.expected.toLowerCase().includes(searchVal.toLowerCase()) ||
        test.actual.toLowerCase().includes(searchVal.toLowerCase())
      const matchFilter =
        filter === 'all' ||
        (filter === 'passed' && test.status === 'passed') ||
        (filter === 'bug' && test.status === 'bug') ||
        (filter === 'todo' && test.status === 'todo') ||
        (filter === 'not-run' && test.status === 'not-run')
      return matchSearch && matchFilter
    })

    // Sort
    const statusOrder: Record<string, number> = { bug: 0, failed: 1, todo: 2, 'not-run': 3, passed: 4 }
    const priorityOrder: Record<string, number> = { smoke: 0, regression: 1, sanity: 2 }

    result.sort((a, b) => {
      let cmp = 0
      switch (sortCol) {
        case 'id':
          cmp = a.id.localeCompare(b.id, undefined, { numeric: true })
          break
        case 'description':
          cmp = a.description.localeCompare(b.description)
          break
        case 'status':
          cmp = (statusOrder[a.status] ?? 5) - (statusOrder[b.status] ?? 5)
          break
        case 'priority':
          cmp = (priorityOrder[a.priority ?? ''] ?? 3) - (priorityOrder[b.priority ?? ''] ?? 3)
          break
        case 'date':
          cmp = (a.date || 'zzz').localeCompare(b.date || 'zzz')
          break
        default:
          cmp = 0
      }
      return sortDir === 'desc' ? -cmp : cmp
    })

    return result
  }, [allTests, searchVal, filter, sortCol, sortDir])

  const totalTests = allTests.length
  const passedCount = allTests.filter((t) => t.status === 'passed').length
  const bugCount = allTests.filter((t) => t.status === 'bug').length
  const todoCount = allTests.filter((t) => t.status === 'todo').length
  const notRunCount = allTests.filter((t) => t.status === 'not-run').length

  const getStatusDisplay = (test: TestSpecItem) => {
    if (test.status === 'bug') {
      return { label: 'BUG', color: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400', icon: '\u{1F41B}' }
    }
    if (test.status === 'passed') {
      return { label: 'PASS', color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400', icon: '\u2705' }
    }
    if (test.status === 'failed') {
      return { label: 'FAIL', color: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400', icon: '\u274C' }
    }
    if (test.status === 'todo') {
      return { label: 'TODO', color: 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400', icon: '\u{1F4CB}' }
    }
    return { label: '\u2014', color: 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400', icon: '\u2014' }
  }

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* ─── Toolbar ─── */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-100 dark:border-gray-700 shrink-0 flex-wrap">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-gray-400" />
          <Input
            placeholder="Search tests..."
            value={searchVal}
            onChange={(e) => setSearchVal(e.target.value)}
            className="h-8 pl-8 text-[13px] bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-600 text-gray-800 dark:text-gray-100"
          />
        </div>
        <Select value={filter} onValueChange={(v) => setFilter(v as typeof filter)}>
          <SelectTrigger className="h-8 w-28 text-[13px] bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-600">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All ({totalTests})</SelectItem>
            <SelectItem value="passed">Passed ({passedCount})</SelectItem>
            <SelectItem value="bug">Bug ({bugCount})</SelectItem>
            <SelectItem value="todo">Todo ({todoCount})</SelectItem>
            <SelectItem value="not-run">Not Run ({notRunCount})</SelectItem>
          </SelectContent>
        </Select>
        <Button
          variant="outline"
          className="h-8 text-[13px] gap-1.5 border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300"
          onClick={() => {
            if (typeof window !== 'undefined') {
              const allData = (window as any).__ALL_TEST_CASES__
              if (!allData) return
              import('xlsx').then((XLSX) => {
                const wb = XLSX.utils.book_new()
                for (const [key, val] of Object.entries(allData)) {
                  const mod = val as { label: string; tests: any[] }
                  const rows = mod.tests.map((t) => ({
                    '#': t.id,
                    'Description': t.description,
                    'Steps': t.steps,
                    'Expected Result': t.expected,
                    'Actual Result': t.actual,
                    'Status': t.status,
                    'Date': t.date,
                  }))
                  const ws = XLSX.utils.json_to_sheet(rows)
                  XLSX.utils.book_append_sheet(wb, ws, mod.label.substring(0, 31))
                }
                XLSX.writeFile(wb, 'RhythmERP_Test_Specifications.xlsx')
              }).catch(() => {
                alert('xlsx library not installed. Run: npm install xlsx')
              })
            }
          }}
        >
          <FileSpreadsheet className="size-3.5" />
          Export
        </Button>
        <div className="flex-1" />
        <Separator orientation="vertical" className="h-5 mx-1" />
        <div className="flex items-center gap-3 text-[12px]">
          <span className="text-gray-500 dark:text-gray-400">{filteredTests.length} of {totalTests}</span>
          {bugCount > 0 && (
            <span className="text-red-500 dark:text-red-400 font-medium">{'\u{1F41B}'} {bugCount} bug{bugCount !== 1 ? 's' : ''}</span>
          )}
        </div>
      </div>

      {/* ─── Summary Badges ─── */}
      {totalTests > 0 && (
        <div className="flex items-center gap-2 px-4 py-2 border-b border-gray-50 dark:border-gray-800 shrink-0">
          <button
            onClick={() => setFilter('all')}
            className={`text-[11px] px-2 py-0.5 rounded-full font-medium transition-colors cursor-pointer ${filter === 'all' ? 'bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-100' : 'bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'}`}
          >
            All {totalTests}
          </button>
          <button
            onClick={() => setFilter('passed')}
            className={`text-[11px] px-2 py-0.5 rounded-full font-medium transition-colors cursor-pointer ${filter === 'passed' ? 'bg-green-200 dark:bg-green-800 text-green-800 dark:text-green-200' : 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 hover:bg-green-100 dark:hover:bg-green-900/40'}`}
          >
            {'\u2705'} Passed {passedCount}
          </button>
          <button
            onClick={() => setFilter('bug')}
            className={`text-[11px] px-2 py-0.5 rounded-full font-medium transition-colors cursor-pointer ${filter === 'bug' ? 'bg-red-200 dark:bg-red-800 text-red-800 dark:text-red-200' : 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/40'}`}
          >
            {'\u{1F41B}'} Bug {bugCount}
          </button>
          {todoCount > 0 && (
            <button
              onClick={() => setFilter('todo')}
              className={`text-[11px] px-2 py-0.5 rounded-full font-medium transition-colors cursor-pointer ${filter === 'todo' ? 'bg-amber-200 dark:bg-amber-800 text-amber-800 dark:text-amber-200' : 'bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 hover:bg-amber-100 dark:hover:bg-amber-900/40'}`}
            >
              {'\u{1F4CB}'} Todo {todoCount}
            </button>
          )}
          {notRunCount > 0 && (
            <button
              onClick={() => setFilter('not-run')}
              className={`text-[11px] px-2 py-0.5 rounded-full font-medium transition-colors cursor-pointer ${filter === 'not-run' ? 'bg-gray-300 dark:bg-gray-600 text-gray-800 dark:text-gray-200' : 'bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'}`}
            >
              Not Run {notRunCount}
            </button>
          )}
        </div>
      )}

      {/* ─── Table ─── */}
      <ScrollArea className="flex-1 min-h-0">
        <Table>
          <TableHeader>
            <TableRow className="bg-[#DFE9FB] dark:bg-indigo-900/30 hover:bg-[#DFE9FB] dark:hover:bg-indigo-900/30">
              <TableHead
                className="text-[#3F51B5] dark:text-indigo-300 text-[12px] font-semibold cursor-pointer select-none w-12"
                onClick={() => handleSort('id')}
              >
                <span className="inline-flex items-center gap-1"># <SortArrow col="id" sortCol={sortCol} sortDir={sortDir} /></span>
              </TableHead>
              <TableHead
                className="text-[#3F51B5] dark:text-indigo-300 text-[12px] font-semibold cursor-pointer select-none"
                onClick={() => handleSort('description')}
              >
                <span className="inline-flex items-center gap-1">Description <SortArrow col="description" sortCol={sortCol} sortDir={sortDir} /></span>
              </TableHead>
              <TableHead
                className="text-[#3F51B5] dark:text-indigo-300 text-[12px] font-semibold cursor-pointer select-none w-24"
                onClick={() => handleSort('status')}
              >
                <span className="inline-flex items-center gap-1">Status <SortArrow col="status" sortCol={sortCol} sortDir={sortDir} /></span>
              </TableHead>
              <TableHead
                className="text-[#3F51B5] dark:text-indigo-300 text-[12px] font-semibold cursor-pointer select-none w-28"
                onClick={() => handleSort('priority')}
              >
                <span className="inline-flex items-center gap-1">Priority <SortArrow col="priority" sortCol={sortCol} sortDir={sortDir} /></span>
              </TableHead>
              <TableHead
                className="text-[#3F51B5] dark:text-indigo-300 text-[12px] font-semibold cursor-pointer select-none w-28"
                onClick={() => handleSort('date')}
              >
                <span className="inline-flex items-center gap-1">Date <SortArrow col="date" sortCol={sortCol} sortDir={sortDir} /></span>
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredTests.map((test) => {
              const isExpanded = expandedTests.has(test.id)
              const statusInfo = getStatusDisplay(test)

              return (
                <React.Fragment key={test.id}>
                  {/* ─── Main Row ─── */}
                  <TableRow
                    className={`cursor-pointer transition-colors hover:bg-gray-50 dark:hover:bg-gray-800/50 ${isExpanded ? 'bg-gray-50/50 dark:bg-gray-800/30' : ''} ${test.status === 'bug' ? 'border-l-2 border-l-red-400 dark:border-l-red-500' : test.status === 'todo' ? 'border-l-2 border-l-amber-400 dark:border-l-amber-500' : ''}`}
                    onClick={() => toggleTest(test.id)}
                  >
                    <TableCell className="text-[12px] text-gray-500 dark:text-gray-400 font-mono py-2.5">
                      {test.id}
                    </TableCell>
                    <TableCell className="text-[13px] text-gray-800 dark:text-gray-100 py-2.5">
                      <div className="flex items-center gap-2">
                        {isExpanded ? (
                          <ChevronDown className="size-3.5 text-gray-400 dark:text-gray-500 shrink-0" />
                        ) : (
                          <ChevronRight className="size-3.5 text-gray-400 dark:text-gray-500 shrink-0" />
                        )}
                        <span className="truncate">{test.description}</span>
                      </div>
                    </TableCell>
                    <TableCell className="py-2.5">
                      <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium whitespace-nowrap ${statusInfo.color}`}>
                        {statusInfo.icon} {statusInfo.label}
                      </span>
                    </TableCell>
                    <TableCell className="py-2.5">
                      <PriorityBadge priority={test.priority} />
                    </TableCell>
                    <TableCell className="text-[11px] text-gray-500 dark:text-gray-400 py-2.5">
                      {test.date || '\u2014'}
                    </TableCell>
                  </TableRow>

                  {/* ─── Expanded Detail Row ─── */}
                  {isExpanded && (
                    <TableRow
                      className={`bg-gray-50/40 dark:bg-gray-800/20 hover:bg-gray-50/40 dark:hover:bg-gray-800/20 ${test.status === 'bug' ? 'border-l-2 border-l-red-400 dark:border-l-red-500' : test.status === 'todo' ? 'border-l-2 border-l-amber-400 dark:border-l-amber-500' : ''}`}
                    >
                      <TableCell colSpan={5} className="py-0 px-6">
                        <div className="py-3 pl-7 space-y-3">
                          {test.screenName && (
                            <div className="flex items-start gap-3">
                              <span className="text-[11px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider w-20 shrink-0 pt-0.5">Screen</span>
                              <span className="text-[12px] text-gray-600 dark:text-gray-300">{test.screenName}</span>
                            </div>
                          )}
                          {test.steps && (
                            <div className="flex items-start gap-3">
                              <span className="text-[11px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider w-20 shrink-0 pt-0.5">Steps</span>
                              <p className="text-[12px] text-gray-600 dark:text-gray-300 leading-5 whitespace-pre-line flex-1">{test.steps}</p>
                            </div>
                          )}
                          <div className="flex items-start gap-3">
                            <span className="text-[11px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider w-20 shrink-0 pt-0.5">Expected</span>
                            <p className="text-[12px] text-gray-600 dark:text-gray-300 leading-5 flex-1">{test.expected}</p>
                          </div>
                          <div className="flex items-start gap-3">
                            <span className="text-[11px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider w-20 shrink-0 pt-0.5">Actual</span>
                            <p className="text-[12px] text-gray-600 dark:text-gray-300 leading-5 flex-1">{test.actual || '\u2014'}</p>
                          </div>
                          {test.bugDetails && (
                            <div className="flex items-start gap-3">
                              <span className="text-[11px] font-semibold text-red-500 dark:text-red-400 uppercase tracking-wider w-20 shrink-0 pt-0.5">Bug</span>
                              <p className="text-[12px] text-red-600 dark:text-red-400 leading-5 bg-red-50 dark:bg-red-900/20 px-2.5 py-1.5 rounded flex-1">
                                {test.bugDetails}
                              </p>
                            </div>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  )}
                </React.Fragment>
              )
            })}

            {filteredTests.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} className="h-40 text-center">
                  <div className="flex flex-col items-center justify-center text-gray-400 dark:text-gray-500">
                    <Search className="size-8 mb-2 opacity-50" />
                    <p className="text-[13px]">No tests match your search criteria</p>
                  </div>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </ScrollArea>
    </div>
  )
}
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
  const pendingOrRunning = tests.filter((t) => t.status === 'pending' || t.status === 'running')
  const allSelected = pendingOrRunning.length > 0 && pendingOrRunning.every((t) => testChecks.has(t.id))
  const noneSelected = pendingOrRunning.every((t) => !testChecks.has(t.id))

  const handleSelectAll = useCallback(() => {
    if (allSelected) {
      // Deselect all
      pendingOrRunning.forEach((t) => { if (testChecks.has(t.id)) toggleTestCheck(t.id) })
    } else {
      // Select all pending/running
      pendingOrRunning.forEach((t) => { if (!testChecks.has(t.id)) toggleTestCheck(t.id) })
    }
  }, [allSelected, pendingOrRunning, testChecks, toggleTestCheck])

  const passedCount = tests.filter((t) => t.status === 'passed').length
  const failedCount = tests.filter((t) => t.status === 'failed').length
  const pendingCount = tests.filter((t) => t.status === 'pending').length
  const selectedRunnable = tests.filter((t) => t.status === 'pending' && testChecks.has(t.id)).length
  const smokeCount = tests.filter((t) => t.priority === 'smoke' && (t.status === 'pending' || t.status === 'running')).length
  const regressionCount = tests.filter((t) => t.priority === 'regression' && (t.status === 'pending' || t.status === 'running')).length

  // Group tests by class
  const testGroups: { name: string; tests: TestItem[] }[] = []
  let currentGroup: string | null = null
  for (const t of tests) {
    const cls = t.id.replace(/\d+$/, '').replace(/T/, 'Test')
    if (cls !== currentGroup) {
      currentGroup = cls
      testGroups.push({ name: cls, tests: [] })
    }
    testGroups[testGroups.length - 1].tests.push(t)
  }

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Action Bar */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-100 dark:border-gray-700 shrink-0 flex-wrap" data-tour="run-buttons">
        <Button
          onClick={() => onRun(false)}
          disabled={isRunning || pendingCount === 0}
          className="bg-[#2D3FC7] hover:bg-[#3F51B5] text-white h-9 text-[13px] gap-2 px-5 cursor-pointer font-['Roboto']"
        >
          <Play className="size-4" />
          Run All ({pendingCount})
        </Button>
        <Button
          onClick={() => onRun(true)}
          disabled={isRunning || selectedRunnable === 0}
          className="bg-[#2D3FC7] hover:bg-[#3F51B5] text-white h-9 text-[13px] gap-2 px-5 cursor-pointer"
        >
          <Play className="size-4" />
          Run Selected ({selectedRunnable})
        </Button>
                <Button
          onClick={handleSelectAll}
          disabled={isRunning}
          variant="outline"
          className="border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 h-9 text-[13px] gap-2 px-4 cursor-pointer"
        >
          {allSelected ? '✖ Deselect All' : '☑ Select All'}
          <span className="text-[11px] opacity-60">({selectedRunnable}/{pendingCount})</span>
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
          className="bg-[#2D3FC7] hover:bg-[#3F51B5] text-white h-9 text-[13px] gap-2 px-4 cursor-pointer"
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
      <ScrollArea className="flex-1 min-h-0">
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
                      <span className="text-[11px] text-gray-400 dark:text-gray-500 font-mono w-16 shrink-0 truncate" title={test.id}>{test.id.split('::').pop()?.replace(/^test_/, '') || test.id}</span>
                      <span className={`text-[13px] flex-1 truncate ${
                        test.status === 'running' ? 'text-indigo-600 dark:text-indigo-400 font-medium' :
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

// ─── LIVE SCREENCAST ─────────────────────────────────────
function LiveScreencast({ isRunning, onScreenshotReady }: { isRunning: boolean; onScreenshotReady?: (src: string, active: boolean) => void }) {
  const [imgSrc, setImgSrc] = useState<string>('')
  const [active, setActive] = useState(false)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    if (!isRunning) {
      if (intervalRef.current) clearInterval(intervalRef.current)
      return
    }

    const poll = async () => {
      try {
        const data = await fetchScreenshot()
        if (data.active && data.screenshot) {
          const src = `data:image/png;base64,${data.screenshot}`
          setImgSrc(src)
          setActive(true)
          onScreenshotReady?.(src, true)
        } else {
          setActive(false)
          onScreenshotReady?.('', false)
        }
      } catch {
        setActive(false)
      }
    }

    poll()
    intervalRef.current = setInterval(poll, 1000)
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [isRunning])

  if (!active || !imgSrc) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center gap-3 bg-gray-900">
        <Loader2 className="size-8 text-green-400 animate-spin" />
        <p className="text-[13px] text-gray-400">Connecting to browser...</p>
        <p className="text-[11px] text-gray-600">Make sure FastAPI backend is running</p>
      </div>
    )
  }

  return (
    <div className="w-full h-full relative bg-black">
      <img
        src={imgSrc}
        alt="Live browser"
        className="w-full h-full object-contain"
      />
      <div className="absolute top-2 right-2 flex items-center gap-1.5 bg-black/60 text-white text-[10px] px-2 py-1 rounded-full">
        <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
        LIVE
      </div>
    </div>
  )
}

// ─── LIVE EXECUTION TAB (Browser view + Console) ────────
function LiveExecutionTab({
  tests,
  testGroups,
  isRunning,
  runningProgress,
  onStop,
  onBack,
  onRerunFailed,
}: {
  tests: TestItem[]
  testGroups: TestClassGroup[]
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


  const [tvPopupOpen, setTvPopupOpen] = useState(false)
  const [tvImgSrc, setTvImgSrc] = useState<string>('')
  const [tvActive, setTvActive] = useState(false)
  const handleScreenshotReady = useCallback((src: string, active: boolean) => {
    setTvImgSrc(src)
    setTvActive(active)
  }, [])

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && tvPopupOpen) setTvPopupOpen(false)
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [tvPopupOpen])
  const [consoleHeight, setConsoleHeight] = useState(220)
  const isResizingRef = useRef(false)
  const resizeStartRef = useRef({ y: 0, h: 0 })
  const handleConsoleResizeStart = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    isResizingRef.current = true
    resizeStartRef.current = { y: e.clientY, h: consoleHeight }
    const onMove = (ev: MouseEvent) => {
      if (!isResizingRef.current) return
      const delta = resizeStartRef.current.y - ev.clientY
      setConsoleHeight(Math.max(120, Math.min(500, resizeStartRef.current.h + delta)))
    }
    const onUp = () => {
      isResizingRef.current = false
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
    }
    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onUp)
  }, [consoleHeight])

  const runningTest = tests.find((t) => t.status === 'running')
  const runningTestId = runningTest?.id || null

  const runningSteps = useMemo(() => {
    if (!runningTestId) return []
    for (const g of testGroups) {
      const t = g.tests.find((x) =>
        x.id === runningTestId ||
        runningTestId.endsWith('::' + x.id) ||
        runningTestId.includes(x.id)
      )
      if (t) {
        const stepsText = t.steps || t.description || ''
        const arrowSteps = stepsText.split('→').map((s) => s.trim()).filter(Boolean)
        if (arrowSteps.length > 1) return arrowSteps
        const numberedSteps = stepsText.split(/\d+\.\s+/).map((s) => s.trim()).filter(Boolean)
        if (numberedSteps.length > 1) return numberedSteps
        const newlineSteps = stepsText.split('\n').map((s) => s.trim()).filter(Boolean)
        if (newlineSteps.length > 1) return newlineSteps
        const sentenceSteps = stepsText.split(/\.\s+/).map((s) => s.trim()).filter(Boolean)
        if (sentenceSteps.length > 1) return sentenceSteps
        const trimmed = stepsText.trim()
        if (trimmed.length <= 80) return [trimmed]
        const words = trimmed.split(' ')
        const lines: string[] = []
        let current = ''
        for (const word of words) {
          if ((current + ' ' + word).trim().length > 60 && current.length > 0) {
            lines.push(current.trim())
            current = word
          } else {
            current = current ? current + ' ' + word : word
          }
        }
        if (current) lines.push(current.trim())
        return lines
      }
    }
    for (const g of testSpecGroups) {
      const t = g.tests.find((x) => x.id === runningTestId)
      if (t) {
        const arrowSteps = t.steps.split('→').map((s) => s.trim()).filter(Boolean)
        if (arrowSteps.length > 0) return arrowSteps
      }
    }
    const rt = tests.find((t) => t.id === runningTestId)
    return rt ? [rt.name] : ['Running test...']
  }, [runningTestId, testGroups, tests])

  useEffect(() => {
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

﻿  return (
    <>
    <div className="flex flex-col h-full min-h-0">
      {/* ── Top Bar ── */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-white/10 bg-slate-900/80 backdrop-blur-sm shrink-0">
        <Button variant="ghost" onClick={onBack} className="h-8 text-[13px] gap-1.5 text-slate-400 hover:text-white hover:bg-white/5 cursor-pointer px-2.5 rounded-lg">
          <ArrowLeft className="size-4" />
          Test Runner
        </Button>
        <div className="w-px h-5 bg-white/10" />
        {isRunning ? (
          <>
            <div className="flex items-center gap-3 flex-1">
              <Progress value={progressPercent} className="h-2 flex-1 [&>div]:bg-gradient-to-r [&>div]:from-emerald-500 [&>div]:to-emerald-400" />
              <span className="text-[13px] text-slate-300 font-semibold tabular-nums min-w-[80px]">
                {completedCount}/{tests.length}
                <span className="text-slate-500 ml-1">({progressPercent}%)</span>
              </span>
            </div>
            <div className="flex-1" />
            <Button onClick={onStop} className="bg-red-500/90 hover:bg-red-500 text-white h-8 text-[13px] gap-1.5 cursor-pointer rounded-lg shadow-lg shadow-red-500/20">
              <Square className="size-3.5" />
              Stop
            </Button>
          </>
        ) : completedCount > 0 ? (
          <>
            <span className="text-[13px] text-slate-400">
              Run complete — <span className="text-emerald-400 font-semibold">{passedCount} passed</span>, <span className="text-red-400 font-semibold">{failedCount} failed</span>
            </span>
            <div className="flex-1" />
            {failedCount > 0 && (
              <Button onClick={onRerunFailed} className="bg-amber-500/90 hover:bg-amber-500 text-white h-8 text-[13px] gap-1.5 cursor-pointer rounded-lg shadow-lg shadow-amber-500/20 mr-2">
                <RotateCcw className="size-3.5" />
                Rerun Failed ({failedCount})
              </Button>
            )}
            <Button onClick={onBack} className="bg-blue-500/90 hover:bg-blue-500 text-white h-8 text-[13px] gap-1.5 cursor-pointer rounded-lg shadow-lg shadow-blue-500/20">
              <RotateCcw className="size-3.5" />
              New Run
            </Button>
          </>
        ) : (
          <>
            <span className="text-[13px] text-slate-500">No test running</span>
            <div className="flex-1" />
          </>
        )}
        <div className="flex items-center gap-2 ml-2">
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-[12px] font-medium tabular-nums">
            <CheckCircle2 className="size-3.5" /> {passedCount}
          </span>
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-500/10 text-red-400 text-[12px] font-medium tabular-nums">
            <XCircle className="size-3.5" /> {failedCount}
          </span>
        </div>
      </div>

      {/* ── Main Content ── */}
      <div className="flex-1 overflow-hidden flex flex-col">
        <div className="flex-1 px-4 pt-3 pb-2 min-h-0 flex gap-4">
          {/* Step Progress Panel */}
          {isRunning && runningTest && runningSteps.length > 0 && (
            <div className="w-72 shrink-0 flex flex-col rounded-xl bg-slate-900 border border-white/[0.06] shadow-2xl shadow-black/40 overflow-hidden">
              <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.06] bg-gradient-to-r from-blue-500/10 to-purple-500/10">
                <div className="flex items-center gap-2.5">
                  <div className="w-6 h-6 rounded-md bg-blue-500/20 flex items-center justify-center">
                    <ClipboardList className="size-3.5 text-blue-400" />
                  </div>
                  <span className="text-[13px] font-semibold text-slate-200">Test Steps</span>
                </div>
                <span className="text-[11px] text-blue-400 font-semibold tabular-nums px-2 py-0.5 rounded-full bg-blue-500/10">
                  {Math.min(currentStepIndex + 1, runningSteps.length)}/{runningSteps.length}
                </span>
              </div>
              <div className="flex-1 overflow-auto p-3 space-y-1.5">
                {runningSteps.map((step, idx) => {
                  const isCompleted = idx < currentStepIndex
                  const isCurrent = idx === currentStepIndex
                  return (
                    <div key={idx} className={
                      'flex items-start gap-2 px-3 py-2 rounded-lg text-[12px] transition-all duration-200 ' +
                      (isCompleted
                        ? 'bg-emerald-500/[0.07] text-emerald-300/80'
                        : isCurrent
                          ? 'bg-blue-500/[0.12] text-blue-200 ring-1 ring-blue-500/30 shadow-lg shadow-blue-500/5'
                          : 'text-slate-600 hover:text-slate-500')
                    }>
                      <span className="text-[10px] font-mono tabular-nums mt-0.5 w-4 shrink-0 text-right opacity-40">{idx + 1}</span>
                      {isCompleted ? (
                        <CheckCircle2 className="size-4 text-emerald-400/70 shrink-0 mt-0.5" />
                      ) : isCurrent ? (
                        <Loader2 className="size-4 text-blue-400 shrink-0 mt-0.5 animate-spin" />
                      ) : (
                        <Circle className="size-3.5 text-slate-700 shrink-0 mt-1" />
                      )}
                      <span className="flex-1 leading-relaxed">{step}</span>
                      {isCurrent && (
                        <span className="text-[10px] text-blue-400 font-medium shrink-0 mt-0.5 flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
                          Run
                        </span>
                      )}
                    </div>
                  )
                })}
              </div>
              <div className="px-4 py-3 border-t border-white/[0.06] bg-slate-900/50">
                <div className="flex items-center justify-between text-[11px] text-slate-500 mb-2">
                  <span>Progress</span>
                  <span className="font-semibold text-slate-300 tabular-nums">
                    {Math.round(((currentStepIndex + 1) / runningSteps.length) * 100)}%
                  </span>
                </div>
                <Progress value={((currentStepIndex + 1) / runningSteps.length) * 100} className="h-2 bg-slate-800 [&>div]:bg-gradient-to-r [&>div]:from-blue-500 [&>div]:to-cyan-400" />
              </div>
            </div>
          )}

          {/* Live Browser View */}
          <div className="flex-1 min-w-0 flex flex-col">
            <div className="flex-1 rounded-xl border border-white/[0.08] overflow-hidden flex flex-col shadow-2xl shadow-black/30 bg-slate-900 min-h-0">
              {/* Chrome bar */}
              <div className="bg-slate-800 px-4 py-2 flex items-center gap-3 shrink-0 border-b border-white/[0.04]">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-[#ff5f57]" />
                  <div className="w-3 h-3 rounded-full bg-[#febc2e]" />
                  <div className="w-3 h-3 rounded-full bg-[#28c840]" />
                </div>
                <div className="flex-1 flex items-center justify-center">
                  <div className="bg-slate-900/80 rounded-lg px-4 py-1 flex items-center gap-2 text-[11px] text-slate-500 border border-white/[0.06] max-w-md w-full">
                    <Globe className="size-3.5 text-slate-600 shrink-0" />
                    <span className="truncate text-center">
                      {isRunning ? 'https://rhythmerp.com — ' + (runningTest?.name || 'Running...') : 'https://rhythmerp.com'}
                    </span>
                  </div>
                </div>
                {isRunning && runningTest && (
                  <button
                    onClick={() => setTvPopupOpen(true)}
                    className="flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-medium text-slate-400 hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
                    title="Pop-out TV Screen"
                  >
                    <Monitor className="size-3.5" />
                    <span>TV Screen</span>
                    <Maximize2 className="size-3" />
                  </button>
                )}
                <MoreHorizontal className="size-4 text-slate-600" />
              </div>

              {/* Browser content */}
              <div className="flex-1 overflow-hidden relative bg-slate-950">
                {isRunning && runningTest ? (
                  <LiveScreencast isRunning={isRunning} onScreenshotReady={handleScreenshotReady} />
                ) : completedCount > 0 ? (
                  <div className="w-full h-full flex flex-col items-center justify-center gap-3">
                    <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 flex items-center justify-center">
                      <CheckCircle2 className="size-8 text-emerald-400" />
                    </div>
                    <div className="text-center">
                      <p className="text-[15px] font-semibold text-slate-200">Run Complete</p>
                      <p className="text-[13px] text-slate-500 mt-1">{passedCount} passed, {failedCount} failed</p>
                    </div>
                  </div>
                ) : (
                  <div className="w-full h-full flex flex-col items-center justify-center gap-4">
                    <div className="w-20 h-20 rounded-full bg-slate-800 flex items-center justify-center border border-white/[0.06]">
                      <Play className="size-8 text-slate-600 ml-1" />
                    </div>
                    <div className="text-center">
                      <p className="text-[14px] text-slate-500 font-medium">No test running</p>
                      <p className="text-[12px] text-slate-600 mt-1">Go to Test Runner, select tests and click Run</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Currently running info */}
            {isRunning && runningTest && (
              <div className="flex items-center gap-3 mt-2 px-1">
                <span className="text-[12px] text-slate-500">
                  Currently: <span className="font-medium text-slate-300">{runningTest.id}</span> — {runningTest.name}
                </span>
                <div className="w-px h-3 bg-slate-700" />
                <span className="text-[12px] text-blue-400 flex items-center gap-1.5">
                  <Loader2 className="size-3 animate-spin" />
                  Running...
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Console resize handle */}
        <div
          className="shrink-0 h-1.5 bg-slate-800 cursor-row-resize hover:bg-blue-500/50 active:bg-blue-500/50 transition-colors flex items-center justify-center group"
          onMouseDown={handleConsoleResizeStart}
        >
          <div className="w-8 h-0.5 rounded-full bg-slate-600 group-hover:bg-blue-400 transition-colors" />
        </div>

        {/* Console */}
        <div className="shrink-0 flex flex-col border-t border-white/[0.06]" style={{ height: consoleHeight }}>
          <div className="flex items-center gap-2 px-3 py-2 bg-slate-900 border-b border-white/[0.06] shrink-0">
            <Terminal className="size-3.5 text-emerald-400" />
            <span className="text-[12px] font-semibold text-slate-300 tracking-wide">LIVE CONSOLE</span>
            <span className="text-[10px] text-slate-600 ml-auto font-mono bg-slate-800 px-1.5 py-0.5 rounded">pytest</span>
          </div>
          <div className="flex-1 bg-slate-950 overflow-auto p-3">
            <div className="space-y-px">
              {consoleLines.map((line, i) => (
                <div key={i} className={
                  'text-xs font-mono leading-5 ' +
                  (line.includes('PASSED') || line.includes('passed')
                    ? 'text-emerald-400'
                    : line.includes('FAILED') || line.includes('ERROR') || line.includes('failed')
                      ? 'text-red-400'
                      : line.includes('Running') || line.includes('Navigating') || line.includes('Clicking') || line.includes('Typing')
                        ? 'text-amber-300'
                        : line.startsWith('>')
                          ? 'text-blue-400'
                          : 'text-slate-500')
                }>
                  {line}
                </div>
              ))}
              <div ref={consoleEndRef} />
            </div>
          </div>
        </div>
      </div>
    </div>

      {/* TV Screen Popup */}
      {tvPopupOpen && (
        <div
          className="fixed inset-0 z-[9999] bg-black/90 flex items-center justify-center p-4"
          onClick={() => setTvPopupOpen(false)}
        >
          <div
            className="relative w-full max-w-[90vw] h-[85vh] rounded-2xl overflow-hidden border-[3px] border-gray-600 flex flex-col bg-black"
            onClick={(e) => e.stopPropagation()}
            style={{ boxShadow: "0 0 0 1px rgba(255,255,255,0.08), 0 0 80px rgba(0,0,0,0.8)" }}
          >
            <div className="shrink-0 bg-gradient-to-b from-gray-800 to-gray-900 px-4 py-2 flex items-center justify-between border-b border-gray-700">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded-full bg-red-500" /><div className="w-3 h-3 rounded-full bg-yellow-500" /><div className="w-3 h-3 rounded-full bg-green-500" /></div>
                {tvActive && <div className="flex items-center gap-1.5 bg-red-600/80 text-white text-[10px] font-bold px-2.5 py-0.5 rounded-full"><span className="w-2 h-2 rounded-full bg-white animate-pulse" />LIVE</div>}
              </div>
              <div className="flex-1 max-w-[600px] mx-4"><div className="bg-gray-800/80 rounded-lg px-4 py-1 flex items-center gap-2 text-[12px] text-gray-400 border border-gray-700"><Globe className="size-3.5" /><span className="truncate">https://rhythmerp.com - {runningTest?.name || "Running..."}</span></div></div>
              <button onClick={() => setTvPopupOpen(false)} className="flex items-center gap-1.5 px-3 py-1 rounded-lg text-[12px] font-medium text-gray-300 hover:bg-gray-700 hover:text-white transition-colors cursor-pointer"><X className="size-4" /><span>Close</span></button>
            </div>
            <div className="flex-1 relative bg-black overflow-hidden">
              {tvActive && tvImgSrc ? <img src={tvImgSrc} alt="TV view" className="w-full h-full object-contain" /> : <div className="w-full h-full flex flex-col items-center justify-center gap-3"><Loader2 className="size-10 text-green-400 animate-spin" /><p className="text-[14px] text-gray-500">Connecting...</p></div>}
            </div>
            <div className="shrink-0 h-3 bg-gradient-to-t from-gray-800 to-gray-900 border-t border-gray-700 rounded-b-2xl" />
            {isRunning && runningTest && <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-black/70 text-white px-5 py-2 rounded-full flex items-center gap-3 text-[12px] border border-white/10"><Loader2 className="size-3.5 animate-spin text-blue-400" /><span className="font-medium">{runningTest.id}</span><span className="text-gray-400">-</span><span className="text-gray-300">{runningTest.name}</span></div>}
          </div>
        </div>
      )}
    </>
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
    const loadRuns = async () => setRuns(await getScheduledRuns())
    loadRuns()
  }, [])

  // Countdown timer
  useEffect(() => {
    const tick = async () => {
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
            await updateScheduledRun(run.id, { lastRunAt: new Date().toISOString(), enabled: false })
            await addNotification({ type: 'run_complete', title: 'Scheduled run completed', message: `Scheduled run for ${run.moduleName} completed (mock)` })
            setRuns(await getScheduledRuns())
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

  const handleAddRun = useCallback(async () => {
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

    await addScheduledRun({
      moduleId,
      moduleName: modName,
      frequency,
      scheduledTime: scheduledTimeStr,
      testSelection,
      enabled: true,
      createdBy: userName,
    })
    setRuns(await getScheduledRuns())
    setShowForm(false)
    toast.success(`Scheduled run created for ${modName}`)
  }, [moduleId, frequency, scheduledDate, scheduledTime, weeklyDay, testSelection, userName, sidebarModules])

  const handleDelete = useCallback(async (id: string) => {
    await deleteScheduledRun(id)
    setRuns(await getScheduledRuns())
    toast.success('Schedule deleted')
  }, [])

  const handleToggle = useCallback(async (id: string, enabled: boolean) => {
    await updateScheduledRun(id, { enabled: !enabled })
    setRuns(await getScheduledRuns())
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
  }, [sidebarModules])

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
            className="bg-[#2D3FC7] hover:bg-[#3F51B5] text-white text-[12px] cursor-pointer rounded-lg font-semibold"
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
              <Button size="sm" onClick={handleAddRun} className="bg-[#2D3FC7] hover:bg-[#3F51B5] text-white text-[12px] cursor-pointer rounded-lg font-semibold">
                <CalendarClock className="size-3.5 mr-1" /> Create Schedule
              </Button>
              <Button size="sm" onClick={() => { setShowForm(false); setFrequency('one-time'); setScheduledDate(''); setScheduledTime('') }} className="text-[12px] cursor-pointer bg-transparent text-[#F44336] hover:bg-red-50">
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
    setTimeout(async () => {
      await addBugReport({
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
          <Button onClick={onClose} className="cursor-pointer text-[12px] bg-transparent text-[#F44336] hover:bg-red-50">Cancel</Button>
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
        <div className={`rounded-lg p-4 text-center ${allPassed ? 'bg-[#E8F5E9] dark:bg-green-900/20' : 'bg-[#FFF3E0] dark:bg-orange-900/20'}`}>
          <div className="flex justify-center mb-2">
            {allPassed ? (
              <div className="w-14 h-14 rounded-full bg-[#C8E6C9] dark:bg-green-900/40 flex items-center justify-center">
                <CheckCircle2 className="size-8 text-[#2E7D32] dark:text-green-400" />
              </div>
            ) : (
              <div className="w-14 h-14 rounded-full bg-[#FFE0B2] dark:bg-orange-900/40 flex items-center justify-center">
                <AlertTriangle className="size-8 text-[#E65100] dark:text-orange-400" />
              </div>
            )}
          </div>
          <h3 className={`text-[18px] font-bold ${allPassed ? 'text-[#2E7D32] dark:text-green-400' : 'text-[#E65100] dark:text-orange-400'}`}>
            {allPassed ? 'All Tests Passed!' : 'Tests Completed with Failures'}
          </h3>
          <p className="text-[13px] text-gray-500 dark:text-gray-400 mt-1">
            {allPassed ? 'Congratulations! Every test in this run passed successfully.' : `${failedCount} test${failedCount !== 1 ? 's' : ''} failed. Review results for details.`}
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-[#E8F5E9] dark:bg-green-900/20 rounded-lg p-3 text-center border border-[#C8E6C9] dark:border-green-800/50">
            <div className="text-[11px] text-[#4CAF50] dark:text-green-400 font-medium uppercase">Passed</div>
            <div className="text-2xl font-bold text-[#2E7D32] dark:text-green-400 mt-1">{passedCount}</div>
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
          <Button onClick={onNewRun} className="flex-1 h-9 text-[13px] gap-2 bg-[#2D3FC7] hover:bg-[#3F51B5] text-white cursor-pointer font-['Roboto']">
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
  bugReportsList,
}: {
  tests: TestItem[]
  passedCount: number
  failedCount: number
  totalCount: number
  runHistory: RunSnapshot[]
  onReportTest: (test: TestItem) => void
  bugReportsList: { id: string; testId: string; desc: string; status: string }[]
}) {
  const passRate = Math.round((passedCount / totalCount) * 100)
  const [resultFilter, setResultFilter] = useState<'all' | 'passed' | 'failed'>('all')
  const [compareRun1, setCompareRun1] = useState<string>('')
  const [compareRun2, setCompareRun2] = useState<string>('')
  const [sortCol, setSortCol] = useState<'status' | 'id' | 'test' | 'duration'>('id')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')

  const handleSort = (col: 'status' | 'id' | 'test' | 'duration') => {
    if (sortCol === col) {
      setSortDir(prev => prev === 'asc' ? 'desc' : 'asc')
    } else {
      setSortCol(col)
      setSortDir('asc')
    }
  }

  const filteredTests = tests
    .filter((t) => {
      if (resultFilter === 'all') return true
      return resultFilter === 'passed' ? t.status === 'passed' : t.status === 'failed'
    })
    .sort((a, b) => {
      const dir = sortDir === 'asc' ? 1 : -1
      switch (sortCol) {
        case 'status': return dir * a.status.localeCompare(b.status)
        case 'id': return dir * a.id.localeCompare(b.id)
        case 'test': return dir * a.name.localeCompare(b.name)
        case 'duration': {
          const parseDur = (d: string) => { const p = d.split(':'); return p.length === 2 ? parseInt(p[0]) * 60 + parseInt(p[1]) : 0 }
          return dir * (parseDur(a.duration) - parseDur(b.duration))
        }
        default: return 0
      }
    })

  // Get error info from testSpecGroups
  const getTestError = (id: string): string | undefined => {
    for (const g of testSpecGroups) {
      const t = g.tests.find((x) => x.id === id)
      if (t) return t.bugDetails || (t.status === 'bug' ? t.actual : undefined)
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
          <div className="bg-indigo-50 dark:bg-indigo-900/20 rounded-lg p-4 border border-indigo-100 dark:border-indigo-800/50">
            <div className="text-[12px] text-indigo-600 dark:text-indigo-400 font-medium mb-1">Pass Rate</div>
            <div className="text-2xl font-bold text-indigo-700 dark:text-indigo-400">{passRate}%</div>
            <Progress value={passRate} className="h-1.5 mt-2 bg-indigo-100 dark:bg-indigo-800" />
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
              <TableRow className="bg-[#DFE9FB] dark:bg-indigo-900/30 hover:bg-[#DFE9FB] dark:hover:bg-indigo-900/30">
                <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 w-12 cursor-pointer select-none" onClick={() => handleSort('status')}>
                  <span className="inline-flex items-center gap-1">Status <SortArrow col="status" sortCol={sortCol} sortDir={sortDir} /></span>
                </TableHead>
                <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 w-14 cursor-pointer select-none" onClick={() => handleSort('id')}>
                  <span className="inline-flex items-center gap-1">ID <SortArrow col="id" sortCol={sortCol} sortDir={sortDir} /></span>
                </TableHead>
                <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 cursor-pointer select-none" onClick={() => handleSort('test')}>
                  <span className="inline-flex items-center gap-1">Test <SortArrow col="test" sortCol={sortCol} sortDir={sortDir} /></span>
                </TableHead>
                <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 w-16 text-center cursor-pointer select-none" onClick={() => handleSort('duration')}>
                  <span className="inline-flex items-center gap-1">Duration <SortArrow col="duration" sortCol={sortCol} sortDir={sortDir} /></span>
                </TableHead>
                <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300">Error</TableHead>
                <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 w-24 text-center">Actions</TableHead>
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
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm" className="h-7 w-7 p-0 cursor-pointer hover:bg-[#DFE9FB] dark:hover:bg-indigo-900/30">
                              <MoreVertical className="size-4 text-gray-500 dark:text-gray-400" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="w-40">
                            <DropdownMenuItem onClick={() => onReportTest(test)} className="text-[12px] gap-2 cursor-pointer">
                              <Eye className="size-3.5" />
                              View Details
                            </DropdownMenuItem>
                            {test.status === 'failed' && (
                              <DropdownMenuItem onClick={() => onReportTest(test)} className="text-[12px] gap-2 cursor-pointer text-orange-600 dark:text-orange-400">
                                <MessageSquare className="size-3.5" />
                                Report Bug
                              </DropdownMenuItem>
                            )}
                            <DropdownMenuItem onClick={() => onReportTest(test)} className="text-[12px] gap-2 cursor-pointer">
                              <RotateCcw className="size-3.5" />
                              Re-run Test
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
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
                  <TableRow className="bg-[#DFE9FB] dark:bg-indigo-900/30 hover:bg-[#DFE9FB] dark:hover:bg-indigo-900/30">
                    <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 w-14">Test ID</TableHead>
                    <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300">Test Name</TableHead>
                    <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 text-center">{comparisonData.run1Label}</TableHead>
                    <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 text-center">{comparisonData.run2Label}</TableHead>
                    <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 text-center">Change</TableHead>
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
              <TableRow className="bg-[#DFE9FB] dark:bg-indigo-900/30 hover:bg-[#DFE9FB] dark:hover:bg-indigo-900/30">
                <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300">Date</TableHead>
                <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300">Duration</TableHead>
                <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 text-center">Passed</TableHead>
                <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 text-center">Failed</TableHead>
                <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 text-center">Rate</TableHead>
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
              <TableRow className="bg-[#DFE9FB] dark:bg-indigo-900/30 hover:bg-[#DFE9FB] dark:hover:bg-indigo-900/30">
                <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300">Bug ID</TableHead>
                <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300">Description</TableHead>
                <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 text-center">Status</TableHead>
                <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300">Related Tests</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {bugReportsList.map((bug) => (
                <TableRow key={bug.id} className="dark:border-gray-700">
                  <TableCell className="text-[13px] font-mono text-gray-600 dark:text-gray-400">{bug.id.slice(0, 8).toUpperCase()}</TableCell>
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
                  <TableCell className="text-[13px] text-gray-500 dark:text-gray-400">{bug.testId}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  )
}

// ─── NAV TOAST ───────────────────────────────────────────
function NavToast({ label, parent }: { label: string; parent?: string | null }) {
  const [visible, setVisible] = useState(true)
  const [fading, setFading] = useState(false)

  useEffect(() => {
    const fadeTimer = setTimeout(() => setFading(true), 1200)
    const hideTimer = setTimeout(() => setVisible(false), 1600)
    return () => { clearTimeout(fadeTimer); clearTimeout(hideTimer) }
  }, [])

  if (!visible) return null

  return (
    <div
      className={`pointer-events-none absolute top-3 left-1/2 z-50 transition-all duration-300 ease-out ${
        fading ? 'opacity-0' : 'opacity-100'
      }`}
      style={{ transform: `translateX(-50%) translateY(${fading ? '-4px' : '0px'})` }}
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

  // Keyboard shortcuts cheat sheet
  const [showShortcuts, setShowShortcuts] = useState(false)
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
      .catch(() => {
        // Backend not running — this is expected when FastAPI isn't available
      })
  }, [])

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

  // Load run history and bug reports on mount
  useEffect(() => {
    loadRunHistory()
    loadBugReports()
  }, [loadRunHistory, loadBugReports])

  // Compute module health from real run history
  const moduleHealth = useMemo(() => {
    // Build a mapping of sidebar module IDs to their parent group and display name
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

    // Group runs by moduleId
    const runsByModule = new Map<string, RunSnapshot[]>()
    for (const run of runHistory) {
      const existing = runsByModule.get(run.moduleId) || []
      existing.push(run)
      runsByModule.set(run.moduleId, existing)
    }

    // Build health data for all known modules
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
        // Use the latest run for stats
        const latestRun = runs[0] // already sorted desc by loadRunHistory
        const passedTests = latestRun.passed
        const failedTests = latestRun.failed
        const totalTests = latestRun.total
        const passRate = totalTests > 0 ? Math.round((passedTests / totalTests) * 100) : 0
        // Trend: last 7 run pass rates (oldest → newest)
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
        const durationStr = `${mins}:${String(secs).padStart(2, '0')}`
        setCompletionStats({
          passed,
          failed,
          duration: durationStr,
        })
        setCompletionModalOpen(true)

        // Save run to Prisma DB
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
        }).catch(() => {
          // Silently fail — run will still be tracked locally
        })
        currentRunIdRef.current = null
      }
    }
    prevIsRunningRef.current = isRunning
  }, [isRunning, tests, selectedModule, sidebarModules, loadRunHistory])

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
      if (next.has(id)) {
        // Toggle close: clicking an already-open section closes it
        next.delete(id)
      } else {
        // Accordion behavior: figure out which level this item is at
        // and close siblings at the same level, keeping parents open
        const isTopLevel = ALL_SIDEBAR_MODULES.some(m => m.id === id)
        if (isTopLevel) {
          // Top-level: close all other top-level sections
          ALL_SIDEBAR_MODULES.forEach(m => next.delete(m.id))
        } else {
          // Sub-level: find siblings and close them, keep parent open
          const findSiblings = (modules: SidebarModule[]): string[] => {
            for (const mod of modules) {
              if (mod.id === id) return [] // shouldn't happen for sub-items
              if (mod.children) {
                const childIds = mod.children.map(c => c.id)
                if (childIds.includes(id)) {
                  // Found the parent — return all sibling IDs (only those with children are expandable)
                  return mod.children.filter(c => c.children && c.children.length > 0).map(c => c.id)
                }
                // Check deeper
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
        tests: moduleData.tests.map((t) => ({
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
      const items: TestItem[] = moduleData.tests.map((t) => ({
        id: t.id,
        name: t.description,
        status: mapToTestItemStatus(t.status),
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
      if (t) return t.bugDetails || (t.status === 'bug' ? t.actual : undefined)
    }
    // Also check currentTestGroups for loaded module tests
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
          // Capture run ID from the first SSE event
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

  // Keyboard shortcuts: Ctrl+B sidebar, Ctrl+K quick switcher, Ctrl+D dark mode, Ctrl+R run tests, Ctrl+1-5 switch tabs, Ctrl+/ cheat sheet
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      // Don't fire shortcuts when typing in inputs/textareas
      const target = e.target as HTMLElement
      const isInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable

      // Escape — close any open panel/dialog
      if (e.key === 'Escape') {
        if (quickSwitcherOpen) {
          setQuickSwitcherOpen(false)
          return
        }
        if (showShortcuts) {
          setShowShortcuts(false)
          return
        }
        if (notifDropdownOpen) {
          setNotifDropdownOpen(false)
          return
        }
      }

      // All Ctrl/Cmd shortcuts below — skip if typing in input
      if (isInput) return
      if (!(e.ctrlKey || e.metaKey)) return

      // Ctrl+B — toggle sidebar
      if (e.key === 'b') {
        e.preventDefault()
        setSidebarOpen((prev) => !prev)
        return
      }

      // Ctrl+K — quick switcher
      if (e.key === 'k') {
        e.preventDefault()
        setQuickSwitcherOpen((prev) => !prev)
        setQuickSearch('')
        return
      }

      // Ctrl+D — toggle dark mode
      if (e.key === 'd') {
        e.preventDefault()
        toggleDarkMode()
        return
      }

      // Ctrl+/ — show shortcuts cheat sheet
      if (e.key === '/') {
        e.preventDefault()
        setShowShortcuts((prev) => !prev)
        return
      }

      // Ctrl+R — run all pending tests (only when on a module with pending tests)
      if (e.key === 'r' && selectedModule !== 'dashboard' && selectedModule !== 'my-tickets' && !isRunning) {
        e.preventDefault()
        const pendingCount = tests.filter((t) => t.status === 'pending').length
        if (pendingCount > 0) {
          runTests(false)
          setActiveTab('live-execution')
        }
        return
      }

      // Ctrl+1-5 — switch tabs (only when on a module page)
      if (selectedModule !== 'dashboard' && selectedModule !== 'my-tickets') {
        const tabMap: Record<string, string> = { '1': 'operations', '2': 'test-runner', '3': 'live-execution', '4': 'results', '5': 'schedule' }
        const tabId = tabMap[e.key]
        if (tabId) {
          e.preventDefault()
          setActiveTab(tabId)
          return
        }
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [quickSwitcherOpen, showShortcuts, notifDropdownOpen, selectedModule, isRunning, tests, toggleDarkMode, runTests])

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
      <div className="h-screen flex items-center justify-center bg-[#F1F2F7] dark:bg-gray-900">
        <div className="flex flex-col items-center gap-3">
          <Image src="/agdi-logo.png" alt="AgDi" width={80} height={36} className="object-contain animate-pulse" />
          <Loader2 className="size-5 text-[#3F51B5] animate-spin" />
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
              { keys: 'Ctrl + 5', desc: 'Schedule tab' },
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
            <Image src="/agdi-logo.png" alt="AgDi" width={70} height={28} className="object-contain" />
            <span className="text-[#888888] dark:text-gray-500 text-[13px]">Automation Runner</span>
          </div>
          {/* AgDi-style Search Bar */}
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
          {/* Feature 6: Dark mode toggle */}
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleDarkMode}
            data-tour="dark-mode"
            className="size-8 text-[#888888] dark:text-gray-400 hover:text-[#333333] dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer"
            title={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {darkMode ? <Sun className="size-4" /> : <Moon className="size-4" />}
          </Button>
          {/* Help / Tour Button */}
          <Button
            variant="ghost"
            size="icon"
            onClick={startAppTour}
            data-tour="help-btn"
            className="size-8 text-[#3F51B5] hover:text-[#2D3FC7] hover:bg-[#E8F5E9] dark:hover:bg-indigo-900/20 cursor-pointer"
            title="Take a tour of the app"
          >
            <HelpCircle className="size-4" />
          </Button>
          {/* Keyboard Shortcuts Button */}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setShowShortcuts(true)}
            data-tour="keyboard-shortcuts"
            className="size-8 text-[#888888] dark:text-gray-400 hover:text-[#333333] dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer"
            title="Keyboard shortcuts (Ctrl+/)"
          >
            <Zap className="size-4" />
          </Button>
          {/* Bell Notification */}
          <div className="relative" data-tour="notifications">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => {
                setNotifDropdownOpen((prev) => !prev)
                if (!notifDropdownOpen) handleMarkAllRead()
              }}
              className="size-8 text-[#888888] dark:text-gray-400 hover:text-[#333333] dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer relative"
              title="Notifications"
            >
              <Bell className="size-4" />
              {unreadCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-[#6777EF] text-white text-[9px] font-bold rounded-full flex items-center justify-center">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </Button>
            {notifDropdownOpen && (
              <div className="absolute right-0 top-10 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50">
                <div className="px-3 py-2 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
                  <span className="text-[13px] font-semibold text-[#333333] dark:text-gray-100">Notifications</span>
                  <button onClick={handleMarkAllRead} className="text-[11px] text-[#3F51B5] hover:text-[#2D3FC7] cursor-pointer">Mark all read</button>
                </div>
                <div className="max-h-64 overflow-y-auto">
                  {notifications.length === 0 ? (
                    <div className="p-6 text-center text-[12px] text-gray-400">No notifications yet</div>
                  ) : (
                    notifications.slice(0, 15).map((n) => (
                      <div key={n.id} className={`px-3 py-2 border-b border-gray-50 dark:border-gray-700/50 ${!n.read ? 'bg-[#E8F5E9]/50 dark:bg-green-900/10' : ''}`}>
                        <div className="text-[12px] font-medium text-[#333333] dark:text-gray-200">{n.title}</div>
                        <div className="text-[11px] text-[#666666] dark:text-gray-400 mt-0.5">{n.message}</div>
                        <div className="text-[10px] text-[#888888] mt-0.5">{new Date(n.createdAt).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}</div>
                      </div>
                    ))
                  )}
                </div>
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
            <Avatar className="size-7">
              <AvatarFallback className="bg-[#6777EF] text-white text-xs font-semibold">
                {userInitials}
              </AvatarFallback>
            </Avatar>
            <div className="hidden sm:flex flex-col">
              <span className="text-[12px] text-[#333333] dark:text-gray-200 font-medium max-w-[120px] truncate leading-tight">
                {user.name}
              </span>
              <span className="text-[10px] text-[#888888] dark:text-gray-500 leading-tight">
                {user.role}
              </span>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleLogout}
              data-tour="logout-btn"
              className="size-7 text-[#888888] hover:text-red-500 cursor-pointer"
              title="Sign out"
            >
              <LogOut className="size-3.5" />
            </Button>
          </div>
        </div>
      </header>

      {/* ─── BODY ───────────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">
        {/* ─── SIDEBAR ──────────────────────────────────── */}
        <div
          className="shrink-0 overflow-hidden h-full"
          style={{ width: sidebarOpen ? sidebarWidth : 0 }}
        >
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
            {/* Rural Landscape Illustration */}
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
          <div
            onMouseDown={handleResizeStart}
            className="w-1 cursor-col-resize bg-transparent hover:bg-[#3F51B5]/40 active:bg-[#3F51B5]/60 transition-colors shrink-0 relative z-10"
          />
        )}

        {/* ─── MAIN CONTENT ─────────────────────────────── */}
        <main className="flex-1 flex flex-col overflow-hidden bg-[#F1F2F7] dark:bg-gray-900 relative">
          {navToast && (
            <NavToast key={navToast.key} label={navToast.label} parent={navToast.parent} />
          )}
          {/* Breadcrumb (when sidebar collapsed + not on Dashboard) */}
          {!sidebarOpen && selectedModule !== 'dashboard' && (
            <div className="flex items-center gap-1.5 px-4 py-2 border-b border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-900 shrink-0">
              <button
                onClick={handleGoHome}
                className="text-[12px] text-[#3F51B5] hover:text-[#2D3FC7] dark:hover:text-indigo-400 font-medium cursor-pointer transition-colors hover:underline"
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
            <div data-tour="dashboard">
              <DashboardTab onSelectModule={handleSelectModule} moduleHealth={moduleHealth} />
            </div>
          )}

          {/* ── MY TICKETS VIEW ── */}
          {selectedModule === 'my-tickets' && user && (
            <div className='p-8 text-center text-gray-400 text-sm'>No tickets yet</div>
          )}

          {/* ── MODULE VIEW (module selected — tabs + content) ── */}
          {selectedModule !== 'dashboard' && selectedModule !== 'my-tickets' && (
              <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
              {/* Tab bar */}
              <div className="border-b border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/30 shrink-0" data-tour="tab-bar">
                <div className="flex items-center h-10 px-4 gap-0">
                  {tabs.map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`px-4 h-full text-[13px] font-medium transition-colors border-b-2 cursor-pointer ${
                        activeTab === tab.id
                          ? 'border-[#3F51B5] text-[#3F51B5] dark:text-indigo-400 bg-white dark:bg-gray-900'
                          : 'border-transparent text-[#888888] dark:text-gray-400 hover:text-[#333333] dark:hover:text-gray-200 hover:bg-gray-100/50 dark:hover:bg-gray-800/30'
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
                  <div data-tour="operations">
                  <OperationsTab
                    testGroups={currentTestGroups}
                    testCasesModule={
                      allTestCases[selectedModule?.toLowerCase().replace(' ', '_').replace('-', '_')]
                    }
                  />
                  </div>
                )}
            {activeTab === 'test-runner' && (
              <div data-tour="test-runner">
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
              </div>
            )}
            {activeTab === 'live-execution' && (
              <div data-tour="live-execution">
              <LiveExecutionTab
                tests={tests}
                testGroups={currentTestGroups}
                isRunning={isRunning}
                runningProgress={runningProgress}
                onStop={async () => {
                  const runId = currentRunIdRef.current
                  if (runId) {
                    try {
                      await stopRun(runId)
                      toast.success('Run stopped')
                    } catch (err) {
                      toast.error('Failed to stop run', { description: err instanceof Error ? err.message : 'Unknown error' })
                    }
                  }
                  setIsRunning(false)
                }}
                onBack={() => setActiveTab('test-runner')}
                onRerunFailed={() => {
                  const failedIds = tests.filter((t) => t.status === 'failed').map((t) => t.id)
                  if (failedIds.length > 0) {
                    rerunTestIds(failedIds)
                    runTests(true, failedIds)
                  }
                }}
              />
              </div>
            )}
            {activeTab === 'results' && (
              <div data-tour="results">
              <ResultsTab
                tests={tests}
                passedCount={passedCount}
                failedCount={failedCount}
                totalCount={tests.length}
                runHistory={runHistory}
                onReportTest={handleReportTest}
                bugReportsList={bugReportsList}
              />
              </div>
            )}
            {activeTab === 'schedule' && user && (
              <div data-tour="schedule-runs">
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
          className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 bg-[#3F51B5] hover:bg-[#2D3FC7] text-white transition-all duration-200 rounded-xl px-5 py-2.5 flex items-center gap-2 cursor-pointer hover:-translate-y-0.5"
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
                            ? 'bg-[#E8F5E9] dark:bg-[#1B4332]/20 text-[#1B4332] dark:text-green-400'
                            : 'text-[#333333] dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700/50'
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
                        {isActive && <CheckCircle2 className="size-3.5 text-[#3F51B5] shrink-0" />}
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

      {/* ─── FOOTER (ERP-style) ───────────────────────────── */}
      <footer className="shrink-0 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-4 py-1.5 flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-[10px] text-gray-400 dark:text-gray-500">
          <Copyright className="size-3" />
          <span>2026 AgDi Solutions Pvt. Ltd. All rights reserved.</span>
        </div>
        <div className="flex items-center gap-3 text-[10px] text-gray-400 dark:text-gray-500">
          <span className="flex items-center gap-1">
            Version 1.0.0
          </span>
          <a
            href="https://rhythmerp.algorhythms.in"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 hover:text-[#3F51B5] dark:hover:text-indigo-400 transition-colors cursor-pointer"
          >
            <HelpCircle className="size-3" />
            Help
            <ExternalLink className="size-2.5" />
          </a>
        </div>
      </footer>
    </div>
  )
}
