import { sidebarToFolderMapping, type ApiModule, type ApiSubModule } from '@/lib/api'
import { type TestClassGroup, type TestItem, testSpecGroups } from '@/data/testSpecGroups'

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
    testType: (t.type === 'api' ? 'api' : 'ui') as 'ui' | 'api',
  }))

  return { groups, items }
}
