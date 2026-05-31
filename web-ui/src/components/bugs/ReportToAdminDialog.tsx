'use client'

import React, { useState, useCallback, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { MessageSquare, Send, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { addBugReport } from '@/lib/bug-reports'

// ─── REPORT TO ADMIN DIALOG ──────────────────────────────
export function ReportToAdminDialog({
  open,
  onClose,
  testId,
  testDescription,
  error,
  moduleName,
  userName,
  userEmail,
}: {
  open: boolean
  onClose: () => void
  testId: string
  testDescription: string
  error?: string
  moduleName: string
  userName: string
  userEmail: string
}) {
  const [note, setNote] = useState('')
  const [priority, setPriority] = useState<'low' | 'medium' | 'high'>('medium')
  const [sending, setSending] = useState(false)

  const handleSend = useCallback(() => {
    setSending(true)
    setTimeout(async () => {
      await addBugReport({
        testId,
        testDescription,
        moduleName,
        error: error || 'Unknown error',
        userNote: note,
        priority,
        reporterName: userName,
        reporterEmail: userEmail,
      })
      setSending(false)
      setNote('')
      setPriority('medium')
      onClose()
      toast.success(`Bug report sent to admin`, {
        description: `${testId} — ${testDescription}`,
        duration: 4000,
      })
    }, 500)
  }, [testId, testDescription, moduleName, error, note, priority, userName, userEmail, onClose])

  useEffect(() => {
    const reset = () => { setNote(''); setPriority('medium') }
    if (open) reset()
  }, [open])

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-[480px] dark:bg-gray-800 dark:border-gray-700">
        <DialogHeader>
          <DialogTitle className="text-[16px] flex items-center gap-2">
            <MessageSquare className="size-5 text-orange-500" />
            Report Issue to Admin
          </DialogTitle>
          <DialogDescription>
            Send a bug report about this test failure to the automation team.
          </DialogDescription>
        </DialogHeader>

        {/* Pre-filled error info */}
        <div className="bg-red-50 dark:bg-red-900/15 rounded-lg p-3 border border-red-100 dark:border-red-800/40 space-y-1.5">
          <div className="flex items-center gap-2 text-[12px]">
            <span className="text-gray-500 dark:text-gray-400 w-16 shrink-0">Test ID</span>
            <span className="font-mono font-semibold text-gray-800 dark:text-gray-100">{testId}</span>
            <span className="text-gray-400 dark:text-gray-500">—</span>
            <span className="text-gray-700 dark:text-gray-200">{testDescription}</span>
          </div>
          <div className="flex items-center gap-2 text-[12px]">
            <span className="text-gray-500 dark:text-gray-400 w-16 shrink-0">Module</span>
            <span className="text-gray-700 dark:text-gray-200">{moduleName}</span>
          </div>
          {error && (
            <div className="flex items-start gap-2 text-[12px]">
              <span className="text-gray-500 dark:text-gray-400 w-16 shrink-0">Error</span>
              <span className="text-red-600 dark:text-red-400 break-all">{error}</span>
            </div>
          )}
        </div>

        {/* User note */}
        <div className="space-y-1.5">
          <Label className="text-[12px] text-gray-700 dark:text-gray-300 font-medium">
            Additional Notes <span className="text-gray-400 font-normal">(optional)</span>
          </Label>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            rows={3}
            className="w-full px-3 py-2 text-[12px] rounded-md border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/50 text-gray-800 dark:text-gray-100 resize-none focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 placeholder:text-gray-400 dark:placeholder:text-gray-500"
            placeholder="Describe what happened or any context that might help..."
          />
        </div>

        {/* Priority */}
        <div className="space-y-1.5">
          <Label className="text-[12px] text-gray-700 dark:text-gray-300 font-medium">Priority</Label>
          <div className="flex gap-2">
            {(['low', 'medium', 'high'] as const).map((p) => (
              <button
                key={p}
                onClick={() => setPriority(p)}
                className={`flex-1 px-3 py-2 rounded-md text-[12px] font-medium transition-all cursor-pointer border ${
                  priority === p
                    ? p === 'high'
                      ? 'bg-red-100 dark:bg-red-900/30 border-red-300 dark:border-red-700 text-red-700 dark:text-red-400 ring-1 ring-red-200 dark:ring-red-800'
                      : p === 'medium'
                        ? 'bg-orange-100 dark:bg-orange-900/30 border-orange-300 dark:border-orange-700 text-orange-700 dark:text-orange-400 ring-1 ring-orange-200 dark:ring-orange-800'
                        : 'bg-green-100 dark:bg-green-900/30 border-green-300 dark:border-green-700 text-green-700 dark:text-green-400 ring-1 ring-green-200 dark:ring-green-800'
                    : 'border-gray-200 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'
                }`}
              >
                {p === 'high' ? '🔴 High' : p === 'medium' ? '🟡 Medium' : '🟢 Low'}
              </button>
            ))}
          </div>
        </div>

        <DialogFooter className="gap-2 pt-1">
          <Button onClick={onClose} className="cursor-pointer text-[12px] bg-transparent text-[#F44336] hover:bg-red-50">Cancel</Button>
          <Button onClick={handleSend} disabled={sending} className="bg-orange-500 hover:bg-orange-600 text-white cursor-pointer text-[12px] gap-1.5">
            {sending ? <Loader2 className="size-3.5 animate-spin" /> : <Send className="size-3.5" />}
            {sending ? 'Sending...' : 'Send Report'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
