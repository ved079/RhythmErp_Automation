'use client'

import React from 'react'
import { Progress } from '@/components/ui/progress'
import { Sparkline } from '@/components/ui/sparkline'
import {
  PassRateTrendChart, ModuleHealthBarChart, BugDistributionPie, TestExecutionTimeline,
} from '@/components/dashboard/DashboardCharts'
import { ExportMenu } from '@/components/export/ExportUtils'
import { DashboardTab } from '@/components/dashboard/DashboardTab'
import {
  RefreshCw, Loader2, CheckCircle2, Bug, Play, LayoutDashboard, AlertTriangle,
  BarChart3, Activity, Clock, XCircle, ChevronRight, TrendingUp,
} from 'lucide-react'
import type { RunSnapshot, ModuleHealth } from '@/lib/types'

interface DashboardRendererProps {
  dashboardStats: Record<string, unknown> | null
  dashboardLoading: boolean
  runHistory: RunSnapshot[]
  moduleHealth: ModuleHealth[]
  handleSelectModule: (id: string) => void
  handleRunModule?: (moduleId: string) => void
  loadDashboardStats: () => Promise<void>
}

const STATUS_BUG: Record<string, string> = {
  open:        'bg-orange-50 dark:bg-orange-900/20 text-orange-700 dark:text-orange-400 border border-orange-200 dark:border-orange-800/40',
  in_progress: 'bg-[#3F51B5]/[0.08] dark:bg-[#3F51B5]/20 text-[#3F51B5] dark:text-[#7986CB] border border-[#3F51B5]/20',
  fixed:       'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/40',
  closed:      'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 border border-gray-200 dark:border-gray-600',
  rejected:    'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 border border-gray-200 dark:border-gray-600',
}
const STATUS_LABEL: Record<string, string> = { open: 'Open', in_progress: 'In Progress', fixed: 'Fixed', closed: 'Closed', rejected: 'Rejected' }
const PRIORITY_CLS: Record<string, string> = {
  high:   'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800/40',
  medium: 'bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800/40',
  low:    'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/40',
}

function Panel({ title, icon: Icon, children, className = '' }: { title: string; icon: React.ElementType; children: React.ReactNode; className?: string }) {
  return (
    <div className={`bg-white dark:bg-gray-800/80 rounded-lg border border-gray-200 dark:border-gray-700/70 shadow-sm overflow-hidden ${className}`}>
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-gray-100 dark:border-gray-700/60 bg-gradient-to-r from-[#3F51B5]/[0.05] to-transparent">
        <Icon className="size-3.5 text-[#3F51B5] dark:text-[#7986CB]" />
        <span className="text-[12px] font-semibold text-gray-700 dark:text-gray-200">{title}</span>
      </div>
      <div className="p-4">{children}</div>
    </div>
  )
}

export function DashboardRenderer({
  dashboardStats,
  dashboardLoading,
  runHistory,
  moduleHealth,
  handleSelectModule,
  handleRunModule,
  loadDashboardStats,
}: DashboardRendererProps) {
  const stats = dashboardStats as Record<string, any> | null
  const totalTests      = (stats?.totalTests      as number) ?? 0
  const totalPassed     = (stats?.totalPassed     as number) ?? 0
  const totalFailed     = (stats?.totalFailed     as number) ?? 0
  const passRate        = (stats?.passRate        as number) ?? 0
  const totalBugs       = (stats?.totalBugs       as number) ?? 0
  const openBugs        = (stats?.openBugs        as number) ?? 0
  const inProgressBugs  = (stats?.inProgressBugs  as number) ?? 0
  const fixedBugs       = (stats?.fixedBugs       as number) ?? 0
  const highPriorityBugs = (stats?.highPriorityBugs as number) ?? 0
  const totalRuns       = (stats?.totalRuns       as number) ?? 0
  const completedRuns   = (stats?.completedRuns   as number) ?? 0
  const failedRuns      = (stats?.failedRuns      as number) ?? 0
  const activeUsers     = (stats?.activeUsers     as number) ?? 0
  const activeModules   = (stats?.activeModules   as number) ?? 0
  const activeEnvs      = (stats?.activeEnvs      as number) ?? 0
  const recentRuns      = (stats?.recentRuns      as Array<Record<string, any>>) ?? []
  const recentBugs      = (stats?.recentBugs      as Array<Record<string, any>>) ?? []
  const bugTrend        = (stats?.bugTrend        as Array<{ date: string; count: number }>) ?? []
  const runTrend        = (stats?.runTrend        as Array<Record<string, any>>) ?? []
  const apiModuleHealth = (stats?.moduleHealth    as Array<Record<string, any>>) ?? []
  const bugByPriority   = (stats?.bugByPriority   as Record<string, number>) ?? {}
  const bugByStatus     = (stats?.bugByStatus     as Record<string, number>) ?? {}

  const apiRunHistory: RunSnapshot[] = runTrend.map((r) => ({
    id: r.id ?? '', date: r.startedAt ?? '', moduleId: r.moduleName ?? '', results: [],
    passed: r.passed ?? 0, failed: r.failed ?? 0, total: r.total ?? 0,
    duration: r.duration ?? '—', rate: r.passRate ?? 0,
  }))
  const apiModuleHealthData: ModuleHealth[] = apiModuleHealth.map((m) => ({
    moduleId: m.moduleName ?? '', moduleName: m.moduleName ?? '',
    passRate: m.passRate ?? 0, totalTests: m.total ?? 0,
    passedTests: m.passed ?? 0, failedTests: m.failed ?? 0, lastRun: '',
  }))
  const chartRunHistory   = apiRunHistory.length > 0 ? apiRunHistory : runHistory
  const chartModuleHealth = apiModuleHealthData.length > 0 ? apiModuleHealthData : moduleHealth
  const bugTrendData  = bugTrend.map((b) => b.count)
  const runTrendData  = runTrend.map((r) => r.passRate ?? 0)

  return (
    <div data-tour="dashboard" className="flex-1 min-h-0 overflow-auto bg-gray-50/40 dark:bg-transparent">
      <div className="p-5 space-y-5 max-w-6xl w-full mx-auto">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-[17px] font-semibold text-gray-800 dark:text-gray-100 tracking-tight">Dashboard</h2>
            <p className="text-[12px] text-gray-400 dark:text-gray-500 mt-0.5">RhythmERP test automation overview</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={loadDashboardStats}
              disabled={dashboardLoading}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[12px] text-gray-500 dark:text-gray-400 hover:text-[#3F51B5] dark:hover:text-[#7986CB] hover:bg-[#3F51B5]/[0.06] border border-gray-200 dark:border-gray-700 cursor-pointer transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`size-3.5 ${dashboardLoading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <ExportMenu runHistory={runHistory} moduleHealth={moduleHealth} />
          </div>
        </div>

        {/* Loading */}
        {dashboardLoading && !dashboardStats && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="size-7 text-[#3F51B5] animate-spin mr-3" />
            <span className="text-[13px] text-gray-500 dark:text-gray-400">Loading stats…</span>
          </div>
        )}

        {/* KPI Row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {/* Total Tests */}
          <div className="bg-white dark:bg-gray-800/80 rounded-lg border border-gray-200 dark:border-gray-700/70 shadow-sm p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="w-8 h-8 rounded-md bg-[#3F51B5]/[0.08] dark:bg-[#3F51B5]/20 flex items-center justify-center">
                <CheckCircle2 className="size-4 text-[#3F51B5] dark:text-[#7986CB]" />
              </div>
              {runTrendData.length >= 2 && (
                <Sparkline data={runTrendData} width={52} height={18}
                  strokeColor={runTrendData[runTrendData.length - 1] >= runTrendData[runTrendData.length - 2] ? '#10b981' : '#ef4444'}
                  fillColor={runTrendData[runTrendData.length - 1] >= runTrendData[runTrendData.length - 2] ? '#10b981' : '#ef4444'}
                  strokeWidth={1.5}
                />
              )}
            </div>
            <div className="text-[22px] font-bold text-gray-800 dark:text-gray-100 leading-none">{totalTests.toLocaleString()}</div>
            <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-1.5 font-medium">Total Tests</div>
            <div className="flex items-center gap-2 mt-2 text-[11px]">
              <span className="text-emerald-600 dark:text-emerald-400">{totalPassed.toLocaleString()} passed</span>
              <span className="text-gray-300 dark:text-gray-600">·</span>
              <span className="text-red-500 dark:text-red-400">{totalFailed.toLocaleString()} failed</span>
            </div>
            <div className="mt-2">
              <Progress value={passRate} className="h-1 bg-gray-100 dark:bg-gray-700" />
              <span className="text-[10px] text-[#3F51B5] dark:text-[#7986CB] font-medium mt-0.5 block">{passRate.toFixed(1)}% pass rate</span>
            </div>
          </div>

          {/* Total Bugs */}
          <div className="bg-white dark:bg-gray-800/80 rounded-lg border border-gray-200 dark:border-gray-700/70 shadow-sm p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="w-8 h-8 rounded-md bg-red-50 dark:bg-red-900/20 flex items-center justify-center">
                <Bug className="size-4 text-red-600 dark:text-red-400" />
              </div>
              {bugTrendData.length >= 2 && (
                <Sparkline data={bugTrendData} width={52} height={18} strokeColor="#ef4444" fillColor="#ef4444" strokeWidth={1.5} />
              )}
            </div>
            <div className="text-[22px] font-bold text-gray-800 dark:text-gray-100 leading-none">{totalBugs.toLocaleString()}</div>
            <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-1.5 font-medium">Total Bugs</div>
            <div className="flex items-center gap-2 mt-2 text-[11px]">
              <span className="text-red-500 dark:text-red-400">{openBugs} open</span>
              <span className="text-gray-300 dark:text-gray-600">·</span>
              <span className="text-amber-500 dark:text-amber-400">{inProgressBugs} in progress</span>
            </div>
            {highPriorityBugs > 0 && (
              <div className="flex items-center gap-1 mt-1.5">
                <AlertTriangle className="size-3 text-amber-500" />
                <span className="text-[10px] text-amber-600 dark:text-amber-400 font-medium">{highPriorityBugs} high priority</span>
              </div>
            )}
          </div>

          {/* Total Runs */}
          <div className="bg-white dark:bg-gray-800/80 rounded-lg border border-gray-200 dark:border-gray-700/70 shadow-sm p-4">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-md bg-[#3F51B5]/[0.08] dark:bg-[#3F51B5]/20 flex items-center justify-center">
                <Play className="size-4 text-[#3F51B5] dark:text-[#7986CB]" />
              </div>
            </div>
            <div className="text-[22px] font-bold text-gray-800 dark:text-gray-100 leading-none">{totalRuns.toLocaleString()}</div>
            <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-1.5 font-medium">Total Runs</div>
            <div className="flex items-center gap-2 mt-2 text-[11px]">
              <span className="text-emerald-600 dark:text-emerald-400">{completedRuns} completed</span>
              <span className="text-gray-300 dark:text-gray-600">·</span>
              <span className="text-red-500 dark:text-red-400">{failedRuns} failed</span>
            </div>
          </div>

          {/* Active Modules */}
          <div className="bg-white dark:bg-gray-800/80 rounded-lg border border-gray-200 dark:border-gray-700/70 shadow-sm p-4">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-md bg-[#3F51B5]/[0.08] dark:bg-[#3F51B5]/20 flex items-center justify-center">
                <LayoutDashboard className="size-4 text-[#3F51B5] dark:text-[#7986CB]" />
              </div>
            </div>
            <div className="text-[22px] font-bold text-gray-800 dark:text-gray-100 leading-none">{activeModules}</div>
            <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-1.5 font-medium">Active Modules</div>
            <div className="flex items-center gap-2 mt-2 text-[11px]">
              <span className="text-gray-500 dark:text-gray-400">{activeUsers} users</span>
              <span className="text-gray-300 dark:text-gray-600">·</span>
              <span className="text-gray-500 dark:text-gray-400">{activeEnvs} envs</span>
            </div>
          </div>
        </div>

        {/* Charts row 1 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Panel title="Pass Rate Trend" icon={TrendingUp}>
            <PassRateTrendChart runHistory={chartRunHistory} />
          </Panel>
          <Panel title="Bug Distribution" icon={Bug}>
            <BugDistributionPie moduleHealth={chartModuleHealth} />
          </Panel>
        </div>

        {/* Charts row 2 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Panel title="Module Health" icon={BarChart3}>
            <ModuleHealthBarChart moduleHealth={chartModuleHealth} />
          </Panel>

          {/* Bug Status & Priority */}
          <Panel title="Bug Status & Priority" icon={Activity}>
            <div className="grid grid-cols-2 gap-6">
              <div>
                <p className="text-[11px] text-gray-400 dark:text-gray-500 uppercase tracking-wider font-semibold mb-2">By Status</p>
                <div className="space-y-2">
                  {Object.entries(bugByStatus).map(([status, count]) => (
                    <div key={status} className="flex items-center justify-between">
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${STATUS_BUG[status] ?? 'bg-gray-100 text-gray-500 border border-gray-200'}`}>
                        {STATUS_LABEL[status] ?? status}
                      </span>
                      <span className="text-[12px] font-semibold text-gray-700 dark:text-gray-200">{count as number}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-[11px] text-gray-400 dark:text-gray-500 uppercase tracking-wider font-semibold mb-2">By Priority</p>
                <div className="space-y-2">
                  {Object.entries(bugByPriority).map(([priority, count]) => (
                    <div key={priority} className="flex items-center justify-between">
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${PRIORITY_CLS[priority] ?? 'bg-gray-100 text-gray-500 border border-gray-200'}`}>
                        {priority.charAt(0).toUpperCase() + priority.slice(1)}
                      </span>
                      <span className="text-[12px] font-semibold text-gray-700 dark:text-gray-200">{count as number}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </Panel>
        </div>

        {/* Execution Timeline */}
        <Panel title="Execution Timeline" icon={Activity}>
          <TestExecutionTimeline runHistory={chartRunHistory} />
        </Panel>

        {/* Recent Bugs + Recent Runs */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Panel title="Recent Bugs" icon={Bug}>
            {recentBugs.length === 0 ? (
              <div className="py-6 text-center">
                <CheckCircle2 className="size-7 text-emerald-500 mx-auto mb-2" />
                <p className="text-[12px] text-gray-400">No bugs reported yet</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-50 dark:divide-gray-700/40 -mx-4">
                {recentBugs.map((bug) => (
                  <div key={bug.id as string} className="flex items-start gap-3 px-4 py-2.5 hover:bg-gray-50/60 dark:hover:bg-gray-700/20 transition-colors">
                    <div className="flex-1 min-w-0">
                      <p className="text-[12px] font-medium text-gray-700 dark:text-gray-200 truncate">
                        {(bug.testDescription as string) || (bug.testId as string)}
                      </p>
                      <div className="flex items-center gap-1.5 mt-1 flex-wrap">
                        {(bug.moduleName as string) && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 border border-gray-200 dark:border-gray-600">
                            {bug.moduleName as string}
                          </span>
                        )}
                        {(bug.priority as string) && (
                          <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${PRIORITY_CLS[bug.priority as string] ?? ''}`}>
                            {(bug.priority as string).charAt(0).toUpperCase() + (bug.priority as string).slice(1)}
                          </span>
                        )}
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${STATUS_BUG[bug.status as string] ?? ''}`}>
                          {STATUS_LABEL[bug.status as string] ?? bug.status as string}
                        </span>
                        <span className="text-[10px] text-gray-400 ml-auto">
                          {(bug.createdAt as string) ? new Date(bug.createdAt as string).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }) : ''}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Panel>

          <Panel title="Recent Runs" icon={Clock}>
            {recentRuns.length === 0 ? (
              <div className="py-6 text-center">
                <Play className="size-7 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
                <p className="text-[12px] text-gray-400">No runs recorded yet</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-50 dark:divide-gray-700/40 -mx-4">
                {recentRuns.map((run) => {
                  const rate = (run.rate as number) ?? 0
                  return (
                    <button
                      key={run.id as string}
                      onClick={() => { if (run.moduleId as string) handleSelectModule(run.moduleId as string) }}
                      className="w-full text-left flex items-center gap-3 px-4 py-2.5 hover:bg-[#3F51B5]/[0.04] dark:hover:bg-[#3F51B5]/[0.08] transition-colors cursor-pointer group"
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-[12px] font-semibold text-gray-700 dark:text-gray-200 truncate">
                          {(run.moduleName as string) || '—'}
                        </p>
                        <div className="flex items-center gap-2 mt-0.5 text-[11px]">
                          <span className="text-emerald-600 dark:text-emerald-400">{(run.passed as number) ?? 0} passed</span>
                          <span className="text-red-500 dark:text-red-400">{(run.failed as number) ?? 0} failed</span>
                          <span className="text-gray-400">{(run.date as string) ? new Date(run.date as string).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }) : ''}</span>
                        </div>
                      </div>
                      <span className={`text-[12px] font-bold shrink-0 ${rate >= 80 ? 'text-emerald-600 dark:text-emerald-400' : rate >= 50 ? 'text-amber-600 dark:text-amber-400' : 'text-red-600 dark:text-red-400'}`}>
                        {rate.toFixed(1)}%
                      </span>
                      <ChevronRight className="size-3.5 text-gray-400 opacity-0 group-hover:opacity-60 transition-opacity" />
                    </button>
                  )
                })}
              </div>
            )}
          </Panel>
        </div>

        <DashboardTab onSelectModule={handleSelectModule} moduleHealth={moduleHealth} onRunModule={handleRunModule} runHistory={runHistory} />
      </div>
    </div>
  )
}
