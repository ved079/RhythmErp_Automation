'use client'

import React, { useState, useMemo } from 'react'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { GitCompare, MoreVertical, Eye, MessageSquare, RotateCcw } from 'lucide-react'
import type { TestItem, TestClassGroup, RunSnapshot, ModuleHealth } from '@/lib/types'
import { TestStatusIcon } from '@/components/home/TestStatusIcon'
import { SortArrow } from '@/components/home/SortArrow'
import { ExportMenu } from '@/components/export/ExportUtils'
import { testSpecGroups } from '@/lib/constants'

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
}) {
  const passRate = Math.round((passedCount / totalCount) * 100)
  const [resultFilter, setResultFilter] = useState<'all' | 'passed' | 'failed'>('all')
  const [compareRun1, setCompareRun1] = useState<string>('')
  const [compareRun2, setCompareRun2] = useState<string>('')
  const [sortCol, setSortCol] = useState<'status' | 'id' | 'test' | 'duration'>('id')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')

  const handleSort = (col: 'status' | 'id' | 'test' | 'duration') => {
    if (sortCol === col) {
      setSortDir(prev => prev === 'asc' ? 'desc' : 'asc')
    } else {
      setSortCol(col)
      setSortDir('asc')
    }
  }

  const filteredTests = tests
    .filter((t) => {
      if (resultFilter === 'all') return true
      return resultFilter === 'passed' ? t.status === 'passed' : t.status === 'failed'
    })
    .sort((a, b) => {
      const dir = sortDir === 'asc' ? 1 : -1
      switch (sortCol) {
        case 'status': return dir * a.status.localeCompare(b.status)
        case 'id': return dir * a.id.localeCompare(b.id)
        case 'test': return dir * a.name.localeCompare(b.name)
        case 'duration': {
          const parseDur = (d: string) => { const p = d.split(':'); return p.length === 2 ? parseInt(p[0]) * 60 + parseInt(p[1]) : 0 }
          return dir * (parseDur(a.duration) - parseDur(b.duration))
        }
        default: return 0
      }
    })

  // Get error info from testSpecGroups
  const getTestError = (id: string): string | undefined => {
    for (const g of testSpecGroups) {
      const t = g.tests.find((x) => x.id === id)
      if (t) return t.bugDetails || (t.status === 'bug' ? t.actual : undefined)
    }
    return undefined
  }

  // Comparison logic (Feature 5)
  const comparisonData = useMemo(() => {
    if (!compareRun1 || !compareRun2) return null
    const run1 = runHistory.find((r) => String(r.id) === compareRun1)
    const run2 = runHistory.find((r) => String(r.id) === compareRun2)
    if (!run1 || !run2) return null

    const allTestIds = new Set([...run1.results.map((r) => r.testId), ...run2.results.map((r) => r.testId)])
    const rows: {
      testId: string
      testName: string
      run1Status: 'passed' | 'failed' | 'skipped'
      run2Status: 'passed' | 'failed' | 'skipped'
      change: 'fixed' | 'regressed' | 'unchanged'
    }[] = []

    let improved = 0
    let regressed = 0
    let unchanged = 0

    for (const id of allTestIds) {
      const r1 = run1.results.find((r) => r.testId === id)
      const r2 = run2.results.find((r) => r.testId === id)
      const s1 = r1?.status || 'skipped' as const
      const s2 = r2?.status || 'skipped' as const
      let change: 'fixed' | 'regressed' | 'unchanged' = 'unchanged'
      if (s1 === 'failed' && s2 === 'passed') { change = 'fixed'; improved++ }
      else if (s1 === 'passed' && s2 === 'failed') { change = 'regressed'; regressed++ }
      else { unchanged++ }

      // Find test name
      let testName = id
      for (const g of testSpecGroups) {
        const t = g.tests.find((x) => x.id === id)
        if (t) { testName = t.description; break }
      }

      rows.push({ testId: id, testName, run1Status: s1, run2Status: s2, change })
    }

    return { rows, improved, regressed, unchanged, run1Label: run1.date, run2Label: run2.date }
  }, [compareRun1, compareRun2, runHistory])

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Summary Cards */}
      <div className="px-4 pt-4 pb-3 shrink-0">
        <h3 className="text-[14px] font-semibold text-gray-800 dark:text-gray-100 mb-3">Test Results Summary</h3>
        <div className="grid grid-cols-4 gap-3">
          <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4 border border-gray-100 dark:border-gray-700">
            <div className="text-[12px] text-gray-500 dark:text-gray-400 font-medium mb-1">Total Tests</div>
            <div className="text-2xl font-bold text-gray-800 dark:text-gray-100">{totalCount}</div>
          </div>
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 border border-green-100 dark:border-green-800/50">
            <div className="text-[12px] text-green-600 dark:text-green-400 font-medium mb-1">Passed</div>
            <div className="text-2xl font-bold text-green-700 dark:text-green-400">{passedCount}</div>
          </div>
          <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4 border border-red-100 dark:border-red-800/50">
            <div className="text-[12px] text-red-600 dark:text-red-400 font-medium mb-1">Failed</div>
            <div className="text-2xl font-bold text-red-700 dark:text-red-400">{failedCount}</div>
          </div>
          <div className="bg-indigo-50 dark:bg-indigo-900/20 rounded-lg p-4 border border-indigo-100 dark:border-indigo-800/50">
            <div className="text-[12px] text-indigo-600 dark:text-indigo-400 font-medium mb-1">Pass Rate</div>
            <div className="text-2xl font-bold text-indigo-700 dark:text-indigo-400">{passRate}%</div>
            <Progress value={passRate} className="h-1.5 mt-2 bg-indigo-100 dark:bg-indigo-800" />
          </div>
        </div>
      </div>

      <Separator className="mx-4" />

      {/* Run Results Drill-Down */}
      <ScrollArea className="flex-1 min-h-0">
      <div className="px-4 pt-3 pb-3">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-[14px] font-semibold text-gray-800 dark:text-gray-100">Run Results</h3>
          <div className="flex items-center gap-2">
            {(['all', 'passed', 'failed'] as const).map((f) => (
              <button
                key={f}
                onClick={() => setResultFilter(f)}
                className={`px-2.5 py-1 rounded-md text-[12px] font-medium transition-colors cursor-pointer ${
                  resultFilter === f
                    ? f === 'failed'
                      ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                      : f === 'passed'
                        ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200'
                    : 'text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
                }`}
              >
                {f === 'all' ? `All (${totalCount})` : f === 'passed' ? `Passed (${passedCount})` : `Failed (${failedCount})`}
              </button>
            ))}
            {/* Compare Runs & Export Buttons */}
            <Separator orientation="vertical" className="h-5 mx-1" />
            {onCompareRuns && runHistory.length >= 2 && (
              <Button
                variant="outline"
                size="sm"
                onClick={onCompareRuns}
                className="h-7 text-[12px] gap-1.5 cursor-pointer border-[#3F51B5]/30 text-[#3F51B5] hover:bg-[#3F51B5] hover:text-white dark:border-indigo-500/30 dark:text-indigo-400 dark:hover:bg-indigo-600 dark:hover:text-white"
              >
                <GitCompare className="size-3" />
                Compare
              </Button>
            )}
            <ExportMenu
              testGroups={testGroups}
              runHistory={runHistory}
              moduleHealth={moduleHealth}
              moduleName={moduleName}
            />
          </div>
        </div>
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="bg-[#DFE9FB] dark:bg-indigo-900/30 hover:bg-[#DFE9FB] dark:hover:bg-indigo-900/30">
                <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 w-12 cursor-pointer select-none" onClick={() => handleSort('status')}>
                  <span className="inline-flex items-center gap-1">Status <SortArrow col="status" sortCol={sortCol} sortDir={sortDir} /></span>
                </TableHead>
                <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 w-14 cursor-pointer select-none" onClick={() => handleSort('id')}>
                  <span className="inline-flex items-center gap-1">ID <SortArrow col="id" sortCol={sortCol} sortDir={sortDir} /></span>
                </TableHead>
                <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 cursor-pointer select-none" onClick={() => handleSort('test')}>
                  <span className="inline-flex items-center gap-1">Test <SortArrow col="test" sortCol={sortCol} sortDir={sortDir} /></span>
                </TableHead>
                <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 w-16 text-center cursor-pointer select-none" onClick={() => handleSort('duration')}>
                  <span className="inline-flex items-center gap-1">Duration <SortArrow col="duration" sortCol={sortCol} sortDir={sortDir} /></span>
                </TableHead>
                <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300">Error</TableHead>
                <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 w-24 text-center">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredTests.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-[13px] text-gray-400 dark:text-gray-500 py-6">
                    No {resultFilter} tests
                  </TableCell>
                </TableRow>
              ) : (
                filteredTests.map((test) => {
                  const error = getTestError(test.id)
                  return (
                    <TableRow key={test.id} className={`dark:border-gray-700 ${test.status === 'failed' ? 'bg-red-50/30 dark:bg-red-900/10' : ''}`}>
                      <TableCell>
                        <TestStatusIcon status={test.status} size={3.5} />
                      </TableCell>
                      <TableCell className="text-[12px] font-mono text-gray-500 dark:text-gray-400">{test.id}</TableCell>
                      <TableCell className={`text-[13px] ${test.status === 'failed' ? 'text-red-700 dark:text-red-400 font-medium' : 'text-gray-700 dark:text-gray-200'}`}>
                        {test.name}
                      </TableCell>
                      <TableCell className="text-center text-[12px] font-mono text-gray-500 dark:text-gray-400">{test.duration}</TableCell>
                      <TableCell className="text-[12px] text-red-500 dark:text-red-400 max-w-[250px] truncate">
                        {error || '—'}
                      </TableCell>
                      <TableCell className="text-center">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm" className="h-7 w-7 p-0 cursor-pointer hover:bg-[#DFE9FB] dark:hover:bg-indigo-900/30">
                              <MoreVertical className="size-4 text-gray-500 dark:text-gray-400" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="w-40">
                            <DropdownMenuItem onClick={() => onReportTest(test)} className="text-[12px] gap-2 cursor-pointer">
                              <Eye className="size-3.5" />
                              View Details
                            </DropdownMenuItem>
                            {test.status === 'failed' && (
                              <DropdownMenuItem onClick={() => onReportTest(test)} className="text-[12px] gap-2 cursor-pointer text-orange-600 dark:text-orange-400">
                                <MessageSquare className="size-3.5" />
                                Report Bug
                              </DropdownMenuItem>
                            )}
                            <DropdownMenuItem onClick={() => onReportTest(test)} className="text-[12px] gap-2 cursor-pointer">
                              <RotateCcw className="size-3.5" />
                              Re-run Test
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
      </div>

      <Separator className="mx-4" />

      {/* Compare Runs Section (Feature 5) */}
      <div className="px-4 pt-3 pb-3 shrink-0">
        <h3 className="text-[14px] font-semibold text-gray-800 dark:text-gray-100 mb-3 flex items-center gap-2">
          <GitCompare className="size-4 text-gray-500 dark:text-gray-400" />
          Compare Runs
        </h3>
        <div className="flex items-center gap-3 mb-3 flex-wrap">
          <div className="flex items-center gap-2">
            <span className="text-[12px] text-gray-500 dark:text-gray-400 font-medium">Run 1:</span>
            <Select value={compareRun1} onValueChange={setCompareRun1}>
              <SelectTrigger className="h-8 w-56 text-[12px] bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-600">
                <SelectValue placeholder="Select a run..." />
              </SelectTrigger>
              <SelectContent>
                {runHistory.map((r) => (
                  <SelectItem key={r.id} value={String(r.id)}>
                    {r.date} ({r.rate}%)
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <span className="text-gray-400 dark:text-gray-500 text-lg">vs</span>
          <div className="flex items-center gap-2">
            <span className="text-[12px] text-gray-500 dark:text-gray-400 font-medium">Run 2:</span>
            <Select value={compareRun2} onValueChange={setCompareRun2}>
              <SelectTrigger className="h-8 w-56 text-[12px] bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-600">
                <SelectValue placeholder="Select a run..." />
              </SelectTrigger>
              <SelectContent>
                {runHistory.map((r) => (
                  <SelectItem key={r.id} value={String(r.id)}>
                    {r.date} ({r.rate}%)
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {comparisonData ? (
          <>
            {/* Summary */}
            <div className="flex items-center gap-4 mb-3">
              <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                ✅ {comparisonData.improved} Fixed
              </span>
              <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400">
                ❌ {comparisonData.regressed} Regressed
              </span>
              <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">
                ➡️ {comparisonData.unchanged} Unchanged
              </span>
            </div>

            {/* Comparison Table */}
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="bg-[#DFE9FB] dark:bg-indigo-900/30 hover:bg-[#DFE9FB] dark:hover:bg-indigo-900/30">
                    <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 w-14">Test ID</TableHead>
                    <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300">Test Name</TableHead>
                    <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 text-center">{comparisonData.run1Label}</TableHead>
                    <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 text-center">{comparisonData.run2Label}</TableHead>
                    <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 text-center">Change</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {comparisonData.rows.map((row) => (
                    <TableRow key={row.testId} className="dark:border-gray-700">
                      <TableCell className="text-[12px] font-mono text-gray-500 dark:text-gray-400">{row.testId}</TableCell>
                      <TableCell className="text-[13px] text-gray-700 dark:text-gray-200">{row.testName}</TableCell>
                      <TableCell className="text-center">
                        <TestStatusIcon status={row.run1Status} size={3.5} />
                      </TableCell>
                      <TableCell className="text-center">
                        <TestStatusIcon status={row.run2Status} size={3.5} />
                      </TableCell>
                      <TableCell className="text-center">
                        <span className={`text-[12px] font-medium ${
                          row.change === 'fixed' ? 'text-green-600 dark:text-green-400' :
                          row.change === 'regressed' ? 'text-red-600 dark:text-red-400' :
                          'text-gray-500 dark:text-gray-400'
                        }`}>
                          {row.change === 'fixed' ? '✅ Fixed' : row.change === 'regressed' ? '❌ Regressed' : '➡️ Unchanged'}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </>
        ) : (
          <div className="text-center py-6 text-gray-400 dark:text-gray-500">
            <GitCompare className="size-8 mx-auto mb-2 opacity-50" />
            <p className="text-[13px]">Select two runs above to compare</p>
          </div>
        )}
      </div>

      <Separator className="mx-4" />

      {/* Recent Runs */}
      <div className="px-4 pt-3 pb-3 shrink-0">
        <h3 className="text-[14px] font-semibold text-gray-800 dark:text-gray-100 mb-3">Recent Runs</h3>
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="bg-[#DFE9FB] dark:bg-indigo-900/30 hover:bg-[#DFE9FB] dark:hover:bg-indigo-900/30">
                <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300">Date</TableHead>
                <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300">Duration</TableHead>
                <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 text-center">Passed</TableHead>
                <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 text-center">Failed</TableHead>
                <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 text-center">Rate</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {runHistory.slice(0, 5).map((run) => (
                <TableRow
                  key={run.id}
                  className={`dark:border-gray-700 ${onRunDetail ? 'cursor-pointer hover:bg-[#DFE9FB]/30 dark:hover:bg-indigo-900/10 transition-colors' : ''}`}
                  onClick={() => onRunDetail?.(run)}
                >
                  <TableCell className="text-[13px] text-gray-700 dark:text-gray-200">{run.date}</TableCell>
                  <TableCell className="text-[13px] text-gray-600 dark:text-gray-400 font-mono">{run.duration}</TableCell>
                  <TableCell className="text-center">
                    <span className="text-green-600 dark:text-green-400 font-medium text-[13px]">{run.passed}</span>
                  </TableCell>
                  <TableCell className="text-center">
                    <span className={`font-medium text-[13px] ${run.failed > 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-400 dark:text-gray-500'}`}>
                      {run.failed}
                    </span>
                  </TableCell>
                  <TableCell className="text-center">
                    <span
                      className={`text-[12px] font-medium px-2 py-0.5 rounded-full ${
                        run.rate >= 90
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                          : run.rate >= 75
                            ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
                            : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                      }`}
                    >
                      {run.rate}%
                    </span>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>

      <Separator className="mx-4" />

      {/* Bug Registry */}
      <div className="px-4 pt-3 pb-4">
        <h3 className="text-[14px] font-semibold text-gray-800 dark:text-gray-100 mb-3">Bug Registry</h3>
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="bg-[#DFE9FB] dark:bg-indigo-900/30 hover:bg-[#DFE9FB] dark:hover:bg-indigo-900/30">
                <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300">Bug ID</TableHead>
                <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300">Description</TableHead>
                <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 text-center">Status</TableHead>
                <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300">Related Tests</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {bugReportsList.map((bug) => (
                <TableRow key={bug.id} className="dark:border-gray-700">
                  <TableCell className="text-[13px] font-mono text-gray-600 dark:text-gray-400">{bug.id.slice(0, 8).toUpperCase()}</TableCell>
                  <TableCell className="text-[13px] text-gray-700 dark:text-gray-200">{bug.desc}</TableCell>
                  <TableCell className="text-center">
                    <span
                      className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${
                        bug.status === 'Open' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                      }`}
                    >
                      {bug.status}
                    </span>
                  </TableCell>
                  <TableCell className="text-[13px] text-gray-500 dark:text-gray-400">{bug.testId}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
      </ScrollArea>
    </div>
  )
}
