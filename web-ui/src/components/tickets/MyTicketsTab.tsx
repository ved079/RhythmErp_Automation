'use client'

import React, { useState, useEffect, useCallback, useMemo } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Ticket, RefreshCw, Filter, Loader2, Send, Timer, Play, CheckCircle2, RotateCcw, MessageSquare } from 'lucide-react'
import { toast } from 'sonner'
import type { BugReport } from '@/lib/bug-reports'
import { getBugReports, markReportReadByUser, addReplyToReport, updateBugReportStatus, getSLAStatus, getSLADeadline } from '@/lib/bug-reports'

// ─── MY TICKETS TAB (Feature 1) ──────────────────────────
export function MyTicketsTab({
  userEmail,
  userName,
}: {
  userEmail: string
  userName: string
}) {
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
    const colors = {
      open: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400',
      'in-progress': 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
      fixed: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
    }
    const labels = { open: 'Open', 'in-progress': 'In Progress', fixed: 'Fixed' }
    return (
      <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${colors[s as keyof typeof colors] || 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'}`}>
        {labels[s as keyof typeof labels] || s}
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
    <div className="flex flex-col h-full overflow-auto">
      <div className="p-5 space-y-4">
        {/* Page Header */}
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

        {/* Filters */}
        <div className="flex items-center gap-3 flex-wrap">
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
                      ? 'bg-[#DFE9FB] dark:bg-indigo-900/30 text-[#3F51B5] dark:text-indigo-400'
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
                      ? 'bg-[#DFE9FB] dark:bg-indigo-900/30 text-[#3F51B5] dark:text-indigo-400'
                      : 'text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
                >
                  {labels[p]} ({count})
                </button>
              )
            })}
          </div>
        </div>

        {/* Tickets List */}
        {filteredReports.length === 0 ? (
          <div className="text-center py-16">
            <Ticket className="size-12 mx-auto text-gray-300 dark:text-gray-600 mb-3" />
            <p className="text-[14px] text-gray-500 dark:text-gray-400 font-medium">No tickets found</p>
            <p className="text-[12px] text-gray-400 dark:text-gray-500 mt-1">
              {allReports.length === 0
                ? 'You haven\'t reported any bugs yet'
                : 'Try adjusting your filters'}
            </p>
          </div>
        ) : (
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="bg-[#DFE9FB] dark:bg-indigo-900/30 hover:bg-[#DFE9FB] dark:hover:bg-indigo-900/30">
                  <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 w-24">Ticket ID</TableHead>
                  <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300">Description</TableHead>
                  <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 w-28">Module</TableHead>
                  <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 w-20 text-center">Priority</TableHead>
                  <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 w-24 text-center">Status</TableHead>
                  <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 w-32 text-center">SLA</TableHead>
                  <TableHead className="text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 w-28">Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredReports.map((report) => {
                  const sla = getSLAStatus(report.priority, report.createdAt, report.status)
                  const isUnread = !report.readByUser
                  return (
                    <TableRow
                      key={report.id}
                      className={`cursor-pointer hover:bg-[#DFE9FB]/30 dark:hover:bg-indigo-900/10 transition-colors ${isUnread ? 'bg-blue-50/50 dark:bg-indigo-900/10' : ''}`}
                      onClick={() => setSelectedTicket(report)}
                    >
                      <TableCell className="text-[12px] font-mono font-semibold text-[#3F51B5] dark:text-indigo-400">
                        {report.id.slice(0, 8).toUpperCase()}
                        {isUnread && <span className="ml-1.5 inline-block size-1.5 rounded-full bg-blue-500" />}
                      </TableCell>
                      <TableCell className="text-[13px] text-gray-700 dark:text-gray-200 max-w-[250px] truncate">
                        {report.testDescription}
                      </TableCell>
                      <TableCell className="text-[12px] text-gray-500 dark:text-gray-400">
                        {report.moduleName}
                      </TableCell>
                      <TableCell className="text-center">{priorityBadge(report.priority)}</TableCell>
                      <TableCell className="text-center">{statusBadge(report.status)}</TableCell>
                      <TableCell className="text-center">
                        <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${sla.color}`}>
                          {sla.label}
                        </span>
                        <div className="text-[10px] text-gray-400 dark:text-gray-500 mt-0.5">{sla.remaining}</div>
                      </TableCell>
                      <TableCell className="text-[12px] text-gray-500 dark:text-gray-400">
                        {new Date(report.createdAt).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })}
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </div>

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

                {/* Status Change Buttons */}
                <div className="flex items-center gap-2">
                  <span className="text-[12px] text-gray-500 dark:text-gray-400 font-medium">Change Status:</span>
                  {selectedTicket.status === 'open' && (
                    <Button
                      size="sm"
                      onClick={() => handleStatusChange('in-progress')}
                      className="text-[12px] bg-[#2D3FC7] hover:bg-[#3F51B5] text-white gap-1 cursor-pointer"
                    >
                      <Play className="size-3" />
                      Mark In Progress
                    </Button>
                  )}
                  {selectedTicket.status === 'in-progress' && (
                    <Button
                      size="sm"
                      onClick={() => handleStatusChange('fixed')}
                      className="text-[12px] bg-green-600 hover:bg-green-700 text-white gap-1 cursor-pointer"
                    >
                      <CheckCircle2 className="size-3" />
                      Mark Fixed
                    </Button>
                  )}
                  {selectedTicket.status === 'fixed' && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleStatusChange('open')}
                      className="text-[12px] gap-1 cursor-pointer"
                    >
                      <RotateCcw className="size-3" />
                      Reopen
                    </Button>
                  )}
                </div>
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
  )
}
