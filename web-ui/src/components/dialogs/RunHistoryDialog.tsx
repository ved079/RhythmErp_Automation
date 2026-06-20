'use client'

import React, { useState, useMemo, useEffect } from 'react'
import { Search, X, Eye, ChevronLeft, ChevronRight, Clock, Filter } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import type { RunSnapshot } from '@/lib/types'

function getModuleName(moduleId: string, sidebarModules: { id: string; label: string; children?: any[] }[]): string {
  for (const mod of sidebarModules) {
    if (mod.id === moduleId) return mod.label
    if (mod.children) {
      for (const child of mod.children) {
        if (child.id === moduleId) return child.label
        if (child.children) {
          for (const sub of child.children) {
            if (sub.id === moduleId) return sub.label
          }
        }
      }
    }
  }
  return moduleId.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const PERIODS = [
  { label: 'All Time', value: 'all' },
  { label: 'Today', value: 'today' },
  { label: 'This Week', value: 'week' },
  { label: 'This Month', value: 'month' },
] as const

const STATUS_OPTIONS = [
  { label: 'All', value: 'all' },
  { label: 'Passed', value: 'passed' },
  { label: 'Failed', value: 'failed' },
] as const

function isWithinPeriod(dateStr: string, period: string): boolean {
  if (period === 'all') return true
  const date = new Date(dateStr)
  const now = new Date()
  const startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  if (period === 'today') return date >= startOfDay
  if (period === 'week') {
    const startOfWeek = new Date(startOfDay)
    startOfWeek.setDate(startOfWeek.getDate() - startOfWeek.getDay())
    return date >= startOfWeek
  }
  if (period === 'month') {
    return date >= new Date(now.getFullYear(), now.getMonth(), 1)
  }
  return true
}

const PAGE_SIZE = 15

export function RunHistoryDialog({
  open,
  onClose,
  runHistory,
  sidebarModules,
  currentModuleId,
  onRunDetail,
}: {
  open: boolean
  onClose: () => void
  runHistory: RunSnapshot[]
  sidebarModules: { id: string; label: string; children?: any[] }[]
  currentModuleId?: string
  onRunDetail?: (run: RunSnapshot) => void
}) {
  const [moduleFilter, setModuleFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')
  const [periodFilter, setPeriodFilter] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [page, setPage] = useState(0)

  const scopedRuns = useMemo(
    () => currentModuleId ? runHistory.filter(r => r.moduleId === currentModuleId) : runHistory,
    [runHistory, currentModuleId]
  )

  const uniqueModules = useMemo(() => {
    const seen = new Set<string>()
    return scopedRuns.filter(r => {
      if (seen.has(r.moduleId)) return false
      seen.add(r.moduleId)
      return true
    }).map(r => ({
      id: r.moduleId,
      name: getModuleName(r.moduleId, sidebarModules),
    })).sort((a, b) => a.name.localeCompare(b.name))
  }, [scopedRuns, sidebarModules])

  const filteredRuns = useMemo(() => {
    let result = [...scopedRuns]
    if (moduleFilter !== 'all') result = result.filter(r => r.moduleId === moduleFilter)
    if (statusFilter === 'passed') result = result.filter(r => r.failed === 0 && r.passed > 0)
    if (statusFilter === 'failed') result = result.filter(r => r.failed > 0)
    if (periodFilter !== 'all') result = result.filter(r => isWithinPeriod(r.date, periodFilter))
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      result = result.filter(r => getModuleName(r.moduleId, sidebarModules).toLowerCase().includes(q))
    }
    return result.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
  }, [scopedRuns, moduleFilter, statusFilter, periodFilter, searchQuery, sidebarModules])

  const totalPages = Math.ceil(filteredRuns.length / PAGE_SIZE)
  const paginatedRuns = filteredRuns.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  useEffect(() => { setPage(0) }, [moduleFilter, statusFilter, periodFilter, searchQuery])

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-[800px] dark:bg-gray-800 dark:border-gray-600/60 p-0 gap-0">
        <DialogTitle className="sr-only">Run History</DialogTitle>
        <DialogDescription className="sr-only">Browse all past test runs</DialogDescription>

        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-600/40">
          <div className="flex items-center gap-2">
            <Clock className="size-4 text-gray-500" />
            <h2 className="text-[15px] font-semibold text-gray-800 dark:text-gray-100">Run History</h2>
            <span className="text-[12px] text-gray-400 dark:text-gray-500">({scopedRuns.length} total)</span>
          </div>
          <button onClick={onClose} className="size-6 flex items-center justify-center rounded-md text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer">
            <X className="size-4" />
          </button>
        </div>

        {/* Filter bar */}
        <div className="flex items-center gap-2 px-4 py-2.5 border-b border-gray-200 dark:border-gray-600/40 bg-gray-50/50 dark:bg-gray-800/30">
          <Filter className="size-3.5 text-gray-400 shrink-0" />

          <select value={moduleFilter} onChange={(e) => setModuleFilter(e.target.value)}
            className="h-7 text-[12px] px-2 rounded border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 outline-none focus:border-indigo-400 cursor-pointer"
          >
            <option value="all">All Modules</option>
            {uniqueModules.map(m => (
              <option key={m.id} value={m.id}>{m.name}</option>
            ))}
          </select>

          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}
            className="h-7 text-[12px] px-2 rounded border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 outline-none focus:border-indigo-400 cursor-pointer"
          >
            {STATUS_OPTIONS.map(s => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>

          <select value={periodFilter} onChange={(e) => setPeriodFilter(e.target.value)}
            className="h-7 text-[12px] px-2 rounded border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 outline-none focus:border-indigo-400 cursor-pointer"
          >
            {PERIODS.map(p => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>

          <div className="relative flex-1 max-w-[200px]">
            <Search className="size-3 absolute left-2 top-1/2 -translate-y-1/2 text-gray-400" />
            <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search module..."
              className="w-full h-7 text-[12px] pl-6 pr-2 rounded border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 outline-none focus:border-indigo-400 placeholder:text-gray-400"
            />
          </div>
        </div>

        {/* Table */}
        <div className="overflow-y-auto max-h-[420px]">
          {paginatedRuns.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-gray-400 dark:text-gray-500">
              <Search className="size-8 mb-2" />
              <p className="text-[13px]">No runs match your filters</p>
            </div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="text-[11px] text-gray-500 dark:text-gray-400 uppercase tracking-wider border-b border-gray-100 dark:border-gray-700/40 bg-gray-50 dark:bg-gray-800/50">
                  <th className="text-left px-4 py-2 font-medium w-10">#</th>
                  <th className="text-left px-3 py-2 font-medium">Date</th>
                  <th className="text-left px-3 py-2 font-medium">Module</th>
                  <th className="text-right px-3 py-2 font-medium">Passed</th>
                  <th className="text-right px-3 py-2 font-medium">Failed</th>
                  <th className="text-right px-3 py-2 font-medium">Total</th>
                  <th className="text-right px-3 py-2 font-medium">Rate</th>
                  <th className="text-right px-3 py-2 font-medium">Duration</th>
                  <th className="w-10"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700/40">
                {paginatedRuns.map((run, idx) => (
                  <tr key={run.id}
                    onClick={() => onRunDetail?.(run)}
                    className="text-[13px] text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors cursor-pointer"
                  >
                    <td className="px-4 py-2.5 text-gray-400 dark:text-gray-500 font-mono text-[12px]">{page * PAGE_SIZE + idx + 1}</td>
                    <td className="px-3 py-2.5 whitespace-nowrap text-[12px] text-gray-600 dark:text-gray-300">{run.date}</td>
                    <td className="px-3 py-2.5 truncate max-w-[140px]">{getModuleName(run.moduleId, sidebarModules)}</td>
                    <td className="px-3 py-2.5 text-right text-green-600 dark:text-green-400 font-medium">{run.passed}</td>
                    <td className={`px-3 py-2.5 text-right font-medium ${run.failed > 0 ? 'text-red-500 dark:text-red-400' : 'text-gray-400 dark:text-gray-500'}`}>{run.failed}</td>
                    <td className="px-3 py-2.5 text-right text-gray-600 dark:text-gray-300">{run.total}</td>
                    <td className="px-3 py-2.5 text-right">
                      <span className={`text-[12px] font-medium px-1.5 py-0.5 rounded ${
                        run.rate >= 90 ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                          : run.rate >= 75 ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
                          : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                      }`}>{run.rate}%</span>
                    </td>
                    <td className="px-3 py-2.5 text-right font-mono text-[12px] text-gray-500 dark:text-gray-400">{run.duration}</td>
                    <td className="px-3 py-2.5 text-center">
                      <Eye className="size-3.5 text-gray-400" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-2.5 border-t border-gray-200 dark:border-gray-600/40 bg-gray-50/50 dark:bg-gray-800/30">
            <span className="text-[12px] text-gray-500 dark:text-gray-400">{filteredRuns.length} run{filteredRuns.length !== 1 ? 's' : ''}</span>
            <div className="flex items-center gap-1">
              <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}
                className="size-6 flex items-center justify-center rounded text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors cursor-pointer"
              >
                <ChevronLeft className="size-3.5" />
              </button>
              {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                const start = Math.max(0, Math.min(page - 2, totalPages - 5))
                const p = start + i
                return (
                  <button key={p} onClick={() => setPage(p)}
                    className={`size-6 text-[12px] rounded transition-colors cursor-pointer ${
                      p === page ? 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 font-medium' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                  >
                    {p + 1}
                  </button>
                )
              })}
              <button onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1}
                className="size-6 flex items-center justify-center rounded text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors cursor-pointer"
              >
                <ChevronRight className="size-3.5" />
              </button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
