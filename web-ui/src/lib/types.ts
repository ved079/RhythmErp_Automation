// ─── Shared Type Definitions ─────────────────────────────

export type TestPriority = 'smoke' | 'regression' | 'sanity'

export interface SidebarModule {
  id: string
  label: string
  badge?: string
  badgeType?: 'success' | 'warning' | 'wip' | 'none'
  children?: SidebarModule[]
  defaultExpanded?: boolean
}

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

export interface AuthUser {
  id: string
  email: string
  name: string
  role: string
}

export interface RunSnapshot {
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

export interface ModuleHealth {
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
