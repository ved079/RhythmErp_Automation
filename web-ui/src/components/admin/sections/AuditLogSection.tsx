'use client'

import { useState, useMemo } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import {
  Search, ChevronLeft, ChevronRight, RotateCcw, FileText,
} from 'lucide-react'
import Spinner from '@/components/ui/Spinner'
interface AuditEntry {
  id: string; userId: string; userName: string; action: string
  targetType: string; targetId: string; targetLabel: string
  details: string; createdAt: string
}

export function AuditLogSection({
  auditLog, auditLoaded,
}: {
  auditLog: AuditEntry[]
  auditLoaded: boolean
}) {
  const [auditPage, setAuditPage] = useState(1)
  const [auditSearch, setAuditSearch] = useState('')
  const [auditActionFilter, setAuditActionFilter] = useState('all')
  const [auditUserFilter, setAuditUserFilter] = useState('all')
  const perPage = 25

  const filteredAuditLog = useMemo(() => {
    return auditLog.filter(a => {
      const ms = !auditSearch || a.userName.toLowerCase().includes(auditSearch.toLowerCase()) || a.targetLabel.toLowerCase().includes(auditSearch.toLowerCase()) || a.details.toLowerCase().includes(auditSearch.toLowerCase()) || a.targetType.toLowerCase().includes(auditSearch.toLowerCase())
      const mst = auditActionFilter === 'all' || a.action === auditActionFilter
      const mu = auditUserFilter === 'all' || a.userName === auditUserFilter
      return ms && mst && mu
    })
  }, [auditLog, auditSearch, auditActionFilter, auditUserFilter])

  const uniqueAuditUsers = useMemo(() => {
    const s = new Set<string>()
    for (const a of auditLog) s.add(a.userName)
    return [...s].sort()
  }, [auditLog])

  const totalPages = Math.ceil(filteredAuditLog.length / perPage) || 1
  const paged = filteredAuditLog.slice((auditPage - 1) * perPage, auditPage * perPage)

  const actionColor = (action: string) => {
    if (action === 'create') return 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300'
    if (action === 'update') return 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300'
    if (action === 'delete') return 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300'
    if (action === 'login') return 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300'
    if (action === 'logout') return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
    if (action === 'reset_password') return 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300'
    if (action === 'toggle') return 'bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-300'
    return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <h2 className="text-xl font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">Audit Log</h2>
        <Badge variant="outline" className="text-xs font-['Poppins']">{filteredAuditLog.length} entries</Badge>
      </div>
      <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 size-4 text-[#888]" />
            <Input placeholder="Search user, target, details..." value={auditSearch} onChange={e => { setAuditSearch(e.target.value); setAuditPage(1) }}
              className="pl-9 h-9 text-sm font-['Poppins']" />
          </div>
          <Select value={auditActionFilter} onValueChange={v => { setAuditActionFilter(v); setAuditPage(1) }}>
            <SelectTrigger className="h-9 text-sm"><SelectValue placeholder="Action" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Actions</SelectItem>
              <SelectItem value="create">Create</SelectItem>
              <SelectItem value="update">Update</SelectItem>
              <SelectItem value="delete">Delete</SelectItem>
              <SelectItem value="login">Login</SelectItem>
              <SelectItem value="logout">Logout</SelectItem>
              <SelectItem value="reset_password">Reset Password</SelectItem>
              <SelectItem value="toggle">Toggle</SelectItem>
            </SelectContent>
          </Select>
          <Select value={auditUserFilter} onValueChange={v => { setAuditUserFilter(v); setAuditPage(1) }}>
            <SelectTrigger className="h-9 text-sm"><SelectValue placeholder="User" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Users</SelectItem>
              {uniqueAuditUsers.map(u => <SelectItem key={u} value={u}>{u}</SelectItem>)}
            </SelectContent>
          </Select>
          <Button variant="outline" className="h-9 text-xs font-['Poppins']" onClick={() => { setAuditSearch(''); setAuditActionFilter('all'); setAuditUserFilter('all'); setAuditPage(1) }}>
            <RotateCcw className="size-3 mr-1" /> Clear Filters
          </Button>
        </div>
      </div>
      {!auditLoaded ? (
        <div className="flex justify-center py-12"><Spinner size={24} /></div>
      ) : filteredAuditLog.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-12 border border-gray-100 dark:border-gray-700 text-center">
          <FileText className="size-10 text-[#888] dark:text-gray-500 mx-auto mb-2" />
          <p className="text-sm text-[#888] dark:text-gray-400 font-['Poppins']">No audit entries match your filters</p>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div className="space-y-1 p-3">
            {paged.map(a => (
              <div key={a.id} className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-white dark:bg-gray-800/20 border border-gray-100 dark:border-gray-700/40 hover:bg-gray-50/50 dark:hover:bg-gray-800/30 transition-colors">
                <span className="text-[10px] font-['Poppins'] text-[#888] dark:text-gray-400 shrink-0 w-32">
                  {new Date(a.createdAt).toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                </span>
                <span className="text-xs font-['Poppins'] text-[#333] dark:text-gray-100 shrink-0 w-28 truncate">{a.userName}</span>
                <Badge className={`text-[9px] border-0 shrink-0 ${actionColor(a.action)}`}>{a.action.replace('_', ' ')}</Badge>
                <div className="text-xs font-['Poppins'] min-w-0 flex-1">
                  <span className="text-[#888] dark:text-gray-400">{a.targetType}</span>
                  <span className="text-[#333] dark:text-gray-100 ml-1">{a.targetLabel}</span>
                </div>
                <span className="text-[10px] font-['Poppins'] text-[#545454] dark:text-gray-300 max-w-[200px] truncate shrink-0">{a.details}</span>
              </div>
            ))}
          </div>
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100 dark:border-gray-700">
            <span className="text-xs text-[#888] dark:text-gray-400 font-['Poppins']">
              Showing {(auditPage - 1) * perPage + 1}–{Math.min(auditPage * perPage, filteredAuditLog.length)} of {filteredAuditLog.length}
            </span>
            <div className="flex gap-1">
              <Button size="sm" variant="outline" disabled={auditPage <= 1} onClick={() => setAuditPage(p => p - 1)} className="h-7 text-xs"><ChevronLeft className="size-3" /></Button>
              <span className="flex items-center px-2 text-xs text-[#545454] dark:text-gray-300 font-['Poppins']">{auditPage} / {totalPages}</span>
              <Button size="sm" variant="outline" disabled={auditPage >= totalPages} onClick={() => setAuditPage(p => p + 1)} className="h-7 text-xs"><ChevronRight className="size-3" /></Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
