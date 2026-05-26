'use client'

import React, { useState, useMemo } from 'react'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { AlertTriangle, CheckCircle2, XCircle, TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface TestItem {
  id: string
  name: string
  status: 'passed' | 'failed' | 'pending' | 'running'
  duration: string
  error?: string
}

interface RunSnapshot {
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

interface ResultsTabProps {
  tests: TestItem[]
  passedCount: number
  failedCount: number
  totalCount: number
  runHistory: RunSnapshot[]
  onReportTest: (test: TestItem) => void
}

export function ResultsTab({
  tests,
  passedCount,
  failedCount,
  totalCount,
  runHistory,
  onReportTest,
}: ResultsTabProps) {
  const passRate = Math.round((passedCount / totalCount) * 100)
  const [resultFilter, setResultFilter] = useState<'all' | 'passed' | 'failed'>('all')
  const [compareRun1, setCompareRun1] = useState<string>('')
  const [compareRun2, setCompareRun2] = useState<string>('')

  const filteredTests = tests.filter((t) => {
    if (resultFilter === 'all') return true
    return resultFilter === 'passed' ? t.status === 'passed' : t.status === 'failed'
  })

  // Comparison logic
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

      // Find test name from current tests
      const test = tests.find((t) => t.id === id)
      const testName = test?.name || id

      rows.push({ testId: id, testName, run1Status: s1, run2Status: s2, change })
    }

    return { rows, improved, regressed, unchanged, run1Label: run1.date, run2Label: run2.date }
  }, [compareRun1, compareRun2, runHistory, tests])

  return (
    <div className="flex flex-col h-full overflow-auto">
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
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-100 dark:border-blue-800/50">
            <div className="text-[12px] text-blue-600 dark:text-blue-400 font-medium mb-1">Pass Rate</div>
            <div className="text-2xl font-bold text-blue-700 dark:text-blue-400">{passRate}%</div>
            <Progress value={passRate} className="h-1.5 mt-2 bg-blue-100 dark:bg-blue-800" />
          </div>
        </div>
      </div>

      <Separator className="mx-4" />

      {/* Run Results Drill-Down */}
      <div className="px-4 pt-3 pb-3 shrink-0">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-[14px] font-semibold text-gray-800 dark:text-gray-100">Run Results</h3>
          <div className="flex items-center gap-1">
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
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <ScrollArea className="h-[300px] border border-gray-200 dark:border-gray-700 rounded-md">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[400px]">Test Name</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead className="w-[100px]">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredTests.map((test) => (
                <TableRow key={test.id}>
                  <TableCell className="font-medium text-[13px]">{test.name}</TableCell>
                  <TableCell>
                    <Badge
                      variant={test.status === 'passed' ? 'default' : 'destructive'}
                      className={test.status === 'passed' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : ''}
                    >
                      {test.status === 'passed' ? (
                        <CheckCircle2 className="size-3 mr-1" />
                      ) : (
                        <XCircle className="size-3 mr-1" />
                      )}
                      {test.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-[13px] text-gray-500">{test.duration}</TableCell>
                  <TableCell>
                    {test.status === 'failed' && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-7 text-[11px]"
                        onClick={() => onReportTest(test)}
                      >
                        <AlertTriangle className="size-3 mr-1" />
                        Report
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </ScrollArea>
      </div>

      {/* Run Comparison */}
      <div className="px-4 pt-3 pb-3 shrink-0">
        <h3 className="text-[14px] font-semibold text-gray-800 dark:text-gray-100 mb-3">Compare Runs</h3>
        <div className="flex items-center gap-3 mb-3">
          <Select value={compareRun1} onValueChange={setCompareRun1}>
            <SelectTrigger className="w-[200px] h-8">
              <SelectValue placeholder="Select Run 1" />
            </SelectTrigger>
            <SelectContent>
              {runHistory.map((run) => (
                <SelectItem key={run.id} value={String(run.id)}>
                  Run #{run.id} - {run.date}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <span className="text-gray-400">vs</span>
          <Select value={compareRun2} onValueChange={setCompareRun2}>
            <SelectTrigger className="w-[200px] h-8">
              <SelectValue placeholder="Select Run 2" />
            </SelectTrigger>
            <SelectContent>
              {runHistory.map((run) => (
                <SelectItem key={run.id} value={String(run.id)}>
                  Run #{run.id} - {run.date}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {comparisonData && (
          <>
            <div className="flex items-center gap-4 mb-3">
              <div className="flex items-center gap-1.5 text-green-600 dark:text-green-400">
                <TrendingUp className="size-4" />
                <span className="text-[13px] font-medium">{comparisonData.improved} Improved</span>
              </div>
              <div className="flex items-center gap-1.5 text-red-600 dark:text-red-400">
                <TrendingDown className="size-4" />
                <span className="text-[13px] font-medium">{comparisonData.regressed} Regressed</span>
              </div>
              <div className="flex items-center gap-1.5 text-gray-500">
                <Minus className="size-4" />
                <span className="text-[13px] font-medium">{comparisonData.unchanged} Unchanged</span>
              </div>
            </div>

            <ScrollArea className="h-[250px] border border-gray-200 dark:border-gray-700 rounded-md">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Test</TableHead>
                    <TableHead>{comparisonData.run1Label}</TableHead>
                    <TableHead>{comparisonData.run2Label}</TableHead>
                    <TableHead>Change</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {comparisonData.rows.map((row) => (
                    <TableRow key={row.testId}>
                      <TableCell className="font-medium text-[13px]">{row.testName}</TableCell>
                      <TableCell>
                        <Badge
                          variant={row.run1Status === 'passed' ? 'default' : 'destructive'}
                          className={row.run1Status === 'passed' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}
                        >
                          {row.run1Status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={row.run2Status === 'passed' ? 'default' : 'destructive'}
                          className={row.run2Status === 'passed' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}
                        >
                          {row.run2Status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {row.change === 'fixed' && (
                          <span className="text-green-600 flex items-center gap-1 text-[12px]">
                            <TrendingUp className="size-3" /> Fixed
                          </span>
                        )}
                        {row.change === 'regressed' && (
                          <span className="text-red-600 flex items-center gap-1 text-[12px]">
                            <TrendingDown className="size-3" /> Regressed
                          </span>
                        )}
                        {row.change === 'unchanged' && (
                          <span className="text-gray-400 flex items-center gap-1 text-[12px]">
                            <Minus className="size-3" /> Same
                          </span>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </ScrollArea>
          </>
        )}
      </div>
    </div>
  )
}
