'use client'

import React, { useCallback, useMemo, useState } from 'react'
import { Play, RotateCcw, CheckCircle2, XCircle, Circle, Key, Monitor, Terminal, Search, ChevronDown, ChevronRight, RefreshCw, SlidersHorizontal } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { ScrollArea } from '@/components/ui/scroll-area'
import { type TestPriority, type TestItem } from '@/data/testSpecGroups'
import { PriorityBadge, TestStatusIcon } from '@/components/shared/PriorityBadge'

function parseTestInfo(test: TestItem): { badge: string; description: string } {
  const id = (test.id.split('::').pop() || test.id).replace(/^test_/, '')
  const match = id.match(/^([A-Z]+)_([A-Z]+\d+)_(.+)$/)
  const badge = match ? `${match[1]}-${match[2]}` : ''
  const description = test.description || (match ? match[3].replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase()) : test.name || id.replace(/_/g, ' '))
  return { badge, description }
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
}) {
  const [search, setSearch] = useState('')
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set())

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

  const toggleGroup = useCallback((name: string) => {
    setCollapsedGroups((prev) => {
      const next = new Set(prev)
      if (next.has(name)) next.delete(name); else next.add(name)
      return next
    })
  }, [])

  const testGroups = useMemo(() => {
    const groups: { name: string; tests: TestItem[] }[] = []
    let currentGroup: string | null = null
    for (const t of tests) {
      const cls = t.id.replace(/\d+$/, '').replace(/T/, 'Test')
      if (cls !== currentGroup) {
        currentGroup = cls
        groups.push({ name: cls, tests: [] })
      }
      groups[groups.length - 1].tests.push(t)
    }
    return groups
  }, [tests])

  const filteredGroups = useMemo(() => {
    if (!search.trim()) return testGroups
    const q = search.toLowerCase()
    return testGroups
      .map((g) => ({ ...g, tests: g.tests.filter((t) => t.name.toLowerCase().includes(q) || t.id.toLowerCase().includes(q)) }))
      .filter((g) => g.tests.length > 0)
  }, [testGroups, search])

  const progressPct = totalTests > 0 ? Math.round((totalComplete / totalTests) * 100) : 0

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* Action Bar */}
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-gray-100 dark:border-gray-700 shrink-0 flex-wrap bg-white dark:bg-gray-900">
        <Button
          onClick={() => onRun(false)}
          disabled={isRunning || pendingCount === 0}
          className="bg-[#2D3FC7] hover:bg-[#3F51B5] text-white h-8 text-[12px] gap-1.5 px-4 cursor-pointer font-medium shadow-sm"
        >
          <Play className="size-3.5" />
          Run All
          <span className="ml-0.5 opacity-80">({pendingCount})</span>
        </Button>
        <Button
          onClick={() => onRun(true)}
          disabled={isRunning || selectedRunnable === 0}
          className="bg-[#2D3FC7] hover:bg-[#3F51B5] text-white h-8 text-[12px] gap-1.5 px-4 cursor-pointer font-medium shadow-sm"
        >
          <Play className="size-3.5" />
          Run Selected
          <span className="ml-0.5 opacity-80">({selectedRunnable})</span>
        </Button>
        <Button
          onClick={handleSelectAll}
          disabled={isRunning}
          variant="outline"
          className="border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 h-8 text-[12px] gap-1.5 px-3 cursor-pointer"
        >
          {allSelected ? '✖ Deselect All' : '☑ Select All'}
        </Button>
        {totalFailed > 0 && (
          <Button
            onClick={onRerunFailed}
            disabled={isRunning}
            variant="outline"
            className="border-orange-300 dark:border-orange-700 text-orange-600 dark:text-orange-400 h-8 text-[12px] gap-1.5 px-3 cursor-pointer"
          >
            <RotateCcw className="size-3.5" />
            Rerun Failed ({totalFailed})
          </Button>
        )}
        {tokenBadge}
        <div className="flex-1" />
        {runningCount > 0 && (
          <span className="flex items-center gap-1.5 text-[11px] text-blue-600 dark:text-blue-400 font-medium animate-pulse">
            <RefreshCw className="size-3 animate-spin" />
            {runningCount} running
          </span>
        )}
        <div className="flex items-center gap-3 text-[12px]">
          <span className="flex items-center gap-1.5 text-green-600 dark:text-green-400 font-medium">
            <CheckCircle2 className="size-3.5" /> {passedCount}
          </span>
          <span className="flex items-center gap-1.5 text-red-500 dark:text-red-400 font-medium">
            <XCircle className="size-3.5" /> {failedCount}
          </span>
          <span className="flex items-center gap-1.5 text-gray-400">
            <Circle className="size-3" /> {pendingCount}
          </span>
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

      {/* Search + filter bar */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-gray-100 dark:border-gray-700 shrink-0 bg-gray-50/50 dark:bg-gray-800/20">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search tests by name..."
            className="w-full pl-8 pr-3 py-1.5 text-[12px] bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md text-gray-800 dark:text-gray-100 placeholder:text-gray-400 focus:outline-none focus:ring-1 focus:ring-indigo-400"
          />
        </div>
        <span className="text-[11px] text-gray-400 dark:text-gray-500">
          {filteredGroups.reduce((s, g) => s + g.tests.length, 0)} / {totalTests} tests
        </span>
      </div>

      {/* Test List */}
      <ScrollArea className="flex-1 min-h-0">
        <div className="px-4 py-3 space-y-3">
          {filteredGroups.length === 0 && (
            <div className="text-center py-10">
              <SlidersHorizontal className="size-8 mx-auto text-gray-300 dark:text-gray-600 mb-2" />
              <p className="text-[13px] text-gray-400 dark:text-gray-500">{search ? 'No tests match your search' : 'No tests available'}</p>
            </div>
          )}
          {filteredGroups.map((group) => {
            const groupPassed = group.tests.filter((t) => t.status === 'passed').length
            const groupFailed = group.tests.filter((t) => t.status === 'failed').length
            const groupPending = group.tests.filter((t) => t.status === 'pending').length
            const isCollapsed = collapsedGroups.has(group.name)

            return (
              <div key={group.name} className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden shadow-[0_1px_2px_rgba(0,0,0,0.03)] dark:shadow-none">
                {/* Group Header */}
                <button
                  onClick={() => toggleGroup(group.name)}
                  className="w-full flex items-center gap-2.5 px-4 py-2.5 bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800/70 transition-colors cursor-pointer group"
                >
                  {isCollapsed ? <ChevronRight className="size-3.5 text-gray-400" /> : <ChevronDown className="size-3.5 text-gray-400" />}
                  <span className="text-[13px] font-semibold text-gray-800 dark:text-gray-100 flex-1 text-left">{group.name}</span>
                  <span className="text-[11px] text-gray-500 dark:text-gray-400 mr-1">{group.tests.length} tests</span>
                  {groupPassed > 0 && (
                    <span className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                      <CheckCircle2 className="size-2.5" /> {groupPassed}
                    </span>
                  )}
                  {groupFailed > 0 && (
                    <span className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400">
                      <XCircle className="size-2.5" /> {groupFailed}
                    </span>
                  )}
                  {groupPending > 0 && (
                    <span className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400">
                      <Circle className="size-2.5" /> {groupPending}
                    </span>
                  )}
                </button>

                {/* Test Rows */}
                {!isCollapsed && (
                  <div className="divide-y divide-gray-100 dark:divide-gray-800">
                    {group.tests.map((test) => {
                      const cfg = test.status === 'passed' ? statusConfig.passed : test.status === 'failed' ? statusConfig.failed : test.status === 'running' ? statusConfig.running : statusConfig.pending
                      const StatusIcon = cfg.icon

                      return (
                        <div
                          key={test.id}
                          className={`flex items-center gap-3 px-4 py-2.5 transition-colors ${cfg.bg} ${cfg.border} border-l-2 ${test.status === 'running' ? 'border-l-blue-500' : test.status === 'failed' ? 'border-l-red-500' : test.status === 'passed' ? 'border-l-green-500' : 'border-l-transparent'}`}
                        >
                          <Checkbox
                            checked={testChecks.has(test.id) || test.status === 'passed' || test.status === 'failed'}
                            disabled={isRunning || test.status !== 'pending'}
                            onCheckedChange={() => { if (test.status === 'pending') toggleTestCheck(test.id) }}
                            className="size-3.5 data-[state=checked]:bg-[#2D3FC7] data-[state=checked]:border-[#2D3FC7]"
                          />
                          <div className="flex-1 min-w-0 flex items-center gap-2.5">
                            {(() => {
                              const { badge, description } = parseTestInfo(test)
                              return (
                                <>
                                  {badge && (
                                    <span className="text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 shrink-0">
                                      {badge}
                                    </span>
                                  )}
                                  <span className={`text-[13px] leading-snug truncate ${
                                    test.status === 'running' ? 'text-indigo-600 dark:text-indigo-400 font-medium' :
                                    test.status === 'failed' ? 'text-red-700 dark:text-red-300 font-medium' :
                                    test.status === 'passed' ? 'text-gray-500 dark:text-gray-400' :
                                    'text-gray-800 dark:text-gray-100'
                                  }`}>
                                    {description}
                                    {test.status === 'running' && (
                                      <span className="ml-2 inline-flex">
                                        <span className="animate-ping size-1.5 rounded-full bg-indigo-500 mr-0.5" />
                                        <span className="animate-ping size-1.5 rounded-full bg-indigo-500 mr-0.5" />
                                      </span>
                                    )}
                                  </span>
                                </>
                              )
                            })()}
                          </div>
                          {test.status === 'running' && (
                            <span className="text-[10px] text-indigo-600 dark:text-indigo-400 font-medium bg-indigo-50 dark:bg-indigo-900/30 px-2 py-0.5 rounded-full">Running</span>
                          )}
                          {test.status !== 'running' && (
                            <>
                              <PriorityBadge priority={test.priority} />
                              <StatusIcon className={`size-3.5 ${cfg.label}`} />
                            </>
                          )}
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })}
        </div>
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
  onOpenCredentials,
  onRunApi,
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
  onOpenCredentials?: () => void
  onRunApi?: (selectedOnly: boolean) => void
}) {
  const [activeTab, setActiveTab] = useState<'ui' | 'api'>('ui')

  const uiTests = tests.filter((t) => !t.testType || t.testType === 'ui')
  const apiTests = tests.filter((t) => t.testType === 'api')
  const hasApi = apiTests.length > 0
  const hasUi = uiTests.length > 0

  const effectiveTab = hasApi ? activeTab : 'ui'

  const visibleTests = effectiveTab === 'ui' ? uiTests : apiTests

  const handleRun = (selectedOnly: boolean) => {
    if (effectiveTab === 'api' && !erpToken && onOpenCredentials) {
      onOpenCredentials()
      return
    }
    onRun(selectedOnly, effectiveTab)
  }

  const visibleTotalFailed = visibleTests.filter((t) => t.status === 'failed').length

  if (!hasUi && !hasApi) {
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
      </div>
    </div>
  )

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
        tokenBadge={effectiveTab === 'api' ? (
          <span className={`flex items-center gap-1.5 text-[11px] px-2 py-1 rounded-full ${erpToken ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' : 'bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400'}`}>
            <Key className="size-3" />
            {erpToken ? 'Token set' : (
              <button onClick={onOpenCredentials} className="underline font-medium cursor-pointer">Set Token</button>
            )}
          </span>
        ) : undefined}
      />
    </div>
  )
}