'use client'

import React, { useState, useMemo } from 'react'
import { GitCompare, MoreVertical, Eye, MessageSquare, RotateCcw, Bug, TrendingUp, TrendingDown, Minus, ChevronDown, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { testSpecGroups, type TestClassGroup, type TestItem } from '@/data/testSpecGroups'
import type { RunSnapshot, ModuleHealth } from '@/lib/types'
import { ExportMenu } from '@/components/export/ExportUtils'
import { TestStatusIcon, SortArrow } from '@/components/shared/PriorityBadge'


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


/* ── Helpers ── */
function parseDuration(d: string) {
  const p = d.split(':')
  return p.length === 2 ? parseInt(p[0]) * 60 + parseInt(p[1]) : 0
}
function fmtDuration(sec: number) {
  const m = Math.floor(sec / 60), s = sec % 60
  return `${m}:${String(s).padStart(2, '0')}`
}


export function ResultsTab({
  tests,
  passedCount,
  failedCount,
  totalCount,
  runHistory,
  onReportTest,
  bugReportsList,
  onRunDetail,
  onCompareRuns,
  testGroups,
  moduleHealth,
  moduleName,
  currentModuleId,
  autoReportedTestIds,
}: {
  tests: TestItem[]
  passedCount: number
  failedCount: number
  totalCount: number
  runHistory: RunSnapshot[]
  onReportTest: (test: TestItem) => void
  bugReportsList: { id: string; testId: string; desc: string; status: string }[]
  onRunDetail?: (run: RunSnapshot) => void
  onCompareRuns?: () => void
  testGroups?: TestClassGroup[]
  moduleHealth?: ModuleHealth[]
  moduleName?: string
  currentModuleId?: string
  autoReportedTestIds?: Set<string>
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
  const [resultFilter, setResultFilter] = useState<'all' | 'passed' | 'failed'>('all')
  const [sortCol, setSortCol] = useState<'status' | 'test' | 'duration'>('status')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const [bugOpen, setBugOpen] = useState(false)

  const handleSort = (col: 'status' | 'test' | 'duration') => {
    if (sortCol === col) { setSortDir(prev => prev === 'asc' ? 'desc' : 'asc') }
    else { setSortCol(col); setSortDir('asc') }
  }

  const filteredTests = tests
    .filter(t => resultFilter === 'all' || (resultFilter === 'passed' ? t.status === 'passed' : t.status === 'failed'))
    .sort((a, b) => {
      const dir = sortDir === 'asc' ? 1 : -1
      switch (sortCol) {
        case 'status': return dir * a.status.localeCompare(b.status)
        case 'test': return dir * (a.description || a.name || a.id).localeCompare(b.description || b.name || b.id)
        case 'duration': return dir * (parseDuration(a.duration) - parseDuration(b.duration))
        default: return 0
      }
    })

  const getTestError = (id: string): string | undefined => {
    for (const g of testSpecGroups) {
      const t = g.tests.find(x => x.id === id)
      if (t) return t.bugDetails || (t.status === 'bug' ? t.actual : undefined)
    }
    return undefined
  }

  const lastRun = moduleRuns[0]
  const prevRun = moduleRuns[1]

  const statusCounts = useMemo(() => {
    let p = 0, f = 0
    for (const t of tests) {
      if (t.status === 'passed') p++
      else if (t.status === 'failed') f++
    }
    return { passed: p, failed: f, pending: tests.length - p - f }
  }, [tests])

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
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              {(['all', 'passed', 'failed'] as const).map(f => {
                const count = f === 'all' ? totalCount : f === 'passed' ? statusCounts.passed : statusCounts.failed
                const active = resultFilter === f
                return (
                  <button key={f} onClick={() => setResultFilter(f)}
                    className={`px-3 py-1.5 rounded-md text-[12px] font-medium transition-all cursor-pointer ${
                      active
                        ? f === 'failed' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 shadow-sm'
                          : f === 'passed' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 shadow-sm'
                          : 'bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 shadow-sm'
                        : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700/50'
                    }`}
                  >
                    {f === 'all' ? 'All' : f === 'passed' ? 'Passed' : 'Failed'}
                    <span className="ml-1.5 opacity-70">({count})</span>
                  </button>
                )
              })}
            </div>
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

          {/* ── Test Results table ── */}
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                  <TableHead className="text-[11px] font-semibold text-gray-500 dark:text-gray-400 w-10 cursor-pointer select-none uppercase tracking-wider" onClick={() => handleSort('status')}>
                    <span className="inline-flex items-center gap-1"><SortArrow col="status" sortCol={sortCol} sortDir={sortDir} /></span>
                  </TableHead>
                  <TableHead className="text-[11px] font-semibold text-gray-500 dark:text-gray-400 cursor-pointer select-none uppercase tracking-wider" onClick={() => handleSort('test')}>
                    <span className="inline-flex items-center gap-1">Test <SortArrow col="test" sortCol={sortCol} sortDir={sortDir} /></span>
                  </TableHead>
                  <TableHead className="text-[11px] font-semibold text-gray-500 dark:text-gray-400 w-16 text-center cursor-pointer select-none uppercase tracking-wider" onClick={() => handleSort('duration')}>
                    <span className="inline-flex items-center gap-1">Time <SortArrow col="duration" sortCol={sortCol} sortDir={sortDir} /></span>
                  </TableHead>
                  <TableHead className="text-[11px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Error</TableHead>
                  <TableHead className="w-10" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredTests.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center text-[13px] text-gray-400 dark:text-gray-500 py-8">
                      No {resultFilter} tests
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredTests.map(test => {
                    const error = getTestError(test.id)
                    const displayName = test.description || test.name || test.id
                    return (
                      <TableRow key={test.id}
                        className={`dark:border-gray-700 transition-colors ${test.status === 'failed' ? 'bg-red-50/40 dark:bg-red-900/8' : 'hover:bg-gray-50/50 dark:hover:bg-gray-800/30'}`}
                      >
                        <TableCell><TestStatusIcon status={test.status} size={3.5} /></TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <span className={`text-[13px] ${test.status === 'failed' ? 'text-red-700 dark:text-red-400 font-medium' : 'text-gray-700 dark:text-gray-200'}`}>
                              {displayName}
                            </span>
                            {autoReportedTestIds?.has(test.id) && <Bug className="size-3 text-red-500 shrink-0" title="Auto-reported bug" />}
                          </div>
                        </TableCell>
                        <TableCell className="text-center text-[12px] font-mono text-gray-400 dark:text-gray-500">{test.duration}</TableCell>
                        <TableCell className="text-[12px] text-red-500 dark:text-red-400 max-w-[240px] truncate">{error || <span className="text-gray-300 dark:text-gray-600">—</span>}</TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm" className="h-7 w-7 p-0 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700">
                                <MoreVertical className="size-4 text-gray-400" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="w-48">
                              <DropdownMenuItem onClick={() => onReportTest(test)} className="text-[12px] gap-2 cursor-pointer">
                                <Eye className="size-3.5" /> View Details
                              </DropdownMenuItem>
                              {test.status === 'failed' && (
                                <DropdownMenuItem onClick={() => onReportTest(test)} className="text-[12px] gap-2 cursor-pointer text-orange-600 dark:text-orange-400">
                                  <MessageSquare className="size-3.5" /> Report Bug
                                </DropdownMenuItem>
                              )}
                              <DropdownMenuItem onClick={() => onReportTest(test)} className="text-[12px] gap-2 cursor-pointer">
                                <RotateCcw className="size-3.5" /> Re-run Test
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

          {/* ── Recent Runs ── */}
          {moduleRuns.length > 0 && (
            <div>
              <h3 className="text-[13px] font-semibold text-gray-700 dark:text-gray-200 mb-2.5">Recent Runs</h3>
              <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden divide-y divide-gray-100 dark:divide-gray-700/50">
                {moduleRuns.slice(0, 5).map(run => (
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

          {/* ── Bug Registry (collapsible) ── */}
          {bugReportsList.length > 0 && (
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
              <button onClick={() => setBugOpen(!bugOpen)}
                className="w-full flex items-center gap-2 px-4 py-2.5 bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-800/70 transition-colors cursor-pointer text-left"
              >
                {bugOpen ? <ChevronDown className="size-3.5 text-gray-400" /> : <ChevronRight className="size-3.5 text-gray-400" />}
                <Bug className="size-3.5 text-gray-500" />
                <span className="text-[13px] font-semibold text-gray-700 dark:text-gray-200 flex-1">Bug Registry</span>
                <span className="text-[11px] text-gray-500 dark:text-gray-400">{bugReportsList.length}</span>
              </button>
              {bugOpen && (
                <div className="divide-y divide-gray-100 dark:divide-gray-700/50">
                  {bugReportsList.map(bug => (
                    <div key={bug.id} className="flex items-center gap-3 px-4 py-2.5">
                      <span className="text-[11px] font-mono text-gray-400 dark:text-gray-500 w-16">{bug.id.slice(0, 8).toUpperCase()}</span>
                      <span className="flex-1 text-[13px] text-gray-700 dark:text-gray-200 truncate">{bug.desc}</span>
                      <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full shrink-0 ${
                        bug.status === 'Open' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                          : bug.status === 'In Progress' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
                          : bug.status === 'Resolved' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                      }`}>{bug.status}</span>
                      <span className="text-[12px] text-gray-400 dark:text-gray-500">{bug.testId}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

        </div>
      </ScrollArea>
    </div>
  )
}
