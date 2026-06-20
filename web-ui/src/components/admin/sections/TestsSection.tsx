'use client'

import { useState, useMemo } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import {
  Search, Loader2, ChevronLeft, ChevronRight, CheckCircle2, XCircle, Circle,
} from 'lucide-react'
interface AdminTest {
  id: string; description: string; className: string
  status: 'active' | 'draft' | 'disabled'; priority: 'smoke' | 'regression' | 'sanity'
  steps: string; expected: string; moduleId: string; moduleName: string
  error?: string; lastResult?: 'passed' | 'failed' | 'not-run'; lastRun?: string
}

const priorityConfig: Record<string, { label: string; color: string }> = {
  smoke: { label: 'Smoke', color: 'text-orange-700 bg-orange-100 dark:text-orange-300 dark:bg-orange-900/40' },
  regression: { label: 'Regression', color: 'text-[#3F51B5] bg-[#E8EAF6] dark:text-[#7986CB] dark:bg-[#1A237E]/30' },
  sanity: { label: 'Sanity', color: 'text-purple-700 bg-purple-100 dark:text-purple-300 dark:bg-purple-900/40' },
}

export function TestsSection({
  tests, testsLoaded,
}: {
  tests: AdminTest[]
  testsLoaded: boolean
}) {
  const [testSearch, setTestSearch] = useState('')
  const [testStatusFilter, setTestStatusFilter] = useState('all')
  const [testModuleFilter, setTestModuleFilter] = useState('all')
  const [testPriorityFilter, setTestPriorityFilter] = useState('all')
  const [testPage, setTestPage] = useState(1)
  const perPage = 25

  const filteredTests = useMemo(() => {
    return tests.filter(t => {
      const ms = !testSearch || t.id.toLowerCase().includes(testSearch.toLowerCase()) || t.description.toLowerCase().includes(testSearch.toLowerCase()) || t.className.toLowerCase().includes(testSearch.toLowerCase())
      const mst = testStatusFilter === 'all' || t.status === testStatusFilter
      const mm = testModuleFilter === 'all' || t.moduleId === testModuleFilter
      const mp = testPriorityFilter === 'all' || t.priority === testPriorityFilter
      return ms && mst && mm && mp
    })
  }, [tests, testSearch, testStatusFilter, testModuleFilter, testPriorityFilter])

  const uniqueTestModules = useMemo(() => {
    const m = new Map<string, string>()
    for (const t of tests) { if (!m.has(t.moduleId)) m.set(t.moduleId, t.moduleName) }
    return Array.from(m.entries()).sort((a, b) => a[1].localeCompare(b[1]))
  }, [tests])

  const totalPages = Math.ceil(filteredTests.length / perPage) || 1
  const paged = filteredTests.slice((testPage - 1) * perPage, testPage * perPage)

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <h2 className="text-xl font-semibold font-['Poppins'] text-[#333] dark:text-gray-100">Test Management</h2>
        <Badge variant="outline" className="text-xs font-['Manrope']">{filteredTests.length} tests</Badge>
      </div>
      <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 size-4 text-[#888]" />
            <Input placeholder="Search tests..." value={testSearch} onChange={e => { setTestSearch(e.target.value); setTestPage(1) }}
              className="pl-9 h-9 text-sm font-['Manrope']" />
          </div>
          <Select value={testStatusFilter} onValueChange={v => { setTestStatusFilter(v); setTestPage(1) }}>
            <SelectTrigger className="h-9 text-sm"><SelectValue placeholder="Status" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="draft">Draft</SelectItem>
              <SelectItem value="disabled">Disabled</SelectItem>
            </SelectContent>
          </Select>
          <Select value={testModuleFilter} onValueChange={v => { setTestModuleFilter(v); setTestPage(1) }}>
            <SelectTrigger className="h-9 text-sm"><SelectValue placeholder="Module" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Modules</SelectItem>
              {uniqueTestModules.map(([id, label]) => <SelectItem key={id} value={id}>{label}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={testPriorityFilter} onValueChange={v => { setTestPriorityFilter(v); setTestPage(1) }}>
            <SelectTrigger className="h-9 text-sm"><SelectValue placeholder="Priority" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Priorities</SelectItem>
              <SelectItem value="smoke">Smoke</SelectItem>
              <SelectItem value="regression">Regression</SelectItem>
              <SelectItem value="sanity">Sanity</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
        {!testsLoaded ? (
          <div className="flex justify-center py-12"><Loader2 className="size-6 animate-spin text-[#3F51B5]" /></div>
        ) : filteredTests.length === 0 ? (
          <div className="text-center py-12 text-[#888] dark:text-gray-400 font-['Manrope'] text-sm">No tests found</div>
        ) : (
          <>
            <div className="space-y-1 p-3">
              {paged.map(t => (
                <div key={t.id} className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-white dark:bg-gray-800/20 border border-gray-100 dark:border-gray-700/40 hover:bg-gray-50/50 dark:hover:bg-gray-800/30 transition-colors">
                  <span className="text-[11px] font-mono text-[#545454] dark:text-gray-400 w-12 shrink-0">{t.id}</span>
                  <span className="flex-1 text-[13px] font-['Manrope'] text-[#333] dark:text-gray-100 truncate">{t.description}</span>
                  <span className="text-[11px] font-['Manrope'] text-[#545454] dark:text-gray-400 shrink-0">{t.moduleName}</span>
                  <Badge variant="outline" className="text-[10px] shrink-0">{t.status}</Badge>
                  <Badge className={`text-[10px] border-0 shrink-0 ${priorityConfig[t.priority]?.color || ''}`}>{priorityConfig[t.priority]?.label || t.priority}</Badge>
                  <span className="shrink-0">
                    {t.lastResult === 'passed' ? <CheckCircle2 className="size-4 text-[#4CAF50]" />
                      : t.lastResult === 'failed' ? <XCircle className="size-4 text-[#F44336]" />
                      : <Circle className="size-4 text-gray-400" />}
                  </span>
                </div>
              ))}
            </div>
            <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100 dark:border-gray-700">
              <span className="text-xs text-[#888] dark:text-gray-400 font-['Manrope']">
                Showing {(testPage - 1) * perPage + 1}–{Math.min(testPage * perPage, filteredTests.length)} of {filteredTests.length}
              </span>
              <div className="flex gap-1">
                <Button size="sm" variant="outline" disabled={testPage <= 1} onClick={() => setTestPage(p => p - 1)} className="h-7 text-xs"><ChevronLeft className="size-3" /></Button>
                <span className="flex items-center px-2 text-xs text-[#545454] dark:text-gray-300 font-['Manrope']">{testPage} / {totalPages}</span>
                <Button size="sm" variant="outline" disabled={testPage >= totalPages} onClick={() => setTestPage(p => p + 1)} className="h-7 text-xs"><ChevronRight className="size-3" /></Button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
