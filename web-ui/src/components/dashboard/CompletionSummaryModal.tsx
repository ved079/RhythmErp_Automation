import React from 'react';

export default function CompletionSummaryModal({
  open,
  onClose,
  passedCount,
  failedCount,
  totalDuration,
  onViewResults,
  onRerunFailed,
  onNewRun,
}: {
  open: boolean
  onClose: () => void
  passedCount: number
  failedCount: number
  totalDuration: string
  onViewResults: () => void
  onRerunFailed: () => void
  onNewRun: () => void
}) {
  const total = passedCount + failedCount
  const passRate = total > 0 ? Math.round((passedCount / total) * 100) : 0
  const allPassed = failedCount === 0

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-[460px] dark:bg-gray-800 dark:border-gray-700">
        <DialogHeader>
          <DialogTitle className="sr-only">Run Complete</DialogTitle>
          <DialogDescription className="sr-only">Test run completion summary</DialogDescription>
        </DialogHeader>

        {/* Header */}
        <div className={`rounded-lg p-4 text-center ${allPassed ? 'bg-green-50 dark:bg-green-900/20' : 'bg-orange-50 dark:bg-orange-900/20'}`}>
          <div className="flex justify-center mb-2">
            {allPassed ? (
              <div className="w-14 h-14 rounded-full bg-green-100 dark:bg-green-900/40 flex items-center justify-center">
                <CheckCircle2 className="size-8 text-green-600 dark:text-green-400" />
              </div>
            ) : (
              <div className="w-14 h-14 rounded-full bg-orange-100 dark:bg-orange-900/40 flex items-center justify-center">
                <AlertTriangle className="size-8 text-orange-600 dark:text-orange-400" />
              </div>
            )}
          </div>
          <h3 className={`text-[18px] font-bold ${allPassed ? 'text-green-700 dark:text-green-400' : 'text-orange-700 dark:text-orange-400'}`}>
            {allPassed ? 'All Tests Passed!' : 'Tests Completed with Failures'}
          </h3>
          <p className="text-[13px] text-gray-500 dark:text-gray-400 mt-1">
            {allPassed ? 'Congratulations! Every test in this run passed successfully.' : `${failedCount} test${failedCount !== 1 ? 's' : ''} failed. Review results for details.`}
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 text-center border border-green-100 dark:border-green-800/50">
            <div className="text-[11px] text-green-600 dark:text-green-400 font-medium uppercase">Passed</div>
            <div className="text-2xl font-bold text-green-700 dark:text-green-400 mt-1">{passedCount}</div>
          </div>
          <div className={`rounded-lg p-3 text-center border ${failedCount > 0 ? 'bg-red-50 dark:bg-red-900/20 border-red-100 dark:border-red-800/50' : 'bg-gray-50 dark:bg-gray-800 border-gray-100 dark:border-gray-700'}`}>
            <div className={`text-[11px] font-medium uppercase ${failedCount > 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-500 dark:text-gray-400'}`}>Failed</div>
            <div className={`text-2xl font-bold mt-1 ${failedCount > 0 ? 'text-red-700 dark:text-red-400' : 'text-gray-500 dark:text-gray-400'}`}>{failedCount}</div>
          </div>
          <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 text-center border border-gray-100 dark:border-gray-700">
            <div className="text-[11px] text-gray-500 dark:text-gray-400 font-medium uppercase">Duration</div>
            <div className="text-lg font-bold text-gray-800 dark:text-gray-100 mt-1">{totalDuration}</div>
          </div>
        </div>

        {/* Pass Rate */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-[12px]">
            <span className="text-gray-600 dark:text-gray-300 font-medium">Pass Rate</span>
            <span className={`font-bold ${passRate === 100 ? 'text-green-600 dark:text-green-400' : passRate >= 75 ? 'text-orange-600 dark:text-orange-400' : 'text-red-600 dark:text-red-400'}`}>
              {passRate}%
            </span>
          </div>
          <Progress value={passRate} className="h-2.5" />
        </div>

        {/* Actions */}
        <DialogFooter className="flex-col sm:flex-row gap-2 pt-2">
          <Button onClick={onViewResults} variant="outline" className="flex-1 h-9 text-[13px] gap-2 border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 cursor-pointer">
            <ClipboardList className="size-4" />
            View Results
          </Button>
          {failedCount > 0 && (
            <Button onClick={onRerunFailed} className="flex-1 h-9 text-[13px] gap-2 bg-orange-500 hover:bg-orange-600 text-white cursor-pointer">
              <RotateCcw className="size-4" />
              Rerun Failed
            </Button>
          )}
          <Button onClick={onNewRun} className="flex-1 h-9 text-[13px] gap-2 bg-[#1976d2] hover:bg-[#1565c0] text-white cursor-pointer">
            <RotateCcw className="size-4" />
            New Run
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// â”€â”€â”€ RESULTS TAB â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

// â”€â”€â”€ NAV TOAST â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function NavToast({ label, parent }: { label: string; parent?: string | null }) {
  const [visible, setVisible] = useState(true)
  const [fading, setFading] = useState(false)

  useEffect(() => {
    const fadeTimer = setTimeout(() => setFading(true), 1200)
    const hideTimer = setTimeout(() => setVisible(false), 1600)
    return () => { clearTimeout(fadeTimer); clearTimeout(hideTimer) }
  }, [])

  if (!visible) return null
