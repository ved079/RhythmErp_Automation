'use client'

import React, { useState, useEffect } from 'react'
import { BarChart3, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog'
import type { RunSnapshot } from '@/lib/types'
import { TestStatusIcon } from '@/components/shared/PriorityBadge'

export function RunDetailDialog({
  open,
  onClose,
  run,
}: {
  open: boolean
  onClose: () => void
  run: RunSnapshot | null
}) {
  const [runDetail, setRunDetail] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!open || !run) return
    let cancelled = false
    // Use a microtask to avoid synchronous setState in effect
    const loadDetail = async () => {
      setLoading(true)
      setRunDetail(null)
      try {
        const detail = await fetch(`/api/runs/${run.id}`).then(r => r.ok ? r.json() : null)
        if (!cancelled) setRunDetail(detail)
      } catch {
        if (!cancelled) setRunDetail(null)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    loadDetail()
    return () => { cancelled = true }
  }, [open, run])

  if (!run) return null

  const passRate = run.total > 0 ? Math.round((run.passed / run.total) * 100) : 0

  // Build test results from either full API detail or from the run snapshot
  const testResults = runDetail?.results?.map((r) => ({
    id: r.name,
    name: r.name.split('::').pop() || r.name,
    status: r.status,
    duration: r.duration ? `${(r.duration / 1000).toFixed(1)}s` : '—',
    message: r.message,
  })) ?? run.results.map((r) => ({
    id: r.testId,
    name: r.testId,
    status: r.status === 'passed' ? 'passed' as const : 'failed' as const,
    duration: '—',
    message: null as string | null,
  }))

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="max-w-[700px] max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <BarChart3 className="size-5 text-[#3F51B5]" />
            Run Details
          </DialogTitle>
          <DialogDescription className="text-[13px] text-gray-500 dark:text-gray-400">
            {run.date}
          </DialogDescription>
        </DialogHeader>

        {/* Run Metadata */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3 text-center">
            <div className="text-[11px] text-gray-500 dark:text-gray-400 font-medium uppercase">Date</div>
            <div className="text-[13px] text-gray-800 dark:text-gray-200 font-medium mt-0.5">{run.date}</div>
          </div>
          <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3 text-center">
            <div className="text-[11px] text-gray-500 dark:text-gray-400 font-medium uppercase">Duration</div>
            <div className="text-[13px] text-gray-800 dark:text-gray-200 font-mono mt-0.5">{run.duration}</div>
          </div>
          <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3 text-center">
            <div className="text-[11px] text-gray-500 dark:text-gray-400 font-medium uppercase">Pass Rate</div>
            <div className="text-[13px] font-bold mt-0.5">
              <span className={
                passRate >= 90 ? 'text-green-600 dark:text-green-400'
                  : passRate >= 75 ? 'text-yellow-600 dark:text-yellow-400'
                    : 'text-red-600 dark:text-red-400'
              }>
                {passRate}%
              </span>
            </div>
          </div>
          <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3 text-center">
            <div className="text-[11px] text-gray-500 dark:text-gray-400 font-medium uppercase">Total Tests</div>
            <div className="text-[13px] text-gray-800 dark:text-gray-200 font-medium mt-0.5">{run.total}</div>
            <div className="text-[10px] text-gray-400 dark:text-gray-500">
              <span className="text-green-600 dark:text-green-400">{run.passed} passed</span>
              {' / '}
              <span className="text-red-600 dark:text-red-400">{run.failed} failed</span>
            </div>
          </div>
        </div>

        <Separator />

        {/* Full Test Results Table */}
        <div>
          <h4 className="text-[13px] font-semibold text-gray-800 dark:text-gray-100 mb-2">
            Test Results ({testResults.length})
          </h4>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="size-5 text-[#3F51B5] animate-spin" />
              <span className="ml-2 text-[13px] text-gray-500 dark:text-gray-400">Loading details...</span>
            </div>
          ) : testResults.length === 0 ? (
            <div className="text-center py-6 text-[12px] text-gray-400 dark:text-gray-500">
              No test results available for this run
            </div>
          ) : (
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden max-h-72 overflow-y-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-[#DFE9FB] dark:bg-indigo-900/30 hover:bg-[#DFE9FB] dark:hover:bg-indigo-900/30">
                    <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 w-10">Status</TableHead>
                    <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300">Test ID / Name</TableHead>
                    <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 w-20 text-center">Duration</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {testResults.map((t) => (
                    <TableRow key={t.id} className="dark:border-gray-700">
                      <TableCell>
                        <TestStatusIcon status={t.status} size={3.5} />
                      </TableCell>
                      <TableCell className="text-[12px]">
                        <div className="font-mono text-gray-500 dark:text-gray-400 text-[11px]">{t.id}</div>
                        {t.name !== t.id && (
                          <div className="text-gray-700 dark:text-gray-200">{t.name}</div>
                        )}
                        {t.message && (
                          <div className="text-red-500 dark:text-red-400 text-[11px] mt-0.5 truncate max-w-[350px]">{t.message}</div>
                        )}
                      </TableCell>
                      <TableCell className="text-center text-[12px] font-mono text-gray-500 dark:text-gray-400">{t.duration}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} className="cursor-pointer">
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
