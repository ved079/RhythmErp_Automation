'use client'

import React, { useState, useMemo, useCallback } from 'react'
import { GitCompare, Bug, TrendingUp, TrendingDown, Minus, ChevronDown, ChevronRight, BookmarkCheck, ArrowUp, ArrowDown, Flag } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'

import type { TestClassGroup, TestItem } from '@/data/testSpecGroups'
import type { RunSnapshot, ModuleHealth } from '@/lib/types'
import { ExportMenu } from '@/components/export/ExportUtils'
import { ErrorDetailDialog } from '@/components/dialogs/ErrorDetailDialog'

/* ── Tiny inline sparkline (7 data points) ── */
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


export function ResultsTab({
  tests,
  passedCount,
  failedCount,
  totalCount,
  runHistory,
  bugReportsList,
  onRunDetail,
  onCompareRuns,
  onViewAllRuns,
  onReportTest,
  testGroups,
  moduleHealth,
  moduleName,
  currentModuleId,
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
}) {
  /* ── Filter data to current module only ── */
  const moduleRuns = useMemo(
    () => currentModuleId ? runHistory.filter(r => r.moduleId === currentModuleId) : runHistory,
    [runHistory, currentModuleId]
  )
  const moduleHealthData = useMemo(
    () => currentModuleId ? (moduleHealth || []).filter(m => m.moduleId === currentModuleId) : (moduleHealth || []),
    [moduleHealth, currentModuleId]
  )

  const passRate = totalCount > 0 ? Math.round((passedCount / totalCount) * 100) : 0
  const [errorOpen, setErrorOpen] = useState(true)
  const [errorDetailOpen, setErrorDetailOpen] = useState(false)
  const [selectedError, setSelectedError] = useState<{ testId: string; message: string; date: string; runRate: number } | null>(null)

  // Error history — extract failed test messages from recent runs
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

  const lastRun = moduleRuns[0]
  const prevRun = moduleRuns[1]

  // Baseline-aware regression overview
  const [savedBaselineId, setSavedBaselineId] = useState<string | null>(() =>
    currentModuleId ? localStorage.getItem(`baseline_${currentModuleId}`) : null
  )
  const baselineRun = savedBaselineId ? moduleRuns.find(r => r.id === savedBaselineId) : null
  const regressionSummary = useMemo(() => {
    if (!baselineRun || !lastRun) return null
    const allTestIds = new Set([
      ...baselineRun.results.map(r => r.testId),
      ...lastRun.results.map(r => r.testId),
    ])
    let regressed = 0, fixed = 0
    for (const testId of allTestIds) {
      const b = baselineRun.results.find(r => r.testId === testId)
      const l = lastRun.results.find(r => r.testId === testId)
      if (b && l && b.status === 'passed' && l.status === 'failed') regressed++
      if (b && l && b.status === 'failed' && l.status === 'passed') fixed++
    }
    return { regressed, fixed, deltaRate: lastRun.rate - baselineRun.rate }
  }, [baselineRun, lastRun])

  const handleClearBaseline = useCallback(() => {
    if (!currentModuleId) return
    localStorage.removeItem(`baseline_${currentModuleId}`)
    setSavedBaselineId(null)
  }, [currentModuleId])

  return (
    <div className="flex flex-col h-full min-h-0">
      <ScrollArea className="flex-1 min-h-0">
        <div className="px-4 pt-4 pb-4 space-y-4">

          {/* ── Summary bar ── */}
          <div className="flex items-stretch gap-3">
            <div className="flex items-center gap-5 bg-gray-50 dark:bg-gray-800/50 rounded-lg px-4 py-3 border border-gray-100 dark:border-gray-700 flex-1">
              <div className="flex items-center gap-4 text-[13px]">
                <div><span className="text-gray-500 dark:text-gray-400">Total </span><span className="font-semibold text-gray-800 dark:text-gray-100">{totalCount}</span></div>
                <div className="w-px h-4 bg-gray-200 dark:bg-gray-600" />
                <div><span className="text-green-600 dark:text-green-400 font-semibold">{passedCount}</span><span className="text-gray-500 dark:text-gray-400 ml-1">passed</span></div>
                <div className="w-px h-4 bg-gray-200 dark:bg-gray-600" />
                <div><span className="text-red-500 dark:text-red-400 font-semibold">{failedCount}</span><span className="text-gray-500 dark:text-gray-400 ml-1">failed</span></div>
              </div>
              <div className="flex-1 max-w-[180px]">
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div className="h-full rounded-full transition-all duration-500" style={{ width: `${passRate}%`, background: passRate >= 90 ? '#22c55e' : passRate >= 75 ? '#eab308' : '#ef4444' }} />
                  </div>
                  <span className="text-[13px] font-semibold" style={{ color: passRate >= 90 ? '#22c55e' : passRate >= 75 ? '#ca8a04' : '#ef4444' }}>{passRate}%</span>
                </div>
              </div>
              {lastRun && (
                <>
                  <div className="w-px h-4 bg-gray-200 dark:bg-gray-600" />
                  <div className="flex items-center gap-2 text-[12px] text-gray-500 dark:text-gray-400">
                    <TrendIcon current={lastRun.rate} previous={prevRun?.rate} />
                    <span>Last: {lastRun.rate}%</span>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* ── Module health cards (with sparklines) ── */}
          {moduleHealthData && moduleHealthData.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {moduleHealthData.map(m => {
                const barColor = m.passRate >= 90 ? 'bg-green-500' : m.passRate >= 75 ? 'bg-yellow-500' : 'bg-red-500'
                return (
                  <div key={m.moduleId} className="flex items-center gap-3 bg-white dark:bg-gray-800/30 rounded-lg px-3.5 py-2 border border-gray-100 dark:border-gray-700/50 shadow-[0_1px_2px_rgba(0,0,0,0.03)]">
                    <div>
                      <div className="text-[11px] text-gray-500 dark:text-gray-400 font-medium">{m.moduleName}</div>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className={`text-[13px] font-semibold ${m.passRate >= 90 ? 'text-green-600 dark:text-green-400' : m.passRate >= 75 ? 'text-yellow-600 dark:text-yellow-400' : 'text-red-600 dark:text-red-400'}`}>{m.passRate}%</span>
                        {m.trend && m.trend.length >= 2 && <Sparkline data={m.trend} className="text-gray-400 dark:text-gray-500" />}
                      </div>
                    </div>
                    <div className="w-16 h-1 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden self-end mb-0.5">
                      <div className={`h-full rounded-full ${barColor}`} style={{ width: `${m.passRate}%` }} />
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          {/* ── Run Results toolbar ── */}
          <div className="flex items-center justify-end">
            <div className="flex items-center gap-2">
              {onCompareRuns && moduleRuns.length >= 2 && (
                <Button variant="outline" size="sm" onClick={onCompareRuns}
                  className="h-7 text-[12px] gap-1.5 cursor-pointer border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700"
                >
                  <GitCompare className="size-3" />
                  Compare Runs
                </Button>
              )}
              <ExportMenu testGroups={testGroups} runHistory={moduleRuns} moduleHealth={moduleHealthData} moduleName={moduleName} />
            </div>
          </div>

          {/* ── Regression Overview ── */}
          {regressionSummary && (
            <div className="border border-indigo-200 dark:border-indigo-800/40 bg-indigo-50/60 dark:bg-indigo-900/10 rounded-lg px-4 py-3 flex items-center gap-4">
              <BookmarkCheck className="size-4 text-indigo-500 shrink-0" />
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
                  <span className={`text-[12px] flex items-center gap-0.5 ${
                    regressionSummary.deltaRate >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                  }`}>
                    {regressionSummary.deltaRate >= 0 ? <ArrowUp className="size-3" /> : <ArrowDown className="size-3" />}
                    {regressionSummary.deltaRate >= 0 ? '+' : ''}{regressionSummary.deltaRate}%
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-1.5 shrink-0">
                {onCompareRuns && (
                  <Button variant="outline" size="sm" onClick={onCompareRuns}
                    className="h-7 text-[11px] cursor-pointer border-indigo-300 dark:border-indigo-700 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-100 dark:hover:bg-indigo-900/30"
                  >
                    Full Report
                  </Button>
                )}
                <button onClick={handleClearBaseline}
                  className="text-[11px] text-gray-400 dark:text-gray-500 hover:text-red-500 dark:hover:text-red-400 transition-colors cursor-pointer"
                  title="Clear baseline"
                >
                  ✕
                </button>
              </div>
            </div>
          )}

          {/* ── Recent Runs (compact + View All) ── */}
          {moduleRuns.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-2.5">
                <h3 className="text-[13px] font-semibold text-gray-700 dark:text-gray-200">Recent Runs</h3>
                <button onClick={onViewAllRuns}
                  className="text-[12px] text-indigo-500 hover:text-indigo-600 dark:text-indigo-400 dark:hover:text-indigo-300 transition-colors cursor-pointer font-medium"
                >
                  View All ({moduleRuns.length})
                </button>
              </div>
              <div className="border border-gray-300 dark:border-gray-500/70 rounded-lg overflow-hidden divide-y divide-gray-200 dark:divide-gray-600/40">
                {moduleRuns.slice(0, 3).map(run => (
                  <div key={run.id}
                    onClick={() => onRunDetail?.(run)}
                    className={`flex items-center gap-4 px-4 py-2.5 ${onRunDetail ? 'cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors' : ''}`}
                  >
                    <div className="flex items-center gap-2.5 flex-1 min-w-0">
                      <span className={`size-2 rounded-full shrink-0 ${run.rate >= 90 ? 'bg-green-500' : run.rate >= 75 ? 'bg-yellow-500' : 'bg-red-500'}`} />
                      <span className="text-[13px] text-gray-700 dark:text-gray-200 truncate">{run.date}</span>
                    </div>
                    <span className="text-[12px] text-gray-400 dark:text-gray-500 font-mono w-14 text-right">{run.duration}</span>
                    <span className="text-[12px] text-green-600 dark:text-green-400 font-medium w-12 text-right">{run.passed}</span>
                    <span className={`text-[12px] font-medium w-10 text-right ${run.failed > 0 ? 'text-red-500 dark:text-red-400' : 'text-gray-400 dark:text-gray-500'}`}>{run.failed}</span>
                    <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full w-14 text-center ${
                      run.rate >= 90 ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                        : run.rate >= 75 ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
                        : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                    }`}>
                      {run.rate}%
                    </span>
                    {prevRun && run.trend && run.trend.length >= 2 && <Sparkline data={run.trend} className="text-gray-300 dark:text-gray-600" />}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Error History (collapsible) ── */}
          {errorHistory.length > 0 && (
            <div className="border border-red-200/60 dark:border-red-900/40 rounded-lg overflow-hidden shadow-[0_1px_3px_rgba(239,68,68,0.06)]">
              <button onClick={() => setErrorOpen(!errorOpen)}
                className="w-full flex items-center gap-2.5 px-4 py-3 bg-gradient-to-r from-red-50/80 to-red-50/30 dark:from-red-950/20 dark:to-transparent hover:from-red-100/80 hover:to-red-50/50 dark:hover:from-red-950/30 dark:hover:to-transparent transition-all cursor-pointer text-left"
              >
                <div className="size-7 rounded-lg bg-red-100 dark:bg-red-900/40 flex items-center justify-center shrink-0">
                  <Bug className="size-3.5 text-red-600 dark:text-red-400" />
                </div>
                <span className="text-[13px] font-semibold text-gray-800 dark:text-gray-100 flex-1">Error History</span>
                <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-red-100/80 dark:bg-red-900/40 text-red-700 dark:text-red-400">{errorHistory.length}</span>
                {errorOpen ? <ChevronDown className="size-3.5 text-gray-400" /> : <ChevronRight className="size-3.5 text-gray-400" />}
              </button>
              {errorOpen && (
                <div className="py-1.5 px-1.5 space-y-1">
                  {errorHistory.map(err => (
                    <div key={err.testId}
                      className="flex items-start gap-3 px-3 py-2.5 rounded-lg border border-transparent hover:border-red-200/40 dark:hover:border-red-800/40 hover:bg-red-50/40 dark:hover:bg-red-950/20 transition-all group cursor-pointer"
                      onClick={() => { setSelectedError({ testId: err.testId, message: err.message, date: err.date, runRate: err.runRate }); setErrorDetailOpen(true) }}
                    >
                      <div className="size-2 mt-1.5 rounded-full bg-red-500 shrink-0 ring-2 ring-red-200 dark:ring-red-800" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-[13px] font-medium text-gray-800 dark:text-gray-100 truncate">{err.testId}</span>
                          <span className="text-[10px] text-gray-400 dark:text-gray-500 shrink-0">{err.date}</span>
                          <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full shrink-0 ${
                            err.runRate >= 90 ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                              : err.runRate >= 75 ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
                              : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                          }`}>{err.runRate}%</span>
                        </div>
                        <div className="text-[11px] text-red-600 dark:text-red-400 font-mono mt-1 leading-snug line-clamp-2">{err.message}</div>
                      </div>
                      <button onClick={(e) => { e.stopPropagation(); onReportTest?.(err.testId, err.testId, err.message) }}
                        className="shrink-0 size-7 flex items-center justify-center rounded-md text-gray-600 dark:text-gray-300 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 cursor-pointer"
                        title="Report bug"
                      >
                        <Flag className="size-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
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
