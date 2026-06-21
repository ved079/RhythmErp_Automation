'use client'

import React, { useMemo } from 'react'
import {
  Activity, CheckCircle2, XCircle, Bug, FolderTree,
  Clock, TrendingUp, TrendingDown, Minus, AlertTriangle,
  BarChart2, Play, ChevronRight, Calendar,
} from 'lucide-react'

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

const STATUS_CONFIG: Record<string, { label: string; cls: string }> = {
  open:        { label: 'Open',        cls: 'bg-orange-50 dark:bg-orange-900/20 text-orange-700 dark:text-orange-400 border border-orange-200 dark:border-orange-800/50' },
  in_progress: { label: 'In Progress', cls: 'bg-[#3F51B5]/[0.08] dark:bg-[#3F51B5]/20 text-[#3F51B5] dark:text-[#7986CB] border border-[#3F51B5]/20 dark:border-[#3F51B5]/30' },
  fixed:       { label: 'Fixed',       cls: 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/50' },
  closed:      { label: 'Closed',      cls: 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 border border-gray-200 dark:border-gray-600' },
  rejected:    { label: 'Rejected',    cls: 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 border border-gray-200 dark:border-gray-600' },
}

function fmtDate(iso: string) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}
function fmtDateTime(iso: string) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
}

function RateBar({ rate }: { rate: number }) {
  const color = rate >= 80 ? '#10b981' : rate >= 50 ? '#f59e0b' : '#ef4444'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all" style={{ width: `${Math.min(rate, 100)}%`, backgroundColor: color }} />
      </div>
      <span className="text-[11px] font-semibold w-9 text-right" style={{ color }}>{rate.toFixed(0)}%</span>
    </div>
  )
}

function TrendIcon({ runs }: { runs: Array<{ rate: number }> }) {
  if (runs.length < 2) return <Minus className="size-3.5 text-gray-400" />
  const last = runs[0].rate
  const prev = runs[1].rate
  const delta = last - prev
  if (Math.abs(delta) < 2) return <Minus className="size-3.5 text-gray-400" />
  if (delta > 0) return <TrendingUp className="size-3.5 text-emerald-500" />
  return <TrendingDown className="size-3.5 text-red-500" />
}

export function PersonalDashboardTab({
  userName,
  userRole,
  stats,
  onRunTests,
  onSelectModule,
}: PersonalDashboardTabProps) {
  const openBugs = useMemo(
    () => stats.recentBugs.filter((b) => b.status === 'open' || b.status === 'in_progress').length,
    [stats.recentBugs],
  )

  const lastRun = stats.recentRuns[0]
  const todayRuns = useMemo(() => {
    const today = new Date().toDateString()
    return stats.recentRuns.filter((r) => r.date && new Date(r.date).toDateString() === today).length
  }, [stats.recentRuns])

  const roleLabel = {
    admin: 'Administrator',
    qa_lead: 'QA Lead',
    tester: 'Tester',
    viewer: 'Viewer',
  }[userRole] ?? userRole

  return (
    <div className="flex flex-col h-full overflow-auto bg-gray-50/40 dark:bg-transparent">
      <div className="p-5 space-y-5 max-w-5xl w-full mx-auto">

        {/* ── Header ───────────────────────────────────── */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-[17px] font-semibold text-gray-800 dark:text-gray-100 tracking-tight">
              {userName}
            </h2>
            <p className="text-[12px] text-gray-400 dark:text-gray-500 mt-0.5 flex items-center gap-1.5">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-[#3F51B5]/60" />
              {roleLabel}
              <span className="text-gray-300 dark:text-gray-600">·</span>
              <Calendar className="size-3 text-gray-400" />
              {new Date().toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'long', year: 'numeric' })}
            </p>
          </div>
          <button
            onClick={onRunTests}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-[#3F51B5] hover:bg-[#3949AB] text-white text-[12px] font-semibold cursor-pointer transition-colors shrink-0"
          >
            <Play className="size-3.5" />
            Run Tests
          </button>
        </div>

        {/* ── KPI Row ──────────────────────────────────── */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {/* Total Runs */}
          <div className="bg-white dark:bg-gray-800/80 rounded-lg border border-gray-200 dark:border-gray-700/70 shadow-sm p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="w-8 h-8 rounded-md bg-[#3F51B5]/[0.08] dark:bg-[#3F51B5]/20 flex items-center justify-center">
                <Activity className="size-4 text-[#3F51B5] dark:text-[#7986CB]" />
              </div>
              <TrendIcon runs={stats.recentRuns} />
            </div>
            <div className="text-[22px] font-bold text-gray-800 dark:text-gray-100 leading-none">{stats.totalRuns}</div>
            <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-1.5 font-medium">Total Runs</div>
            {todayRuns > 0 && <div className="text-[10px] text-[#3F51B5] dark:text-[#7986CB] mt-1">{todayRuns} today</div>}
          </div>

          {/* Pass Rate */}
          <div className="bg-white dark:bg-gray-800/80 rounded-lg border border-gray-200 dark:border-gray-700/70 shadow-sm p-4">
            <div className="flex items-center justify-between mb-3">
              <div className={`w-8 h-8 rounded-md flex items-center justify-center ${stats.passRate >= 80 ? 'bg-emerald-50 dark:bg-emerald-900/20' : stats.passRate >= 50 ? 'bg-amber-50 dark:bg-amber-900/20' : 'bg-red-50 dark:bg-red-900/20'}`}>
                <BarChart2 className={`size-4 ${stats.passRate >= 80 ? 'text-emerald-600 dark:text-emerald-400' : stats.passRate >= 50 ? 'text-amber-600 dark:text-amber-400' : 'text-red-600 dark:text-red-400'}`} />
              </div>
              {stats.passRate >= 80 ? <CheckCircle2 className="size-3.5 text-emerald-500" /> : stats.passRate >= 50 ? <AlertTriangle className="size-3.5 text-amber-500" /> : <XCircle className="size-3.5 text-red-500" />}
            </div>
            <div className={`text-[22px] font-bold leading-none ${stats.passRate >= 80 ? 'text-emerald-600 dark:text-emerald-400' : stats.passRate >= 50 ? 'text-amber-600 dark:text-amber-400' : 'text-red-600 dark:text-red-400'}`}>
              {stats.passRate.toFixed(1)}%
            </div>
            <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-1.5 font-medium">Pass Rate</div>
            <div className="mt-2 h-1 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
              <div className="h-full rounded-full" style={{ width: `${Math.min(stats.passRate, 100)}%`, backgroundColor: stats.passRate >= 80 ? '#10b981' : stats.passRate >= 50 ? '#f59e0b' : '#ef4444' }} />
            </div>
          </div>

          {/* Bugs */}
          <div className="bg-white dark:bg-gray-800/80 rounded-lg border border-gray-200 dark:border-gray-700/70 shadow-sm p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="w-8 h-8 rounded-md bg-red-50 dark:bg-red-900/20 flex items-center justify-center">
                <Bug className="size-4 text-red-600 dark:text-red-400" />
              </div>
              {openBugs > 0 && <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400">{openBugs} open</span>}
            </div>
            <div className="text-[22px] font-bold text-gray-800 dark:text-gray-100 leading-none">{stats.bugsReported}</div>
            <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-1.5 font-medium">Bugs Reported</div>
            {openBugs === 0 && stats.bugsReported > 0 && <div className="text-[10px] text-emerald-600 dark:text-emerald-400 mt-1">All resolved</div>}
          </div>

          {/* Modules */}
          <div className="bg-white dark:bg-gray-800/80 rounded-lg border border-gray-200 dark:border-gray-700/70 shadow-sm p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="w-8 h-8 rounded-md bg-[#3F51B5]/[0.08] dark:bg-[#3F51B5]/20 flex items-center justify-center">
                <FolderTree className="size-4 text-[#3F51B5] dark:text-[#7986CB]" />
              </div>
            </div>
            <div className="text-[22px] font-bold text-gray-800 dark:text-gray-100 leading-none">{stats.modulesTested}</div>
            <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-1.5 font-medium">Modules Tested</div>
            {lastRun && <div className="text-[10px] text-gray-400 dark:text-gray-500 mt-1">Last: {lastRun.moduleName}</div>}
          </div>
        </div>

        {/* ── Two-column content ────────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-[3fr_2fr] gap-4">

          {/* Recent Runs */}
          <div className="bg-white dark:bg-gray-800/80 rounded-lg border border-gray-200 dark:border-gray-700/70 shadow-sm overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-2.5 border-b border-gray-100 dark:border-gray-700/60 bg-gradient-to-r from-[#3F51B5]/[0.05] to-transparent">
              <Clock className="size-3.5 text-[#3F51B5] dark:text-[#7986CB]" />
              <span className="text-[12px] font-semibold text-gray-700 dark:text-gray-200">Recent Runs</span>
              <span className="ml-auto text-[11px] text-gray-400 dark:text-gray-500">{stats.recentRuns.length} recorded</span>
            </div>
            {stats.recentRuns.length === 0 ? (
              <div className="py-10 flex flex-col items-center gap-2 text-center px-4">
                <div className="w-9 h-9 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                  <Activity className="size-4 text-gray-400 dark:text-gray-500" />
                </div>
                <p className="text-[13px] font-medium text-gray-500 dark:text-gray-400">No runs yet</p>
                <button onClick={onRunTests} className="text-[12px] text-[#3F51B5] dark:text-[#7986CB] hover:underline cursor-pointer">Run your first test</button>
              </div>
            ) : (
              <div className="divide-y divide-gray-50 dark:divide-gray-700/40">
                {stats.recentRuns.map((run) => (
                  <button
                    key={run.id}
                    onClick={() => onSelectModule?.(run.moduleName?.toLowerCase().replace(/\s+/g, '-'))}
                    className="w-full text-left px-4 py-3 hover:bg-[#3F51B5]/[0.03] dark:hover:bg-[#3F51B5]/[0.08] transition-colors group cursor-pointer"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[12px] font-semibold text-gray-700 dark:text-gray-200 truncate max-w-[200px]">{run.moduleName}</span>
                      <div className="flex items-center gap-2 text-[11px] text-gray-400 dark:text-gray-500 shrink-0">
                        <span>{fmtDateTime(run.date)}</span>
                        <ChevronRight className="size-3 opacity-0 group-hover:opacity-60 transition-opacity text-[#3F51B5]" />
                      </div>
                    </div>
                    <div className="flex items-center gap-3 mb-1.5">
                      <span className="text-[11px] text-emerald-600 dark:text-emerald-400">{run.passed} passed</span>
                      {run.failed > 0 && <span className="text-[11px] text-red-500 dark:text-red-400">{run.failed} failed</span>}
                      <span className="text-[11px] text-gray-400 dark:text-gray-500">{run.passed + run.failed} total</span>
                    </div>
                    <RateBar rate={run.rate} />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Bug Reports */}
          <div className="bg-white dark:bg-gray-800/80 rounded-lg border border-gray-200 dark:border-gray-700/70 shadow-sm overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-2.5 border-b border-gray-100 dark:border-gray-700/60 bg-gradient-to-r from-[#3F51B5]/[0.05] to-transparent">
              <Bug className="size-3.5 text-[#3F51B5] dark:text-[#7986CB]" />
              <span className="text-[12px] font-semibold text-gray-700 dark:text-gray-200">Bug Reports</span>
              {openBugs > 0 && <span className="ml-auto text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400">{openBugs} open</span>}
              {openBugs === 0 && <span className="ml-auto text-[11px] text-gray-400 dark:text-gray-500">{stats.recentBugs.length} total</span>}
            </div>
            {stats.recentBugs.length === 0 ? (
              <div className="py-10 flex flex-col items-center gap-2 text-center px-4">
                <div className="w-9 h-9 rounded-full bg-emerald-50 dark:bg-emerald-900/20 flex items-center justify-center">
                  <CheckCircle2 className="size-4 text-emerald-500 dark:text-emerald-400" />
                </div>
                <p className="text-[13px] font-medium text-gray-500 dark:text-gray-400">No bugs filed</p>
                <p className="text-[11px] text-gray-400 dark:text-gray-500">Report issues directly from test results</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-50 dark:divide-gray-700/40 max-h-[340px] overflow-y-auto">
                {stats.recentBugs.map((bug) => {
                  const sc = STATUS_CONFIG[bug.status] ?? STATUS_CONFIG.closed
                  return (
                    <div key={bug.id} className="px-4 py-3 hover:bg-gray-50/60 dark:hover:bg-gray-700/20 transition-colors">
                      <p className="text-[12px] font-medium text-gray-700 dark:text-gray-200 line-clamp-1 mb-1.5">{bug.testDescription || '(no description)'}</p>
                      <div className="flex items-center gap-1.5 flex-wrap">
                        {bug.moduleName && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 border border-gray-200 dark:border-gray-600 font-medium">
                            {bug.moduleName}
                          </span>
                        )}
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold ${sc.cls}`}>{sc.label}</span>
                        <span className="text-[10px] text-gray-400 dark:text-gray-500 ml-auto">{fmtDate(bug.createdAt)}</span>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>

        {/* ── Last run summary bar ──────────────────────── */}
        {lastRun && (
          <div className="bg-white dark:bg-gray-800/80 rounded-lg border border-gray-200 dark:border-gray-700/70 shadow-sm px-4 py-3 flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-6 rounded-full bg-[#3F51B5]" />
              <div>
                <p className="text-[11px] text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wide">Last Run</p>
                <p className="text-[13px] font-semibold text-gray-700 dark:text-gray-200">{lastRun.moduleName}</p>
              </div>
            </div>
            <div className="h-8 w-px bg-gray-200 dark:bg-gray-700" />
            <div className="flex items-center gap-4 text-[12px] flex-wrap">
              <span className="text-emerald-600 dark:text-emerald-400 font-semibold flex items-center gap-1">
                <CheckCircle2 className="size-3.5" />{lastRun.passed} passed
              </span>
              {lastRun.failed > 0 && (
                <span className="text-red-500 dark:text-red-400 font-semibold flex items-center gap-1">
                  <XCircle className="size-3.5" />{lastRun.failed} failed
                </span>
              )}
              <span className="text-gray-400 dark:text-gray-500">{fmtDateTime(lastRun.date)}</span>
            </div>
            <div className="flex-1 min-w-[120px]">
              <RateBar rate={lastRun.rate} />
            </div>
            <button
              onClick={() => onSelectModule?.(lastRun.moduleName?.toLowerCase().replace(/\s+/g, '-'))}
              className="ml-auto flex items-center gap-1 text-[11px] text-[#3F51B5] dark:text-[#7986CB] hover:text-[#3949AB] dark:hover:text-[#9FA8DA] cursor-pointer transition-colors font-medium"
            >
              View module <ChevronRight className="size-3" />
            </button>
          </div>
        )}

      </div>
    </div>
  )
}
