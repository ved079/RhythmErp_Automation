'use client'

import React, { useState, useCallback, useMemo } from 'react'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Search, ChevronDown, ChevronRight, FileSpreadsheet } from 'lucide-react'
import type { TestClassGroup } from '@/lib/types'
import type { TestSpecItem } from '@/lib/types'
import { PriorityBadge } from '@/components/home/PriorityBadge'
import { SortArrow } from '@/components/home/SortArrow'

// ─── OPERATIONS TAB (Test Specification View) ────────────
export function OperationsTab({ testGroups, testCasesModule }: { testGroups: TestClassGroup[]; testCasesModule?: { label: string; tests: any[] } }) {
  const testSpecGroups = testGroups
  const [searchVal, setSearchVal] = useState('')
  const [filter, setFilter] = useState<'all' | 'passed' | 'bug' | 'todo' | 'not-run'>('all')
  const [expandedTests, setExpandedTests] = useState<Set<string>>(new Set())
  const [sortCol, setSortCol] = useState<string>('id')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')

  const toggleTest = useCallback((id: string) => {
    setExpandedTests((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  const handleSort = useCallback((col: string) => {
    if (sortCol === col) {
      setSortDir((d) => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortCol(col)
      setSortDir('asc')
    }
  }, [sortCol])

  // Flatten all tests from all groups into one list for the table
  const allTests = useMemo(() => {
    const flat: (TestSpecItem & { groupName: string })[] = []
    for (const g of testSpecGroups) {
      for (const t of g.tests) {
        flat.push({ ...t, groupName: g.className })
      }
    }
    return flat
  }, [testSpecGroups])

  // Filter + sort
  const filteredTests = useMemo(() => {
    let result = allTests.filter((test) => {
      const matchSearch =
        searchVal === '' ||
        test.id.toLowerCase().includes(searchVal.toLowerCase()) ||
        test.description.toLowerCase().includes(searchVal.toLowerCase()) ||
        test.steps.toLowerCase().includes(searchVal.toLowerCase()) ||
        test.expected.toLowerCase().includes(searchVal.toLowerCase()) ||
        test.actual.toLowerCase().includes(searchVal.toLowerCase())
      const matchFilter =
        filter === 'all' ||
        (filter === 'passed' && test.status === 'passed') ||
        (filter === 'bug' && test.status === 'bug') ||
        (filter === 'todo' && test.status === 'todo') ||
        (filter === 'not-run' && test.status === 'not-run')
      return matchSearch && matchFilter
    })

    // Sort
    const statusOrder: Record<string, number> = { bug: 0, failed: 1, todo: 2, 'not-run': 3, passed: 4 }
    const priorityOrder: Record<string, number> = { smoke: 0, regression: 1, sanity: 2 }

    result.sort((a, b) => {
      let cmp = 0
      switch (sortCol) {
        case 'id':
          cmp = a.id.localeCompare(b.id, undefined, { numeric: true })
          break
        case 'description':
          cmp = a.description.localeCompare(b.description)
          break
        case 'status':
          cmp = (statusOrder[a.status] ?? 5) - (statusOrder[b.status] ?? 5)
          break
        case 'priority':
          cmp = (priorityOrder[a.priority ?? ''] ?? 3) - (priorityOrder[b.priority ?? ''] ?? 3)
          break
        case 'date':
          cmp = (a.date || 'zzz').localeCompare(b.date || 'zzz')
          break
        default:
          cmp = 0
      }
      return sortDir === 'desc' ? -cmp : cmp
    })

    return result
  }, [allTests, searchVal, filter, sortCol, sortDir])

  const totalTests = allTests.length
  const passedCount = allTests.filter((t) => t.status === 'passed').length
  const bugCount = allTests.filter((t) => t.status === 'bug').length
  const todoCount = allTests.filter((t) => t.status === 'todo').length
  const notRunCount = allTests.filter((t) => t.status === 'not-run').length

  const getStatusDisplay = (test: TestSpecItem) => {
    if (test.status === 'bug') {
      return { label: 'BUG', color: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400', icon: '\u{1F41B}' }
    }
    if (test.status === 'passed') {
      return { label: 'PASS', color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400', icon: '\u2705' }
    }
    if (test.status === 'failed') {
      return { label: 'FAIL', color: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400', icon: '\u274C' }
    }
    if (test.status === 'todo') {
      return { label: 'TODO', color: 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400', icon: '\u{1F4CB}' }
    }
    return { label: '\u2014', color: 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400', icon: '\u2014' }
  }

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* ─── Toolbar ─── */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-100 dark:border-gray-700 shrink-0 flex-wrap">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-gray-400" />
          <Input
            placeholder="Search tests..."
            value={searchVal}
            onChange={(e) => setSearchVal(e.target.value)}
            className="h-8 pl-8 text-[13px] bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-600 text-gray-800 dark:text-gray-100"
          />
        </div>
        <Select value={filter} onValueChange={(v) => setFilter(v as typeof filter)}>
          <SelectTrigger className="h-8 w-28 text-[13px] bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-600">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All ({totalTests})</SelectItem>
            <SelectItem value="passed">Passed ({passedCount})</SelectItem>
            <SelectItem value="bug">Bug ({bugCount})</SelectItem>
            <SelectItem value="todo">Todo ({todoCount})</SelectItem>
            <SelectItem value="not-run">Not Run ({notRunCount})</SelectItem>
          </SelectContent>
        </Select>
        <Button
          variant="outline"
          className="h-8 text-[13px] gap-1.5 border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300"
          onClick={() => {
            if (typeof window !== 'undefined') {
              const allData = (window as any).__ALL_TEST_CASES__
              if (!allData) return
              import('xlsx').then((XLSX) => {
                const wb = XLSX.utils.book_new()
                for (const [key, val] of Object.entries(allData)) {
                  const mod = val as { label: string; tests: any[] }
                  const rows = mod.tests.map((t) => ({
                    '#': t.id,
                    'Description': t.description,
                    'Steps': t.steps,
                    'Expected Result': t.expected,
                    'Actual Result': t.actual,
                    'Status': t.status,
                    'Date': t.date,
                  }))
                  const ws = XLSX.utils.json_to_sheet(rows)
                  XLSX.utils.book_append_sheet(wb, ws, mod.label.substring(0, 31))
                }
                XLSX.writeFile(wb, 'RhythmERP_Test_Specifications.xlsx')
              }).catch(() => {
                alert('xlsx library not installed. Run: npm install xlsx')
              })
            }
          }}
        >
          <FileSpreadsheet className="size-3.5" />
          Export
        </Button>
        <div className="flex-1" />
        <Separator orientation="vertical" className="h-5 mx-1" />
        <div className="flex items-center gap-3 text-[12px]">
          <span className="text-gray-500 dark:text-gray-400">{filteredTests.length} of {totalTests}</span>
          {bugCount > 0 && (
            <span className="text-red-500 dark:text-red-400 font-medium">{'\u{1F41B}'} {bugCount} bug{bugCount !== 1 ? 's' : ''}</span>
          )}
        </div>
      </div>

      {/* ─── Summary Badges ─── */}
      {totalTests > 0 && (
        <div className="flex items-center gap-2 px-4 py-2 border-b border-gray-50 dark:border-gray-800 shrink-0">
          <button
            onClick={() => setFilter('all')}
            className={`text-[11px] px-2 py-0.5 rounded-full font-medium transition-colors cursor-pointer ${filter === 'all' ? 'bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-100' : 'bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'}`}
          >
            All {totalTests}
          </button>
          <button
            onClick={() => setFilter('passed')}
            className={`text-[11px] px-2 py-0.5 rounded-full font-medium transition-colors cursor-pointer ${filter === 'passed' ? 'bg-green-200 dark:bg-green-800 text-green-800 dark:text-green-200' : 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 hover:bg-green-100 dark:hover:bg-green-900/40'}`}
          >
            {'\u2705'} Passed {passedCount}
          </button>
          <button
            onClick={() => setFilter('bug')}
            className={`text-[11px] px-2 py-0.5 rounded-full font-medium transition-colors cursor-pointer ${filter === 'bug' ? 'bg-red-200 dark:bg-red-800 text-red-800 dark:text-red-200' : 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/40'}`}
          >
            {'\u{1F41B}'} Bug {bugCount}
          </button>
          {todoCount > 0 && (
            <button
              onClick={() => setFilter('todo')}
              className={`text-[11px] px-2 py-0.5 rounded-full font-medium transition-colors cursor-pointer ${filter === 'todo' ? 'bg-amber-200 dark:bg-amber-800 text-amber-800 dark:text-amber-200' : 'bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 hover:bg-amber-100 dark:hover:bg-amber-900/40'}`}
            >
              {'\u{1F4CB}'} Todo {todoCount}
            </button>
          )}
          {notRunCount > 0 && (
            <button
              onClick={() => setFilter('not-run')}
              className={`text-[11px] px-2 py-0.5 rounded-full font-medium transition-colors cursor-pointer ${filter === 'not-run' ? 'bg-gray-300 dark:bg-gray-600 text-gray-800 dark:text-gray-200' : 'bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'}`}
            >
              Not Run {notRunCount}
            </button>
          )}
        </div>
      )}

      {/* ─── Table ─── */}
      <ScrollArea className="flex-1 min-h-0">
        <Table>
          <TableHeader>
            <TableRow className="bg-[#DFE9FB] dark:bg-indigo-900/30 hover:bg-[#DFE9FB] dark:hover:bg-indigo-900/30">
              <TableHead
                className="text-[#3F51B5] dark:text-indigo-300 text-[12px] font-semibold cursor-pointer select-none w-12"
                onClick={() => handleSort('id')}
              >
                <span className="inline-flex items-center gap-1"># <SortArrow col="id" sortCol={sortCol} sortDir={sortDir} /></span>
              </TableHead>
              <TableHead
                className="text-[#3F51B5] dark:text-indigo-300 text-[12px] font-semibold cursor-pointer select-none"
                onClick={() => handleSort('description')}
              >
                <span className="inline-flex items-center gap-1">Description <SortArrow col="description" sortCol={sortCol} sortDir={sortDir} /></span>
              </TableHead>
              <TableHead
                className="text-[#3F51B5] dark:text-indigo-300 text-[12px] font-semibold cursor-pointer select-none w-24"
                onClick={() => handleSort('status')}
              >
                <span className="inline-flex items-center gap-1">Status <SortArrow col="status" sortCol={sortCol} sortDir={sortDir} /></span>
              </TableHead>
              <TableHead
                className="text-[#3F51B5] dark:text-indigo-300 text-[12px] font-semibold cursor-pointer select-none w-28"
                onClick={() => handleSort('priority')}
              >
                <span className="inline-flex items-center gap-1">Priority <SortArrow col="priority" sortCol={sortCol} sortDir={sortDir} /></span>
              </TableHead>
              <TableHead
                className="text-[#3F51B5] dark:text-indigo-300 text-[12px] font-semibold cursor-pointer select-none w-28"
                onClick={() => handleSort('date')}
              >
                <span className="inline-flex items-center gap-1">Date <SortArrow col="date" sortCol={sortCol} sortDir={sortDir} /></span>
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredTests.map((test) => {
              const isExpanded = expandedTests.has(test.id)
              const statusInfo = getStatusDisplay(test)

              return (
                <React.Fragment key={test.id}>
                  {/* ─── Main Row ─── */}
                  <TableRow
                    className={`cursor-pointer transition-colors hover:bg-gray-50 dark:hover:bg-gray-800/50 ${isExpanded ? 'bg-gray-50/50 dark:bg-gray-800/30' : ''} ${test.status === 'bug' ? 'border-l-2 border-l-red-400 dark:border-l-red-500' : test.status === 'todo' ? 'border-l-2 border-l-amber-400 dark:border-l-amber-500' : ''}`}
                    onClick={() => toggleTest(test.id)}
                  >
                    <TableCell className="text-[12px] text-gray-500 dark:text-gray-400 font-mono py-2.5">
                      {test.id}
                    </TableCell>
                    <TableCell className="text-[13px] text-gray-800 dark:text-gray-100 py-2.5">
                      <div className="flex items-center gap-2">
                        {isExpanded ? (
                          <ChevronDown className="size-3.5 text-gray-400 dark:text-gray-500 shrink-0" />
                        ) : (
                          <ChevronRight className="size-3.5 text-gray-400 dark:text-gray-500 shrink-0" />
                        )}
                        <span className="truncate">{test.description}</span>
                      </div>
                    </TableCell>
                    <TableCell className="py-2.5">
                      <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium whitespace-nowrap ${statusInfo.color}`}>
                        {statusInfo.icon} {statusInfo.label}
                      </span>
                    </TableCell>
                    <TableCell className="py-2.5">
                      <PriorityBadge priority={test.priority} />
                    </TableCell>
                    <TableCell className="text-[11px] text-gray-500 dark:text-gray-400 py-2.5">
                      {test.date || '\u2014'}
                    </TableCell>
                  </TableRow>

                  {/* ─── Expanded Detail Row ─── */}
                  {isExpanded && (
                    <TableRow
                      className={`bg-gray-50/40 dark:bg-gray-800/20 hover:bg-gray-50/40 dark:hover:bg-gray-800/20 ${test.status === 'bug' ? 'border-l-2 border-l-red-400 dark:border-l-red-500' : test.status === 'todo' ? 'border-l-2 border-l-amber-400 dark:border-l-amber-500' : ''}`}
                    >
                      <TableCell colSpan={5} className="py-0 px-6">
                        <div className="py-3 pl-7 space-y-3">
                          {test.screenName && (
                            <div className="flex items-start gap-3">
                              <span className="text-[11px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider w-20 shrink-0 pt-0.5">Screen</span>
                              <span className="text-[12px] text-gray-600 dark:text-gray-300">{test.screenName}</span>
                            </div>
                          )}
                          {test.steps && (
                            <div className="flex items-start gap-3">
                              <span className="text-[11px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider w-20 shrink-0 pt-0.5">Steps</span>
                              <p className="text-[12px] text-gray-600 dark:text-gray-300 leading-5 whitespace-pre-line flex-1">{test.steps}</p>
                            </div>
                          )}
                          <div className="flex items-start gap-3">
                            <span className="text-[11px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider w-20 shrink-0 pt-0.5">Expected</span>
                            <p className="text-[12px] text-gray-600 dark:text-gray-300 leading-5 flex-1">{test.expected}</p>
                          </div>
                          <div className="flex items-start gap-3">
                            <span className="text-[11px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider w-20 shrink-0 pt-0.5">Actual</span>
                            <p className="text-[12px] text-gray-600 dark:text-gray-300 leading-5 flex-1">{test.actual || '\u2014'}</p>
                          </div>
                          {test.bugDetails && (
                            <div className="flex items-start gap-3">
                              <span className="text-[11px] font-semibold text-red-500 dark:text-red-400 uppercase tracking-wider w-20 shrink-0 pt-0.5">Bug</span>
                              <p className="text-[12px] text-red-600 dark:text-red-400 leading-5 bg-red-50 dark:bg-red-900/20 px-2.5 py-1.5 rounded flex-1">
                                {test.bugDetails}
                              </p>
                            </div>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  )}
                </React.Fragment>
              )
            })}

            {filteredTests.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} className="h-40 text-center">
                  <div className="flex flex-col items-center justify-center text-gray-400 dark:text-gray-500">
                    <Search className="size-8 mb-2 opacity-50" />
                    <p className="text-[13px]">No tests match your search criteria</p>
                  </div>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </ScrollArea>
    </div>
  )
}
