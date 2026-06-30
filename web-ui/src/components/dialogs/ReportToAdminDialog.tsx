'use client'

import React, { useState, useEffect, useCallback } from 'react'
import Image from 'next/image'
import { Bug, Send, AlertTriangle, CheckCircle2, MessageSquare, Clock, Loader2 } from 'lucide-react'
import Spinner from '@/components/ui/Spinner'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog'
import { addBugReport, checkDuplicateBugReport, type BugReport } from '@/lib/bug-reports'
import { TicketChat } from '@/components/tickets/TicketChat'
import { toast } from 'sonner'

const priorityColors: Record<string, string> = {
  low: 'bg-green-500',
  medium: 'bg-orange-500',
  high: 'bg-red-500',
}

const statusColors: Record<string, string> = {
  open: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400',
  'in-progress': 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
  fixed: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
  closed: 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400',
  rejected: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400',
}

const statusLabels: Record<string, string> = {
  open: 'Open', 'in-progress': 'In Progress', fixed: 'Fixed', closed: 'Closed', rejected: 'Rejected',
}

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
  const [existingReport, setExistingReport] = useState<BugReport | null>(null)
  const [checking, setChecking] = useState(false)

  useEffect(() => {
    if (open) {
      setNote('')
      setPriority('medium')
      setExistingReport(null)
      setChecking(true)
      checkDuplicateBugReport(testId).then((result) => {
        if (result.exists) {
          setExistingReport(result.bugReport)
        }
      }).finally(() => {
        setChecking(false)
      })
    }
  }, [open, testId])

  const handleSend = useCallback(async () => {
    setSending(true)
    try {
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
        toast.custom((t) => (
          <div className="relative overflow-hidden w-[360px] p-3 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-lg">
            <Image
              src="/agdi-logo-new.png"
              alt=""
              width={120}
              height={120}
              className="absolute -top-6 -right-6 opacity-[0.06] dark:opacity-[0.10] blur-sm select-none pointer-events-none"
            />
            <div className="relative z-10 flex items-start gap-3">
              <div className="bg-emerald-100 dark:bg-emerald-900/40 size-8 rounded-lg flex items-center justify-center shrink-0">
                <CheckCircle2 className="size-5 text-emerald-600 dark:text-emerald-400" />
              </div>
              <div className="flex-1 min-w-0">
                <span className="text-[13px] font-semibold text-gray-900 dark:text-gray-100">Bug report sent</span>
                <p className="text-[12px] text-gray-500 dark:text-gray-400 mt-0.5 truncate">{testDescription}</p>
                <p className="text-[11px] text-gray-400 dark:text-gray-500 mt-0.5 font-mono">{testId}</p>
              </div>
            </div>
          </div>
        ), { duration: 4000 })
      } catch (e) {
        setSending(false)
        toast.error('Failed to send bug report', {
          description: e instanceof Error ? e.message : 'Unknown error',
          duration: 5000,
        })
      }
    }, [testId, testDescription, moduleName, error, note, priority, userName, userEmail, onClose])

  const handleReplySent = useCallback((updated: BugReport) => {
    setExistingReport(updated)
  }, [])

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className={`${existingReport ? 'sm:max-w-[640px] max-h-[85vh]' : 'sm:max-w-[500px]'} dark:bg-gray-800 dark:border-gray-600/60 p-0 gap-0`}>
        {checking ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="size-6 animate-spin text-[#3F51B5]" />
          </div>
        ) : existingReport ? (
          <>
            <DialogHeader className="px-5 pt-4 pb-0 shrink-0">
              <div className="flex items-start gap-3">
                <div className="size-9 rounded-xl bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center shrink-0 mt-0.5">
                  <MessageSquare className="size-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <DialogTitle className="text-[14px] font-semibold text-gray-900 dark:text-gray-100">
                    Already Reported
                  </DialogTitle>
                  <DialogDescription className="text-[12px] text-gray-500 dark:text-gray-400 mt-0.5">
                    You already reported this test. Chat with the admin or wait for a response.
                  </DialogDescription>
                </div>
              </div>
            </DialogHeader>
            <div className="px-5 pt-3 pb-0 shrink-0">
              <div className="flex items-center gap-2.5 bg-gray-50 dark:bg-gray-900/30 rounded-lg px-3.5 py-2.5 border border-gray-200 dark:border-gray-700/60">
                <span className="text-[12px] font-mono font-bold text-[#3F51B5] dark:text-[#7986CB]">
                  #{existingReport.id.slice(0, 8).toUpperCase()}
                </span>
                <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${statusColors[existingReport.status]}`}>
                  {statusLabels[existingReport.status]}
                </span>
                <span className={`size-2 rounded-full ${priorityColors[existingReport.priority]} shrink-0`} />
                <span className="text-[11px] text-gray-500 dark:text-gray-400 capitalize">{existingReport.priority} priority</span>
              </div>
            </div>
            <div className="flex-1 min-h-0 overflow-hidden" style={{ height: 350 }}>
              <TicketChat
                key={existingReport.id}
                bugReport={existingReport}
                userName={userName}
                userRole="user"
                onReplySent={handleReplySent}
              />
            </div>
            <DialogFooter className="px-5 py-3 bg-gray-50 dark:bg-gray-900/30 border-t border-gray-200 dark:border-gray-700/60 shrink-0">
              <Button variant="ghost" onClick={onClose} className="cursor-pointer text-[12px] text-gray-600 dark:text-gray-400">
                Close
              </Button>
            </DialogFooter>
          </>
        ) : (
          <>
            <DialogHeader className="px-6 pt-5 pb-0">
              <div className="flex items-start gap-3">
                <div className="size-10 rounded-xl bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center shrink-0 mt-0.5">
                  <Bug className="size-5 text-orange-600 dark:text-orange-400" />
                </div>
                <div>
                  <DialogTitle className="text-[16px] font-semibold text-gray-900 dark:text-gray-100">
                    Report Issue
                  </DialogTitle>
                  <DialogDescription className="text-[12px] text-gray-500 dark:text-gray-400 mt-0.5">
                    Send a bug report about this test failure to the automation team.
                  </DialogDescription>
                </div>
              </div>
            </DialogHeader>

            <div className="px-6 py-5 space-y-4">
              <div className="grid grid-cols-[80px_1fr] gap-x-3 gap-y-2 text-[12px] bg-gray-50 dark:bg-gray-900/30 rounded-lg px-4 py-3 border border-gray-200 dark:border-gray-700/60">
                <span className="text-gray-500 dark:text-gray-400 font-medium leading-6">Test</span>
                <span className="text-gray-800 dark:text-gray-100 font-semibold leading-6 truncate">{testId}</span>
                <span className="text-gray-500 dark:text-gray-400 font-medium leading-5">Module</span>
                <span className="text-gray-700 dark:text-gray-300 leading-5">{moduleName}</span>
              </div>

              {error && (
                <div className="flex items-start gap-2.5 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/50 rounded-lg px-3.5 py-2.5">
                  <AlertTriangle className="size-4 text-red-500 shrink-0 mt-0.5" />
                  <span className="text-[12px] text-red-700 dark:text-red-400 font-mono leading-relaxed">{error}</span>
                </div>
              )}

              <div className="space-y-1.5">
                <Label className="text-[12px] text-gray-700 dark:text-gray-300 font-medium">
                  Notes <span className="text-gray-400 font-normal">(optional)</span>
                </Label>
                <textarea
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 text-[12px] rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700/50 text-gray-800 dark:text-gray-100 resize-none focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 placeholder:text-gray-400 dark:placeholder:text-gray-500 transition-shadow"
                  placeholder="Describe what happened or any context that might help..."
                />
              </div>

              <div className="space-y-1.5">
                <Label className="text-[12px] text-gray-700 dark:text-gray-300 font-medium">Priority</Label>
                <div className="flex gap-2">
                  {(['low', 'medium', 'high'] as const).map((p) => (
                    <button
                      key={p}
                      onClick={() => setPriority(p)}
                      className={`flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-[12px] font-medium transition-all cursor-pointer border ${
                        priority === p
                          ? 'border-gray-300 dark:border-gray-500 bg-white dark:bg-gray-700 shadow-sm'
                          : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/30 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                      }`}
                    >
                      <span className={`size-2 rounded-full ${priorityColors[p]} ${priority === p ? '' : 'opacity-40'}`} />
                      {p === 'high' ? 'High' : p === 'medium' ? 'Medium' : 'Low'}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <DialogFooter className="px-6 py-4 bg-gray-50 dark:bg-gray-900/30 border-t border-gray-200 dark:border-gray-700/60 gap-2">
              <Button variant="ghost" onClick={onClose} className="cursor-pointer text-[12px] text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200">
                Cancel
              </Button>
              <Button onClick={handleSend} disabled={sending} className="cursor-pointer text-[12px] gap-1.5 bg-orange-500 hover:bg-orange-600 text-white shadow-sm">
                {sending ? <Loader2 className="size-3.5 animate-spin" /> : <Send className="size-3.5" />}
                {sending ? 'Sending...' : 'Send Report'}
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
