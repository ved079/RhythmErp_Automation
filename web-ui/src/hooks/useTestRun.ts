'use client'

import { useState, useCallback, useRef, useEffect } from 'react'
import { toast } from 'sonner'
import { initialTests, testSpecGroups, type TestItem, type TestSpecItem, type TestClassGroup, type TestPriority } from '@/data/testSpecGroups'
import type { ApiModule, TestCasesData, RunCompletionSummary } from '@/lib/api'
import { startRun, stopRun, saveRunResults } from '@/lib/api'
import { getCachedSidebarToFolderMapping } from '@/lib/module-data'
import type { ScreenshotEntry } from '@/components/screenshot/ScreenshotGallery'
import { getTestsForSidebarModule } from '@/lib/test-helpers'
import type { VisibilityData } from '@/lib/test-helpers'
import { withCsrf } from '@/lib/csrf-client'
import { addNotification } from '@/lib/bug-reports'
import type { AuthUser, RunSnapshot } from '@/lib/types'
import type { SidebarModule } from '@/components/sidebar/SidebarModuleItem'

interface UseTestRunParams {
  user: AuthUser | null
  selectedModule: string
  apiModules: ApiModule[]
  allTestCases: TestCasesData
  visibilityData: VisibilityData | null
  loadRunHistory: () => Promise<void>
  loadDashboardStats: () => Promise<void>
  sidebarModules: SidebarModule[]
  loadBugReports: () => Promise<void>
  erpToken: string
  erpTenantId: string
  erpEmail?: string
  erpPassword?: string
}

export function useTestRun(params: UseTestRunParams) {
  const { user, selectedModule, apiModules, allTestCases, visibilityData, loadRunHistory, loadDashboardStats, sidebarModules, loadBugReports, erpToken, erpTenantId, erpEmail, erpPassword } = params

  const [tests, setTests] = useState<TestItem[]>(initialTests)
  const [currentTestGroups, setCurrentTestGroups] = useState<TestClassGroup[]>(testSpecGroups)
  const [testChecks, setTestChecks] = useState<Set<string>>(new Set())
  const [isRunning, setIsRunning] = useState(false)
  const [runningProgress, setRunningProgress] = useState('')
  const [consoleLogs, setConsoleLogs] = useState<string[]>(['> Waiting for tests to start...', '> Select tests in Test Runner and click Run.'])
  const [screenshotEntries, setScreenshotEntries] = useState<ScreenshotEntry[]>([])
  const currentRunIdRef = useRef<string | null>(null)
  const prevIsRunningRef = useRef(false)
  const [completionStats, setCompletionStats] = useState({ passed: 0, failed: 0, duration: '', failedTests: [] as { testId: string; message: string }[], moduleName: '', subModuleName: '' })
  const [completionModalOpen, setCompletionModalOpen] = useState(false)
  const [autoReportedTestIds, setAutoReportedTestIds] = useState<Set<string>>(new Set())

  // Fallback: save run results via the API route when isRunning transitions out
  useEffect(() => {
    if (prevIsRunningRef.current && !isRunning) {
      const passed = tests.filter((t) => t.status === 'passed').length
      const failed = tests.filter((t) => t.status === 'failed').length
      const total = passed + failed
      if (total > 0) {
        currentRunIdRef.current = null
      }
    }
    prevIsRunningRef.current = isRunning
  }, [isRunning, tests])

  const rerunTestIds = useCallback((ids: string[]) => {
    setTests((prev) => prev.map((t) => (ids.includes(t.id) ? { ...t, status: 'pending' as const, duration: '' } : t)))
    setTestChecks(new Set(ids))
  }, [])

  const getTestError = useCallback((id: string): string | undefined => {
    for (const g of testSpecGroups) { const t = g.tests.find((x) => x.id === id); if (t) return t.bugDetails || (t.status === 'bug' ? t.actual : undefined) }
    for (const g of currentTestGroups) { const t = g.tests.find((x) => x.id === id); if (t) return t.bugDetails || (t.status === 'bug' ? t.actual : undefined) }
    return undefined
  }, [currentTestGroups])

  const runTests = useCallback(
    (selectedOnly: boolean, forceIds?: string[], testType?: 'ui' | 'api') => {
      if (isRunning) return
      let testsToRun: TestItem[]
      if (forceIds) testsToRun = tests.filter((t) => forceIds.includes(t.id))
      else if (selectedOnly) testsToRun = tests.filter((t) => testChecks.has(t.id))
      else testsToRun = tests.filter((t) => t.status === 'pending' || t.status === 'failed')
      if (testType) testsToRun = testsToRun.filter((t) => (testType === 'ui' ? (!t.testType || t.testType === 'ui') : t.testType === 'api'))
      if (testsToRun.length === 0) { toast.info('No tests to run'); return }
      const mapping = getCachedSidebarToFolderMapping(selectedModule)
      if (!mapping) { toast.error('Cannot determine module path for: ' + selectedModule); return }
      setTests((prev) => prev.map((t) => testsToRun.some((r) => r.id === t.id) ? { ...t, status: (t.id === testsToRun[0].id ? 'running' as const : 'pending' as const), duration: '' } : t))
      setIsRunning(true); setRunningProgress('Starting tests...'); setConsoleLogs([])
      const testNames = testsToRun.map((t) => t.id)
      const runOnlyTests = selectedOnly || forceIds || testType ? testNames : null
      startRun(mapping.module, mapping.subModule, runOnlyTests,
        (event) => {
          if (!currentRunIdRef.current && (event as Record<string, unknown>).run_id) currentRunIdRef.current = (event as Record<string, unknown>).run_id as string
          if (event.type === 'log') { setRunningProgress(event.message); setConsoleLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${event.message}`]) }
          else if (event.type === 'test_end') {
            const statusLabel = event.status === 'passed' ? 'PASSED' : event.status === 'failed' ? 'FAILED' : 'SKIPPED'
            setConsoleLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${event.test_name} — ${statusLabel}${event.message ? ': ' + event.message : ''}`])
            if (event.test_name && event.status) {
              const testId = testsToRun.find((t) => t.id.endsWith('::' + event.test_name))?.id || testsToRun.find((t) => t.id.includes(event.test_name || ''))?.id
              if (testId) {
                setTests((prev) => prev.map((t) => t.id === testId ? { ...t, status: event.status === 'passed' ? ('passed' as const) : event.status === 'failed' ? ('failed' as const) : ('pending' as const), duration: event.duration ? `${(event.duration / 1000).toFixed(1)}s` : '--' } : t))
                if (event.status === 'failed') {
                  toast.error(`Failed: ${event.test_name}`, { description: event.message || '', duration: 8000 })
                  const moduleName = (() => {
                    for (const mod of sidebarModules) {
                      if (mod.id === selectedModule) return mod.label
                      if (mod.children) { const child = mod.children.find(c => c.id === selectedModule); if (child) return child.label }
                    }
                    return selectedModule
                  })()
                  fetch('/api/bugs', withCsrf({
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                      testId,
                      testDescription: event.test_name,
                      moduleName,
                      error: event.message || 'Test failed during automated run',
                      userNote: 'Auto-reported from failed test run',
                      priority: 'medium',
                      reporterName: user?.name || 'System',
                      reporterEmail: user?.email || '',
                      userId: user?.id,
                    }),
                  })).then(async (res) => {
                    if (res.ok) {
                      const data = await res.json()
                      if (data.skipped) {
                        setAutoReportedTestIds((prev) => { const next = new Set(prev); next.add(testId); return next })
                      } else {
                        setAutoReportedTestIds((prev) => { const next = new Set(prev); next.add(testId); return next })
                        toast.info(`Bug auto-reported for: ${event.test_name}`, { duration: 4000 })
                      }
                      loadBugReports()
                    }
                  }).catch(() => {})
                }
              }
            }
          } else if (event.type === 'run_end') { setRunningProgress('Run complete!'); setConsoleLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] Run complete!`]) }
          else if (event.type === 'error') { toast.error('Run error', { description: event.message, duration: 8000 }); setConsoleLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ERROR: ${event.message}`]) }
        },
        (summary: RunCompletionSummary) => {
          setIsRunning(false); setRunningProgress(''); toast.success('Test run finished!')
          const svTotal = summary.total
          if (svTotal > 0) {
            const { subModuleName, moduleName } = (() => {
              for (const mod of sidebarModules) {
                if (mod.id === selectedModule) return { subModuleName: '', moduleName: mod.label }
                if (mod.children) { const child = mod.children.find(c => c.id === selectedModule); if (child) return { subModuleName: mod.label, moduleName: child.label } }
              }
              return { subModuleName: '', moduleName: selectedModule }
            })()
            const start = new Date(summary.startedAt).getTime()
            const end = summary.completedAt ? new Date(summary.completedAt).getTime() : Date.now()
            const svSecs = Math.round((end - start) / 1000)
            const svDuration = `${Math.floor(svSecs / 60)}:${String(svSecs % 60).padStart(2, '0')}`
            const ft = summary.results.filter(r => r.status === 'failed' && r.message).map(r => ({ testId: r.testId, message: r.message || '' }))
            setCompletionStats({ passed: summary.passed, failed: summary.failed, duration: svDuration, failedTests: ft, moduleName, subModuleName })
            setCompletionModalOpen(true)
          }
          if (summary.total > 0) {
            saveRunResults(summary, user?.id).then((saved) => { if (saved) { loadRunHistory(); loadDashboardStats(); addNotification({ type: 'run_complete', title: `Run complete: ${summary.passed}/${summary.total} passed`, message: `${summary.module}${summary.subModule ? ' → ' + summary.subModule : ''} — ${summary.failed} failed, ${summary.passed} passed` }).catch(() => {}) } })
          }
        },
        (err) => { setIsRunning(false); setRunningProgress(''); toast.error('Connection failed', { description: err.message, duration: 8000 }) },
        erpToken || undefined,
        erpTenantId || undefined,
        erpEmail || undefined,
        erpPassword || undefined,
      )
    },
    [isRunning, tests, testChecks, selectedModule, user, loadRunHistory, loadDashboardStats, sidebarModules, loadBugReports, erpToken, erpTenantId, erpEmail, erpPassword]
  )

  const runByPriority = useCallback((priority: TestPriority) => {
    if (isRunning) return
    const priorityIds = tests.filter((t) => t.priority === priority).map((t) => t.id)
    if (priorityIds.length === 0) return
    rerunTestIds(priorityIds); runTests(true, priorityIds)
  }, [isRunning, tests, rerunTestIds, runTests])

  const handleStopRun = useCallback(async () => {
    const runId = currentRunIdRef.current
    if (runId) {
      try { await stopRun(runId); toast.success('Run stopped') }
      catch (err) { toast.error('Failed to stop run', { description: err instanceof Error ? err.message : 'Unknown error' }) }
    }
    setIsRunning(false)
  }, [])

  return {
    tests, setTests,
    currentTestGroups, setCurrentTestGroups,
    testChecks, setTestChecks,
    isRunning, setIsRunning,
    runningProgress, setRunningProgress,
    consoleLogs, setConsoleLogs,
    screenshotEntries, setScreenshotEntries,
    currentRunIdRef,
    completionStats, setCompletionStats,
    completionModalOpen, setCompletionModalOpen,
    autoReportedTestIds, setAutoReportedTestIds,
    runTests,
    runByPriority,
    rerunTestIds,
    getTestError,
    handleStopRun,
  }
}
