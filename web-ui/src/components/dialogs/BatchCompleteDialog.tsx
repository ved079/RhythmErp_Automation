'use client'

import React from 'react'
import { CheckCircle2, AlertTriangle, Download } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}m ${s}s`
}

interface Props {
  open: boolean
  onClose: () => void
  created: number
  failed: number
  elapsedSeconds: number
  onDownload: () => void
}

export function BatchCompleteDialog({ open, onClose, created, failed, elapsedSeconds, onDownload }: Props) {
  const allPassed = failed === 0
  const total = created + failed

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-[400px] dark:bg-gray-800 dark:border-gray-700">
        <DialogHeader>
          <DialogTitle className="sr-only">Batch Complete</DialogTitle>
          <DialogDescription className="sr-only">Batch data creation summary</DialogDescription>
        </DialogHeader>

        <div className={`rounded-lg p-4 text-center ${allPassed ? 'bg-emerald-50 dark:bg-emerald-900/20' : 'bg-amber-50 dark:bg-amber-900/20'}`}>
          <div className="flex justify-center mb-2">
            {allPassed ? (
              <div className="w-14 h-14 rounded-full bg-emerald-100 dark:bg-emerald-900/40 flex items-center justify-center">
                <CheckCircle2 className="size-8 text-emerald-600 dark:text-emerald-400" />
              </div>
            ) : (
              <div className="w-14 h-14 rounded-full bg-amber-100 dark:bg-amber-900/40 flex items-center justify-center">
                <AlertTriangle className="size-8 text-amber-600 dark:text-amber-400" />
              </div>
            )}
          </div>
          <h3 className={`text-[17px] font-bold ${allPassed ? 'text-emerald-700 dark:text-emerald-400' : 'text-amber-700 dark:text-amber-400'}`}>
            {allPassed ? `${total} Record${total !== 1 ? 's' : ''} Created` : 'Completed with Failures'}
          </h3>
          <p className="text-[13px] text-gray-500 dark:text-gray-400 mt-1">
            {allPassed
              ? 'All records were created successfully in the ERP.'
              : `${failed} record${failed !== 1 ? 's' : ''} failed out of ${total}.`}
          </p>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div className="bg-emerald-50 dark:bg-emerald-900/20 rounded-lg p-3 text-center border border-emerald-100 dark:border-emerald-800/50">
            <div className="text-[11px] text-emerald-600 dark:text-emerald-400 font-medium uppercase">Created</div>
            <div className="text-2xl font-bold text-emerald-700 dark:text-emerald-300 mt-1">{created}</div>
          </div>
          <div className={`rounded-lg p-3 text-center border ${failed > 0 ? 'bg-red-50 dark:bg-red-900/20 border-red-100 dark:border-red-800/50' : 'bg-gray-50 dark:bg-gray-800 border-gray-100 dark:border-gray-700'}`}>
            <div className={`text-[11px] font-medium uppercase ${failed > 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-400 dark:text-gray-500'}`}>Failed</div>
            <div className={`text-2xl font-bold mt-1 ${failed > 0 ? 'text-red-700 dark:text-red-400' : 'text-gray-400 dark:text-gray-500'}`}>{failed}</div>
          </div>
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 text-center border border-gray-100 dark:border-gray-700">
            <div className="text-[11px] text-gray-500 dark:text-gray-400 font-medium uppercase">Duration</div>
            <div className="text-lg font-bold text-gray-800 dark:text-gray-100 mt-1">{formatDuration(elapsedSeconds)}</div>
          </div>
        </div>

        {created > 0 && (
          <Button
            onClick={onDownload}
            className="w-full h-10 text-[13px] bg-emerald-600 hover:bg-emerald-700 cursor-pointer gap-2"
          >
            <Download className="size-4" />
            Download Excel
          </Button>
        )}
      </DialogContent>
    </Dialog>
  )
}
