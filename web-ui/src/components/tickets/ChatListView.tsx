'use client'

import React, { useState, useMemo } from 'react'
import { MessageSquare, Bug, Clock, CheckCircle2, Loader2 } from 'lucide-react'
import { TicketChat } from './TicketChat'
import { type BugReport } from '@/lib/bug-reports'

export function ChatListView({
  reports,
  userName,
  userRole,
  onReportsChange,
}: {
  reports: BugReport[]
  userName: string
  userRole: 'user' | 'admin'
  onReportsChange?: (reports: BugReport[]) => void
}) {
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const sorted = useMemo(() => {
    const withActivity = reports.map(r => {
      const lastReply = r.replies.length > 0
        ? r.replies[r.replies.length - 1].createdAt
        : r.updatedAt || r.createdAt
      return { ...r, lastActivity: new Date(lastReply).getTime() }
    })
    return withActivity.sort((a, b) => b.lastActivity - a.lastActivity)
  }, [reports])

  const selected = selectedId ? sorted.find(r => r.id === selectedId) ?? null : null

  const handleReplySent = (updated: BugReport) => {
    onReportsChange?.(
      reports.map(r => (r.id === updated.id ? updated : r))
    )
  }

  const initials = (name: string) =>
    name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()

  const priorityColor = (p: string) => {
    switch (p) {
      case 'high': return 'border-l-red-400'
      case 'medium': return 'border-l-yellow-400'
      case 'low': return 'border-l-blue-400'
      default: return 'border-l-gray-300'
    }
  }

  const statusDot = (s: string) => {
    switch (s) {
      case 'open': return 'bg-red-500'
      case 'in-progress': return 'bg-yellow-500'
      case 'fixed': return 'bg-green-500'
      case 'closed': return 'bg-gray-400'
      case 'rejected': return 'bg-orange-500'
      default: return 'bg-gray-400'
    }
  }

  const formatLastSeen = (dateStr: string) => {
    const d = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - d.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    const diffHours = Math.floor(diffMins / 60)
    if (diffHours < 24) return `${diffHours}h ago`
    const diffDays = Math.floor(diffHours / 24)
    if (diffDays < 7) return `${diffDays}d ago`
    return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
  }

  return (
    <div className="flex h-full border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden bg-white dark:bg-gray-800/50">
      <div className="w-[320px] shrink-0 border-r border-gray-200 dark:border-gray-700 flex flex-col">
        <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 shrink-0">
          <h3 className="text-[13px] font-semibold text-gray-800 dark:text-gray-100 flex items-center gap-2">
            <MessageSquare className="size-4 text-[#3F51B5]" />
            Conversations ({reports.length})
          </h3>
        </div>
        <div className="flex-1 overflow-y-auto min-h-0">
          {sorted.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center px-4">
              <MessageSquare className="size-10 text-gray-200 dark:text-gray-700 mb-2" />
              <p className="text-[13px] text-gray-400 dark:text-gray-500">No conversations</p>
            </div>
          ) : (
            sorted.map((report) => {
              const isUnread = userRole === 'admin' ? !report.readByAdmin : !report.readByUser
              const lastReply = report.replies[report.replies.length - 1]
              const lastMsg = lastReply?.message ?? 'No messages yet'
              return (
                <button
                  key={report.id}
                  onClick={() => setSelectedId(report.id)}
                  className={`w-full text-left px-4 py-3 border-b border-gray-100 dark:border-gray-700/50 transition-colors cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/30 ${
                    selectedId === report.id ? 'bg-blue-50 dark:bg-indigo-900/20' : ''
                  } ${priorityColor(report.priority)} border-l-2`}
                >
                  <div className="flex items-start gap-2.5">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        {isUnread && <span className="size-2 rounded-full bg-[#3F51B5] shrink-0" />}
                        <span className={`text-[12px] font-mono font-bold text-[#3F51B5] dark:text-[#7986CB] ${isUnread ? '' : 'opacity-70'}`}>
                          #{report.id.slice(0, 8).toUpperCase()}
                        </span>
                        <span className={`size-1.5 rounded-full ${statusDot(report.status)} shrink-0`} />
                      </div>
                      <p className={`text-[12px] mt-0.5 truncate ${isUnread ? 'font-semibold text-gray-800 dark:text-gray-100' : 'text-gray-600 dark:text-gray-400'}`}>
                        {report.testDescription}
                      </p>
                      <p className="text-[11px] text-gray-400 dark:text-gray-500 mt-0.5 truncate">
                        {lastMsg.length > 60 ? lastMsg.slice(0, 60) + '...' : lastMsg}
                      </p>
                    </div>
                    <div className="flex flex-col items-end gap-1 shrink-0">
                      <span className="text-[10px] text-gray-400 dark:text-gray-500 whitespace-nowrap">
                        {formatLastSeen(lastReply?.createdAt ?? report.updatedAt ?? report.createdAt)}
                      </span>
                      {report.replies.length > 0 && (
                        <span className="text-[10px] text-gray-400 dark:text-gray-500 flex items-center gap-0.5">
                          <MessageSquare className="size-3" />
                          {report.replies.length}
                        </span>
                      )}
                    </div>
                  </div>
                </button>
              )
            })
          )}
        </div>
      </div>

      <div className="flex-1 flex flex-col min-w-0">
        {selected ? (
          <TicketChat
            key={selected.id}
            bugReport={selected}
            userName={userName}
            userRole={userRole}
            onReplySent={handleReplySent}
          />
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center px-6">
            <MessageSquare className="size-12 text-gray-200 dark:text-gray-700 mb-3" />
            <p className="text-[14px] text-gray-400 dark:text-gray-500 font-medium">Select a conversation</p>
            <p className="text-[12px] text-gray-400 dark:text-gray-500 mt-1">
              Choose a conversation from the left to view and reply
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
