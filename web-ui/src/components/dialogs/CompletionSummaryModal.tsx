'use client'

import React from 'react'
import { CheckCircle2, XCircle, RotateCcw, ClipboardList, Clock, Beaker, Flag } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogTitle, DialogDescription } from '@/components/ui/dialog'

export function CompletionSummaryModal({
  open,
  onClose,
  passedCount,
  failedCount,
  totalDuration,
  moduleName,
  subModuleName,
  failedTests,
  onViewResults,
  onRerunFailed,
  onNewRun,
  onReportTest,
}: {
  open: boolean
  onClose: () => void
  passedCount: number
  failedCount: number
  totalDuration: string
  moduleName: string
  subModuleName: string
  failedTests: { testId: string; message: string }[]
  onViewResults: () => void
  onRerunFailed: () => void
  onNewRun: () => void
  onReportTest?: (testId: string, testName: string, error: string) => void
}) {
  const total = passedCount + failedCount
  const passRate = total > 0 ? Math.round((passedCount / total) * 100) : 0
  const allPassed = failedCount === 0

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-[500px] dark:bg-gray-800 dark:border-gray-600/60 p-0 gap-0">
        <DialogTitle className="sr-only">Run Complete</DialogTitle>
        <DialogDescription className="sr-only">Test run completion summary</DialogDescription>

        {/* Header */}
        <div className={`px-5 py-4 ${allPassed ? 'bg-green-50 dark:bg-green-900/15' : 'bg-red-50 dark:bg-red-900/15'} border-b border-gray-200 dark:border-gray-600/40`}>
          <div className="flex items-center gap-3">
            <div className={`size-10 rounded-full flex items-center justify-center shrink-0 ${allPassed ? 'bg-green-100 dark:bg-green-900/30' : 'bg-red-100 dark:bg-red-900/30'}`}>
              {allPassed ? <CheckCircle2 className="size-5 text-green-600 dark:text-green-400" /> : <XCircle className="size-5 text-red-600 dark:text-red-400" />}
            </div>
            <div className="min-w-0">
              <h3 className={`text-[15px] font-semibold ${allPassed ? 'text-green-800 dark:text-green-300' : 'text-red-800 dark:text-red-300'}`}>
                {allPassed ? 'All Tests Passed' : `${failedCount} Test${failedCount !== 1 ? 's' : ''} Failed`}
              </h3>
              <p className="text-[12px] text-gray-500 dark:text-gray-400 truncate">
                {subModuleName ? `${moduleName} → ${subModuleName}` : moduleName}
              </p>
            </div>
            <div className="ml-auto text-right shrink-0">
              <div className="text-[22px] font-bold text-gray-800 dark:text-gray-100">{passRate}%</div>
              <div className="text-[11px] text-gray-400 dark:text-gray-500">pass rate</div>
            </div>
          </div>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-4 border-b border-gray-200 dark:border-gray-600/40">
          <div className="px-4 py-3 text-center border-r border-gray-200 dark:border-gray-600/40">
            <div className="text-[11px] text-gray-500 dark:text-gray-400">Passed</div>
            <div className="text-[18px] font-bold text-green-600 dark:text-green-400">{passedCount}</div>
          </div>
          <div className="px-4 py-3 text-center border-r border-gray-200 dark:border-gray-600/40">
            <div className="text-[11px] text-gray-500 dark:text-gray-400">Failed</div>
            <div className={`text-[18px] font-bold ${failedCount > 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-400'}`}>{failedCount}</div>
          </div>
          <div className="px-4 py-3 text-center border-r border-gray-200 dark:border-gray-600/40">
            <div className="text-[11px] text-gray-500 dark:text-gray-400">Total</div>
            <div className="text-[18px] font-bold text-gray-700 dark:text-gray-200">{total}</div>
          </div>
          <div className="px-4 py-3 text-center">
            <div className="text-[11px] text-gray-500 dark:text-gray-400">Duration</div>
            <div className="flex items-center justify-center gap-1 text-[18px] font-bold text-gray-700 dark:text-gray-200">
              <Clock className="size-3.5 text-gray-400" />
              {totalDuration}
            </div>
          </div>
        </div>

        {/* Failed tests list */}
        {failedTests.length > 0 && (
          <div className="max-h-[180px] overflow-y-auto border-b border-gray-200 dark:border-gray-600/40">
            <div className="px-4 py-2 text-[11px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider border-b border-gray-100 dark:border-gray-700/40 bg-gray-50 dark:bg-gray-800/50">
              Failed Tests
            </div>
            {failedTests.map((ft) => (
              <div key={ft.testId} className="px-4 py-2.5 border-b border-gray-100 dark:border-gray-700/40 last:border-0 group">
                <div className="flex items-start gap-2">
                  <Beaker className="size-3.5 text-red-500 shrink-0 mt-0.5" />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-[12px] font-medium text-gray-700 dark:text-gray-200 truncate">{ft.testId}</span>
                      <button onClick={() => onReportTest?.(ft.testId, ft.testId, ft.message)}
                        className="shrink-0 size-5 flex items-center justify-center rounded text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 cursor-pointer"
                        title="Report bug"
                      >
                        <Flag className="size-3" />
                      </button>
                    </div>
                    <div className="text-[11px] text-red-600 dark:text-red-400 font-mono leading-tight mt-0.5 break-words">{ft.message}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2 px-4 py-3">
          <Button onClick={onViewResults} variant="outline" size="sm" className="h-8 text-[12px] gap-1.5 cursor-pointer flex-1 border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300">
            <ClipboardList className="size-3.5" />
            Results
          </Button>
          {failedCount > 0 && (
            <Button onClick={onRerunFailed} size="sm" className="h-8 text-[12px] gap-1.5 cursor-pointer flex-1 bg-orange-500 hover:bg-orange-600 text-white">
              <RotateCcw className="size-3.5" />
              Rerun Failed
            </Button>
          )}
          <Button onClick={onNewRun} size="sm" className="h-8 text-[12px] gap-1.5 cursor-pointer flex-1 bg-[#2D3FC7] hover:bg-[#3F51B5] text-white">
            <RotateCcw className="size-3.5" />
            New Run
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
