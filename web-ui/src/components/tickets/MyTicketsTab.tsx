'use client'

import React, { useState, useEffect, useCallback, useMemo } from 'react'
import { RefreshCw, Filter, Ticket, Play, CheckCircle2, RotateCcw, MessageSquare, Send, Timer, FlaskConical, XCircle, ShieldCheck, Loader2 } from 'lucide-react'
import Spinner from '@/components/ui/Spinner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { toast } from 'sonner'
import {
  getBugReports, addReplyToReport, markReportReadByUser, updateBugReportStatus,
  getSLAStatus, getSLADeadline, type BugReport,
} from '@/lib/bug-reports'
import { ChatListView } from './ChatListView'

export function MyTicketsTab({
  userEmail,
  userName,
  onVerifyFix,
  verifyingTicketId,
  verifyResult,
}: {
  userEmail: string
  userName: string
  onVerifyFix?: (ticket: BugReport) => void
  verifyingTicketId?: string | null
  verifyResult?: { ticketId: string; passed: boolean } | null
}) {
  const [subTab, setSubTab] = useState<'tickets' | 'chats'>('tickets')
  const [allReports, setAllReports] = useState<BugReport[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<'all' | 'open' | 'in-progress' | 'fixed'>('all')
  const [priorityFilter, setPriorityFilter] = useState<'all' | 'high' | 'medium' | 'low'>('all')
  const [selectedTicket, setSelectedTicket] = useState<BugReport | null>(null)
  const [replyText, setReplyText] = useState('')
  const [sendingReply, setSendingReply] = useState(false)

  const loadReports = useCallback(async () => {
    setLoading(true)
    try {
      const reports = await getBugReports()
      setAllReports(reports.filter((r) => r.reporterEmail === userEmail))
    } catch {
      // silent
    } finally {
      setLoading(false)
    }
  }, [userEmail])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadReports()
  }, [loadReports])

  // Mark as read when opening detail
  useEffect(() => {
    if (selectedTicket && !selectedTicket.readByUser) {
      markReportReadByUser(selectedTicket.id).then(() => {
        setAllReports((prev) =>
          prev.map((r) => (r.id === selectedTicket.id ? { ...r, readByUser: true } : r))
        )
        setSelectedTicket((prev) => (prev ? { ...prev, readByUser: true } : prev))
      })
    }
  }, [selectedTicket])

  const filteredReports = useMemo(() => {
    return allReports.filter((r) => {
      if (statusFilter !== 'all' && r.status !== statusFilter) return false
      if (priorityFilter !== 'all' && r.priority !== priorityFilter) return false
      return true
    })
  }, [allReports, statusFilter, priorityFilter])

  const unreadChatCount = useMemo(() =>
    allReports.filter(r => !r.readByUser && (r.replies.length > 0 || r.status === 'open' || r.status === 'in-progress')).length,
  [allReports])

  const handleSendReply = useCallback(async () => {
    if (!selectedTicket || !replyText.trim()) return
    setSendingReply(true)
    try {
      const updated = await addReplyToReport(selectedTicket.id, {
        authorName: userName,
        authorRole: 'user',
        message: replyText.trim(),
      })
      if (updated) {
        setSelectedTicket(updated)
        setAllReports((prev) => prev.map((r) => (r.id === updated.id ? updated : r)))
      }
      setReplyText('')
    } catch {
      toast.error('Failed to send reply')
    } finally {
      setSendingReply(false)
    }
  }, [selectedTicket, replyText, userName])

  const handleStatusChange = useCallback(async (newStatus: BugReport['status']) => {
    if (!selectedTicket) return
    try {
      const updated = await updateBugReportStatus(selectedTicket.id, newStatus)
      if (updated) {
        setSelectedTicket(updated)
        setAllReports((prev) => prev.map((r) => (r.id === updated.id ? updated : r)))
        toast.success(`Status updated to ${newStatus === 'in-progress' ? 'In Progress' : newStatus === 'fixed' ? 'Fixed' : 'Open'}`)
      }
    } catch {
      toast.error('Failed to update status')
    }
  }, [selectedTicket])

  const priorityBadge = (p: BugReport['priority']) => {
    const colors = {
      high: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400',
      medium: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400',
      low: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
    }
    return (
      <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${colors[p]}`}>
        {p.charAt(0).toUpperCase() + p.slice(1)}
      </span>
    )
  }

  const statusBadge = (s: BugReport['status']) => {
    const styles: Record<string, string> = {
      open: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400',
      'in-progress': 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
      fixed: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
      closed: 'bg-gray-100 dark:bg-gray-700/50 text-gray-600 dark:text-gray-400',
      rejected: 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400',
    }
    const labels: Record<string, string> = { open: 'Open', 'in-progress': 'In Progress', fixed: 'Fixed by Admin', closed: 'Closed', rejected: 'Rejected' }
    return (
      <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${styles[s] ?? styles.open}`}>
        {labels[s] ?? s}
      </span>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="size-6 text-[#3F51B5] animate-spin" />
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Sub-tab bar */}
      <div className="flex items-center gap-0 px-5 pt-4 pb-0 shrink-0 border-b border-gray-200 dark:border-gray-700">
        <button
          onClick={() => setSubTab('tickets')}
          className={`px-4 py-2 text-[13px] font-medium border-b-2 transition-colors cursor-pointer ${
            subTab === 'tickets'
              ? 'border-[#3F51B5] text-[#3F51B5] dark:text-[#7986CB]'
              : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
        >
          All Tickets
        </button>
        <button
          onClick={() => setSubTab('chats')}
          className={`px-4 py-2 text-[13px] font-medium border-b-2 transition-colors cursor-pointer flex items-center gap-1.5 ${
            subTab === 'chats'
              ? 'border-[#3F51B5] text-[#3F51B5] dark:text-[#7986CB]'
              : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
        >
          Chats
          {unreadChatCount > 0 && (
            <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-[#3F51B5] text-white leading-none">
              {unreadChatCount}
            </span>
          )}
        </button>
      </div>

      {subTab === 'chats' ? (
        <div className="flex-1 min-h-0 p-4">
          <ChatListView
            reports={allReports}
            userName={userName}
            userRole="user"
            onReportsChange={setAllReports}
          />
        </div>
      ) : (
      <div className="flex-1 flex flex-col min-h-0">
        <div className="p-5 pb-1 shrink-0">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-[18px] font-semibold text-[#333333] dark:text-gray-100">My Tickets</h2>
              <p className="text-[13px] text-[#666666] dark:text-gray-400 mt-0.5">
                Track and manage your bug reports • {allReports.length} ticket{allReports.length !== 1 ? 's' : ''}
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={loadReports}
              className="text-[12px] gap-1.5 cursor-pointer"
            >
              <RefreshCw className="size-3.5" />
              Refresh
            </Button>
          </div>

          <div className="flex items-center gap-3 flex-wrap mt-3">
            <div className="flex items-center gap-1">
              <Filter className="size-3.5 text-[#888888] dark:text-gray-400" />
              <span className="text-[12px] text-[#888888] dark:text-gray-400 font-medium mr-1">Status:</span>
              {(['all', 'open', 'in-progress', 'fixed'] as const).map((s) => {
                const labels: Record<string, string> = { all: 'All', open: 'Open', 'in-progress': 'In Progress', fixed: 'Fixed' }
                const count = s === 'all' ? allReports.length : allReports.filter((r) => r.status === s).length
                return (
                  <button
                    key={s}
                    onClick={() => setStatusFilter(s)}
                    className={`px-2.5 py-1 rounded-md text-[12px] font-medium transition-colors cursor-pointer ${
                      statusFilter === s
                        ? 'bg-[#DFE9FB] dark:bg-[#3F51B5]/20 text-[#3F51B5] dark:text-[#7986CB]'
                        : 'text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
                    }`}
                  >
                    {labels[s]} ({count})
                  </button>
                )
              })}
            </div>
            <div className="flex items-center gap-1">
              <span className="text-[12px] text-[#888888] dark:text-gray-400 font-medium mr-1">Priority:</span>
              {(['all', 'high', 'medium', 'low'] as const).map((p) => {
                const labels: Record<string, string> = { all: 'All', high: 'High', medium: 'Medium', low: 'Low' }
                const count = p === 'all' ? allReports.length : allReports.filter((r) => r.priority === p).length
                return (
                  <button
                    key={p}
                    onClick={() => setPriorityFilter(p)}
                    className={`px-2.5 py-1 rounded-md text-[12px] font-medium transition-colors cursor-pointer ${
                      priorityFilter === p
                        ? 'bg-[#DFE9FB] dark:bg-[#3F51B5]/20 text-[#3F51B5] dark:text-[#7986CB]'
                        : 'text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
                    }`}
                  >
                    {labels[p]} ({count})
                  </button>
                )
              })}
            </div>
          </div>
        </div>

        {filteredReports.length === 0 ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <Ticket className="size-12 mx-auto text-gray-300 dark:text-gray-600 mb-3" />
              <p className="text-[14px] text-gray-500 dark:text-gray-400 font-medium">No tickets found</p>
              <p className="text-[12px] text-gray-400 dark:text-gray-500 mt-1">
                {allReports.length === 0
                  ? 'You haven\'t reported any bugs yet'
                  : 'Try adjusting your filters'}
              </p>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col min-h-0 px-5 pb-5">
            {/* Static header */}
            <div className="flex items-center bg-[#DFE9FB] dark:bg-[#3F51B5]/20 rounded-t-lg border border-gray-300 dark:border-gray-500/70 border-b-0 text-[12px] font-semibold text-[#3F51B5] dark:text-[#7986CB] shrink-0">
              <span className="w-24 px-2 py-2.5">Ticket ID</span>
              <span className="flex-1 px-2 py-2.5">Description</span>
              <span className="w-28 px-2 py-2.5">Module</span>
              <span className="w-20 px-2 py-2.5 text-center">Priority</span>
              <span className="w-24 px-2 py-2.5 text-center">Status</span>
              <span className="w-32 px-2 py-2.5 text-center">SLA</span>
              <span className="w-28 px-2 py-2.5">Created</span>
            </div>
            {/* Scrollable rows */}
            <div className="flex-1 min-h-0 overflow-auto border border-gray-300 dark:border-gray-500/70 border-t-0 rounded-b-lg">
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {filteredReports.map((report) => {
                  const sla = getSLAStatus(report.priority, report.createdAt, report.status)
                  const isUnread = !report.readByUser
                  return (
                    <div
                      key={report.id}
                      onClick={() => setSelectedTicket(report)}
                      className={`flex items-center cursor-pointer hover:bg-[#DFE9FB]/30 dark:hover:bg-indigo-900/10 transition-colors text-[12px] ${isUnread ? 'bg-[#3F51B5]/[0.04] dark:bg-[#3F51B5]/10' : ''}`}
                    >
                      <span className="w-24 px-2 py-2.5 font-mono font-semibold text-[#3F51B5] dark:text-[#7986CB]">
                        {report.id.slice(0, 8).toUpperCase()}
                        {isUnread && <span className="ml-1.5 inline-block size-1.5 rounded-full bg-blue-500" />}
                      </span>
                      <span className="flex-1 px-2 py-2.5 text-[13px] text-gray-700 dark:text-gray-200 truncate">
                        {report.testDescription}
                      </span>
                      <span className="w-28 px-2 py-2.5 text-gray-500 dark:text-gray-400 truncate">
                        {report.moduleName}
                      </span>
                      <span className="w-20 px-2 py-2.5 text-center">{priorityBadge(report.priority)}</span>
                      <span className="w-24 px-2 py-2.5 text-center">{statusBadge(report.status)}</span>
                      <span className="w-32 px-2 py-2.5 text-center">
                        <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${sla.color}`}>
                          {sla.label}
                        </span>
                        <div className="text-[10px] text-gray-400 dark:text-gray-500 mt-0.5">{sla.remaining}</div>
                      </span>
                      <span className="w-28 px-2 py-2.5 text-gray-500 dark:text-gray-400">
                        {new Date(report.createdAt).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        )}

      {/* Ticket Detail Dialog */}
      <Dialog open={!!selectedTicket} onOpenChange={(open) => { if (!open) setSelectedTicket(null) }}>
        <DialogContent className="max-w-[640px] max-h-[85vh] overflow-y-auto">
          {selectedTicket && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <Ticket className="size-5 text-[#3F51B5]" />
                  Ticket {selectedTicket.id.slice(0, 8).toUpperCase()}
                </DialogTitle>
                <DialogDescription className="text-[13px] text-gray-500 dark:text-gray-400">
                  Filed on {new Date(selectedTicket.createdAt).toLocaleString()}
                </DialogDescription>
              </DialogHeader>

              {/* Bug Info */}
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3">
                    <div className="text-[11px] text-gray-500 dark:text-gray-400 font-medium uppercase">Test ID</div>
                    <div className="text-[13px] text-gray-800 dark:text-gray-200 font-mono mt-0.5">{selectedTicket.testId}</div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3">
                    <div className="text-[11px] text-gray-500 dark:text-gray-400 font-medium uppercase">Module</div>
                    <div className="text-[13px] text-gray-800 dark:text-gray-200 mt-0.5">{selectedTicket.moduleName}</div>
                  </div>
                </div>
                <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3">
                  <div className="text-[11px] text-gray-500 dark:text-gray-400 font-medium uppercase">Description</div>
                  <div className="text-[13px] text-gray-800 dark:text-gray-200 mt-0.5">{selectedTicket.testDescription}</div>
                </div>
                {selectedTicket.error && (
                  <div className="bg-red-50 dark:bg-red-900/10 rounded-lg p-3 border border-red-100 dark:border-red-800/30">
                    <div className="text-[11px] text-red-600 dark:text-red-400 font-medium uppercase">Error</div>
                    <div className="text-[12px] text-red-700 dark:text-red-300 mt-0.5 font-mono whitespace-pre-wrap">{selectedTicket.error}</div>
                  </div>
                )}
                {selectedTicket.userNote && (
                  <div className="bg-yellow-50 dark:bg-yellow-900/10 rounded-lg p-3 border border-yellow-100 dark:border-yellow-800/30">
                    <div className="text-[11px] text-yellow-600 dark:text-yellow-400 font-medium uppercase">User Note</div>
                    <div className="text-[12px] text-yellow-700 dark:text-yellow-300 mt-0.5">{selectedTicket.userNote}</div>
                  </div>
                )}

                {/* SLA + Priority + Status */}
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] text-gray-500 dark:text-gray-400 font-medium">Priority:</span>
                    {priorityBadge(selectedTicket.priority)}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] text-gray-500 dark:text-gray-400 font-medium">Status:</span>
                    {statusBadge(selectedTicket.status)}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] text-gray-500 dark:text-gray-400 font-medium">SLA:</span>
                    <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${getSLAStatus(selectedTicket.priority, selectedTicket.createdAt, selectedTicket.status).color}`}>
                      {getSLAStatus(selectedTicket.priority, selectedTicket.createdAt, selectedTicket.status).label}
                    </span>
                  </div>
                </div>

                {/* SLA Deadline */}
                {selectedTicket.status !== 'fixed' && (
                  <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3 flex items-center gap-2">
                    <Timer className="size-4 text-gray-400" />
                    <div>
                      <div className="text-[11px] text-gray-500 dark:text-gray-400">SLA Deadline</div>
                      <div className="text-[13px] text-gray-800 dark:text-gray-200 font-medium">
                        {getSLADeadline(selectedTicket.priority, selectedTicket.createdAt).toLocaleString()}
                      </div>
                      <div className={`text-[11px] font-medium ${getSLAStatus(selectedTicket.priority, selectedTicket.createdAt, selectedTicket.status).overdue ? 'text-red-600 dark:text-red-400' : 'text-gray-500 dark:text-gray-400'}`}>
                        {getSLAStatus(selectedTicket.priority, selectedTicket.createdAt, selectedTicket.status).remaining}
                      </div>
                    </div>
                  </div>
                )}

                {/* Verify Fix banner — shown when admin marked fixed */}
                {selectedTicket.status === 'fixed' && onVerifyFix && (() => {
                  const isVerifying = verifyingTicketId === selectedTicket.id
                  const result = verifyResult?.ticketId === selectedTicket.id ? verifyResult : null
                  return (
                    <div className={`rounded-lg border p-3.5 flex flex-col gap-3 ${
                      result?.passed
                        ? 'bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-800/40'
                        : result?.passed === false
                          ? 'bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-800/40'
                          : 'bg-[#3F51B5]/[0.05] dark:bg-[#3F51B5]/10 border-[#3F51B5]/30 dark:border-[#3F51B5]/40'
                    }`}>
                      <div className="flex items-start gap-2.5">
                        <FlaskConical className={`size-4 shrink-0 mt-0.5 ${result?.passed ? 'text-green-600' : result?.passed === false ? 'text-red-500' : 'text-[#3F51B5] dark:text-[#7986CB]'}`} />
                        <div className="flex-1 min-w-0">
                          <p className="text-[13px] font-semibold text-gray-800 dark:text-gray-100">
                            {result?.passed ? 'Fix Verified ✓' : result?.passed === false ? 'Verification Failed' : 'Admin marked this as fixed'}
                          </p>
                          <p className="text-[12px] text-gray-500 dark:text-gray-400 mt-0.5">
                            {result?.passed
                              ? 'The test passed. This ticket has been closed.'
                              : result?.passed === false
                                ? 'The test still fails. You can reopen the ticket.'
                                : 'Run the test to confirm the fix before closing this ticket.'}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {!result && (
                          <Button size="sm" disabled={isVerifying}
                            onClick={() => onVerifyFix(selectedTicket)}
                            className="text-[12px] bg-[#3F51B5] hover:bg-[#3949AB] text-white gap-1.5 cursor-pointer"
                          >
                            {isVerifying ? <Loader2 className="size-3 animate-spin" /> : <ShieldCheck className="size-3" />}
                            {isVerifying ? 'Running test…' : 'Verify Fix'}
                          </Button>
                        )}
                        {result?.passed && (
                          <span className="flex items-center gap-1.5 text-[12px] font-medium text-green-700 dark:text-green-400">
                            <CheckCircle2 className="size-3.5" /> Closed automatically
                          </span>
                        )}
                        {result?.passed === false && (
                          <Button size="sm"
                            onClick={() => onVerifyFix(selectedTicket)}
                            className="text-[12px] bg-[#3F51B5] hover:bg-[#3949AB] text-white gap-1.5 cursor-pointer"
                          >
                            <RefreshCw className="size-3" /> Retry
                          </Button>
                        )}
                        <Button size="sm" variant="outline"
                          onClick={() => handleStatusChange('open')}
                          className="text-[12px] gap-1 cursor-pointer text-gray-500"
                        >
                          <RotateCcw className="size-3" /> Reopen
                        </Button>
                      </div>
                    </div>
                  )
                })()}

                {/* Status Change Buttons — for non-fixed statuses */}
                {selectedTicket.status !== 'fixed' && selectedTicket.status !== 'closed' && (
                  <div className="flex items-center gap-2">
                    <span className="text-[12px] text-gray-500 dark:text-gray-400 font-medium">Change Status:</span>
                    {selectedTicket.status === 'open' && (
                      <Button size="sm" onClick={() => handleStatusChange('in-progress')}
                        className="text-[12px] bg-[#2D3FC7] hover:bg-[#3F51B5] text-white gap-1 cursor-pointer"
                      >
                        <Play className="size-3" /> Mark In Progress
                      </Button>
                    )}
                    {selectedTicket.status === 'in-progress' && (
                      <Button size="sm" onClick={() => handleStatusChange('fixed')}
                        className="text-[12px] bg-green-600 hover:bg-green-700 text-white gap-1 cursor-pointer"
                      >
                        <CheckCircle2 className="size-3" /> Mark Fixed
                      </Button>
                    )}
                  </div>
                )}
              </div>

              <Separator />

              {/* Reply Thread */}
              <div>
                <h4 className="text-[13px] font-semibold text-gray-800 dark:text-gray-100 mb-2 flex items-center gap-1.5">
                  <MessageSquare className="size-4 text-[#3F51B5]" />
                  Replies ({selectedTicket.replies.length})
                </h4>
                {selectedTicket.replies.length === 0 ? (
                  <div className="text-center py-4 text-[12px] text-gray-400 dark:text-gray-500">
                    No replies yet
                  </div>
                ) : (
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {selectedTicket.replies.map((reply) => (
                      <div
                        key={reply.id}
                        className={`rounded-lg p-3 ${
                          reply.authorRole === 'admin'
                            ? 'bg-purple-50 dark:bg-purple-900/10 border border-purple-100 dark:border-purple-800/30'
                            : 'bg-blue-50 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-800/30'
                        }`}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <Avatar className="size-5">
                            <AvatarFallback className={`text-[9px] ${reply.authorRole === 'admin' ? 'bg-purple-500' : 'bg-[#6777EF]'} text-white`}>
                              {reply.authorName.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()}
                            </AvatarFallback>
                          </Avatar>
                          <span className="text-[12px] font-medium text-gray-800 dark:text-gray-200">{reply.authorName}</span>
                          <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full ${
                            reply.authorRole === 'admin'
                              ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400'
                              : 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400'
                          }`}>
                            {reply.authorRole === 'admin' ? 'Admin' : 'You'}
                          </span>
                          <span className="text-[10px] text-gray-400 dark:text-gray-500 ml-auto">
                            {new Date(reply.createdAt).toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                        <div className="text-[12px] text-gray-700 dark:text-gray-300 pl-7">{reply.message}</div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Reply Input */}
                <div className="flex items-center gap-2 mt-3">
                  <Input
                    placeholder="Type a reply..."
                    value={replyText}
                    onChange={(e) => setReplyText(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendReply() } }}
                    className="h-9 text-[13px] bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-600"
                    disabled={sendingReply}
                  />
                  <Button
                    size="sm"
                    onClick={handleSendReply}
                    disabled={!replyText.trim() || sendingReply}
                    className="bg-[#2D3FC7] hover:bg-[#3F51B5] text-white gap-1 cursor-pointer"
                  >
                    {sendingReply ? <Loader2 className="size-3.5 animate-spin" /> : <Send className="size-3.5" />}
                  </Button>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
      </div>
    )}
  </div>
  )
}
