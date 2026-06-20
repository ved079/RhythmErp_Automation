'use client'

import React from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Sparkline } from '@/components/ui/sparkline'
import {
  PassRateTrendChart, ModuleHealthBarChart, BugDistributionPie, TestExecutionTimeline,
} from '@/components/dashboard/DashboardCharts'
import { ExportMenu } from '@/components/export/ExportUtils'
import { DashboardTab } from '@/components/dashboard/DashboardTab'
import {
  RefreshCw, Loader2, CheckCircle2, Bug, Play, LayoutDashboard, AlertTriangle,
  BarChart3, Activity, Clock, XCircle, ChevronRight,
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
  const totalTests = (stats?.totalTests as number) ?? 0
  const totalPassed = (stats?.totalPassed as number) ?? 0
  const totalFailed = (stats?.totalFailed as number) ?? 0
  const passRate = (stats?.passRate as number) ?? 0
  const totalBugs = (stats?.totalBugs as number) ?? 0
  const openBugs = (stats?.openBugs as number) ?? 0
  const inProgressBugs = (stats?.inProgressBugs as number) ?? 0
  const fixedBugs = (stats?.fixedBugs as number) ?? 0
  const highPriorityBugs = (stats?.highPriorityBugs as number) ?? 0
  const totalRuns = (stats?.totalRuns as number) ?? 0
  const completedRuns = (stats?.completedRuns as number) ?? 0
  const failedRuns = (stats?.failedRuns as number) ?? 0
  const activeUsers = (stats?.activeUsers as number) ?? 0
  const activeModules = (stats?.activeModules as number) ?? 0
  const activeEnvs = (stats?.activeEnvs as number) ?? 0
  const recentRuns = (stats?.recentRuns as Array<Record<string, any>>) ?? []
  const recentBugs = (stats?.recentBugs as Array<Record<string, any>>) ?? []
  const bugTrend = (stats?.bugTrend as Array<{ date: string; count: number }>) ?? []
  const runTrend = (stats?.runTrend as Array<Record<string, any>>) ?? []
  const apiModuleHealth = (stats?.moduleHealth as Array<Record<string, any>>) ?? []
  const bugByPriority = (stats?.bugByPriority as Record<string, number>) ?? {}
  const bugByStatus = (stats?.bugByStatus as Record<string, number>) ?? {}
  const apiRunHistory: RunSnapshot[] = runTrend.map((r) => ({ id: r.id ?? '', date: r.startedAt ?? '', moduleId: r.moduleName ?? '', results: [], passed: r.passed ?? 0, failed: r.failed ?? 0, total: r.total ?? 0, duration: r.duration ?? '\u2014', rate: r.passRate ?? 0 }))
  const apiModuleHealthData: ModuleHealth[] = apiModuleHealth.map((m) => ({ moduleId: m.moduleName ?? '', moduleName: m.moduleName ?? '', passRate: m.passRate ?? 0, totalTests: m.total ?? 0, passedTests: m.passed ?? 0, failedTests: m.failed ?? 0, lastRun: '' }))
  const chartRunHistory = apiRunHistory.length > 0 ? apiRunHistory : runHistory
  const chartModuleHealth = apiModuleHealthData.length > 0 ? apiModuleHealthData : moduleHealth
  const bugTrendData = bugTrend.map((b) => b.count)
  const runTrendData = runTrend.map((r) => r.passRate ?? 0)

  return (
    <div data-tour="dashboard" className="flex-1 min-h-0 overflow-auto">
      <div className="p-5 space-y-5">
        <div className="flex items-center justify-between">
          <div><h2 className="text-[18px] font-semibold text-[#333333] dark:text-gray-100 font-['Poppins']">Dashboard</h2><p className="text-[13px] text-[#666666] dark:text-gray-400 mt-0.5 font-['Manrope']">Overview of all RhythmERP automation modules</p></div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={loadDashboardStats} disabled={dashboardLoading} className="h-8 px-3 text-[12px] text-[#666666] dark:text-gray-400 hover:text-[#3F51B5] dark:hover:text-indigo-400"><RefreshCw className={`size-3.5 mr-1 ${dashboardLoading ? 'animate-spin' : ''}`} />Refresh</Button>
            <ExportMenu runHistory={runHistory} moduleHealth={moduleHealth} />
          </div>
        </div>
        {dashboardLoading && !dashboardStats && (
          <div className="flex items-center justify-center py-20"><div className="flex flex-col items-center gap-3"><Loader2 className="size-8 text-[#3F51B5] animate-spin" /><span className="text-[13px] text-[#888888] dark:text-gray-400 font-['Manrope']">Loading dashboard stats...</span></div></div>
        )}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700"><div className="flex items-center justify-between mb-2"><div className="flex items-center gap-2"><div className="w-8 h-8 rounded-lg bg-[#E8F5E9] dark:bg-green-900/30 flex items-center justify-center"><CheckCircle2 className="size-4 text-[#4CAF50]" /></div><span className="text-[11px] text-[#888888] dark:text-gray-400 font-medium uppercase tracking-wider font-['Poppins']">Total Tests</span></div>{runTrendData.length >= 2 && <Sparkline data={runTrendData} width={56} height={18} strokeColor={runTrendData[runTrendData.length - 1] >= runTrendData[runTrendData.length - 2] ? '#22c55e' : '#ef4444'} fillColor={runTrendData[runTrendData.length - 1] >= runTrendData[runTrendData.length - 2] ? '#22c55e' : '#ef4444'} strokeWidth={1.5} />}</div>
            <div className="text-xl font-bold text-[#333333] dark:text-gray-100 font-['Poppins']">{totalTests.toLocaleString()}</div>
            <div className="flex items-center gap-2 mt-1"><span className="text-[11px] text-[#4CAF50] dark:text-green-400 font-medium font-['Manrope']">{totalPassed.toLocaleString()} passed</span><span className="text-[11px] text-[#888888] dark:text-gray-500">\u2022</span><span className="text-[11px] text-[#F44336] dark:text-red-400 font-medium font-['Manrope']">{totalFailed.toLocaleString()} failed</span></div>
            <div className="mt-2"><Progress value={passRate} className="h-1.5 bg-gray-100 dark:bg-gray-700" /><span className="text-[10px] text-[#3F51B5] dark:text-indigo-400 font-medium font-['Manrope']">{passRate.toFixed(1)}% pass rate</span></div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700"><div className="flex items-center justify-between mb-2"><div className="flex items-center gap-2"><div className="w-8 h-8 rounded-lg bg-[#FFEBEE] dark:bg-red-900/30 flex items-center justify-center"><Bug className="size-4 text-[#F44336]" /></div><span className="text-[11px] text-[#888888] dark:text-gray-400 font-medium uppercase tracking-wider font-['Poppins']">Total Bugs</span></div>{bugTrendData.length >= 2 && <Sparkline data={bugTrendData} width={56} height={18} strokeColor="#F44336" fillColor="#F44336" strokeWidth={1.5} />}</div>
            <div className="text-xl font-bold text-[#333333] dark:text-gray-100 font-['Poppins']">{totalBugs.toLocaleString()}</div>
            <div className="flex items-center gap-2 mt-1"><span className="text-[11px] text-[#F44336] dark:text-red-400 font-medium font-['Manrope']">{openBugs} open</span><span className="text-[11px] text-[#888888] dark:text-gray-500">\u2022</span><span className="text-[11px] text-[#FF9800] dark:text-orange-400 font-medium font-['Manrope']">{inProgressBugs} in progress</span></div>
            {highPriorityBugs > 0 && <div className="flex items-center gap-1 mt-1.5"><AlertTriangle className="size-3 text-[#FF9800]" /><span className="text-[10px] text-[#FF9800] dark:text-orange-400 font-medium font-['Manrope']">{highPriorityBugs} high priority</span></div>}
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700"><div className="flex items-center gap-2 mb-2"><div className="w-8 h-8 rounded-lg bg-[#DFE9FB] dark:bg-indigo-900/30 flex items-center justify-center"><Play className="size-4 text-[#3F51B5]" /></div><span className="text-[11px] text-[#888888] dark:text-gray-400 font-medium uppercase tracking-wider font-['Poppins']">Total Runs</span></div>
            <div className="text-xl font-bold text-[#333333] dark:text-gray-100 font-['Poppins']">{totalRuns.toLocaleString()}</div>
            <div className="flex items-center gap-2 mt-1"><span className="text-[11px] text-[#4CAF50] dark:text-green-400 font-medium font-['Manrope']">{completedRuns} completed</span><span className="text-[11px] text-[#888888] dark:text-gray-500">\u2022</span><span className="text-[11px] text-[#F44336] dark:text-red-400 font-medium font-['Manrope']">{failedRuns} failed</span></div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700"><div className="flex items-center gap-2 mb-2"><div className="w-8 h-8 rounded-lg bg-[#FFF3E0] dark:bg-orange-900/30 flex items-center justify-center"><LayoutDashboard className="size-4 text-[#FF9800]" /></div><span className="text-[11px] text-[#888888] dark:text-gray-400 font-medium uppercase tracking-wider font-['Poppins']">Active Modules</span></div>
            <div className="text-xl font-bold text-[#333333] dark:text-gray-100 font-['Poppins']">{activeModules}</div>
            <div className="flex items-center gap-2 mt-1"><span className="text-[11px] text-[#888888] dark:text-gray-400 font-['Manrope']">{activeUsers} users</span><span className="text-[11px] text-[#888888] dark:text-gray-500">\u2022</span><span className="text-[11px] text-[#888888] dark:text-gray-400 font-['Manrope']">{activeEnvs} envs</span></div>
          </div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700"><h3 className="text-[13px] font-semibold text-[#333333] dark:text-gray-100 mb-3 flex items-center gap-2 font-['Poppins']"><LayoutDashboard className="size-4 text-[#3F51B5]" />Pass Rate Trend</h3><PassRateTrendChart runHistory={chartRunHistory} /></div>
          <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700"><h3 className="text-[13px] font-semibold text-[#333333] dark:text-gray-100 mb-3 flex items-center gap-2 font-['Poppins']"><AlertTriangle className="size-4 text-[#F44336]" />Bug Distribution</h3><BugDistributionPie moduleHealth={chartModuleHealth} /></div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700"><h3 className="text-[13px] font-semibold text-[#333333] dark:text-gray-100 mb-3 flex items-center gap-2 font-['Poppins']"><BarChart3 className="size-4 text-[#3F51B5]" />Module Health Overview</h3><ModuleHealthBarChart moduleHealth={chartModuleHealth} /></div>
          <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700">
            <h3 className="text-[13px] font-semibold text-[#333333] dark:text-gray-100 mb-3 flex items-center gap-2 font-['Poppins']"><Activity className="size-4 text-[#3F51B5]" />Bug Status &amp; Priority</h3>
            <div className="grid grid-cols-2 gap-4">
              <div><div className="text-[11px] text-[#888888] dark:text-gray-400 font-medium uppercase tracking-wider mb-2 font-['Poppins']">By Status</div><div className="space-y-2">{Object.entries(bugByStatus).map(([status, count]) => { const statusColors: Record<string, string> = { open: 'bg-[#F44336] text-white', in_progress: 'bg-[#FF9800] text-white', fixed: 'bg-[#4CAF50] text-white', closed: 'bg-[#888888] text-white', rejected: 'bg-gray-400 text-white' }; const statusLabels: Record<string, string> = { open: 'Open', in_progress: 'In Progress', fixed: 'Fixed', closed: 'Closed', rejected: 'Rejected' }; return (<div key={status} className="flex items-center justify-between"><div className="flex items-center gap-1.5"><span className={`w-2 h-2 rounded-full ${statusColors[status]?.split(' ')[0] ?? 'bg-gray-400'}`} /><span className="text-[12px] text-[#333333] dark:text-gray-200 font-['Manrope']">{statusLabels[status] ?? status}</span></div><span className="text-[12px] font-semibold text-[#333333] dark:text-gray-100 font-['Poppins']">{count as number}</span></div>) })}</div></div>
              <div><div className="text-[11px] text-[#888888] dark:text-gray-400 font-medium uppercase tracking-wider mb-2 font-['Poppins']">By Priority</div><div className="space-y-2">{Object.entries(bugByPriority).map(([priority, count]) => { const priorityColors: Record<string, string> = { high: 'bg-[#F44336]', medium: 'bg-[#FF9800]', low: 'bg-[#4CAF50]' }; const priorityLabels: Record<string, string> = { high: 'High', medium: 'Medium', low: 'Low' }; return (<div key={priority} className="flex items-center justify-between"><div className="flex items-center gap-1.5"><span className={`w-2 h-2 rounded-full ${priorityColors[priority] ?? 'bg-gray-400'}`} /><span className="text-[12px] text-[#333333] dark:text-gray-200 font-['Manrope']">{priorityLabels[priority] ?? priority}</span></div><span className="text-[12px] font-semibold text-[#333333] dark:text-gray-100 font-['Poppins']">{count as number}</span></div>) })}</div></div>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700"><h3 className="text-[13px] font-semibold text-[#333333] dark:text-gray-100 mb-3 flex items-center gap-2 font-['Poppins']"><Activity className="size-4 text-[#3F51B5]" />Execution Timeline</h3><TestExecutionTimeline runHistory={chartRunHistory} /></div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700"><h3 className="text-[13px] font-semibold text-[#333333] dark:text-gray-100 mb-3 flex items-center gap-2 font-['Poppins']"><Bug className="size-4 text-[#F44336]" />Recent Bugs</h3>{recentBugs.length === 0 ? <div className="text-center py-8"><CheckCircle2 className="size-8 text-[#4CAF50] mx-auto mb-2" /><p className="text-[12px] text-[#888888] dark:text-gray-400 font-['Manrope']">No bugs reported yet</p></div> : <div className="space-y-2 max-h-72 overflow-y-auto">{recentBugs.map((bug) => { const priorityColor: Record<string, string> = { high: 'bg-[#FFEBEE] text-[#C62828] dark:bg-red-900/30 dark:text-red-400', medium: 'bg-[#FFF3E0] text-[#E65100] dark:bg-orange-900/30 dark:text-orange-400', low: 'bg-[#E8F5E9] text-[#2E7D32] dark:bg-green-900/30 dark:text-green-400' }; const statusColor: Record<string, string> = { open: 'bg-[#F44336] text-white', in_progress: 'bg-[#FF9800] text-white', fixed: 'bg-[#4CAF50] text-white', closed: 'bg-[#888888] text-white', rejected: 'bg-gray-400 text-white' }; const statusLabel: Record<string, string> = { open: 'Open', in_progress: 'In Progress', fixed: 'Fixed', closed: 'Closed', rejected: 'Rejected' }; return (<div key={bug.id as string} className="flex items-start gap-2 p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"><div className="flex-1 min-w-0"><div className="flex items-center gap-1.5 mb-0.5"><span className="text-[12px] font-medium text-[#333333] dark:text-gray-100 truncate font-['Manrope']">{(bug.testDescription as string) || (bug.testId as string)}</span></div><div className="flex items-center gap-1.5">{(bug.moduleName as string) && <Badge variant="outline" className="text-[10px] h-4 px-1.5 font-['Manrope']">{bug.moduleName as string}</Badge>}<Badge className={`text-[10px] h-4 px-1.5 ${priorityColor[bug.priority as string] ?? 'bg-gray-100 text-gray-600'}`}>{(bug.priority as string)?.charAt(0).toUpperCase() + (bug.priority as string)?.slice(1)}</Badge><Badge className={`text-[10px] h-4 px-1.5 ${statusColor[bug.status as string] ?? 'bg-gray-100 text-gray-600'}`}>{statusLabel[bug.status as string] ?? (bug.status as string)?.charAt(0).toUpperCase() + (bug.status as string)?.slice(1)}</Badge></div></div><span className="text-[10px] text-[#888888] dark:text-gray-500 shrink-0 font-['Manrope']">{(bug.createdAt as string) ? new Date(bug.createdAt as string).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }) : ''}</span></div>) })}</div>}</div>
          <div className="bg-white dark:bg-gray-800 rounded-[14px] shadow-sm p-4 border border-gray-100 dark:border-gray-700"><h3 className="text-[13px] font-semibold text-[#333333] dark:text-gray-100 mb-3 flex items-center gap-2 font-['Poppins']"><Clock className="size-4 text-[#3F51B5]" />Recent Runs</h3>{recentRuns.length === 0 ? <div className="text-center py-8"><Play className="size-8 text-[#888888] mx-auto mb-2" /><p className="text-[12px] text-[#888888] dark:text-gray-400 font-['Manrope']">No runs recorded yet</p></div> : <div className="space-y-0 max-h-72 overflow-y-auto"><div className="space-y-1 max-h-72 overflow-y-auto">{recentRuns.map((run) => { const runStatus = run.status as string; const runRate = (run.rate as number) ?? 0; return (<div key={run.id as string} className="flex items-center gap-3 px-3 py-2 rounded-lg bg-white dark:bg-gray-800/20 border border-gray-100 dark:border-gray-700/40 hover:bg-gray-50/50 dark:hover:bg-gray-800/30 cursor-pointer transition-colors" onClick={() => { if (run.moduleId as string) handleSelectModule(run.moduleId as string) }}><span className="text-[12px] font-['Manrope'] text-[#333333] dark:text-gray-200 truncate max-w-[120px] shrink-0">{(run.moduleName as string) || '\u2014'}</span><Badge className={`text-[10px] h-4 px-1.5 ${runStatus === 'completed' ? 'bg-[#4CAF50] text-white' : runStatus === 'failed' ? 'bg-[#F44336] text-white' : 'bg-[#FF9800] text-white'}`}>{runStatus === 'completed' ? <CheckCircle2 className="size-2.5 mr-0.5" /> : runStatus === 'failed' ? <XCircle className="size-2.5 mr-0.5" /> : <Clock className="size-2.5 mr-0.5" />}{runStatus.charAt(0).toUpperCase() + runStatus.slice(1)}</Badge><span className="text-[12px] text-[#4CAF50] dark:text-green-400 font-medium font-['Manrope'] shrink-0">{run.passed as number ?? 0}</span><span className="text-[12px] text-[#F44336] dark:text-red-400 font-medium font-['Manrope'] shrink-0">{run.failed as number ?? 0}</span><span className={`text-[12px] font-medium font-['Manrope'] shrink-0 ${runRate >= 80 ? 'text-[#2E7D32] dark:text-green-400' : runRate >= 50 ? 'text-[#E65100] dark:text-orange-400' : 'text-[#C62828] dark:text-red-400'}`}>{runRate.toFixed(1)}%</span><span className="text-[10px] text-[#888888] dark:text-gray-500 font-['Manrope'] shrink-0">{(run.date as string) ? new Date(run.date as string).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }) : ''}</span></div>) })}</div></div>}</div>
        </div>
        <DashboardTab onSelectModule={handleSelectModule} moduleHealth={moduleHealth} onRunModule={handleRunModule} runHistory={runHistory} />
      </div>
    </div>
  )
}
