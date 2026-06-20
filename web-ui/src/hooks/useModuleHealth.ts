'use client'

import { useMemo } from 'react'
import type { SidebarModule, RunSnapshot, ModuleHealth } from '@/lib/types'
import type { SidebarModule as SidebarModuleItem } from '@/components/sidebar/SidebarModuleItem'

export function useModuleHealth(runHistory: RunSnapshot[], sidebarModules: SidebarModuleItem[]): ModuleHealth[] {
  return useMemo(() => {
    const moduleInfo = new Map<string, { name: string; parentGroup: string }>()
    function collectModules(items: SidebarModule[], parent?: string) {
      for (const item of items) {
        if (item.id !== 'dashboard' && item.id !== 'my-tickets') {
          const group = parent || (item.children ? item.label : undefined) || 'Standalone'
          moduleInfo.set(item.id, { name: item.label, parentGroup: group })
          if (item.children) collectModules(item.children, item.label)
        }
      }
    }
    collectModules(sidebarModules)
    const runsByModule = new Map<string, RunSnapshot[]>()
    for (const run of runHistory) {
      const existing = runsByModule.get(run.moduleId) || []
      existing.push(run)
      runsByModule.set(run.moduleId, existing)
    }
    const health: ModuleHealth[] = []
    for (const [modId, info] of moduleInfo) {
      const runs = runsByModule.get(modId) || []
      if (runs.length === 0) {
        health.push({ moduleId: modId, moduleName: info.name, parentGroup: info.parentGroup, passRate: 0, totalTests: 0, passedTests: 0, failedTests: 0, lastRun: '\u2014' })
      } else {
        const latestRun = runs[0]
        const passedTests = latestRun.passed
        const failedTests = latestRun.failed
        const totalTests = latestRun.total
        const passRate = totalTests > 0 ? Math.round((passedTests / totalTests) * 100) : 0
        const sortedRuns = [...runs].reverse().slice(-7)
        const trend = sortedRuns.map((r) => r.total > 0 ? Math.round((r.passed / r.total) * 100) : 0)
        health.push({ moduleId: modId, moduleName: info.name, parentGroup: info.parentGroup, passRate, totalTests, passedTests, failedTests, lastRun: latestRun.date, trend })
      }
    }
    return health
  }, [runHistory, sidebarModules])
}
