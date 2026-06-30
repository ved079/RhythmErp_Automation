'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Send, MessageSquare, Bug, Loader2 } from 'lucide-react'
import Spinner from '@/components/ui/Spinner'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { addReplyToReport, type BugReport } from '@/lib/bug-reports'
import { toast } from 'sonner'

const priorityColors: Record<string, string> = {
  high: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400',
  medium: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400',
  low: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
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

export function TicketChat({
  bugReport,
  userName,
  userRole,
  onReplySent,
}: {
  bugReport: BugReport
  userName: string
  userRole: 'user' | 'admin'
  onReplySent?: (updated: BugReport) => void
}) {
  const [message, setMessage] = useState('')
  const [sending, setSending] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [bugReport.replies])

  const handleSend = async () => {
    if (!message.trim() || sending) return
    setSending(true)
    try {
      const updated = await addReplyToReport(bugReport.id, {
        authorName: userName,
        authorRole: userRole,
        message: message.trim(),
      })
      if (updated) {
        onReplySent?.(updated)
      }
      setMessage('')
    } catch {
      toast.error('Failed to send message')
    } finally {
      setSending(false)
    }
  }

  const initials = (name: string) =>
    name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()

  return (
    <div className="flex flex-col h-full">
      <div className="bg-white dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700 px-4 py-3 shrink-0">
        <div className="flex items-center gap-2.5">
          <Bug className="size-4 text-gray-400 shrink-0" />
          <span className="text-[13px] font-mono font-bold text-[#3F51B5] dark:text-[#7986CB]">
            #{bugReport.id.slice(0, 8).toUpperCase()}
          </span>
          <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${statusColors[bugReport.status]}`}>
            {statusLabels[bugReport.status]}
          </span>
          <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${priorityColors[bugReport.priority]}`}>
            {bugReport.priority}
          </span>
          <span className="text-[12px] text-gray-500 dark:text-gray-400 truncate flex-1 ml-1">
            {bugReport.testDescription}
          </span>
        </div>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-3 space-y-3 min-h-0">
        {bugReport.replies.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <MessageSquare className="size-8 text-gray-300 dark:text-gray-600 mb-2" />
            <p className="text-[13px] text-gray-400 dark:text-gray-500 font-medium">No messages yet</p>
            <p className="text-[11px] text-gray-400 dark:text-gray-500 mt-0.5">
              {userRole === 'admin'
                ? 'Reply to start a conversation with the reporter'
                : 'Send a message to start a conversation with the admin'}
            </p>
          </div>
        )}
        {bugReport.replies.map((reply) => {
          const isAdmin = reply.authorRole === 'admin'
          return (
            <div key={reply.id} className={`flex gap-2.5 ${isAdmin ? 'justify-end' : 'justify-start'}`}>
              {!isAdmin && (
                <Avatar className="size-7 shrink-0 mt-1">
                  <AvatarFallback className="text-[9px] bg-[#6777EF] text-white">
                    {initials(reply.authorName)}
                  </AvatarFallback>
                </Avatar>
              )}
              <div className={`max-w-[75%] rounded-xl px-3.5 py-2.5 text-[13px] ${
                isAdmin
                  ? 'bg-[#3F51B5] text-white rounded-br-sm'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-bl-sm'
              }`}>
                <div className="flex items-center gap-2 mb-0.5">
                  <span className={`text-[11px] font-semibold ${isAdmin ? 'text-white/80' : 'text-gray-500 dark:text-gray-300'}`}>
                    {reply.authorName}
                  </span>
                  <span className={`text-[9px] ${isAdmin ? 'text-white/50' : 'text-gray-400'}`}>
                    {isAdmin ? 'Admin' : 'You'}
                  </span>
                </div>
                <p className={isAdmin ? 'text-white/90 leading-relaxed' : 'leading-relaxed'}>{reply.message}</p>
                <p className={`text-[10px] mt-1 ${isAdmin ? 'text-white/40' : 'text-gray-400'}`}>
                  {new Date(reply.createdAt).toLocaleString('en-IN', {
                    day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
                  })}
                </p>
              </div>
              {isAdmin && (
                <Avatar className="size-7 shrink-0 mt-1">
                  <AvatarFallback className="text-[9px] bg-[#3F51B5] text-white">
                    {initials(reply.authorName)}
                  </AvatarFallback>
                </Avatar>
              )}
            </div>
          )
        })}
        <div className="h-2" />
      </div>

      <div className="border-t border-gray-200 dark:border-gray-700 p-3 shrink-0 bg-white dark:bg-gray-800/30">
        <div className="flex items-center gap-2">
          <Input
            placeholder={userRole === 'admin' ? 'Reply as admin...' : 'Type a message...'}
            value={message}
            onChange={e => setMessage(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() } }}
            className="h-9 text-[13px] bg-gray-50 dark:bg-gray-700 border-gray-200 dark:border-gray-600"
            disabled={sending}
          />
          <Button
            size="sm"
            onClick={handleSend}
            disabled={!message.trim() || sending}
            className="h-9 w-9 p-0 bg-[#3F51B5] hover:bg-[#2D3FC7] text-white shrink-0"
          >
            {sending ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
          </Button>
        </div>
      </div>
    </div>
  )
}
