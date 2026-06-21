'use client'

import React from 'react'
import { Activity, CheckCircle2, Bug, FolderTree, Play, Plus, Clock, ChevronRight, TrendingUp } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

export interface PersonalDashboardTabProps {
  userName: string
  userRole: string
  stats: {
    totalRuns: number
    passRate: number
    bugsReported: number
    modulesTested: number
    recentRuns: Array<{
      id: string
      moduleName: string
      passed: number
      failed: number
      date: string
      rate: number
    }>
    recentBugs: Array<{
      id: string
      testDescription: string
      moduleName: string
      status: string
      createdAt: string
    }>
  }
  onRunTests?: () => void
  onReportBug?: () => void
  onSelectModule?: (moduleId: string) => void
}

const STATUS_BADGE: Record<string, string> = {
  open:        'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400',
  in_progress: 'bg-[#3F51B5]/15 dark:bg-[#3F51B5]/20 text-[#3F51B5] dark:text-[#7986CB]',
  fixed:       'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400',
  closed:      'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400',
  rejected:    'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400',
}
const STATUS_LABEL: Record<string, string> = {
  open: 'Open', in_progress: 'In Progress', fixed: 'Fixed', closed: 'Closed', rejected: 'Rejected',
}

const STAT_CARDS = [
  { key: 'totalRuns',       label: 'Test Runs',       icon: Activity,     suffix: 'completed',       color: 'text-[#3F51B5] dark:text-[#7986CB]', bg: 'bg-[#3F51B5]/[0.08] dark:bg-[#3F51B5]/20' },
  { key: 'passRate',        label: 'Pass Rate',        icon: TrendingUp,   suffix: 'success rate',    color: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-50 dark:bg-emerald-900/20' },
  { key: 'bugsReported',   label: 'Bugs Reported',   icon: Bug,          suffix: 'reports filed',   color: 'text-red-600 dark:text-red-400', bg: 'bg-red-50 dark:bg-red-900/20' },
  { key: 'modulesTested',  label: 'Modules Tested',  icon: FolderTree,   suffix: 'modules covered', color: 'text-[#3F51B5] dark:text-[#7986CB]', bg: 'bg-[#3F51B5]/[0.08] dark:bg-[#3F51B5]/20' },
] as const

export function PersonalDashboardTab({
  userName,
  userRole,
  stats,
  onRunTests,
  onReportBug,
  onSelectModule,
}: PersonalDashboardTabProps) {

  return (
    <div className="flex flex-col h-full overflow-auto">
      <div className="p-5 space-y-5 max-w-4xl">

        {/* Greeting */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-[18px] font-semibold text-gray-800 dark:text-gray-100">
              Welcome back, {userName}
            </h2>
            <p className="text-[13px] text-gray-500 dark:text-gray-400 mt-0.5">
              {userRole} · Personal testing overview
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              onClick={onRunTests}
              size="sm"
              className="bg-[#3F51B5] hover:bg-[#3949AB] text-white text-[12px] gap-1.5 cursor-pointer"
            >
              <Play className="size-3.5" />
              Run Tests
            </Button>
            <Button
              onClick={onReportBug}
              variant="outline"
              size="sm"
              className="text-[12px] gap-1.5 cursor-pointer border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800"
            >
              <Plus className="size-3.5" />
              Report Bug
            </Button>
          </div>
        </div>

        {/* Stat Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {STAT_CARDS.map(({ key, label, icon: Icon, suffix, color, bg }) => {
            const rawVal = stats[key as keyof typeof stats]
            const val = key === 'passRate' ? `${(rawVal as number).toFixed(1)}%` : String(rawVal)
            return (
              <div key={key} className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm p-4">
                <div className="flex items-center gap-2 mb-3">
                  <div className={`w-8 h-8 rounded-md flex items-center justify-center ${bg}`}>
                    <Icon className={`size-4 ${color}`} />
                  </div>
                  <span className="text-[11px] text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wider">{label}</span>
                </div>
                <div className={`text-2xl font-bold ${color}`}>{val}</div>
                <div className="text-[11px] text-gray-400 dark:text-gray-500 mt-1">{suffix}</div>
              </div>
            )
          })}
        </div>

        {/* Two Column */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

          {/* Recent Runs */}
          <div className="border border-gray-300 dark:border-gray-500/70 rounded-lg overflow-hidden shadow-sm">
            <div className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-[#3F51B5]/[0.07] to-[#3F51B5]/[0.03] dark:from-[#3F51B5]/20 dark:to-[#3F51B5]/10 border-b border-gray-300 dark:border-gray-500/70">
              <Clock className="size-4 text-[#3F51B5] dark:text-[#7986CB]" />
              <span className="text-[13px] font-semibold text-gray-700 dark:text-gray-200">Recent Runs</span>
              <span className="ml-auto text-[11px] text-gray-400">{stats.recentRuns.length} runs</span>
            </div>
            {stats.recentRuns.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-10 text-center px-4">
                <Activity className="size-8 text-gray-300 dark:text-gray-600 mb-2" />
                <p className="text-[13px] text-gray-500 dark:text-gray-400">No runs recorded yet</p>
                <p className="text-[11px] text-gray-400 mt-0.5">Run some tests to see history here</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-100 dark:divide-gray-700/50 max-h-72 overflow-y-auto">
                {stats.recentRuns.map((run) => (
                  <button
                    key={run.id}
                    onClick={() => onSelectModule?.(run.moduleName?.toLowerCase().replace(/\s+/g, '-'))}
                    className="w-full text-left px-4 py-2.5 hover:bg-[#3F51B5]/[0.04] dark:hover:bg-[#3F51B5]/10 transition-colors group cursor-pointer"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[13px] font-medium text-gray-700 dark:text-gray-200 truncate">{run.moduleName}</span>
                      <ChevronRight className="size-3.5 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
                    </div>
                    <div className="flex items-center gap-3 text-[11px]">
                      <span className="text-emerald-600 dark:text-emerald-400 font-medium">{run.passed} passed</span>
                      <span className="text-red-500 dark:text-red-400 font-medium">{run.failed} failed</span>
                      <span className={`font-semibold ${run.rate >= 80 ? 'text-emerald-600 dark:text-emerald-400' : run.rate >= 50 ? 'text-orange-500 dark:text-orange-400' : 'text-red-600 dark:text-red-400'}`}>
                        {run.rate.toFixed(1)}%
                      </span>
                      <span className="text-gray-400 dark:text-gray-500 ml-auto">
                        {run.date ? new Date(run.date).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : ''}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Bug Reports */}
          <div className="border border-gray-300 dark:border-gray-500/70 rounded-lg overflow-hidden shadow-sm">
            <div className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-[#3F51B5]/[0.07] to-[#3F51B5]/[0.03] dark:from-[#3F51B5]/20 dark:to-[#3F51B5]/10 border-b border-gray-300 dark:border-gray-500/70">
              <Bug className="size-4 text-[#3F51B5] dark:text-[#7986CB]" />
              <span className="text-[13px] font-semibold text-gray-700 dark:text-gray-200">Bug Reports</span>
              <span className="ml-auto text-[11px] text-gray-400">{stats.recentBugs.length} filed</span>
            </div>
            {stats.recentBugs.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-10 text-center px-4">
                <CheckCircle2 className="size-8 text-emerald-400 dark:text-emerald-500 mb-2" />
                <p className="text-[13px] text-gray-500 dark:text-gray-400">No bugs reported yet</p>
                <p className="text-[11px] text-gray-400 mt-0.5">Bugs appear here when you report them</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-100 dark:divide-gray-700/50 max-h-72 overflow-y-auto">
                {stats.recentBugs.map((bug) => (
                  <div key={bug.id} className="flex items-start gap-3 px-4 py-2.5 hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors">
                    <div className="flex-1 min-w-0">
                      <p className="text-[13px] text-gray-700 dark:text-gray-200 truncate">{bug.testDescription}</p>
                      <div className="flex items-center gap-1.5 mt-1">
                        {bug.moduleName && (
                          <Badge variant="outline" className="text-[10px] h-4 px-1.5 font-normal">{bug.moduleName}</Badge>
                        )}
                        <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full ${STATUS_BADGE[bug.status] ?? 'bg-gray-100 text-gray-500'}`}>
                          {STATUS_LABEL[bug.status] ?? bug.status}
                        </span>
                      </div>
                    </div>
                    <span className="text-[10px] text-gray-400 dark:text-gray-500 shrink-0 mt-0.5">
                      {bug.createdAt ? new Date(bug.createdAt).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }) : ''}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  )
}
