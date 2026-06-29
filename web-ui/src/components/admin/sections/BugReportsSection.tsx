'use client'

import React, { useState, useMemo } from 'react'
import {
  Search, ChevronDown, FolderTree, Clock, Inbox,
  Send, RotateCcw, Check, CheckCircle2, MessageSquare,
  XCircle,
} from 'lucide-react'
import Spinner from '@/components/ui/Spinner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import {
  Dialog, DialogContent, DialogTitle,
} from '@/components/ui/dialog'
import { getSLAStatus, type BugReport } from '@/lib/bug-reports'
import { ChatListView } from '@/components/tickets/ChatListView'

interface BugReportsSectionProps {
  bugReports: BugReport[]
  bugsLoaded: boolean
  onBugReportsChange: (reports: BugReport[]) => void
  adminUnreadChats: number
  userName: string
  bugSubTab: 'reports' | 'chats'
  setBugSubTab: (tab: 'reports' | 'chats') => void
  bugStatusFilter: string
  setBugStatusFilter: (filter: string) => void
  bugSearch: string
  setBugSearch: (search: string) => void
  bugModuleFilter: string
  setBugModuleFilter: (filter: string) => void
  bugPriorityFilter: string
  setBugPriorityFilter: (filter: string) => void
  expandedBug: string | null
  setExpandedBug: (id: string | null) => void
  bugReplyText: Record<string, string>
  setBugReplyText: (text: Record<string, string> | ((prev: Record<string, string>) => Record<string, string>)) => void
  pendingBugStatus: Record<string, string>
  setPendingBugStatus: (status: Record<string, string> | ((prev: Record<string, string>) => Record<string, string>)) => void
  handleBugStatusChange: (id: string, status: BugReport['status']) => Promise<void>
  handleBugReply: (reportId: string) => Promise<void>
  handleMarkBugRead: (id: string) => Promise<void>
}

export function BugReportsSection({
  bugReports,
  bugsLoaded,
  bugSubTab,
  setBugSubTab,
  bugStatusFilter,
  setBugStatusFilter,
  bugSearch,
  setBugSearch,
  bugModuleFilter,
  setBugModuleFilter,
  bugPriorityFilter,
  setBugPriorityFilter,
  expandedBug,
  setExpandedBug,
  bugReplyText,
  setBugReplyText,
  pendingBugStatus,
  setPendingBugStatus,
  adminUnreadChats,
  userName,
  handleBugStatusChange,
  handleBugReply,
  handleMarkBugRead,
  onBugReportsChange,
}: BugReportsSectionProps) {
  const statusConfig: Record<string, { bg: string; text: string; dot: string }> = {
    open: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-300', dot: 'bg-red-500' },
    'in-progress': { bg: 'bg-yellow-100 dark:bg-yellow-900/30', text: 'text-yellow-700 dark:text-yellow-300', dot: 'bg-yellow-500' },
    fixed: { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-300', dot: 'bg-green-500' },
    closed: { bg: 'bg-gray-100 dark:bg-gray-700', text: 'text-gray-600 dark:text-gray-400', dot: 'bg-gray-400' },
    rejected: { bg: 'bg-orange-100 dark:bg-orange-900/30', text: 'text-orange-700 dark:text-orange-300', dot: 'bg-orange-500' },
  }

  const filteredByStatus = bugStatusFilter === 'all' ? bugReports : bugReports.filter(b => b.status === bugStatusFilter)
  const filtered = filteredByStatus.filter(b => {
    const ms = !bugSearch || b.testDescription.toLowerCase().includes(bugSearch.toLowerCase()) || b.error.toLowerCase().includes(bugSearch.toLowerCase()) || b.id.toLowerCase().includes(bugSearch.toLowerCase()) || b.reporterName.toLowerCase().includes(bugSearch.toLowerCase())
    const mm = bugModuleFilter === 'all' || b.moduleName.toLowerCase().replace(/\s+/g, '-') === bugModuleFilter || b.moduleName === bugModuleFilter
    const mp = bugPriorityFilter === 'all' || b.priority === bugPriorityFilter
    return ms && mm && mp
  })
  const uniqueBugModules = [...new Set(bugReports.map(b => b.moduleName))].sort()
  const tabs = [
    { id: 'all', label: 'All', count: bugReports.length },
    { id: 'open', label: 'Open', count: bugReports.filter(b => b.status === 'open').length },
    { id: 'in-progress', label: 'In Progress', count: bugReports.filter(b => b.status === 'in-progress').length },
    { id: 'fixed', label: 'Fixed', count: bugReports.filter(b => b.status === 'fixed').length },
    { id: 'closed', label: 'Closed', count: bugReports.filter(b => b.status === 'closed').length },
    { id: 'rejected', label: 'Rejected', count: bugReports.filter(b => b.status === 'rejected').length },
  ]

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <div className="flex items-center gap-0 px-5 pt-4 pb-0 shrink-0 border-b border-gray-200 dark:border-gray-700">
        <button onClick={() => setBugSubTab('reports')}
          className={`px-4 py-2 text-[13px] font-medium border-b-2 transition-colors cursor-pointer ${
            bugSubTab === 'reports'
              ? 'border-[#3F51B5] text-[#3F51B5] dark:text-indigo-400'
              : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
          }`}>
          Reports
        </button>
        <button onClick={() => setBugSubTab('chats')}
          className={`px-4 py-2 text-[13px] font-medium border-b-2 transition-colors cursor-pointer flex items-center gap-1.5 ${
            bugSubTab === 'chats'
              ? 'border-[#3F51B5] text-[#3F51B5] dark:text-indigo-400'
              : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
          }`}>
          Chats
          {adminUnreadChats > 0 && (
            <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-[#3F51B5] text-white leading-none">
              {adminUnreadChats}
            </span>
          )}
        </button>
      </div>

      {bugSubTab === 'chats' ? (
        <div className="flex-1 min-h-0 p-4">
          <ChatListView
            reports={bugReports}
            userName={userName}
            userRole="admin"
            onReportsChange={onBugReportsChange}
          />
        </div>
      ) : (
      <>
      <div className="flex flex-col flex-1 min-h-0 gap-3 p-4">
        <div className="shrink-0 space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <h2 className="text-xl font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">Bug Reports</h2>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-[#888]" />
                <Input placeholder="Search bugs..." value={bugSearch} onChange={e => setBugSearch(e.target.value)}
                  className="h-8 pl-8 pr-3 text-xs font-['Manrope'] w-48" />
              </div>
              <Select value={bugModuleFilter} onValueChange={setBugModuleFilter}>
                <SelectTrigger className="h-8 text-xs w-32"><SelectValue placeholder="Module" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all" className="text-xs">All Modules</SelectItem>
                  {uniqueBugModules.map(m => <SelectItem key={m} value={m} className="text-xs">{m}</SelectItem>)}
                </SelectContent>
              </Select>
              <Select value={bugPriorityFilter} onValueChange={setBugPriorityFilter}>
                <SelectTrigger className="h-8 text-xs w-28"><SelectValue placeholder="Priority" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all" className="text-xs">All</SelectItem>
                  <SelectItem value="high" className="text-xs">High</SelectItem>
                  <SelectItem value="medium" className="text-xs">Medium</SelectItem>
                  <SelectItem value="low" className="text-xs">Low</SelectItem>
                </SelectContent>
              </Select>
              {(bugSearch || bugModuleFilter !== 'all' || bugPriorityFilter !== 'all') && (
                <Button variant="ghost" size="sm" className="h-8 text-xs text-[#888]" onClick={() => { setBugSearch(''); setBugModuleFilter('all'); setBugPriorityFilter('all') }}>
                  <RotateCcw className="size-3 mr-1" /> Clear
                </Button>
              )}
            </div>
          </div>

          <div className="flex gap-1.5 flex-wrap bg-gray-50 dark:bg-gray-800/50 rounded-xl p-1 border border-gray-100 dark:border-gray-700/50">
            {tabs.map(tab => (
              <button key={tab.id} onClick={() => setBugStatusFilter(tab.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-['Manrope'] font-medium transition-all cursor-pointer ${
                  bugStatusFilter === tab.id
                    ? 'bg-white dark:bg-gray-700 text-[#3F51B5] dark:text-[#7986CB] shadow-sm'
                    : 'text-[#888] dark:text-gray-400 hover:text-[#333] dark:hover:text-gray-100'
                }`}>
                {tab.label}
                <span className={`ml-1.5 ${bugStatusFilter === tab.id ? 'text-[#3F51B5] dark:text-[#7986CB]' : 'text-[#aaa]'}`}>({tab.count})</span>
              </button>
            ))}
          </div>
        </div>

        {!bugsLoaded ? (
          <div className="flex-1 flex items-center justify-center"><Spinner size={24} /></div>
        ) : filtered.length === 0 ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <Inbox className="size-10 text-[#888] dark:text-gray-500 mx-auto mb-2" />
              <p className="text-sm text-[#888] dark:text-gray-400 font-['Manrope']">No bug reports found</p>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col min-h-0">
            <div className="flex items-center bg-[#DFE9FB] dark:bg-indigo-900/30 rounded-t-lg border border-gray-300 dark:border-gray-500/70 border-b-0 text-[12px] font-semibold text-[#3F51B5] dark:text-indigo-300 shrink-0">
              <span className="w-24 px-2 py-2.5">Ticket ID</span>
              <span className="flex-1 px-2 py-2.5">Description</span>
              <span className="w-28 px-2 py-2.5">Module</span>
              <span className="w-20 px-2 py-2.5 text-center">Priority</span>
              <span className="w-24 px-2 py-2.5 text-center">Status</span>
              <span className="w-32 px-2 py-2.5 text-center">SLA</span>
              <span className="w-20 px-2 py-2.5 text-center"><MessageSquare className="size-3 mx-auto" /></span>
              <span className="w-28 px-2 py-2.5">Created</span>
            </div>
            <div className="flex-1 min-h-0 overflow-auto border border-gray-300 dark:border-gray-500/70 border-t-0 rounded-b-lg">
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {filtered.map(bug => {
                  const sla = getSLAStatus(bug.priority, bug.createdAt, bug.status)
                  const isUnread = !bug.readByAdmin
                  return (
                    <div key={bug.id} onClick={() => { setExpandedBug(bug.id); if (!bug.readByAdmin) handleMarkBugRead(bug.id) }}
                      className={`flex items-center cursor-pointer hover:bg-[#DFE9FB]/30 dark:hover:bg-indigo-900/10 transition-colors text-[12px] ${isUnread ? 'bg-blue-50/50 dark:bg-indigo-900/10' : ''}`}>
                      <span className="w-24 px-2 py-2.5 font-mono font-semibold text-[#3F51B5] dark:text-indigo-400 flex items-center gap-1">
                        {isUnread && <span className="size-1.5 rounded-full bg-blue-500 shrink-0" />}
                        #{bug.id.slice(0, 8).toUpperCase()}
                      </span>
                      <span className="flex-1 px-2 py-2.5 text-[13px] text-gray-700 dark:text-gray-200 truncate">{bug.testDescription}</span>
                      <span className="w-28 px-2 py-2.5 text-gray-500 dark:text-gray-400 truncate">{bug.moduleName}</span>
                      <span className="w-20 px-2 py-2.5 text-center">
                        <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${
                          bug.priority === 'high' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400' :
                          bug.priority === 'medium' ? 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400' :
                          'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400'
                        }`}>{bug.priority}</span>
                      </span>
                      <span className="w-24 px-2 py-2.5 text-center">
                        <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full ${statusConfig[bug.status]?.bg || ''} ${statusConfig[bug.status]?.text || ''}`}>{bug.status}</span>
                      </span>
                      <span className="w-32 px-2 py-2.5 text-center">
                        <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${sla.color}`}>{sla.label}</span>
                        <div className="text-[10px] text-gray-400 dark:text-gray-500 mt-0.5">{sla.remaining}</div>
                      </span>
                      <span className="w-20 px-2 py-2.5 text-center text-gray-400 dark:text-gray-500">
                        {bug.replies.length > 0 ? bug.replies.length : ''}
                      </span>
                      <span className="w-28 px-2 py-2.5 text-gray-500 dark:text-gray-400">
                        {new Date(bug.createdAt).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bug detail dialog */}
      <Dialog open={expandedBug !== null} onOpenChange={(open) => { if (!open) { setExpandedBug(null); setPendingBugStatus(prev => { const n = { ...prev }; if (expandedBug) delete n[expandedBug]; return n }) }}}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogTitle className="sr-only">Bug Report Detail</DialogTitle>
          {(() => {
            const bug = bugReports.find(b => b.id === expandedBug)
            if (!bug) return null
            const sla = getSLAStatus(bug.priority, bug.createdAt, bug.status)
            const sc = statusConfig[bug.status] || statusConfig.open
            return (
              <div className="font-['Manrope']">
                <div className="flex items-start justify-between gap-4 mb-5">
                  <div>
                    <div className="flex items-center gap-2.5 mb-1">
                      <span className="text-lg font-mono font-bold text-[#3F51B5] dark:text-[#7986CB]">#{bug.id.slice(0, 8).toUpperCase()}</span>
                      <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${sc.bg} ${sc.text}`}>{bug.status}</span>
                      <span className={`text-[11px] font-medium ${bug.priority === 'high' ? 'text-red-600' : bug.priority === 'medium' ? 'text-yellow-600' : 'text-blue-600'}`}>{bug.priority}</span>
                      <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${sla.color || 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'}`}>{sla.label}</span>
                    </div>
                    <p className="text-sm font-semibold text-[#333] dark:text-gray-100">{bug.testDescription}</p>
                    <div className="flex items-center gap-3 mt-1.5 text-xs text-[#888]">
                      <span className="flex items-center gap-1"><FolderTree className="size-3.5" />{bug.moduleName}</span>
                      <span>·</span>
                      <span className="flex items-center gap-1"><Clock className="size-3.5" />{sla.remaining}</span>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-px bg-gray-200 dark:bg-gray-700 rounded-lg overflow-hidden mb-5">
                  <div className="bg-gray-50 dark:bg-gray-800/50 px-4 py-3">
                    <span className="text-[10px] text-[#888] uppercase tracking-wider font-medium">Test ID</span>
                    <p className="text-xs text-[#333] dark:text-gray-100 mt-0.5 font-mono">{bug.testId}</p>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-800/50 px-4 py-3">
                    <span className="text-[10px] text-[#888] uppercase tracking-wider font-medium">Reported by</span>
                    <p className="text-xs text-[#333] dark:text-gray-100 mt-0.5">{bug.reporterName}</p>
                  </div>
                  <div className="sm:col-span-2 bg-gray-50 dark:bg-gray-800/50 px-4 py-3">
                    <span className="text-[10px] text-[#888] uppercase tracking-wider font-medium">Error Message</span>
                    <p className="text-xs text-red-600 dark:text-red-400 mt-0.5 font-mono leading-relaxed">{bug.error}</p>
                  </div>
                  {bug.userNote && (
                    <div className="sm:col-span-2 bg-gray-50 dark:bg-gray-800/50 px-4 py-3">
                      <span className="text-[10px] text-[#888] uppercase tracking-wider font-medium">User Note</span>
                      <p className="text-xs text-[#333] dark:text-gray-100 mt-0.5">{bug.userNote}</p>
                    </div>
                  )}
                </div>

                <div className="mb-5">
                  <span className="text-xs text-[#888] font-semibold uppercase tracking-wider block mb-2">Change Status</span>
                  <div className="flex items-center gap-2 flex-wrap">
                    {(['open', 'in-progress', 'fixed', 'closed', 'rejected'] as const).map(s => {
                      const isCurrent = bug.status === s
                      const isPending = pendingBugStatus[bug.id] === s
                      const colors = statusConfig[s]
                      return (
                        <button key={s} onClick={() => { if (s !== bug.status) setPendingBugStatus(prev => ({ ...prev, [bug.id]: s })) }}
                          className={`text-xs font-['Manrope'] px-3 py-1.5 rounded-lg border transition-all cursor-pointer ${
                            isCurrent
                              ? `${colors.bg} ${colors.text} border-transparent font-semibold`
                              : isPending
                                ? 'border-[#3F51B5] ring-1 ring-[#3F51B5] text-[#3F51B5] dark:text-[#7986CB] font-semibold'
                                : 'border-gray-200 dark:border-gray-600 text-[#888] dark:text-gray-400 hover:border-[#3F51B5]/40 hover:text-[#3F51B5]'
                          }`}>
                          {s.charAt(0).toUpperCase() + s.slice(1).replace('-', ' ')}
                        </button>
                      )
                    })}
                  </div>
                  {pendingBugStatus[bug.id] && pendingBugStatus[bug.id] !== bug.status && (
                    <div className="flex items-center gap-2 mt-3 pt-3 border-t border-gray-100 dark:border-gray-700/50">
                      <button onClick={() => {
                        handleBugStatusChange(bug.id, pendingBugStatus[bug.id] as BugReport['status'])
                        setPendingBugStatus(prev => { const n = { ...prev }; delete n[bug.id]; return n })
                      }}
                        className="text-xs font-['Manrope'] px-4 py-1.5 rounded-lg bg-[#3F51B5] text-white hover:bg-[#2D3FC7] font-medium transition-colors">
                        <Check className="size-3.5 inline mr-1.5" />Confirm & Update
                      </button>
                      <button onClick={() => setPendingBugStatus(prev => { const n = { ...prev }; delete n[bug.id]; return n })}
                        className="text-xs font-['Manrope'] px-3 py-1.5 rounded-lg text-[#888] hover:text-[#555] hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                        Cancel
                      </button>
                      <span className="text-[10px] text-[#aaa]">Status will change from <strong>{bug.status}</strong> to <strong>{pendingBugStatus[bug.id]}</strong></span>
                    </div>
                  )}
                </div>

                <div>
                  <span className="text-xs text-[#888] font-semibold uppercase tracking-wider block mb-3">Discussion ({bug.replies.length})</span>
                  {bug.replies.length > 0 && (
                    <div className="space-y-3 max-h-60 overflow-y-auto mb-3 pr-1">
                      {bug.replies.map(r => (
                        <div key={r.id} className={`flex gap-3 ${r.authorRole === 'admin' ? 'justify-end' : 'justify-start'}`}>
                          {r.authorRole !== 'admin' && (
                            <div className="w-8 h-8 rounded-full bg-[#E8EAF6] dark:bg-[#1A237E]/30 flex items-center justify-center shrink-0">
                              <span className="text-xs font-semibold text-[#3F51B5]">{r.authorName.charAt(0).toUpperCase()}</span>
                            </div>
                          )}
                          <div className={`max-w-[75%] rounded-xl px-3.5 py-2.5 text-sm font-['Manrope'] ${
                            r.authorRole === 'admin'
                              ? 'bg-[#3F51B5] text-white rounded-br-sm'
                              : 'bg-gray-100 dark:bg-gray-700 text-[#333] dark:text-gray-100 rounded-bl-sm'
                          }`}>
                            <div className="flex items-center gap-2 mb-0.5">
                              <span className={`text-xs font-semibold ${r.authorRole === 'admin' ? 'text-white/80' : 'text-[#555] dark:text-gray-300'}`}>{r.authorName}</span>
                              <span className={`text-[10px] ${r.authorRole === 'admin' ? 'text-white/60' : 'text-[#888]'}`}>{r.authorRole}</span>
                            </div>
                            <p className={r.authorRole === 'admin' ? 'text-white/90 leading-relaxed' : 'leading-relaxed'}>{r.message}</p>
                            <p className={`text-[10px] mt-1 ${r.authorRole === 'admin' ? 'text-white/50' : 'text-[#aaa]'}`}>
                              {new Date(r.createdAt).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
                            </p>
                          </div>
                          {r.authorRole === 'admin' && (
                            <div className="w-8 h-8 rounded-full bg-[#3F51B5] flex items-center justify-center shrink-0">
                              <span className="text-xs font-semibold text-white">{r.authorName.charAt(0).toUpperCase()}</span>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="flex gap-2">
                    <Input placeholder="Type a reply..." value={bugReplyText[bug.id] || ''}
                      onChange={e => setBugReplyText(prev => ({ ...prev, [bug.id]: e.target.value }))}
                      onKeyDown={e => { if (e.key === 'Enter') handleBugReply(bug.id) }}
                      className="h-10 text-sm font-['Manrope']" />
                    <Button size="sm" onClick={() => handleBugReply(bug.id)}
                      className="h-10 w-10 p-0 bg-[#3F51B5] hover:bg-[#2D3FC7] text-white shrink-0">
                      <Send className="size-4" />
                    </Button>
                  </div>
                </div>
              </div>
            )
          })()}
        </DialogContent>
      </Dialog>
      </>
      )}
    </div>
  )
}
