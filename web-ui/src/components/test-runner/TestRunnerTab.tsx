'use client'

import React, { useCallback, useMemo, useState } from 'react'
import { Play, RotateCcw, CheckCircle2, XCircle, Circle, Key, Monitor, Terminal, Search, RefreshCw, SlidersHorizontal, Database, ChevronDown } from 'lucide-react'
import { Checkbox } from '@/components/ui/checkbox'
import { ScrollArea } from '@/components/ui/scroll-area'
import { type TestPriority, type TestItem } from '@/data/testSpecGroups'
import { BatchCreateSection } from '@/components/dialogs/BatchCreateSection'

function parseTestInfo(test: TestItem): { description: string } {
  const id = (test.id.split('::').pop() || test.id).replace(/^test_/, '')
  const match = id.match(/^([A-Z]+)_([A-Z]+\d+)_(.+)$/)
  const description = test.description || (match ? match[3].replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase()) : test.name || id.replace(/_/g, ' '))
  return { description }
}

const STATUS_STYLES = {
  passed:  { badge: 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400', dot: 'bg-emerald-500', label: 'Passed' },
  failed:  { badge: 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400', dot: 'bg-red-500', label: 'Failed' },
  running: { badge: 'bg-[#3F51B5]/15 dark:bg-[#3F51B5]/20 text-[#3F51B5] dark:text-[#7986CB]', dot: 'bg-[#3F51B5]', label: 'Running' },
  pending: { badge: 'bg-gray-100 dark:bg-gray-700 text-gray-400 dark:text-gray-500', dot: 'bg-gray-300 dark:bg-gray-600', label: 'Pending' },
}

function StatusBadge({ status }: { status: TestItem['status'] }) {
  const s = STATUS_STYLES[status ?? 'pending']
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium ${s.badge}`}>
      {status === 'running'
        ? <RefreshCw className="size-2.5 animate-spin" />
        : <span className={`size-1.5 rounded-full ${s.dot}`} />}
      {s.label}
    </span>
  )
}

function CredentialDropdown({
  credentials,
  activeCredId,
  onSelectCred,
  onOpenCredentialsScreen,
}: {
  credentials?: { id: string; name: string; email: string; isDefault: boolean }[]
  activeCredId?: string | null
  onSelectCred?: (credId: string) => void
  onOpenCredentialsScreen?: () => void
}) {
  const [open, setOpen] = useState(false)
  const active = credentials?.find(c => c.id === activeCredId)

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className={`flex items-center gap-1.5 text-[11px] px-2.5 py-1 rounded-full cursor-pointer transition-colors ${
          active
            ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400'
            : 'bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400'
        }`}
      >
        <Key className="size-3" />
        {active ? active.name : 'Set Credential'}
        <ChevronDown className="size-3" />
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-50" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full mt-1 z-50 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg min-w-[240px] overflow-hidden">
            {(!credentials || credentials.length === 0) ? (
              <div className="px-3 py-6 text-center text-[12px] text-gray-400 dark:text-gray-500">No saved credentials</div>
            ) : (
              <>
                <div className="max-h-48 overflow-y-auto">
                  {credentials.map(cred => (
                    <button
                      key={cred.id}
                      onClick={() => { onSelectCred?.(cred.id); setOpen(false) }}
                      className={`w-full flex items-center gap-2 px-3 py-2 text-[12px] text-left hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer ${
                        cred.id === activeCredId ? 'bg-[#3F51B5]/10 dark:bg-[#3F51B5]/20' : ''
                      }`}
                    >
                      <div className="flex-1 min-w-0">
                        <div className={`truncate font-medium ${cred.id === activeCredId ? 'text-[#3F51B5] dark:text-[#7986CB]' : 'text-gray-700 dark:text-gray-200'}`}>{cred.name}</div>
                        <div className="truncate text-gray-400">{cred.email}</div>
                      </div>
                      <div className="flex items-center gap-1 shrink-0">
                        {cred.id === activeCredId && <span className="text-[10px] bg-[#3F51B5] text-white px-1.5 py-0.5 rounded-full">Active</span>}
                        {cred.isDefault && <span className="text-yellow-500 text-[12px]">★</span>}
                      </div>
                    </button>
                  ))}
                </div>
                <div className="border-t border-gray-200 dark:border-gray-700">
                  <button
                    onClick={() => { setOpen(false); onOpenCredentialsScreen?.() }}
                    className="w-full px-3 py-2 text-[12px] text-left text-[#3F51B5] dark:text-[#7986CB] hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer font-medium"
                  >
                    Manage credentials...
                  </button>
                </div>
              </>
            )}
          </div>
        </>
      )}
    </div>
  )
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
  uiCredentialBadge,
  tabSwitcher,
  showRawNames,
  sectionLabel,
}: {
  tests: TestItem[]
  testChecks: Set<string>
  toggleTestCheck: (id: string) => void
  isRunning: boolean
  onRun: (selectedOnly: boolean) => void
  totalFailed: number
  onRerunFailed: () => void
  tokenBadge?: React.ReactNode
  uiCredentialBadge?: React.ReactNode
  tabSwitcher?: React.ReactNode
  showRawNames?: boolean
  sectionLabel?: string
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
  const progressPct = totalTests > 0 ? Math.round((totalComplete / totalTests) * 100) : 0

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

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {tabSwitcher}

      {/* Panel */}
      <div className="mx-4 my-3 flex flex-col flex-1 min-h-0 border border-gray-300 dark:border-gray-500/70 rounded-lg overflow-hidden shadow-sm">

        {/* Header */}
        <div className="flex items-center gap-3 px-4 py-2.5 bg-gradient-to-r from-[#3F51B5]/[0.07] to-[#3F51B5]/[0.03] dark:from-[#3F51B5]/20 dark:to-[#3F51B5]/10 border-b border-gray-300 dark:border-gray-500/70 shrink-0">
          <span className="text-[13px] font-semibold text-gray-700 dark:text-gray-200 flex-1">
            {sectionLabel ?? 'Tests'}
            <span className="ml-2 text-[11px] font-normal text-gray-400">{totalTests} total</span>
          </span>

          <div className="flex items-center gap-3">
            {runningCount > 0 && (
              <span className="flex items-center gap-1 text-[11px] text-[#3F51B5] dark:text-[#7986CB] font-medium animate-pulse">
                <RefreshCw className="size-3 animate-spin" />{runningCount} running
              </span>
            )}
            <span className="flex items-center gap-1 text-[12px] font-medium text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="size-3.5" />{passedCount}
            </span>
            <span className="flex items-center gap-1 text-[12px] font-medium text-red-500 dark:text-red-400">
              <XCircle className="size-3.5" />{failedCount}
            </span>
            <span className="flex items-center gap-1 text-[12px] font-medium text-gray-400">
              <Circle className="size-3.5" />{pendingCount}
            </span>
          </div>
        </div>

        {/* Progress bar */}
        {totalComplete > 0 && (
          <div className="h-1 bg-gray-100 dark:bg-gray-800 shrink-0">
            <div
              className="h-full transition-all duration-500"
              style={{
                width: `${progressPct}%`,
                background: failedCount > 0 && progressPct === 100
                  ? 'linear-gradient(90deg, #22c55e 0%, #ef4444 100%)'
                  : progressPct === 100
                  ? '#22c55e'
                  : 'linear-gradient(90deg, #3F51B5, #5C6BC0)',
              }}
            />
          </div>
        )}

        {/* Toolbar */}
        <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shrink-0 flex-wrap">
          <div className="flex items-center gap-1 bg-gray-50 dark:bg-gray-800/50 rounded-lg p-0.5">
            <button
              onClick={() => onRun(false)}
              disabled={isRunning || pendingCount === 0}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-[12px] font-medium bg-[#3F51B5] text-white hover:bg-[#3949AB] disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer"
            >
              <Play className="size-3" />
              Run All
              <span className="text-white/70">({pendingCount})</span>
            </button>
            <button
              onClick={() => onRun(true)}
              disabled={isRunning || selectedRunnable === 0}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-[12px] font-medium text-[#3F51B5] dark:text-[#7986CB] hover:bg-[#3F51B5]/10 dark:hover:bg-[#3F51B5]/20 disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer"
            >
              <Play className="size-3" />
              Selected
              <span className="opacity-60">({selectedRunnable})</span>
            </button>
          </div>

          <button
            onClick={handleSelectAll}
            disabled={isRunning}
            className="flex items-center gap-1 px-2 py-1.5 rounded-md text-[12px] text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-40 transition-colors cursor-pointer"
          >
            <CheckCircle2 className="size-3.5" />
            {allSelected ? 'Deselect All' : 'Select All'}
          </button>

          {totalFailed > 0 && (
            <button
              onClick={onRerunFailed}
              disabled={isRunning}
              className="flex items-center gap-1 px-2 py-1.5 rounded-md text-[12px] text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-40 transition-colors cursor-pointer"
            >
              <RotateCcw className="size-3" />
              Rerun Failed ({totalFailed})
            </button>
          )}

          {uiCredentialBadge && <div className="shrink-0">{uiCredentialBadge}</div>}
          {tokenBadge && <div className="shrink-0">{tokenBadge}</div>}

          <div className="flex-1" />

          <div className="relative">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 size-3 text-gray-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search..."
              className="w-36 pl-6 pr-2 py-1.5 text-[12px] bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md text-gray-800 dark:text-gray-100 placeholder:text-gray-400 focus:outline-none focus:ring-1 focus:ring-[#3F51B5]/50"
            />
          </div>
          <span className="text-[11px] text-gray-400 shrink-0">{filteredTests.length}/{totalTests}</span>
        </div>

        {/* Table */}
        <ScrollArea className="flex-1 min-h-0">
          {filteredTests.length === 0 ? (
            <div className="text-center py-10 px-4">
              <SlidersHorizontal className="size-8 mx-auto text-gray-300 dark:text-gray-600 mb-2" />
              <p className="text-[13px] text-gray-400 dark:text-gray-500">
                {search ? 'No tests match your search' : 'No tests available'}
              </p>
            </div>
          ) : (
            <>
              <div className="flex items-center gap-3 px-4 py-2 bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700 text-[10px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider">
                <div className="w-4 shrink-0" />
                <div className="flex-1">Test Name</div>
                <div className="w-20 shrink-0 text-center">Status</div>
                <div className="w-14 shrink-0 text-right">Duration</div>
              </div>
              <div className="divide-y divide-gray-100 dark:divide-gray-700/50">
                {filteredTests.map((test) => {
                  const { description } = parseTestInfo(test)
                  const isSelectable = test.status === 'pending' && !isRunning
                  return (
                    <div
                      key={test.id}
                      onClick={() => { if (isSelectable) toggleTestCheck(test.id) }}
                      className={`flex items-center gap-3 px-4 py-2.5 transition-colors ${isSelectable ? 'cursor-pointer hover:bg-[#3F51B5]/[0.04] dark:hover:bg-[#3F51B5]/10' : 'cursor-default'} ${test.status === 'running' ? 'bg-[#3F51B5]/[0.03] dark:bg-[#3F51B5]/10' : ''}`}
                    >
                      <Checkbox
                        checked={testChecks.has(test.id) || test.status === 'passed' || test.status === 'failed'}
                        disabled={isRunning || test.status !== 'pending'}
                        onCheckedChange={() => { if (test.status === 'pending') toggleTestCheck(test.id) }}
                        className="size-3.5 shrink-0 data-[state=checked]:bg-[#3F51B5] data-[state=checked]:border-[#3F51B5] pointer-events-none"
                      />
                      <span className={`flex-1 text-[13px] truncate ${
                        test.status === 'passed'  ? 'text-gray-400 dark:text-gray-500' :
                        test.status === 'failed'  ? 'text-red-600 dark:text-red-400' :
                        test.status === 'running' ? 'text-[#3F51B5] dark:text-[#7986CB] font-medium' :
                                                    'text-gray-700 dark:text-gray-200'
                      }`}>
                        {showRawNames ? test.id : description}
                      </span>
                      <div className="w-20 shrink-0 flex justify-center">
                        <StatusBadge status={test.status} />
                      </div>
                      <span className="w-14 shrink-0 text-right text-[11px] text-gray-400 dark:text-gray-500 font-mono">
                        {test.duration || '—'}
                      </span>
                    </div>
                  )
                })}
              </div>
            </>
          )}
        </ScrollArea>
      </div>
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
  credentials,
  activeCredId,
  onSelectCred,
  onOpenCredentialsScreen,
  allowedTabs,
  onSubTabChange,
  initialSubTab,
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
  credentials?: { id: string; name: string; email: string; isDefault: boolean }[]
  activeCredId?: string | null
  onSelectCred?: (credId: string) => void
  onOpenCredentialsScreen?: () => void
  allowedTabs?: ('ui' | 'api' | 'batch')[] | null
  onSubTabChange?: (tab: 'ui' | 'api' | 'batch') => void
  initialSubTab?: 'ui' | 'api' | 'batch'
}) {
  const uiTests = tests.filter((t) => !t.testType || t.testType === 'ui')
  const apiTests = tests.filter((t) => t.testType === 'api')
  const hasApi = apiTests.length > 0

  // Tabs restricted by admin; null = no restriction
  const tabAllowed = (t: 'ui' | 'api' | 'batch') =>
    !allowedTabs || allowedTabs.includes(t)

  const defaultTab: 'ui' | 'api' | 'batch' =
    initialSubTab && tabAllowed(initialSubTab) ? initialSubTab :
    tabAllowed('ui') ? 'ui' : tabAllowed('batch') ? 'batch' : 'api'

  const [activeTab, setActiveTab] = useState<'ui' | 'api' | 'batch'>(defaultTab)

  const isBatch = activeTab === 'batch'
  const effectiveTab = isBatch ? 'batch' : (hasApi ? activeTab : 'ui')
  const visibleTests = !isBatch ? (effectiveTab === 'ui' ? uiTests : apiTests) : []

  const handleRun = (selectedOnly: boolean) => {
    if (effectiveTab === 'api' && !erpToken && onOpenCredentials) {
      onOpenCredentials()
      return
    }
    onRun(selectedOnly, effectiveTab === 'batch' ? undefined : effectiveTab as 'ui' | 'api')
  }

  const visibleTotalFailed = visibleTests.filter((t) => t.status === 'failed').length

  const tabSwitcher = (
    <div className="flex items-center gap-0 px-4 py-0 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shrink-0">
      {(['ui', ...(hasApi ? (['api'] as const) : []), 'batch'] as const).filter(tabAllowed).map((t) => (
        <button
          key={t}
          type="button"
          onClick={() => { setActiveTab(t); onSubTabChange?.(t) }}
          className={`flex items-center gap-1.5 px-3.5 py-2.5 text-[12px] font-medium border-b-2 transition-colors cursor-pointer ${
            effectiveTab === t
              ? 'border-[#3F51B5] text-[#3F51B5] dark:text-[#7986CB]'
              : 'border-transparent text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300'
          }`}
        >
          {t === 'ui'    && <Monitor className="size-3.5" />}
          {t === 'api'   && <Terminal className="size-3.5" />}
          {t === 'batch' && <Database className="size-3.5" />}
          {t === 'ui'    ? 'UI Tests' : t === 'api' ? 'API Tests' : 'Batch Create'}
          {t !== 'batch' && (
            <span className="text-[10px] opacity-60">
              ({t === 'ui' ? uiTests.length : apiTests.length})
            </span>
          )}
        </button>
      ))}
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
        sectionLabel={effectiveTab === 'api' ? 'API Tests' : 'UI Tests'}
        tokenBadge={effectiveTab === 'api' ? (
          <div className="flex items-center gap-1">
            <button
              onClick={onOpenCredentials}
              className={`flex items-center gap-1.5 text-[11px] px-2.5 py-1 rounded-full cursor-pointer transition-colors ${
                erpToken
                  ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400'
                  : 'bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400'
              }`}
            >
              <Key className="size-3" />
              {erpToken ? 'Token set' : 'Set Token'}
            </button>
            <button onClick={() => { onClearToken?.(); onOpenCredentials?.(); }} className="flex items-center gap-1 text-[11px] px-2 py-1 rounded-full cursor-pointer bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20 dark:hover:text-red-400 transition-colors">
              <RotateCcw className="size-3" />
              Reset
            </button>
          </div>
        ) : undefined}
        uiCredentialBadge={effectiveTab === 'ui' && currentModuleId !== 'direct-pb-flow' && currentModuleId !== 'po-qc-pb-flow' ? (
          <CredentialDropdown
            credentials={credentials}
            activeCredId={activeCredId}
            onSelectCred={onSelectCred}
            onOpenCredentialsScreen={onOpenCredentialsScreen}
          />
        ) : undefined}
      />
    </div>
  )
}
