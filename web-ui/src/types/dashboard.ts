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
  priority?: 'smoke' | 'regression' | 'sanity'
}

export interface TestSpecItem {
  id: string
  description: string
  status: 'passed' | 'failed' | 'not-run'
  duration: string
  steps: string
  expected: string
  error?: string
  priority?: 'smoke' | 'regression' | 'sanity'
}

export interface TestClassGroup {
  className: string
  tests: TestSpecItem[]
}

export interface RunSnapshot {
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

export interface ModuleHealth {
  moduleId: string
  moduleName: string
  parentGroup?: string
  passRate: number
  totalTests: number
  passedTests: number
  failedTests: number
  lastRun: string
}
