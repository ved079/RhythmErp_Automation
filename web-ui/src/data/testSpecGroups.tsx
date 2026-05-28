import React from 'react'
import { Flame, Activity, ShieldCheck } from 'lucide-react'

// ─── Types ───────────────────────────────────────────────
export type TestPriority = 'smoke' | 'regression' | 'sanity'

export interface TestItem {
  id: string
  name: string
  status: 'passed' | 'failed' | 'pending' | 'running'
  duration: string
  priority?: TestPriority
}

export interface TestSpecItem {
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

export interface TestClassGroup {
  className: string
  tests: TestSpecItem[]
}

// ─── Helper: get priority ────────────────────────────────
export function getPriority(id: string): TestPriority {
  if (['T01', 'T02', 'T10'].includes(id)) return 'smoke'
  if (['T03', 'T04', 'T05', 'T06', 'T09', 'T11'].includes(id)) return 'regression'
  return 'sanity'
}

// ─── Test Spec Groups ────────────────────────────────────
export const testSpecGroups: TestClassGroup[] = [
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

export const initialTests: TestItem[] = testSpecGroups.flatMap((g) =>
  g.tests.map((t) => ({
    id: t.id,
    name: t.description,
    status: (t.status === 'not-run' || t.status === 'todo' ? 'pending' : t.status === 'bug' ? 'failed' : t.status) as 'passed' | 'failed' | 'pending',
    duration: t.duration === '—' ? '—' : t.duration,
    priority: t.priority,
  }))
)

// ─── Priority Config ────────────────────────────────────
export const priorityConfig = {
  smoke: { icon: <Flame className="size-3" />, label: '🔥 Smoke', color: 'text-[#E65100] bg-[#FFF3E0] dark:text-orange-300 dark:bg-orange-900/40', dot: 'bg-[#FF9800]' },
  regression: { icon: <Activity className="size-3" />, label: '🔄 Regression', color: 'text-[#3F51B5] bg-[#DFE9FB] dark:text-indigo-300 dark:bg-indigo-900/40', dot: 'bg-[#3F51B5]' },
  sanity: { icon: <ShieldCheck className="size-3" />, label: '🛡️ Sanity', color: 'text-[#2E7D32] bg-[#E8F5E9] dark:text-green-300 dark:bg-green-900/40', dot: 'bg-[#4CAF50]' },
} as const
