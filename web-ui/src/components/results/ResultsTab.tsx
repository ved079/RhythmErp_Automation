'use client'

import React, { useState, useMemo, useCallback, useEffect, useRef } from 'react'
import {
  GitCompare, TrendingUp, TrendingDown, Minus, BookmarkCheck,
  ArrowUp, ArrowDown, Flag, RefreshCw, X, CheckCircle2, XCircle,
  RotateCcw, Circle, ChevronDown, ChevronRight,
} from 'lucide-react'
import { ScrollArea } from '@/components/ui/scroll-area'
import type { TestClassGroup, TestItem } from '@/data/testSpecGroups'
import type { RunSnapshot, ModuleHealth } from '@/lib/types'
import { ExportMenu } from '@/components/export/ExportUtils'
import { ErrorDetailDialog } from '@/components/dialogs/ErrorDetailDialog'

/* ── Sparkline ── */
function Sparkline({ data, className }: { data: number[]; className?: string }) {
  if (!data || data.length < 2) return null
  const w = 52, h = 20, pad = 2
  const min = Math.min(...data), max = Math.max(...data)
  const range = max - min || 1
  const pts = data.map((v, i) => `${pad + (i / (data.length - 1)) * (w - 2 * pad)},${h - pad - ((v - min) / range) * (h - 2 * pad)}`).join(' ')
  return (
    <svg width={w} height={h} className={className} viewBox={`0 0 ${w} ${h}`}>
      <polyline fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" points={pts} />
    </svg>
  )
}

/* ── Trend icon ── */
function TrendIcon({ current, previous }: { current: number; previous?: number }) {
  if (previous === undefined) return <Minus className="size-3 text-gray-400" />
  if (current > previous) return <TrendingUp className="size-3 text-green-500" />
  if (current < previous) return <TrendingDown className="size-3 text-red-500" />
  return <Minus className="size-3 text-gray-400" />
}

/* ── Status badge ── */
const STATUS_STYLES = {
  passed:  { badge: 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400', dot: 'bg-emerald-500', label: 'Passed' },
  failed:  { badge: 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400', dot: 'bg-red-500', label: 'Failed' },
  running: { badge: 'bg-[#3F51B5]/15 dark:bg-[#3F51B5]/20 text-[#3F51B5] dark:text-[#7986CB]', dot: 'bg-[#3F51B5]', label: 'Running' },
  pending: { badge: 'bg-gray-100 dark:bg-gray-700 text-gray-400 dark:text-gray-500', dot: 'bg-gray-300 dark:bg-gray-600', label: 'Pending' },
}

function StatusBadge({ status, resolved }: { status: TestItem['status']; resolved?: boolean }) {
  if (resolved) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
        <span className="size-1.5 rounded-full bg-green-500" />
        Resolved
      </span>
    )
  }
  const s = STATUS_STYLES[status ?? 'pending']
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium ${s.badge}`}>
      {status === 'running'
        ? <RefreshCw className="size-2.5 animate-spin" />
        : <span className={`size-1.5 rounded-full ${s.dot}`} />}
      {s.label}
    </span>
  )
}

/* ── Test name formatter ── */
function formatTestName(test: TestItem): string {
  if (test.description) return test.description
  const id = (test.id.split('::').pop() || test.id).replace(/^test_/, '')
  const match = id.match(/^([A-Z]+)_([A-Z]+\d+)_(.+)$/)
  return match ? match[3].replace(/_/g, ' ').replace(/^\w/, c => c.toUpperCase()) : (test.name || id.replace(/_/g, ' '))
}

export function ResultsTab({
  tests,
  passedCount,
  failedCount,
  totalCount,
  runHistory,
  bugReportsList: _bugReportsList,
  onRunDetail,
  onCompareRuns,
  onViewAllRuns,
  onReportTest,
  testGroups,
  moduleHealth,
  moduleName,
  currentModuleId,
  onRerunFailed,
  isRunning,
}: {
  tests: TestItem[]
  passedCount: number
  failedCount: number
  totalCount: number
  runHistory: RunSnapshot[]
  bugReportsList: { id: string; testId: string; desc: string; status: string }[]
  onRunDetail?: (run: RunSnapshot) => void
  onCompareRuns?: () => void
  onViewAllRuns?: () => void
  onReportTest?: (testId: string, testName: string, error: string) => void
  testGroups?: TestClassGroup[]
  moduleHealth?: ModuleHealth[]
  moduleName?: string
  currentModuleId?: string
  onRerunFailed?: () => void
  isRunning?: boolean
}) {
  /* ── Module-scoped data ── */
  const moduleRuns = useMemo(
    () => currentModuleId ? runHistory.filter(r => r.moduleId === currentModuleId) : runHistory,
    [runHistory, currentModuleId]
  )
  const moduleHealthData = useMemo(
    () => currentModuleId ? (moduleHealth || []).filter(m => m.moduleId === currentModuleId) : (moduleHealth || []),
    [moduleHealth, currentModuleId]
  )

  /* ── UI / API filter ── */
  const [testTypeFilter, setTestTypeFilter] = useState<'all' | 'ui' | 'api'>('all')

  const visibleTests = useMemo(
    () => testTypeFilter === 'all' ? tests : tests.filter(t => (t.testType ?? 'ui') === testTypeFilter),
    [tests, testTypeFilter]
  )

  const filteredPassedCount = visibleTests.filter(t => t.status === 'passed').length
  const filteredFailedCount = visibleTests.filter(t => t.status === 'failed').length
  const filteredTotalCount = visibleTests.length
  const passRate = filteredTotalCount > 0 ? Math.round((filteredPassedCount / filteredTotalCount) * 100) : 0
  const pendingCount = visibleTests.filter(t => t.status === 'pending').length

  const uiCount = tests.filter(t => (t.testType ?? 'ui') === 'ui').length
  const apiCount = tests.filter(t => t.testType === 'api').length

  /* ── Error history ── */
  const [errorOpen, setErrorOpen] = useState(true)
  const [resolvedOpen, setResolvedOpen] = useState(false)
  const errorHistoryRef = useRef<HTMLDivElement>(null)
  const [errorDetailOpen, setErrorDetailOpen] = useState(false)
  const [selectedError, setSelectedError] = useState<{ testId: string; message: string; date: string; runRate: number } | null>(null)

  const lastRun = moduleRuns[0]
  const prevRun = moduleRuns[1]

  const errorHistory = useMemo(() => {
    const map = new Map<string, { message: string; runId: string; date: string; runRate: number }>()
    for (const run of moduleRuns) {
      for (const r of run.results) {
        if (r.status === 'failed' && r.message && !map.has(r.testId)) {
          map.set(r.testId, { message: r.message, runId: run.id, date: run.date, runRate: run.rate })
        }
      }
    }
    return Array.from(map.entries())
      .map(([testId, info]) => ({ testId, ...info }))
      .sort((a, b) => b.date.localeCompare(a.date))
  }, [moduleRuns])

  // For each test that has ever failed, find its most recent result across all runs.
  // A test is "resolved" if the most recent run that tested it shows passed.
  const getLatestStatusForTest = useCallback((testId: string): string | null => {
    for (const run of moduleRuns) {
      const result = run.results.find(r => r.testId === testId)
      if (result) return result.status
    }
    return null
  }, [moduleRuns])

  const typeMatchesFilter = useCallback((testId: string) => {
    if (testTypeFilter === 'all') return true
    const test = tests.find(t => t.id === testId)
    const inferredType = test?.testType ?? (testId.includes('test_api') ? 'api' : 'ui')
    return inferredType === testTypeFilter
  }, [testTypeFilter, tests])

  const activeErrors = useMemo(
    () => errorHistory.filter(e => getLatestStatusForTest(e.testId) !== 'passed' && typeMatchesFilter(e.testId)),
    [errorHistory, getLatestStatusForTest, typeMatchesFilter]
  )
  const resolvedErrors = useMemo(
    () => errorHistory.filter(e => getLatestStatusForTest(e.testId) === 'passed' && typeMatchesFilter(e.testId)),
    [errorHistory, getLatestStatusForTest, typeMatchesFilter]
  )

  /* ── Rerun snapshot ── */
  type RerunSnapshot = { fromRunId: string; failedResults: { testId: string; message?: string }[] }
  const [rerunSnapshot, setRerunSnapshot] = useState<RerunSnapshot | null>(null)
  const [rerunComparison, setRerunComparison] = useState<{
    fixed: { testId: string; message?: string }[]
    stillFailing: { testId: string; message?: string }[]
    fromRun: RunSnapshot
    toRun: RunSnapshot
  } | null>(null)

  const handleRerunFailed = useCallback(() => {
    if (!lastRun || failedCount === 0 || isRunning) return
    setRerunSnapshot({ fromRunId: lastRun.id, failedResults: lastRun.results.filter(r => r.status === 'failed') })
    setRerunComparison(null)
    onRerunFailed?.()
  }, [lastRun, failedCount, isRunning, onRerunFailed])

  const prevRunHistoryLenRef = useRef(moduleRuns.length)
  useEffect(() => {
    if (!rerunSnapshot) return
    if (moduleRuns.length > prevRunHistoryLenRef.current) {
      const newRun = moduleRuns[0]
      const fromRun = moduleRuns.find(r => r.id === rerunSnapshot.fromRunId)
      if (newRun && fromRun && newRun.id !== rerunSnapshot.fromRunId) {
        const fixed = rerunSnapshot.failedResults.filter(f => newRun.results.find(r => r.testId === f.testId && r.status === 'passed'))
        const stillFailing = rerunSnapshot.failedResults.filter(f => !newRun.results.find(r => r.testId === f.testId && r.status === 'passed'))
        setRerunComparison({ fixed, stillFailing, fromRun, toRun: newRun })
        setRerunSnapshot(null)
      }
    }
    prevRunHistoryLenRef.current = moduleRuns.length
  }, [moduleRuns, rerunSnapshot])

  /* ── Baseline regression ── */
  const [savedBaselineId, setSavedBaselineId] = useState<string | null>(() =>
    currentModuleId ? localStorage.getItem(`baseline_${currentModuleId}`) : null
  )
  const baselineRun = savedBaselineId ? moduleRuns.find(r => r.id === savedBaselineId) : null
  const regressionSummary = useMemo(() => {
    if (!baselineRun || !lastRun) return null
    const allTestIds = new Set([...baselineRun.results.map(r => r.testId), ...lastRun.results.map(r => r.testId)])
    let regressed = 0, fixed = 0
    for (const testId of allTestIds) {
      const b = baselineRun.results.find(r => r.testId === testId)
      const l = lastRun.results.find(r => r.testId === testId)
      if (b?.status === 'passed' && l?.status === 'failed') regressed++
      if (b?.status === 'failed' && l?.status === 'passed') fixed++
    }
    return { regressed, fixed, deltaRate: lastRun.rate - baselineRun.rate }
  }, [baselineRun, lastRun])

  const handleClearBaseline = useCallback(() => {
    if (!currentModuleId) return
    localStorage.removeItem(`baseline_${currentModuleId}`)
    setSavedBaselineId(null)
  }, [currentModuleId])

  /* ── Progress bar color ── */
  const progressBg = failedCount > 0 && passRate === 100
    ? 'linear-gradient(90deg, #22c55e 0%, #ef4444 100%)'
    : passRate >= 90 ? '#22c55e' : passRate >= 75 ? '#eab308' : '#ef4444'

  return (
    <div className="flex flex-col h-full min-h-0">
      <ScrollArea className="flex-1 min-h-0">
        <div className="px-4 pt-3 pb-4 flex flex-col gap-3">

          {/* ══════════════════════════════════════════
              MAIN RESULTS PANEL
          ══════════════════════════════════════════ */}
          <div className="flex flex-col border border-gray-300 dark:border-gray-500/70 rounded-lg overflow-hidden shadow-sm">

            {/* Header */}
            <div className="flex items-center gap-3 px-4 py-2.5 bg-gradient-to-r from-[#3F51B5]/[0.07] to-[#3F51B5]/[0.03] dark:from-[#3F51B5]/20 dark:to-[#3F51B5]/10 border-b border-gray-300 dark:border-gray-500/70 shrink-0">
              <span className="text-[13px] font-semibold text-gray-700 dark:text-gray-200">Test Results</span>

              {/* UI / API toggle */}
              <div className="flex items-center gap-0.5 bg-white/60 dark:bg-gray-800/60 border border-gray-200 dark:border-gray-600/60 rounded-md p-0.5 ml-1">
                {(['all', 'ui', 'api'] as const).map(f => (
                  <button key={f} onClick={() => setTestTypeFilter(f)}
                    className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors cursor-pointer ${
                      testTypeFilter === f
                        ? 'bg-[#3F51B5] text-white shadow-sm'
                        : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
                    }`}
                  >
                    {f === 'all' ? `All (${totalCount})` : f === 'ui' ? `UI (${uiCount})` : `API (${apiCount})`}
                  </button>
                ))}
              </div>

              <div className="flex-1" />
              <div className="flex items-center gap-3">
                <span className="flex items-center gap-1 text-[12px] font-medium text-emerald-600 dark:text-emerald-400">
                  <CheckCircle2 className="size-3.5" />{filteredPassedCount}
                </span>
                <span className="flex items-center gap-1 text-[12px] font-medium text-red-500 dark:text-red-400">
                  <XCircle className="size-3.5" />{filteredFailedCount}
                </span>
                <span className="flex items-center gap-1 text-[12px] font-medium text-gray-400 dark:text-gray-500">
                  <Circle className="size-3.5" />{pendingCount}
                </span>
                {lastRun && (
                  <>
                    <div className="w-px h-3.5 bg-gray-200 dark:bg-gray-600" />
                    <div className="flex items-center gap-1.5">
                      <TrendIcon current={lastRun.rate} previous={prevRun?.rate} />
                      <span className="text-[12px] font-semibold" style={{ color: passRate >= 90 ? '#22c55e' : passRate >= 75 ? '#ca8a04' : '#ef4444' }}>
                        {passRate}%
                      </span>
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Progress bar */}
            {totalCount > 0 && (
              <div className="h-1 bg-gray-100 dark:bg-gray-800 shrink-0">
                <div className="h-full transition-all duration-500" style={{ width: `${passRate}%`, background: progressBg }} />
              </div>
            )}

            {/* Stat tiles + actions */}
            <div className="flex items-stretch divide-x divide-gray-100 dark:divide-gray-700/60">
              {/* Passed */}
              <div className="flex flex-col items-center justify-center px-6 py-4 flex-1 gap-0.5">
                <span className="text-[22px] font-bold text-emerald-600 dark:text-emerald-400 leading-none">{filteredPassedCount}</span>
                <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-400 mt-1">Passed</span>
              </div>
              {/* Failed */}
              <div className="flex flex-col items-center justify-center px-6 py-4 flex-1 gap-0.5">
                <span className={`text-[22px] font-bold leading-none ${filteredFailedCount > 0 ? 'text-red-500 dark:text-red-400' : 'text-gray-300 dark:text-gray-600'}`}>{filteredFailedCount}</span>
                <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-400 mt-1">Failed</span>
              </div>
              {/* Pending */}
              <div className="flex flex-col items-center justify-center px-6 py-4 flex-1 gap-0.5">
                <span className="text-[22px] font-bold text-gray-400 dark:text-gray-500 leading-none">{pendingCount}</span>
                <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-400 mt-1">Pending</span>
              </div>
              {/* Total */}
              <div className="flex flex-col items-center justify-center px-6 py-4 flex-1 gap-0.5">
                <span className="text-[22px] font-bold text-gray-700 dark:text-gray-200 leading-none">{filteredTotalCount}</span>
                <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-400 mt-1">Total</span>
              </div>
            </div>

            {/* Actions row */}
            <div className="flex items-center gap-2 px-3 py-2 border-t border-gray-100 dark:border-gray-700/60 bg-gray-50/60 dark:bg-gray-800/30 shrink-0">
              {filteredFailedCount > 0 && onRerunFailed && (
                <button disabled={isRunning} onClick={handleRerunFailed}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[12px] font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-40 transition-colors cursor-pointer border border-red-200 dark:border-red-800/50"
                >
                  <RotateCcw className="size-3" />
                  Rerun Failed ({filteredFailedCount})
                </button>
              )}
              <div className="flex-1" />
              {lastRun && (
                <button onClick={() => onRunDetail?.(lastRun)}
                  className="text-[11px] text-gray-400 hover:text-[#3F51B5] dark:hover:text-[#7986CB] transition-colors cursor-pointer"
                >
                  Last run: {lastRun.date} · {lastRun.duration}
                </button>
              )}
              {onCompareRuns && moduleRuns.length >= 2 && (
                <button onClick={onCompareRuns}
                  className="flex items-center gap-1 px-2.5 py-1.5 rounded-md text-[12px] text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors cursor-pointer"
                >
                  <GitCompare className="size-3.5" />
                  Compare
                </button>
              )}
              <ExportMenu testGroups={testGroups} runHistory={moduleRuns} moduleHealth={moduleHealthData} moduleName={moduleName} />
            </div>
          </div>

          {/* ── Rerun Comparison Panel ── */}
          {rerunComparison && (
            <div className="border border-[#3F51B5]/30 bg-white dark:bg-gray-800/80 rounded-lg overflow-hidden shadow-sm">
              <div className="flex items-center gap-2.5 px-4 py-3 border-b border-gray-100 dark:border-gray-700/60 bg-gradient-to-r from-[#3F51B5]/[0.06] to-transparent">
                <RefreshCw className="size-3.5 text-[#3F51B5] dark:text-[#7986CB] shrink-0" />
                <div className="flex-1 min-w-0">
                  <span className="text-[13px] font-semibold text-gray-800 dark:text-gray-100">Rerun Comparison</span>
                  <span className="ml-2 text-[12px] text-gray-500 dark:text-gray-400">
                    {rerunComparison.fixed.length > 0 && <span className="text-green-600 dark:text-green-400 font-medium">{rerunComparison.fixed.length} fixed</span>}
                    {rerunComparison.fixed.length > 0 && rerunComparison.stillFailing.length > 0 && <span className="mx-1 text-gray-300">·</span>}
                    {rerunComparison.stillFailing.length > 0 && <span className="text-red-500 dark:text-red-400 font-medium">{rerunComparison.stillFailing.length} still failing</span>}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-[11px] text-gray-400 dark:text-gray-500">
                  <span>{rerunComparison.fromRun.rate}%</span><span>→</span>
                  <span className={rerunComparison.toRun.rate >= rerunComparison.fromRun.rate ? 'text-green-600 dark:text-green-400 font-semibold' : 'text-red-500 dark:text-red-400 font-semibold'}>{rerunComparison.toRun.rate}%</span>
                </div>
                <button onClick={() => setRerunComparison(null)} className="size-6 flex items-center justify-center rounded text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer">
                  <X className="size-3.5" />
                </button>
              </div>
              <div className="grid grid-cols-2 divide-x divide-gray-100 dark:divide-gray-700/60">
                <div>
                  <div className="px-3 py-2 bg-green-50/60 dark:bg-green-950/20 border-b border-gray-100 dark:border-gray-700/60 flex items-center gap-1.5">
                    <CheckCircle2 className="size-3 text-green-600 dark:text-green-400" />
                    <span className="text-[11px] font-semibold text-green-700 dark:text-green-400 uppercase tracking-wide">Fixed in rerun</span>
                    <span className="ml-auto text-[11px] font-medium text-green-600 dark:text-green-400">{rerunComparison.fixed.length}</span>
                  </div>
                  <div className="divide-y divide-gray-50 dark:divide-gray-700/40">
                    {rerunComparison.fixed.length === 0
                      ? <div className="px-3 py-3 text-[12px] text-gray-400 italic">None</div>
                      : rerunComparison.fixed.map(f => (
                        <div key={f.testId} className="px-3 py-2.5">
                          <div className="flex items-center gap-1.5">
                            <span className="size-1.5 rounded-full bg-green-500 shrink-0" />
                            <span className="text-[12px] font-medium text-gray-800 dark:text-gray-100 truncate">{f.testId}</span>
                          </div>
                          {f.message && <div className="text-[11px] text-gray-400 font-mono mt-0.5 line-clamp-1 ml-3">{f.message}</div>}
                        </div>
                      ))}
                  </div>
                </div>
                <div>
                  <div className="px-3 py-2 bg-red-50/60 dark:bg-red-950/20 border-b border-gray-100 dark:border-gray-700/60 flex items-center gap-1.5">
                    <XCircle className="size-3 text-red-500 dark:text-red-400" />
                    <span className="text-[11px] font-semibold text-red-600 dark:text-red-400 uppercase tracking-wide">Still failing</span>
                    <span className="ml-auto text-[11px] font-medium text-red-500 dark:text-red-400">{rerunComparison.stillFailing.length}</span>
                  </div>
                  <div className="divide-y divide-gray-50 dark:divide-gray-700/40">
                    {rerunComparison.stillFailing.length === 0
                      ? <div className="px-3 py-3 text-[12px] text-gray-400 italic">All failures resolved 🎉</div>
                      : rerunComparison.stillFailing.map(f => (
                        <div key={f.testId} className="px-3 py-2.5 group">
                          <div className="flex items-center gap-1.5">
                            <span className="size-1.5 rounded-full bg-red-500 shrink-0" />
                            <span className="text-[12px] font-medium text-gray-800 dark:text-gray-100 truncate">{f.testId}</span>
                            <button onClick={() => onReportTest?.(f.testId, f.testId, f.message || '')}
                              className="ml-auto size-5 flex items-center justify-center rounded text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 cursor-pointer opacity-0 group-hover:opacity-100 transition-opacity"
                            >
                              <Flag className="size-3" />
                            </button>
                          </div>
                          {f.message && <div className="text-[11px] text-red-500 font-mono mt-0.5 line-clamp-1 ml-3">{f.message}</div>}
                        </div>
                      ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ── Regression Overview ── */}
          {regressionSummary && (
            <div className="border border-[#3F51B5]/30 bg-[#3F51B5]/[0.04] dark:bg-[#3F51B5]/10 rounded-lg px-4 py-3 flex items-center gap-4">
              <BookmarkCheck className="size-4 text-[#3F51B5] dark:text-[#7986CB] shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="text-[12px] text-gray-600 dark:text-gray-300">
                  <span className="font-medium">Baseline:</span> {baselineRun!.date} ({baselineRun!.rate}%)
                  <span className="mx-2 text-gray-400">→</span>
                  <span className="font-medium">Latest:</span> {lastRun!.date} ({lastRun!.rate}%)
                </div>
                <div className="flex items-center gap-3 mt-1">
                  {regressionSummary.regressed > 0 && (
                    <span className="text-[12px] text-red-600 dark:text-red-400 flex items-center gap-1">
                      <ArrowDown className="size-3" /> {regressionSummary.regressed} regression{regressionSummary.regressed !== 1 ? 's' : ''}
                    </span>
                  )}
                  {regressionSummary.fixed > 0 && (
                    <span className="text-[12px] text-green-600 dark:text-green-400 flex items-center gap-1">
                      <ArrowUp className="size-3" /> {regressionSummary.fixed} fix{regressionSummary.fixed !== 1 ? 'es' : ''}
                    </span>
                  )}
                  <span className={`text-[12px] flex items-center gap-0.5 ${regressionSummary.deltaRate >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                    {regressionSummary.deltaRate >= 0 ? <ArrowUp className="size-3" /> : <ArrowDown className="size-3" />}
                    {regressionSummary.deltaRate >= 0 ? '+' : ''}{regressionSummary.deltaRate}%
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-1.5 shrink-0">
                {onCompareRuns && (
                  <button onClick={onCompareRuns}
                    className="h-7 px-3 text-[11px] cursor-pointer border border-[#3F51B5]/40 text-[#3F51B5] dark:text-[#7986CB] hover:bg-[#3F51B5]/10 rounded-md transition-colors"
                  >
                    Full Report
                  </button>
                )}
                <button onClick={handleClearBaseline} className="text-[11px] text-gray-400 hover:text-red-500 transition-colors cursor-pointer" title="Clear baseline">✕</button>
              </div>
            </div>
          )}

          {/* ── Recent Runs ── */}
          {moduleRuns.length > 0 && (
            <div className="border border-gray-300 dark:border-gray-500/70 rounded-lg overflow-hidden shadow-sm">
              <div className="flex items-center gap-3 px-4 py-2.5 bg-gradient-to-r from-[#3F51B5]/[0.07] to-[#3F51B5]/[0.03] dark:from-[#3F51B5]/20 dark:to-[#3F51B5]/10 border-b border-gray-300 dark:border-gray-500/70">
                <span className="text-[13px] font-semibold text-gray-700 dark:text-gray-200 flex-1">Recent Runs</span>
                <button onClick={onViewAllRuns} className="text-[12px] text-[#3F51B5] hover:text-[#3949AB] dark:text-[#7986CB] transition-colors cursor-pointer font-medium">
                  View All ({moduleRuns.length})
                </button>
              </div>
              <div className="divide-y divide-gray-100 dark:divide-gray-700/50">
                {moduleRuns.slice(0, 5).map(run => (
                  <div key={run.id}
                    onClick={() => onRunDetail?.(run)}
                    className={`flex items-center gap-3 px-4 py-2.5 ${onRunDetail ? 'cursor-pointer hover:bg-[#3F51B5]/[0.04] dark:hover:bg-[#3F51B5]/10 transition-colors' : ''}`}
                  >
                    <div className="flex items-center gap-2.5 flex-1 min-w-0">
                      <span className={`size-2 rounded-full shrink-0 ${run.rate >= 90 ? 'bg-green-500' : run.rate >= 75 ? 'bg-yellow-500' : 'bg-red-500'}`} />
                      <span className="text-[13px] text-gray-700 dark:text-gray-200 truncate">{run.date}</span>
                    </div>
                    <span className="text-[12px] text-gray-400 font-mono w-16 text-right shrink-0">{run.duration}</span>
                    <span className="text-[12px] text-emerald-600 dark:text-emerald-400 font-medium w-10 text-right shrink-0">{run.passed}</span>
                    <span className={`text-[12px] font-medium w-10 text-right shrink-0 ${run.failed > 0 ? 'text-red-500 dark:text-red-400' : 'text-gray-400 dark:text-gray-500'}`}>{run.failed}</span>
                    <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full w-14 text-center shrink-0 ${
                      run.rate >= 90 ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                        : run.rate >= 75 ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
                        : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                    }`}>{run.rate}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Error History ── */}
          {errorHistory.length > 0 && (
            <div ref={errorHistoryRef} className="border border-gray-300 dark:border-gray-500/70 rounded-lg overflow-hidden shadow-sm">
              {/* Header */}
              <button onClick={() => {
                const opening = !errorOpen
                setErrorOpen(opening)
                if (opening) {
                  setTimeout(() => errorHistoryRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50)
                }
              }}
                className="w-full flex items-center gap-3 px-4 py-2.5 bg-gradient-to-r from-red-50/80 to-red-50/30 dark:from-red-950/20 dark:to-transparent hover:from-red-100/80 hover:to-red-50/50 dark:hover:from-red-950/30 transition-all cursor-pointer text-left border-b border-gray-300 dark:border-gray-500/70"
              >
                <span className="text-[13px] font-semibold text-gray-700 dark:text-gray-200 flex-1">Error History</span>
                <div className="flex items-center gap-1.5">
                  {activeErrors.length > 0 && (
                    <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-red-100/80 dark:bg-red-900/40 text-red-700 dark:text-red-400">{activeErrors.length} active</span>
                  )}
                  {resolvedErrors.length > 0 && (
                    <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-green-100/80 dark:bg-green-900/40 text-green-700 dark:text-green-400">{resolvedErrors.length} resolved</span>
                  )}
                </div>
                {errorOpen ? <ChevronDown className="size-3.5 text-gray-400" /> : <ChevronRight className="size-3.5 text-gray-400" />}
              </button>

              {errorOpen && (
                <>
                  {/* Active failures */}
                  <div className="divide-y divide-gray-100 dark:divide-gray-700/50">
                    {activeErrors.length === 0 ? (
                      <div className="flex items-center gap-2 px-4 py-3 text-[12px] text-green-600 dark:text-green-400">
                        <CheckCircle2 className="size-3.5 shrink-0" />
                        No active failures — all previously failing tests are now passing
                      </div>
                    ) : activeErrors.map(err => (
                      <div key={err.testId}
                        className="flex items-center gap-3 px-4 py-2.5 cursor-pointer hover:bg-red-50/40 dark:hover:bg-red-950/10 transition-colors group"
                        onClick={() => { setSelectedError({ testId: err.testId, message: err.message, date: err.date, runRate: err.runRate }); setErrorDetailOpen(true) }}
                      >
                        <div className="flex-1 min-w-0">
                          <span className="text-[13px] font-medium text-gray-800 dark:text-gray-100 truncate block">{err.testId}</span>
                          <span className="text-[11px] text-red-500 dark:text-red-400 font-mono line-clamp-1 mt-0.5 block">{err.message}</span>
                        </div>
                        <div className="w-20 shrink-0 flex justify-center">
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400">
                            <span className="size-1.5 rounded-full bg-red-500" />Active
                          </span>
                        </div>
                        <span className={`text-[11px] font-medium w-20 text-right shrink-0 ${err.runRate >= 90 ? 'text-green-600 dark:text-green-400' : err.runRate >= 75 ? 'text-yellow-600 dark:text-yellow-400' : 'text-red-500 dark:text-red-400'}`}>{err.runRate}%</span>
                        <button onClick={e => { e.stopPropagation(); onReportTest?.(err.testId, err.testId, err.message) }}
                          className="w-6 shrink-0 size-6 flex items-center justify-center rounded text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 cursor-pointer opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <Flag className="size-3" />
                        </button>
                      </div>
                    ))}
                  </div>

                  {/* Resolved sub-section */}
                  {resolvedErrors.length > 0 && (
                    <div className="border-t border-gray-200 dark:border-gray-700">
                      <button onClick={() => setResolvedOpen(!resolvedOpen)}
                        className="w-full flex items-center gap-2 px-4 py-2 hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors cursor-pointer text-left"
                      >
                        <CheckCircle2 className="size-3 text-green-500 shrink-0" />
                        <span className="text-[12px] font-medium text-gray-500 dark:text-gray-400 flex-1">Resolved in latest run</span>
                        <span className="text-[11px] text-green-600 dark:text-green-400 font-medium">{resolvedErrors.length}</span>
                        {resolvedOpen ? <ChevronDown className="size-3 text-gray-400" /> : <ChevronRight className="size-3 text-gray-400" />}
                      </button>
                      {resolvedOpen && (
                        <div className="divide-y divide-gray-50 dark:divide-gray-700/40">
                          {resolvedErrors.map(err => (
                            <div key={err.testId}
                              className="flex items-center gap-3 px-4 py-2.5 cursor-pointer hover:bg-green-50/30 dark:hover:bg-green-950/10 transition-colors opacity-70 hover:opacity-100"
                              onClick={() => { setSelectedError({ testId: err.testId, message: err.message, date: err.date, runRate: err.runRate }); setErrorDetailOpen(true) }}
                            >
                              <div className="flex-1 min-w-0">
                                <span className="text-[13px] font-medium text-gray-600 dark:text-gray-300 truncate block line-through decoration-gray-400/50">{err.testId}</span>
                                <span className="text-[11px] text-gray-400 font-mono line-clamp-1 mt-0.5 block">{err.message}</span>
                              </div>
                              <div className="w-20 shrink-0 flex justify-center">
                                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                                  <span className="size-1.5 rounded-full bg-green-500" />Resolved
                                </span>
                              </div>
                              <span className="text-[11px] text-gray-400 w-20 text-right shrink-0">{err.runRate}%</span>
                              <div className="w-6 shrink-0" />
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>
          )}

        </div>
      </ScrollArea>

      <ErrorDetailDialog
        open={errorDetailOpen}
        onClose={() => { setErrorDetailOpen(false); setSelectedError(null) }}
        error={selectedError}
        onReportTest={onReportTest}
      />
    </div>
  )
}
