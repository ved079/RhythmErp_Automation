'use client'

import React, { useCallback, useMemo, useState } from 'react'
import { Play, RotateCcw, CheckCircle2, XCircle, Circle, Key, Monitor, Terminal, Search, ChevronDown, ChevronRight, RefreshCw, SlidersHorizontal, Database } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { ScrollArea } from '@/components/ui/scroll-area'
import { type TestPriority, type TestItem } from '@/data/testSpecGroups'
import { PriorityBadge, TestStatusIcon } from '@/components/shared/PriorityBadge'
import { BatchCreateSection } from '@/components/dialogs/BatchCreateSection'

function parseTestInfo(test: TestItem): { description: string } {
  const id = (test.id.split('::').pop() || test.id).replace(/^test_/, '')
  const match = id.match(/^([A-Z]+)_([A-Z]+\d+)_(.+)$/)
  const description = test.description || (match ? match[3].replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase()) : test.name || id.replace(/_/g, ' '))
  return { description }
}

const statusConfig = {
  passed: { bg: 'bg-green-50 dark:bg-green-900/15', border: 'border-green-200 dark:border-green-800', dot: 'bg-green-500', label: 'text-green-700 dark:text-green-300', icon: CheckCircle2 },
  failed: { bg: 'bg-red-50 dark:bg-red-900/15', border: 'border-red-200 dark:border-red-800', dot: 'bg-red-500', label: 'text-red-700 dark:text-red-300', icon: XCircle },
  pending: { bg: 'bg-transparent', border: 'border-gray-200 dark:border-gray-700', dot: 'bg-gray-400', label: 'text-gray-600 dark:text-gray-400', icon: Circle },
  running: { bg: 'bg-blue-50 dark:bg-blue-900/15', border: 'border-blue-200 dark:border-blue-800', dot: 'bg-blue-500', label: 'text-blue-700 dark:text-blue-300', icon: RefreshCw },
}

function TestSection({
  tests,
  testChecks,
  toggleTestCheck,
  isRunning,
  onRun,
  totalFailed,
  onRerunFailed,
  tokenBadge,
  tabSwitcher,
  showRawNames,
}: {
  tests: TestItem[]
  testChecks: Set<string>
  toggleTestCheck: (id: string) => void
  isRunning: boolean
  onRun: (selectedOnly: boolean) => void
  totalFailed: number
  onRerunFailed: () => void
  tokenBadge?: React.ReactNode
  tabSwitcher?: React.ReactNode
  showRawNames?: boolean
}) {
  const [search, setSearch] = useState('')
  const pendingOrRunning = tests.filter((t) => t.status === 'pending' || t.status === 'running')
  const allSelected = pendingOrRunning.length > 0 && pendingOrRunning.every((t) => testChecks.has(t.id))
  const selectedRunnable = tests.filter((t) => t.status === 'pending' && testChecks.has(t.id)).length
  const passedCount = tests.filter((t) => t.status === 'passed').length
  const failedCount = tests.filter((t) => t.status === 'failed').length
  const pendingCount = tests.filter((t) => t.status === 'pending').length
  const runningCount = tests.filter((t) => t.status === 'running').length
  const totalComplete = passedCount + failedCount
  const totalTests = tests.length

  const handleSelectAll = useCallback(() => {
    if (allSelected) {
      pendingOrRunning.forEach((t) => { if (testChecks.has(t.id)) toggleTestCheck(t.id) })
    } else {
      pendingOrRunning.forEach((t) => { if (!testChecks.has(t.id)) toggleTestCheck(t.id) })
    }
  }, [allSelected, pendingOrRunning, testChecks, toggleTestCheck])

  const filteredTests = useMemo(() => {
    if (!search.trim()) return tests
    const q = search.toLowerCase()
    return tests.filter((t) => t.name.toLowerCase().includes(q) || t.id.toLowerCase().includes(q))
  }, [tests, search])

  const progressPct = totalTests > 0 ? Math.round((totalComplete / totalTests) * 100) : 0

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* Action Bar */}
      <div className="flex items-center gap-1.5 px-4 py-2 border-b border-gray-100 dark:border-gray-700 shrink-0 bg-white dark:bg-gray-900 overflow-x-auto">
        <div className="flex items-center gap-1 bg-gray-50 dark:bg-gray-800/50 rounded-lg p-0.5 shrink-0">
          <button onClick={() => onRun(false)} disabled={isRunning || pendingCount === 0}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-[12px] font-medium bg-[#3F51B5] text-white hover:bg-[#2D3FC7] disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer shrink-0">
            <Play className="size-3" />Run All<span className="text-white/70 ml-0.5">({pendingCount})</span>
          </button>
          <button onClick={() => onRun(true)} disabled={isRunning || selectedRunnable === 0}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-[12px] font-medium text-[#3F51B5] hover:bg-[#E8EAF6] dark:hover:bg-[#1A237E]/30 disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer shrink-0">
            <Play className="size-3" />Selected<span className="text-[#3F51B5]/70 ml-0.5">({selectedRunnable})</span>
          </button>
        </div>
        <button onClick={handleSelectAll} disabled={isRunning}
          className="flex items-center gap-1 px-2 py-1.5 rounded-md text-[12px] font-medium text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer shrink-0">
          <CheckCircle2 className="size-3.5" />{allSelected ? 'Deselect All' : 'Select All'}
        </button>
        {totalFailed > 0 && (
          <button onClick={onRerunFailed} disabled={isRunning}
            className="flex items-center gap-1 px-2 py-1.5 rounded-md text-[12px] font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer shrink-0">
            <RotateCcw className="size-3" />Rerun Failed ({totalFailed})
          </button>
        )}
        {tokenBadge && <div className="shrink-0">{tokenBadge}</div>}
        <div className="relative flex-1 min-w-[120px] max-w-[200px] shrink-0">
          <Search className="absolute left-2 top-1/2 -translate-y-1/2 size-3 text-gray-400" />
          <input type="text" value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder="Search tests..."
            className="w-full pl-7 pr-2 py-1.5 text-[12px] bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md text-gray-800 dark:text-gray-100 placeholder:text-gray-400 focus:outline-none focus:ring-1 focus:ring-indigo-400"
          />
        </div>
        <span className="text-[11px] text-gray-400 dark:text-gray-500 shrink-0">{filteredTests.length}/{totalTests}</span>
        <div className="flex-1 min-w-[4px]" />
        {runningCount > 0 && (
          <span className="flex items-center gap-1 text-[11px] text-blue-600 dark:text-blue-400 font-medium animate-pulse shrink-0">
            <RefreshCw className="size-3 animate-spin" />{runningCount} running
          </span>
        )}
        <div className="flex items-center gap-2 shrink-0">
          <span className="flex items-center gap-1 text-[12px] font-medium text-green-600 dark:text-green-400"><CheckCircle2 className="size-3.5" />{passedCount}</span>
          <span className="flex items-center gap-1 text-[12px] font-medium text-red-500 dark:text-red-400"><XCircle className="size-3.5" />{failedCount}</span>
          <span className="flex items-center gap-1 text-[12px] font-medium text-gray-400"><Circle className="size-3.5" />{pendingCount}</span>
        </div>
      </div>

      {/* Progress bar */}
      {totalComplete > 0 && (
        <div className="h-1 bg-gray-100 dark:bg-gray-800 shrink-0">
          <div
            className="h-full bg-gradient-to-r from-green-500 to-emerald-400 transition-all duration-500"
            style={{ width: `${progressPct}%` }}
          />
        </div>
      )}

      {tabSwitcher}

      {/* Test List */}
      <ScrollArea className="flex-1 min-h-0">
        {filteredTests.length === 0 ? (
          <div className="text-center py-10 px-4">
            <SlidersHorizontal className="size-8 mx-auto text-gray-300 dark:text-gray-600 mb-2" />
            <p className="text-[13px] text-gray-400 dark:text-gray-500">{search ? 'No tests match your search' : 'No tests available'}</p>
          </div>
        ) : (
          <div className="mx-4 my-3 bg-white dark:bg-gray-800/50 rounded-xl border border-gray-300 dark:border-gray-500/70 overflow-hidden shadow-sm">
            <div className="flex items-center gap-3 px-4 py-2.5 bg-[#F1F2F7] dark:bg-gray-800 border-b border-gray-300 dark:border-gray-500/70 text-[11px] font-semibold text-[#3F51B5] dark:text-[#7986CB] tracking-wider">
              <div className="w-5 shrink-0" />
              <div className="flex-1">Test Name</div>
              <div className="w-24 shrink-0 text-center">Status</div>
              <div className="w-16 shrink-0 text-right">Duration</div>
            </div>
            <div className="divide-y divide-gray-200 dark:divide-gray-500/40">
              {filteredTests.map((test) => (
                <div key={test.id}
                  onClick={() => { if (test.status === 'pending' && !isRunning) toggleTestCheck(test.id) }}
                  className="flex items-center gap-3 px-4 py-2.5 hover:bg-[#E8EAF6]/40 dark:hover:bg-[#1A237E]/10 transition-colors cursor-pointer">
                  <Checkbox
                    checked={testChecks.has(test.id) || test.status === 'passed' || test.status === 'failed'}
                    disabled={isRunning || test.status !== 'pending'}
                    onCheckedChange={() => { if (test.status === 'pending') toggleTestCheck(test.id) }}
                    className="size-3.5 shrink-0 data-[state=checked]:bg-[#2D3FC7] data-[state=checked]:border-[#2D3FC7] pointer-events-none"
                  />
                  <span className={`flex-1 text-[14px] truncate ${
                    test.status === 'passed' ? 'text-[#999] dark:text-gray-500' :
                    test.status === 'failed' ? 'text-[#F44336] dark:text-red-400' :
                    'text-[#333] dark:text-gray-100'
                  }`}>
                    {showRawNames ? test.id : parseTestInfo(test).description}
                  </span>
                  <span className="w-24 shrink-0 flex items-center justify-center gap-1.5 text-[12px] font-['Manrope']">
                    {test.status === 'passed' && <><CheckCircle2 className="size-3 text-[#4CAF50]" /><span className="text-[#4CAF50] dark:text-green-400">Passed</span></>}
                    {test.status === 'failed' && <><XCircle className="size-3 text-[#F44336]" /><span className="text-[#F44336] dark:text-red-400">Failed</span></>}
                    {test.status === 'running' && <><RefreshCw className="size-3 animate-spin text-[#3F51B5]" /><span className="text-[#3F51B5] dark:text-[#7986CB]">Running</span></>}
                    {test.status === 'pending' && <><Circle className="size-3 text-[#ccc] dark:text-gray-600" /><span className="text-[#aaa] dark:text-gray-400">Pending</span></>}
                  </span>
                  <span className="w-16 shrink-0 text-right text-[12px] text-[#888] dark:text-gray-400 font-mono">
                    {test.duration || '—'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </ScrollArea>
    </div>
  )
}


export function TestRunnerTab({
  tests,
  testChecks,
  toggleTestCheck,
  isRunning,
  onRun,
  onRunByPriority,
  totalFailed,
  onRerunFailed,
  erpToken,
  erpTenantId,
  currentModuleId,
  onOpenCredentials,
  onClearToken,
  showRawNames,
}: {
  tests: TestItem[]
  testChecks: Set<string>
  toggleTestCheck: (id: string) => void
  isRunning: boolean
  onRun: (selectedOnly: boolean, testType?: 'ui' | 'api') => void
  onRunByPriority: (priority: TestPriority) => void
  totalFailed: number
  onRerunFailed: () => void
  erpToken?: string
  erpTenantId?: string
  currentModuleId?: string
  onOpenCredentials?: () => void
  onClearToken?: () => void
  onRunApi?: (selectedOnly: boolean) => void
  showRawNames?: boolean
}) {
  const [activeTab, setActiveTab] = useState<'ui' | 'api' | 'batch'>('ui')

  const uiTests = tests.filter((t) => !t.testType || t.testType === 'ui')
  const apiTests = tests.filter((t) => t.testType === 'api')
  const hasApi = apiTests.length > 0
  const hasUi = uiTests.length > 0

  const isBatch = activeTab === 'batch'
  const effectiveTab = isBatch ? 'batch' : (hasApi ? activeTab : 'ui')

  const visibleTests = !isBatch ? (effectiveTab === 'ui' ? uiTests : apiTests) : []

  const handleRun = (selectedOnly: boolean) => {
    if (effectiveTab === 'api' && !erpToken && onOpenCredentials) {
      onOpenCredentials()
      return
    }
    onRun(selectedOnly, effectiveTab === 'batch' ? undefined : effectiveTab)
  }

  const visibleTotalFailed = visibleTests.filter((t) => t.status === 'failed').length

  if (!hasUi && !hasApi && activeTab !== 'batch') {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-400 dark:text-gray-500 gap-2">
        <Play className="size-8" />
        <span className="text-[13px]">Select a module to view its tests</span>
      </div>
    )
  }

  const tabSwitcher = (
    <div className="flex justify-center px-4 py-2 border-b border-gray-100 dark:border-gray-700 shrink-0 bg-white dark:bg-gray-900">
      <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-0.5 shadow-sm">
        <button
          onClick={() => setActiveTab('ui')}
          className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-md text-[12px] font-medium transition-colors cursor-pointer ${
            effectiveTab === 'ui'
              ? 'bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 shadow-sm'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
        >
          <Monitor className="size-3.5" />
          UI Tests
          <span className="ml-1 text-[10px] opacity-70">({uiTests.length})</span>
        </button>
        {hasApi && (
          <button
            onClick={() => setActiveTab('api')}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-md text-[12px] font-medium transition-colors cursor-pointer ${
              effectiveTab === 'api'
                ? 'bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 shadow-sm'
                : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            <Terminal className="size-3.5" />
            API Tests
            <span className="ml-1 text-[10px] opacity-70">({apiTests.length})</span>
          </button>
        )}
        <button
          onClick={() => setActiveTab('batch')}
          className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-md text-[12px] font-medium transition-colors cursor-pointer ${
            isBatch
              ? 'bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 shadow-sm'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
        >
            <Database className="size-3.5" />
            Batch
            <span className="ml-1 text-[11px] text-gray-500 dark:text-gray-400 font-normal">(Multiple Validate Create)</span>
          </button>
      </div>
    </div>
  )

  if (isBatch) {
    return (
      <div className="flex flex-col h-full min-h-0">
        {tabSwitcher}
        <div className="flex-1 overflow-auto p-4">
          <BatchCreateSection
            moduleId={currentModuleId || ''}
            erpToken={erpToken || ''}
            erpTenantId={erpTenantId || '681'}
            onNeedsToken={() => onOpenCredentials?.()}
            onClearToken={() => onClearToken?.()}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full min-h-0">
      <TestSection
        tabSwitcher={tabSwitcher}
        tests={visibleTests}
        testChecks={testChecks}
        toggleTestCheck={toggleTestCheck}
        isRunning={isRunning}
        onRun={handleRun}
        totalFailed={visibleTotalFailed}
        onRerunFailed={onRerunFailed}
        showRawNames={showRawNames}
        tokenBadge={effectiveTab === 'api' ? (
          <button onClick={onOpenCredentials} className={`flex items-center gap-1.5 text-[11px] px-2 py-1 rounded-full cursor-pointer ${erpToken ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' : 'bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400'}`}>
            <Key className="size-3" />
            {erpToken ? 'Token set' : 'Set Token'}
          </button>
        ) : undefined}
      />
    </div>
  )
}
