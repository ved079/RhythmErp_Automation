'use client'

import React, { useMemo, useCallback } from 'react'
import { Progress } from '@/components/ui/progress'
import { Sparkline, getSparklineColor, TrendIndicator } from '@/components/ui/sparkline'
import { PassRateTrendChart, ModuleHealthBarChart, BugDistributionPie, TestExecutionTimeline } from '@/components/dashboard/DashboardCharts'
import { ExportMenu } from '@/components/export/ExportUtils'
import { Play, Clock, TrendingUp, BarChart3, AlertTriangle, Activity } from 'lucide-react'
import type { ModuleHealth, RunSnapshot } from '@/lib/types'

// ─── DASHBOARD TAB (Feature 3) ───────────────────────────
function DashboardTab({
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

        {/* Quick Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-3.5 border border-gray-100 dark:border-gray-700 shadow-sm">
            <div className="text-[11px] text-[#888888] dark:text-gray-400 font-medium uppercase tracking-wider">Total Modules</div>
            <div className="text-xl font-bold text-[#333333] dark:text-gray-100 mt-1">{quickStats.total}</div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-3.5 border border-green-100 dark:border-green-800/50 shadow-sm">
            <div className="text-[11px] text-[#4CAF50] dark:text-green-400 font-medium uppercase tracking-wider">Fully Passing</div>
            <div className="text-xl font-bold text-[#2E7D32] dark:text-green-400 mt-1">{quickStats.fullyPassing}</div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-3.5 border border-orange-100 dark:border-orange-800/50 shadow-sm">
            <div className="text-[11px] text-[#FF9800] dark:text-orange-400 font-medium uppercase tracking-wider">Partial / Critical</div>
            <div className="text-xl font-bold text-[#E65100] dark:text-orange-400 mt-1">{quickStats.partiallyPassing}</div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg p-3.5 border border-indigo-100 dark:border-indigo-800/50 shadow-sm">
            <div className="text-[11px] text-[#3F51B5] dark:text-indigo-400 font-medium uppercase tracking-wider">Overall Pass Rate</div>
            <div className="flex items-center gap-2 mt-1">
              <div className="text-xl font-bold text-[#3F51B5] dark:text-indigo-400">
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
            <div className="text-[11px] text-[#888888] dark:text-gray-400 mt-0.5">
              {quickStats.totalPassed} / {quickStats.totalTests} tests passed
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
            <PassRateTrendChart runHistory={runHistory || []} />
          </div>
          {/* Module Health Bar Chart */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-100 dark:border-gray-700 shadow-sm">
            <h3 className="text-[13px] font-semibold text-[#333333] dark:text-gray-100 mb-3 flex items-center gap-2">
              <BarChart3 className="size-4 text-[#3F51B5]" />
              Module Health Overview
            </h3>
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
            <BugDistributionPie moduleHealth={moduleHealth} />
          </div>
          {/* Test Execution Timeline */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-100 dark:border-gray-700 shadow-sm">
            <h3 className="text-[13px] font-semibold text-[#333333] dark:text-gray-100 mb-3 flex items-center gap-2">
              <Activity className="size-4 text-[#3F51B5]" />
              Execution Timeline
            </h3>
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
              <div className="flex items-center gap-2 mb-2.5">
                <span className="text-[14px]">{group.icon}</span>
                <h3 className="text-[14px] font-semibold text-[#333333] dark:text-gray-100">{group.name}</h3>
                <span className="text-[12px] text-[#888888] dark:text-gray-400 ml-1">
                  {group.modules.length} modules
                </span>
                {groupTotal > 0 && (
                  <>
                    <div className="flex-1" />
                    {groupTrend && groupTrend.length >= 2 && (
                      <Sparkline
                        data={groupTrend}
                        width={56}
                        height={16}
                        strokeColor={groupTrend[groupTrend.length - 1] >= groupTrend[groupTrend.length - 2] ? '#22c55e' : '#ef4444'}
                        fillColor={groupTrend[groupTrend.length - 1] >= groupTrend[groupTrend.length - 2] ? '#22c55e' : '#ef4444'}
                        strokeWidth={1.5}
                      />
                    )}
                    <span className={`text-[12px] font-medium ${groupHealth.text}`}>
                      {groupRate}%
                    </span>
                    <span className="text-[11px] text-gray-400 dark:text-gray-500">
                      ({groupPassed}/{groupTotal})
                    </span>
                  </>
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
                      className={`relative text-left p-3.5 rounded-[14px] border transition-all hover:shadow-md hover:-translate-y-0.5 cursor-pointer bg-white dark:bg-gray-800 border-gray-100 dark:border-gray-700 hover:border-[#3F51B5]/30 dark:hover:border-indigo-600/30 shadow-[0_8px_22px_rgba(0,0,0,0.05)]`}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <div className={`w-2.5 h-2.5 rounded-full shrink-0 ${health.indicator}`} />
                        <span className="text-[13px] font-medium text-gray-800 dark:text-gray-100 truncate">{mod.moduleName}</span>
                      </div>
                      <div className="flex items-center gap-3 text-[11px]">
                        {mod.totalTests > 0 ? (
                          <>
                            <span className={`font-medium ${health.text}`}>{mod.passRate}%</span>
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
                        <div className="text-[10px] text-gray-400 dark:text-gray-500 mt-1.5 flex items-center justify-between">
                          <div className="flex items-center gap-1">
                            <Clock className="size-2.5" />
                            {mod.lastRun}
                          </div>
                          {mod.trend && <TrendIndicator data={mod.trend} />}
                        </div>
                      )}
                      {/* Feature 3: Run Tests overlay button */}
                      {mod.totalTests > 0 && onRunModule && (
                        <button
                          onClick={(e) => { e.stopPropagation(); onRunModule(mod.moduleId) }}
                          className="absolute bottom-2.5 right-2.5 flex items-center gap-1 bg-[#2D3FC7] hover:bg-[#3F51B5] text-white text-[10px] font-semibold px-2 py-1 rounded-md shadow-sm transition-all hover:shadow-md cursor-pointer"
                          title="Run all tests for this module"
                        >
                          <Play className="size-2.5" />
                          Run
                        </button>
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

export { DashboardTab }
