'use client'

import React, { useMemo, useCallback } from 'react'
import { Clock, Play, TrendingUp, BarChart3, AlertTriangle, Activity } from 'lucide-react'
import { Progress } from '@/components/ui/progress'
import { Sparkline, getSparklineColor, TrendIndicator } from '@/components/ui/sparkline'
import { PassRateTrendChart, ModuleHealthBarChart, BugDistributionPie, TestExecutionTimeline } from '@/components/dashboard/DashboardCharts'
import { ExportMenu } from '@/components/export/ExportUtils'
import type { ModuleHealth, RunSnapshot } from '@/lib/types'

export function DashboardTab({
  onSelectModule,
  moduleHealth,
  onRunModule,
  runHistory,
}: {
  onSelectModule: (moduleId: string) => void
  moduleHealth: ModuleHealth[]
  onRunModule?: (moduleId: string) => void
  runHistory?: RunSnapshot[]
}) {
  // Group modules by parentGroup, preserving order
  const grouped = useMemo(() => {
    const order = ['Registration', 'Standalone', 'Common Settings', 'Commodity Settings']
    const groups: { name: string; icon: string; modules: ModuleHealth[] }[] = []
    const groupMap = new Map<string, ModuleHealth[]>()

    for (const mod of moduleHealth) {
      const g = mod.parentGroup || 'Other'
      if (!groupMap.has(g)) groupMap.set(g, [])
      groupMap.get(g)!.push(mod)
    }

    for (const name of order) {
      const mods = groupMap.get(name)
      if (mods) groups.push({ name, icon: name === 'Common Settings' ? '⚙️' : name === 'Commodity Settings' ? '📦' : '📁', modules: mods })
    }
    // catch any remaining
    for (const [name, mods] of groupMap) {
      if (!order.includes(name)) groups.push({ name, icon: '📁', modules: mods })
    }
    return groups
  }, [moduleHealth])

  const quickStats = useMemo(() => {
    const total = moduleHealth.length
    const fullyPassing = moduleHealth.filter((m) => m.totalTests > 0 && m.passRate === 100).length
    const partiallyPassing = moduleHealth.filter((m) => m.totalTests > 0 && m.passRate > 0 && m.passRate < 100).length
    const notStarted = moduleHealth.filter((m) => m.totalTests === 0).length
    const totalPassed = moduleHealth.reduce((s, m) => s + m.passedTests, 0)
    const totalFailed = moduleHealth.reduce((s, m) => s + m.failedTests, 0)
    const totalTests = moduleHealth.reduce((s, m) => s + m.totalTests, 0)
    return { total, fullyPassing, partiallyPassing, notStarted, totalPassed, totalFailed, totalTests }
  }, [moduleHealth])

  // Overall trend: average pass rate across last 7 runs (computed from module trends)
  const overallTrend = useMemo(() => {
    const modulesWithTrend = moduleHealth.filter((m) => m.trend && m.trend.length > 0)
    if (modulesWithTrend.length === 0) return [90, 91, 90, 92, 91, 92, 93]
    const maxLen = Math.max(...modulesWithTrend.map((m) => m.trend!.length))
    const avgByRun: number[] = []
    for (let i = 0; i < maxLen; i++) {
      const vals = modulesWithTrend.filter((m) => m.trend![i] !== undefined).map((m) => m.trend![i])
      avgByRun.push(Math.round(vals.reduce((s, v) => s + v, 0) / vals.length))
    }
    return avgByRun
  }, [moduleHealth])

  const getHealthColor = useCallback((rate: number, total: number) => {
    if (total === 0) return { bg: 'bg-gray-50 dark:bg-gray-800', text: 'text-[#888888] dark:text-gray-500', indicator: 'bg-[#888888]', label: 'Not Started' }
    if (rate === 100) return { bg: 'bg-[#E8F5E9] dark:bg-green-900/20', text: 'text-[#2E7D32] dark:text-green-400', indicator: 'bg-[#4CAF50]', label: 'Healthy' }
    if (rate >= 75) return { bg: 'bg-[#FFF3E0] dark:bg-orange-900/20', text: 'text-[#E65100] dark:text-orange-400', indicator: 'bg-[#FF9800]', label: 'Partial' }
    return { bg: 'bg-[#FFEBEE] dark:bg-red-900/20', text: 'text-[#C62828] dark:text-red-400', indicator: 'bg-[#F44336]', label: 'Critical' }
  }, [])

  return (
    <div className="flex flex-col h-full overflow-auto">
      <div className="p-5 space-y-5">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-[18px] font-semibold text-[#333333] dark:text-gray-100">Dashboard</h2>
            <p className="text-[13px] text-[#666666] dark:text-gray-400 mt-0.5">Overview of all RhythmERP automation modules</p>
          </div>
          <ExportMenu
            runHistory={runHistory}
            moduleHealth={moduleHealth}
          />
        </div>

        {/* KPI Banner — most recent run at a glance */}
        {(() => {
          const lastRun = runHistory?.[0]
          return (
            <div className="flex items-center gap-3 px-4 py-2.5 rounded-lg bg-[#F0F4FF] dark:bg-indigo-950/40 border border-indigo-100 dark:border-indigo-800/50 text-[12px]">
              <div className={`w-2 h-2 rounded-full ${lastRun ? 'bg-green-500' : 'bg-gray-300'} shrink-0`} />
              {lastRun ? (
                <>
                  <span className="text-[#555] dark:text-gray-300">Last run:</span>
                  <span className="font-semibold text-[#333] dark:text-gray-100">{lastRun.date}</span>
                  <span className="text-[#555] dark:text-gray-300">·</span>
                  <span className="text-green-600 dark:text-green-400 font-medium">{lastRun.passed} passed</span>
                  {lastRun.failed > 0 && <><span className="text-[#555]">·</span><span className="text-red-500 font-medium">{lastRun.failed} failed</span></>}
                  <span className="text-[#555] dark:text-gray-300">·</span>
                  <span className="font-semibold text-indigo-600 dark:text-indigo-400">{Math.round(lastRun.rate)}% pass rate</span>
                </>
              ) : (
                <span className="text-[#888]">No runs yet — select a module and run tests to populate this dashboard</span>
              )}
            </div>
          )
        })()}

        {/* Quick Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-100 dark:border-gray-700 border-l-4 border-l-indigo-500 shadow-sm">
            <div className="text-[11px] text-[#888888] dark:text-gray-400 font-medium uppercase tracking-wider">Test Cases Automated</div>
            <div className="text-2xl font-bold text-[#333333] dark:text-gray-100 mt-1">{quickStats.totalTests}</div>
            <div className="text-[11px] text-[#888] dark:text-gray-400 mt-0.5">across {quickStats.total} modules</div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-100 dark:border-gray-700 border-l-4 border-l-green-500 shadow-sm">
            <div className="text-[11px] text-[#4CAF50] dark:text-green-400 font-medium uppercase tracking-wider">Modules Healthy</div>
            <div className="text-2xl font-bold text-[#2E7D32] dark:text-green-400 mt-1">{quickStats.fullyPassing}</div>
            <div className="text-[11px] text-[#888] dark:text-gray-400 mt-0.5">{Math.round((quickStats.fullyPassing / quickStats.total) * 100)}% of all modules</div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-100 dark:border-gray-700 border-l-4 border-l-orange-500 shadow-sm">
            <div className="text-[11px] text-[#FF9800] dark:text-orange-400 font-medium uppercase tracking-wider">Modules at Risk</div>
            <div className="text-2xl font-bold text-[#E65100] dark:text-orange-400 mt-1">{quickStats.partiallyPassing}</div>
            <div className="text-[11px] text-[#888] dark:text-gray-400 mt-0.5">
              {moduleHealth.filter(m => m.passRate < 50 && m.totalTests > 0).length} critical, {moduleHealth.filter(m => m.passRate >= 50 && m.passRate < 100 && m.totalTests > 0).length} partial
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-100 dark:border-gray-700 border-l-4 border-l-indigo-500 shadow-sm">
            <div className="text-[11px] text-[#3F51B5] dark:text-indigo-400 font-medium uppercase tracking-wider">Overall Pass Rate</div>
            <div className="flex items-center gap-2 mt-1">
              <div className="text-2xl font-bold text-[#3F51B5] dark:text-indigo-400">
                {quickStats.totalTests > 0 ? Math.round((quickStats.totalPassed / quickStats.totalTests) * 100) : 0}%
              </div>
              <Sparkline
                data={overallTrend}
                width={72}
                height={22}
                strokeColor={overallTrend[overallTrend.length - 1] >= overallTrend[overallTrend.length - 2] ? '#22c55e' : '#ef4444'}
                fillColor={overallTrend[overallTrend.length - 1] >= overallTrend[overallTrend.length - 2] ? '#22c55e' : '#ef4444'}
                strokeWidth={1.5}
              />
            </div>
            <div className="text-[11px] text-[#888] dark:text-gray-400 mt-0.5">
              {quickStats.totalPassed} / {quickStats.totalTests} tests passing
            </div>
          </div>
        </div>

        {/* ── Advanced Charts ── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Pass Rate Trend */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-100 dark:border-gray-700 shadow-sm">
            <h3 className="text-[13px] font-semibold text-[#333333] dark:text-gray-100 mb-3 flex items-center gap-2">
              <TrendingUp className="size-4 text-[#3F51B5]" />
              Pass Rate Trend
            </h3>
            {(() => {
              const recentRuns = runHistory?.slice(-5) || []
              const trendUp = recentRuns.length >= 2 && recentRuns[recentRuns.length-1].rate >= recentRuns[0].rate
              const avgRate = recentRuns.length ? Math.round(recentRuns.reduce((s,r) => s + r.rate, 0) / recentRuns.length) : 0
              const subtitle = recentRuns.length
                ? `Avg ${avgRate}% over last ${recentRuns.length} runs · ${trendUp ? '↑ improving' : '↓ declining'}`
                : 'Run tests to see trend'
              return <p className="text-[11px] text-[#888] dark:text-gray-400 mt-0.5 mb-3">{subtitle}</p>
            })()}
            <PassRateTrendChart runHistory={runHistory || []} />
          </div>
          {/* Module Health Bar Chart */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-100 dark:border-gray-700 shadow-sm">
            <h3 className="text-[13px] font-semibold text-[#333333] dark:text-gray-100 mb-3 flex items-center gap-2">
              <BarChart3 className="size-4 text-[#3F51B5]" />
              Module Health Overview
            </h3>
            {(() => {
              const topModule = [...moduleHealth].sort((a,b) => b.passRate - a.passRate)[0]
              const subtitle = topModule?.totalTests > 0
                ? `Top: ${topModule.moduleName} at ${topModule.passRate}%`
                : 'No runs yet'
              return <p className="text-[11px] text-[#888] dark:text-gray-400 mt-0.5 mb-3">{subtitle}</p>
            })()}
            <ModuleHealthBarChart moduleHealth={moduleHealth} />
          </div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Bug Distribution Pie */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-100 dark:border-gray-700 shadow-sm">
            <h3 className="text-[13px] font-semibold text-[#333333] dark:text-gray-100 mb-3 flex items-center gap-2">
              <AlertTriangle className="size-4 text-[#F44336]" />
              Bug Distribution
            </h3>
            {(() => {
              const worstModule = [...moduleHealth].sort((a,b) => b.failedTests - a.failedTests)[0]
              const subtitle = worstModule?.failedTests > 0
                ? `${quickStats.totalFailed} open failures · most in ${worstModule.moduleName}`
                : 'No failures recorded'
              return <p className="text-[11px] text-[#888] dark:text-gray-400 mt-0.5 mb-3">{subtitle}</p>
            })()}
            <BugDistributionPie moduleHealth={moduleHealth} />
          </div>
          {/* Test Execution Timeline */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-100 dark:border-gray-700 shadow-sm">
            <h3 className="text-[13px] font-semibold text-[#333333] dark:text-gray-100 mb-3 flex items-center gap-2">
              <Activity className="size-4 text-[#3F51B5]" />
              Execution Timeline
            </h3>
            {(() => {
              const subtitle = runHistory?.length
                ? `${runHistory.length} total runs recorded`
                : 'No runs yet'
              return <p className="text-[11px] text-[#888] dark:text-gray-400 mt-0.5 mb-3">{subtitle}</p>
            })()}
            <TestExecutionTimeline runHistory={runHistory || []} />
          </div>
        </div>

        {/* Module Groups */}
        {grouped.map((group) => {
          const groupTotal = group.modules.reduce((s, m) => s + m.totalTests, 0)
          const groupPassed = group.modules.reduce((s, m) => s + m.passedTests, 0)
          const groupFailed = group.modules.reduce((s, m) => s + m.failedTests, 0)
          const groupRate = groupTotal > 0 ? Math.round((groupPassed / groupTotal) * 100) : 0
          const groupHealth = getHealthColor(groupRate, groupTotal)

          // Group trend: average of module trends per run
          const groupTrend = (() => {
            const modulesWithTrend = group.modules.filter((m) => m.trend && m.trend.length > 0)
            if (modulesWithTrend.length === 0) return null
            const maxLen = Math.max(...modulesWithTrend.map((m) => m.trend!.length))
            const avgByRun: number[] = []
            for (let i = 0; i < maxLen; i++) {
              const vals = modulesWithTrend.filter((m) => m.trend![i] !== undefined).map((m) => m.trend![i])
              avgByRun.push(Math.round(vals.reduce((s, v) => s + v, 0) / vals.length))
            }
            return avgByRun
          })()

          return (
            <div key={group.name}>
              {/* Group Header */}
              <div className="flex items-center gap-3 mb-3 mt-2">
                <div className="flex items-center gap-2">
                  <span className="text-[13px]">{group.icon}</span>
                  <h3 className="text-[13px] font-semibold text-[#444] dark:text-gray-200 uppercase tracking-wide">{group.name}</h3>
                  <span className="text-[11px] text-[#aaa] dark:text-gray-500">{group.modules.length} modules</span>
                </div>
                <div className="flex-1 h-px bg-gray-100 dark:bg-gray-700" />
                {groupTotal > 0 && (
                  <span className={`text-[12px] font-semibold px-2 py-0.5 rounded-full ${
                    groupRate === 100 ? 'bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                    groupRate >= 75 ? 'bg-orange-50 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' :
                    'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                  }`}>
                    {groupRate}%
                  </span>
                )}
              </div>

              {/* Module Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2.5">
                {group.modules.map((mod) => {
                  const health = getHealthColor(mod.passRate, mod.totalTests)
                  const sparkColor = mod.trend ? getSparklineColor(mod.passRate, mod.trend[mod.trend.length - 2]) : { stroke: 'currentColor', fill: 'currentColor' }
                  return (
                    <button
                      key={mod.moduleId}
                      onClick={() => onSelectModule(mod.moduleId)}
                      title={`${mod.moduleName} — ${mod.passRate}% pass rate (${mod.passedTests}/${mod.totalTests} tests)`}
                      className={`relative text-left p-4 rounded-[14px] border transition-all hover:shadow-md hover:-translate-y-0.5 cursor-pointer bg-white dark:bg-gray-800 border-gray-100 dark:border-gray-700 hover:border-[#3F51B5]/30 dark:hover:border-indigo-600/30 shadow-[0_8px_22px_rgba(0,0,0,0.05)]`}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <div className={`w-2.5 h-2.5 rounded-full shrink-0 ${health.indicator}`} />
                        <span className="text-[14px] font-semibold text-gray-800 dark:text-gray-100 truncate">{mod.moduleName}</span>
                      </div>
                      <div className="flex items-center gap-3 text-[11px]">
                        {mod.totalTests > 0 ? (
                          <>
                            <span className={`text-[16px] font-bold ${health.text}`}>{mod.passRate}%</span>
                            <span className="text-gray-400 dark:text-gray-500">
                              {mod.passedTests}/{mod.totalTests}
                            </span>
                            {mod.trend && mod.trend.length >= 2 && (
                              <Sparkline
                                data={mod.trend}
                                width={64}
                                height={20}
                                strokeColor={sparkColor.stroke}
                                fillColor={sparkColor.fill}
                                strokeWidth={1.5}
                                className="ml-auto"
                              />
                            )}
                            {!mod.trend && (
                              <Progress value={mod.passRate} className="h-1.5 flex-1 bg-gray-200 dark:bg-gray-700" />
                            )}
                          </>
                        ) : (
                          <span className="text-gray-400 dark:text-gray-500">No tests yet</span>
                        )}
                      </div>
                      {mod.totalTests > 0 && (
                        <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-1.5 flex items-center justify-between">
                          <div className="flex items-center gap-1">
                            <Clock className="size-2.5" />
                            {mod.lastRun}
                          </div>
                          {mod.trend && <TrendIndicator data={mod.trend} />}
                        </div>
                      )}
                      {/* Feature 3: Run Tests overlay button */}
                      {mod.totalTests > 0 && onRunModule && (
                        <span
                          onClick={(e) => { e.stopPropagation(); onRunModule(mod.moduleId) }}
                          className="absolute bottom-2.5 right-2.5 flex items-center gap-1 bg-[#2D3FC7] hover:bg-[#3F51B5] text-white text-[10px] font-semibold px-2 py-1 rounded-md shadow-sm transition-all hover:shadow-md cursor-pointer"
                          title="Run all tests for this module"
                        >
                          <Play className="size-2.5" />
                          Run
                        </span>
                      )}
                    </button>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
