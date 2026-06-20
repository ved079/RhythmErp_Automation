'use client'

import React from 'react'
import { PersonalDashboardTab } from '@/components/dashboard/PersonalDashboardTab'
import type { AuthUser, RunSnapshot } from '@/lib/types'
import type { SidebarModule } from '@/components/sidebar/SidebarModuleItem'

interface PersonalDashboardRendererProps {
  user: AuthUser
  dashboardStats: Record<string, unknown> | null
  runHistory: RunSnapshot[]
  selectedModule: string
  sidebarModules: SidebarModule[]
  handleSelectModule: (id: string) => void
  setActiveTab: (tab: string) => void
}

export function PersonalDashboardRenderer({
  user,
  dashboardStats,
  runHistory,
  selectedModule,
  sidebarModules,
  handleSelectModule,
  setActiveTab,
}: PersonalDashboardRendererProps) {
  const stats = dashboardStats as Record<string, any> | null
  const totalRuns = (stats?.totalRuns as number) ?? 0
  const passRate = (stats?.passRate as number) ?? 0
  const totalBugs = (stats?.totalBugs as number) ?? 0
  const recentRuns = (stats?.recentRuns as Array<Record<string, any>>) ?? []
  const recentBugs = (stats?.recentBugs as Array<Record<string, any>>) ?? []
  const modulesTested = new Set(runHistory.map((r) => r.moduleId)).size
  const personalStats = {
    totalRuns, passRate, bugsReported: totalBugs, modulesTested,
    recentRuns: recentRuns.slice(0, 5).map((r) => ({ id: r.id as string, moduleName: (r.moduleName as string) || '\u2014', passed: (r.passed as number) ?? 0, failed: (r.failed as number) ?? 0, date: (r.startedAt as string) || '', rate: (r.rate as number) ?? 0 })),
    recentBugs: recentBugs.slice(0, 5).map((b) => ({ id: b.id as string, testDescription: (b.testDescription as string) || (b.testId as string) || '', moduleName: (b.moduleName as string) || '', status: (b.status as string) || 'open', createdAt: (b.createdAt as string) || '' })),
  }

  return (
    <div data-tour="dashboard" className="flex-1 min-h-0 overflow-auto">
      <PersonalDashboardTab userName={user.name || 'User'} userRole={user.role || 'tester'} stats={personalStats}
        onRunTests={() => { if (selectedModule === 'dashboard') { const firstModule = sidebarModules.find(m => m.id !== 'dashboard' && m.id !== 'my-tickets'); if (firstModule) { handleSelectModule(firstModule.id); setTimeout(() => { setActiveTab('test-runner') }, 100) } } }}
        onReportBug={() => { if (selectedModule === 'dashboard') { const firstModule = sidebarModules.find(m => m.id !== 'dashboard' && m.id !== 'my-tickets'); if (firstModule) { handleSelectModule(firstModule.id) } } }}
        onSelectModule={(moduleId) => handleSelectModule(moduleId)}
      />
    </div>
  )
}
