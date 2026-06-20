'use client'

import React from 'react'
import { AlertTriangle, Bug, Calendar, Percent, Flag } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog'

interface ErrorDetail {
  testId: string
  message: string
  date: string
  runRate: number
}

export function ErrorDetailDialog({
  open,
  onClose,
  error,
  onReportTest,
}: {
  open: boolean
  onClose: () => void
  error: ErrorDetail | null
  onReportTest?: (testId: string, testName: string, error: string) => void
}) {
  if (!error) return null

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-[480px] dark:bg-gray-800 dark:border-gray-600/60">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <div className="size-7 rounded-lg bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
              <AlertTriangle className="size-4 text-red-600 dark:text-red-400" />
            </div>
            Error Detail
          </DialogTitle>
          <DialogDescription className="text-[12px] text-gray-500 dark:text-gray-400">
            Failed test details from run history
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
            <div className="text-[11px] text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wider mb-1">Test</div>
            <div className="text-[14px] font-semibold text-gray-800 dark:text-gray-100 break-words">{error.testId}</div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-1.5 text-[11px] text-gray-500 dark:text-gray-400 font-medium mb-1">
                <Calendar className="size-3" />
                Date
              </div>
              <div className="text-[13px] text-gray-800 dark:text-gray-200">{error.date}</div>
            </div>
            <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-1.5 text-[11px] text-gray-500 dark:text-gray-400 font-medium mb-1">
                <Percent className="size-3" />
                Run Rate
              </div>
              <div className={`text-[13px] font-semibold ${
                error.runRate >= 90 ? 'text-green-600 dark:text-green-400'
                  : error.runRate >= 75 ? 'text-yellow-600 dark:text-yellow-400'
                  : 'text-red-600 dark:text-red-400'
              }`}>{error.runRate}%</div>
            </div>
          </div>

          <div>
            <div className="text-[11px] text-gray-500 dark:text-gray-400 font-medium mb-1">Error Message</div>
            <div className="bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900/50 rounded-lg p-3">
              <div className="text-[12px] text-red-700 dark:text-red-400 font-mono leading-relaxed whitespace-pre-wrap break-words max-h-[120px] overflow-y-auto">
                {error.message}
              </div>
            </div>
          </div>
        </div>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onClose} className="cursor-pointer">
            Close
          </Button>
          <Button onClick={() => onReportTest?.(error.testId, error.testId, error.message)}
            className="cursor-pointer bg-red-600 hover:bg-red-700 text-white gap-1.5"
          >
            <Flag className="size-3.5" />
            Report Bug
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
