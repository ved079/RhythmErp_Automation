/**
 * Module data and sidebar builder utilities for RhythmERP Automation Runner.
 * Contains the master sidebar module list, test spec data, and functions
 * to build/filter sidebar modules based on API data and user access.
 */

import { type ApiModule, type ApiSubModule, folderToSidebarId, sidebarToFolderMapping } from '@/lib/api'
import { type SidebarModule, type TestClassGroup, type TestItem, type TestSpecItem } from '@/lib/types'

// ─── Full sidebar module tree ────────────────────────────
// This is the master list of ALL sidebar modules (with or without tests).
// API data enriches these with real test counts.

export const ALL_SIDEBAR_MODULES: SidebarModule[] = [
  { id: 'dashboard', label: 'Dashboard' },
  {
    id: 'registration',
    label: 'Registration',
    defaultExpanded: true,
    children: [
      { id: 'farmer', label: 'Farmer', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'employee', label: 'Employee', badge: '📝 No tests', badgeType: 'none' as const },
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
  {
    id: 'document',
    label: 'Document',
    defaultExpanded: true,
    children: [
      { id: 'directors', label: 'Directors', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'member', label: 'Member', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'constituent-documents', label: 'Constituent Documents', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'miscellaneous-documents', label: 'Miscellaneous Documents', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'register-of-loan', label: 'Register of Loan', badge: '📝 No tests', badgeType: 'none' as const },
      { id: 'register-charges', label: 'Register Charges', badge: '📝 No tests', badgeType: 'none' as const },
    ],
  },
  {
    id: 'private-b2b',
    label: 'Private (B2B)',
    defaultExpanded: true,
    children: [
      {
        id: 'purchase-group',
        label: 'Purchase',
        defaultExpanded: true,
        children: [
          { id: 'purchase-order', label: 'Purchase Order', badge: '📝 No tests', badgeType: 'none' as const },
          { id: 'goods-receipt-note', label: 'Goods Receipt Note', badge: '📝 No tests', badgeType: 'none' as const },
          { id: 'gate-pass', label: 'Gate Pass', badge: '📝 No tests', badgeType: 'none' as const },
          { id: 'quality-check', label: 'Quality Check', badge: '📝 No tests', badgeType: 'none' as const },
        ],
      },
    ],
  },
  { id: 'my-tickets', label: 'My Tickets' },
]

// ─── Test spec data (static fallback for tax-rate module) ──

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

// ─── Sidebar builder functions ───────────────────────────

/**
 * Build sidebar by merging real API test counts into the full module list.
 * Modules without tests keep the "📝 No tests" badge.
 */
export function buildSidebarModules(apiModules: ApiModule[]): SidebarModule[] {
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

/**
 * Filter sidebar modules based on user's role and moduleAccess.
 * - admin/qa_lead: full access (all modules)
 * - Others: only modules listed in moduleAccess (or 'all' for legacy)
 * - 'dashboard' and 'my-tickets' are always visible
 */
export function filterSidebarByAccess(modules: SidebarModule[], user: { role: string; moduleAccess?: string[] }): SidebarModule[] {
  // Admin and QA Lead get full access
  if (user.role === 'admin' || user.role === 'qa_lead') return modules

  const access = user.moduleAccess || []
  // Legacy support: ['all'] means full access
  if (access.includes('all')) return modules

  // Always-visible module IDs
  const alwaysVisible = new Set(['dashboard', 'my-tickets'])

  function filterItems(items: SidebarModule[]): SidebarModule[] {
    return items
      .filter(item => {
        if (alwaysVisible.has(item.id)) return true
        // Check if this module ID or any of its children are in the access list
        if (access.includes(item.id)) return true
        if (item.children) {
          const visibleChildren = item.children.filter(c =>
            alwaysVisible.has(c.id) || access.includes(c.id) || (c.children && c.children.some(gc => access.includes(gc.id)))
          )
          if (visibleChildren.length > 0) return true
        }
        return false
      })
      .map(item => {
        if (!item.children) return item
        // Filter children recursively
        const filteredChildren = filterItems(item.children)
        return { ...item, children: filteredChildren.length > 0 ? filteredChildren : undefined }
      })
  }

  return filterItems(modules)
}

/**
 * Given a sidebar module ID (e.g. "seasons") and the API modules data,
 * return { groups: TestClassGroup[], items: TestItem[] } from real test functions.
 * Returns empty arrays for modules without API tests.
 */
export function getTestsForSidebarModule(
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

/**
 * Map test case status string to TestSpecItem status.
 */
export function mapTestCaseStatus(s: string): TestSpecItem['status'] {
  const upper = s.toUpperCase().trim()
  if (upper === 'PASSED' || upper === 'PASS') return 'passed'
  if (upper === 'BUG') return 'bug'
  if (upper === 'TODO') return 'todo'
  if (upper === 'FAILED' || upper === 'FAIL') return 'failed'
  return 'not-run'
}

/**
 * Map test case status string to TestItem status.
 */
export function mapToTestItemStatus(s: string): 'passed' | 'failed' | 'pending' {
  const upper = s.toUpperCase().trim()
  if (upper === 'PASSED' || upper === 'PASS') return 'passed'
  if (upper === 'BUG' || upper === 'FAILED' || upper === 'FAIL') return 'failed'
  return 'pending'
}
