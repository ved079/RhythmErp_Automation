'use client'

import { useEffect, useCallback, useMemo } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchTestCases, type TestCasesData } from '@/lib/api'
import { getBugReports } from '@/lib/bug-reports'
import { warmModuleCache } from '@/lib/module-data'
import type { RunSnapshot, AuthUser } from '@/lib/types'
import type { VisibilityData } from '@/lib/test-helpers'

export interface UsePageDataInput {
  user: AuthUser | null
  selectedModule: string
}

export interface UsePageDataReturn {
  dashboardStats: Record<string, unknown> | null
  dashboardLoading: boolean
  runHistory: RunSnapshot[]
  bugReportsList: Array<{ id: string; testId: string; desc: string; status: string }>
  myTicketUnread: number
  visibilityData: VisibilityData | null
  allTestCases: TestCasesData
  loadRunHistory: () => Promise<void>
  loadBugReports: () => Promise<void>
  loadDashboardStats: () => Promise<void>
  loadVisibility: () => Promise<VisibilityData | null>
}

async function fetchRunHistory(): Promise<RunSnapshot[]> {
  try {
    const res = await fetch('/api/runs?limit=50')
    if (!res.ok) return []
    const data = await res.json()
    return (data as Array<{
      id: string; moduleId: string; moduleName: string; passed: number; failed: number;
      total: number; duration: string; rate: number;
      results: { testId: string; status: string }[] | null; startedAt: string;
      completedAt: string | null; status: string;
    }>).map((r) => ({
      id: r.id,
      date: r.startedAt ? new Date(r.startedAt).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '\u2014',
      moduleId: r.moduleId,
      results: Array.isArray(r.results) ? r.results.map((x: { testId: string; status: string; message?: string }) => ({
        testId: x.testId, status: x.status === 'passed' ? 'passed' as const : 'failed' as const, message: x.message,
      })) : [],
      passed: r.passed || 0, failed: r.failed || 0, total: r.total || 0,
      duration: r.duration || '\u2014', rate: r.rate || 0,
    }))
  } catch { return [] }
}

async function fetchDashboardStats(): Promise<Record<string, unknown> | null> {
  try {
    const res = await fetch('/api/dashboard/stats')
    if (!res.ok) return null
    return res.json()
  } catch { return null }
}

async function fetchVisibility(): Promise<VisibilityData | null> {
  try {
    const res = await fetch('/api/admin/tests/visibility')
    if (!res.ok) return null
    return res.json()
  } catch { return null }
}

export function usePageData({ user, selectedModule }: UsePageDataInput): UsePageDataReturn {
  const qc = useQueryClient()

  const runHistoryQuery = useQuery({
    queryKey: ['runs'],
    queryFn: fetchRunHistory,
    enabled: !!user,
  })

  const bugReportsQuery = useQuery({
    queryKey: ['bugReports'],
    queryFn: getBugReports,
    enabled: !!user,
  })

  const bugReportsList = useMemo(() => {
    if (!bugReportsQuery.data) return []
    return bugReportsQuery.data.map((r) => ({
      id: r.id, testId: r.testId, desc: r.error || r.testDescription,
      status: r.status === 'open' ? 'Open' : r.status === 'in-progress' ? 'In Progress' : 'Fixed',
    }))
  }, [bugReportsQuery.data])

  const myTicketUnread = useMemo(() => {
    if (!bugReportsQuery.data) return 0
    return bugReportsQuery.data.filter(r => !r.readByUser && (r.replies.length > 0 || r.status === 'open' || r.status === 'in-progress')).length
  }, [bugReportsQuery.data])

  const dashboardQuery = useQuery({
    queryKey: ['dashboardStats'],
    queryFn: fetchDashboardStats,
    enabled: !!user && selectedModule === 'dashboard',
  })

  const visibilityQuery = useQuery({
    queryKey: ['visibility'],
    queryFn: fetchVisibility,
    enabled: !!user,
  })

  const testCasesQuery = useQuery({
    queryKey: ['testCases'],
    queryFn: fetchTestCases,
    enabled: !!user,
  })

  useEffect(() => {
    if (!user) return
    warmModuleCache().catch(() => {})
  }, [user])

  const loadRunHistory = useCallback((): Promise<void> => {
    return qc.invalidateQueries({ queryKey: ['runs'] })
  }, [qc])

  const loadBugReports = useCallback((): Promise<void> => {
    return qc.invalidateQueries({ queryKey: ['bugReports'] })
  }, [qc])

  const loadDashboardStats = useCallback((): Promise<void> => {
    return qc.invalidateQueries({ queryKey: ['dashboardStats'] })
  }, [qc])

  const loadVisibility = useCallback(async (): Promise<VisibilityData | null> => {
    try {
      return await qc.fetchQuery({ queryKey: ['visibility'], queryFn: fetchVisibility })
    } catch { return null }
  }, [qc])

  useEffect(() => {
    if (typeof window !== 'undefined' && testCasesQuery.data) {
      (window as any).__ALL_TEST_CASES__ = testCasesQuery.data
    }
  }, [testCasesQuery.data])

  return {
    dashboardStats: dashboardQuery.data ?? null,
    dashboardLoading: dashboardQuery.isFetching,
    runHistory: runHistoryQuery.data ?? [],
    bugReportsList,
    myTicketUnread,
    visibilityData: visibilityQuery.data ?? null,
    allTestCases: testCasesQuery.data ?? {},
    loadRunHistory,
    loadBugReports,
    loadDashboardStats,
    loadVisibility,
  }
}
