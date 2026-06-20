import { type ApiModule, type ApiSubModule } from '@/lib/api'
import { getCachedSidebarToFolderMapping } from '@/lib/module-data'
import { type TestClassGroup, type TestItem, testSpecGroups } from '@/data/testSpecGroups'

export interface VisibilityData {
  excludedTestNames: string[]
  overrides: Record<string, { displayName?: string; disabled: boolean }>
}

/**
 * Get the step-by-step instructions for a test by its ID.
 * Looks up steps from testSpecGroups and splits on " → ".
 */
export function getStepsForTest(testId: string): string[] {
  for (const g of testSpecGroups) {
    const t = g.tests.find((x) => x.id === testId)
    if (t) return t.steps.split(' → ').map((s) => s.trim())
  }
  return []
}

/**
 * Given a sidebar module ID (e.g. "seasons") and the API modules data,
 * return { groups: TestClassGroup[], items: TestItem[] } from real test functions.
 * Returns empty arrays for modules without API tests.
 * Optionally filters by visibility data (hidden tests + overrides).
 */
export function getTestsForSidebarModule(
  sidebarId: string,
  apiModules: ApiModule[],
  visibility?: VisibilityData | null
): { groups: TestClassGroup[]; items: TestItem[] } {
  const empty = { groups: [] as TestClassGroup[], items: [] as TestItem[] }
  const mapping = getCachedSidebarToFolderMapping(sidebarId)
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
  let apiTests = [...new Map(allApiTests.map(t => [t.name, t])).values()]
  if (apiTests.length === 0) return empty

  // Apply visibility filtering (hide disabled tests + user-excluded tests)
  if (visibility) {
    const excludedSet = new Set(visibility.excludedTestNames || [])
    apiTests = apiTests.filter(t => {
      const ov = visibility.overrides?.[t.name]
      if (ov?.disabled) return false
      if (excludedSet.has(t.name)) return false
      return true
    })
  }

  // Apply display name overrides
  const getDisplayName = (t: ApiSubModule['tests'][0]): string => {
    if (visibility?.overrides?.[t.name]?.displayName) {
      return visibility.overrides[t.name].displayName!
    }
    return t.display_name || t.name.split('::').pop() || t.name
  }

  // Group all tests under one group (API names don't include file paths)
  const groups: TestClassGroup[] = [{
    className: 'All Tests',
    tests: apiTests.map((t) => ({
      id: t.name,
      description: getDisplayName(t),
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
    name: getDisplayName(t),
    description: getDisplayName(t),
    status: 'pending' as const,
    duration: '',
    testType: (t.type === 'api' ? 'api' : 'ui') as 'ui' | 'api',
  }))

  return { groups, items }
}
