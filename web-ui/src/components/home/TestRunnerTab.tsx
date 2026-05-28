'use client'

import React, { useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Play, RotateCcw, Flame, Activity, CheckCircle2, XCircle, Circle, ShieldCheck } from 'lucide-react'
import type { TestItem, TestPriority } from '@/lib/types'
import { PriorityBadge } from '@/components/home/PriorityBadge'
import { TestStatusIcon } from '@/components/home/TestStatusIcon'
import { priorityConfig } from '@/lib/constants'

export function TestRunnerTab({
  tests,
  testChecks,
  toggleTestCheck,
  isRunning,
  onRun,
  onRunByPriority,
  totalFailed,
  onRerunFailed,
}: {
  tests: TestItem[]
  testChecks: Set<string>
  toggleTestCheck: (id: string) => void
  isRunning: boolean
  onRun: (selectedOnly: boolean) => void
  onRunByPriority: (priority: TestPriority) => void
  totalFailed: number
  onRerunFailed: () => void
}) {
  const pendingOrRunning = tests.filter((t) => t.status === 'pending' || t.status === 'running')
  const allSelected = pendingOrRunning.length > 0 && pendingOrRunning.every((t) => testChecks.has(t.id))
  const noneSelected = pendingOrRunning.every((t) => !testChecks.has(t.id))

  const handleSelectAll = useCallback(() => {
    if (allSelected) {
      // Deselect all
      pendingOrRunning.forEach((t) => { if (testChecks.has(t.id)) toggleTestCheck(t.id) })
    } else {
      // Select all pending/running
      pendingOrRunning.forEach((t) => { if (!testChecks.has(t.id)) toggleTestCheck(t.id) })
    }
  }, [allSelected, pendingOrRunning, testChecks, toggleTestCheck])

  const passedCount = tests.filter((t) => t.status === 'passed').length
  const failedCount = tests.filter((t) => t.status === 'failed').length
  const pendingCount = tests.filter((t) => t.status === 'pending').length
  const selectedRunnable = tests.filter((t) => t.status === 'pending' && testChecks.has(t.id)).length
  const smokeCount = tests.filter((t) => t.priority === 'smoke' && (t.status === 'pending' || t.status === 'running')).length
  const regressionCount = tests.filter((t) => t.priority === 'regression' && (t.status === 'pending' || t.status === 'running')).length

  // Group tests by class
  const testGroups: { name: string; tests: TestItem[] }[] = []
  let currentGroup: string | null = null
  for (const t of tests) {
    const cls = t.id.replace(/\d+$/, '').replace(/T/, 'Test')
    if (cls !== currentGroup) {
      currentGroup = cls
      testGroups.push({ name: cls, tests: [] })
    }
    testGroups[testGroups.length - 1].tests.push(t)
  }

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Action Bar */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-100 dark:border-gray-700 shrink-0 flex-wrap" data-tour="run-buttons">
        <Button
          onClick={() => onRun(false)}
          disabled={isRunning || pendingCount === 0}
          className="bg-[#2D3FC7] hover:bg-[#3F51B5] text-white h-9 text-[13px] gap-2 px-5 cursor-pointer font-['Roboto']"
        >
          <Play className="size-4" />
          Run All ({pendingCount})
        </Button>
        <Button
          onClick={() => onRun(true)}
          disabled={isRunning || selectedRunnable === 0}
          className="bg-[#2D3FC7] hover:bg-[#3F51B5] text-white h-9 text-[13px] gap-2 px-5 cursor-pointer"
        >
          <Play className="size-4" />
          Run Selected ({selectedRunnable})
        </Button>
                <Button
          onClick={handleSelectAll}
          disabled={isRunning}
          variant="outline"
          className="border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 h-9 text-[13px] gap-2 px-4 cursor-pointer"
        >
          {allSelected ? '✖ Deselect All' : '☑ Select All'}
          <span className="text-[11px] opacity-60">({selectedRunnable}/{pendingCount})</span>
        </Button>
        <Button
          onClick={() => onRunByPriority('smoke')}
          disabled={isRunning || smokeCount === 0}
          className="bg-orange-500 hover:bg-orange-600 text-white h-9 text-[13px] gap-2 px-4 cursor-pointer"
        >
          <Flame className="size-3.5" />
          Run Smoke ({smokeCount})
        </Button>
        <Button
          onClick={() => onRunByPriority('regression')}
          disabled={isRunning || regressionCount === 0}
          className="bg-[#2D3FC7] hover:bg-[#3F51B5] text-white h-9 text-[13px] gap-2 px-4 cursor-pointer"
        >
          <Activity className="size-3.5" />
          Run Regression ({regressionCount})
        </Button>
        {totalFailed > 0 && (
          <Button
            onClick={onRerunFailed}
            disabled={isRunning}
            variant="outline"
            className="border-orange-300 dark:border-orange-700 text-orange-600 dark:text-orange-400 hover:bg-orange-50 dark:hover:bg-orange-900/20 hover:text-orange-700 h-9 text-[13px] gap-2 px-4 cursor-pointer"
          >
            <RotateCcw className="size-3.5" />
            Rerun Failed ({totalFailed})
          </Button>
        )}
        
        <div className="flex-1" />
        <div className="flex items-center gap-4 text-[12px]">
          <span className="flex items-center gap-1 text-green-600 dark:text-green-400">
            <CheckCircle2 className="size-3.5" /> {passedCount} passed
          </span>
          <span className="flex items-center gap-1 text-red-500 dark:text-red-400">
            <XCircle className="size-3.5" /> {failedCount} failed
          </span>
          <span className="flex items-center gap-1 text-gray-400 dark:text-gray-500">
            <Circle className="size-3" /> {pendingCount} pending
          </span>
        </div>
      </div>

      {/* Priority filter pills */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-gray-100 dark:border-gray-700 shrink-0 bg-gray-50/30 dark:bg-gray-800/20">
        <span className="text-[11px] text-gray-500 dark:text-gray-400 font-medium">Priority:</span>
        <span className={`inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full ${priorityConfig.smoke.color}`}>
          <Flame className="size-2.5" /> Smoke: {tests.filter(t => t.priority === 'smoke').length}
        </span>
        <span className={`inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full ${priorityConfig.regression.color}`}>
          <Activity className="size-2.5" /> Regression: {tests.filter(t => t.priority === 'regression').length}
        </span>
        <span className={`inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full ${priorityConfig.sanity.color}`}>
          <ShieldCheck className="size-2.5" /> Sanity: {tests.filter(t => t.priority === 'sanity').length}
        </span>
      </div>

      {/* Test List by Groups */}
      <ScrollArea className="flex-1 min-h-0">
        <div className="px-4 py-3 space-y-3">
          {testGroups.map((group) => {
            const groupPassed = group.tests.filter((t) => t.status === 'passed').length
            const groupFailed = group.tests.filter((t) => t.status === 'failed').length
            const groupPending = group.tests.filter((t) => t.status === 'pending').length
            const allSelected = group.tests.every((t) => testChecks.has(t.id) || t.status !== 'pending')
            const someSelected = group.tests.some((t) => testChecks.has(t.id))

            return (
              <div key={group.name} className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                {/* Group Header */}
                <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700">
                  <Checkbox
                    checked={allSelected}
                    ref={(el) => { if (el) (el as unknown as HTMLInputElement).indeterminate = someSelected && !allSelected }}
                    onCheckedChange={() => {
                      group.tests.forEach((t) => {
                        if (t.status === 'pending') {
                          if (!testChecks.has(t.id)) toggleTestCheck(t.id)
                        }
                      })
                    }}
                    disabled={isRunning}
                    className="size-3.5"
                  />
                  <span className="text-[13px] font-semibold text-gray-700 dark:text-gray-200 flex-1">{group.name}</span>
                  <span className="text-[11px] text-gray-500 dark:text-gray-400">({group.tests.length})</span>
                  {groupPassed > 0 && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">{groupPassed} ✅</span>
                  )}
                  {groupFailed > 0 && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400">{groupFailed} ❌</span>
                  )}
                  {groupPending > 0 && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400">{groupPending} pending</span>
                  )}
                </div>
                {/* Test Rows */}
                <div className="divide-y divide-gray-100 dark:divide-gray-800">
                  {group.tests.map((test) => (
                    <div
                      key={test.id}
                      className={`flex items-center gap-2.5 px-4 py-2 hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors ${
                        test.status === 'running' ? 'bg-blue-50 dark:bg-blue-900/20' : ''
                      }`}
                    >
                      <Checkbox
                        checked={testChecks.has(test.id) || test.status === 'passed' || test.status === 'failed'}
                        disabled={isRunning || test.status !== 'pending'}
                        onCheckedChange={() => { if (test.status === 'pending') toggleTestCheck(test.id) }}
                        className="size-3.5"
                      />
                      <span className="text-[11px] text-gray-400 dark:text-gray-500 font-mono w-16 shrink-0 truncate" title={test.id}>{test.id.split('::').pop()?.replace(/^test_/, '') || test.id}</span>
                      <span className={`text-[13px] flex-1 truncate ${
                        test.status === 'running' ? 'text-indigo-600 dark:text-indigo-400 font-medium' :
                        test.status === 'failed' ? 'text-red-600 dark:text-red-400' :
                        test.status === 'passed' ? 'text-gray-500 dark:text-gray-400' :
                        'text-gray-800 dark:text-gray-100'
                      }`}>{test.name}</span>
                      <PriorityBadge priority={test.priority} />
                      <TestStatusIcon status={test.status} size={3.5} />
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </ScrollArea>
    </div>
  )
}
