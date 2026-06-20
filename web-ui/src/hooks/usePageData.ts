'use client'

import { useState, useEffect, useCallback } from 'react'
import { fetchTestCases, type TestCasesData } from '@/lib/api'
import { getBugReports } from '@/lib/bug-reports'
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

export function usePageData({ user, selectedModule }: UsePageDataInput): UsePageDataReturn {
  const [dashboardStats, setDashboardStats] = useState<Record<string, unknown> | null>(null)
  const [dashboardLoading, setDashboardLoading] = useState(false)
  const [runHistory, setRunHistory] = useState<RunSnapshot[]>([])
  const [bugReportsList, setBugReportsList] = useState<Array<{ id: string; testId: string; desc: string; status: string }>>([])
  const [myTicketUnread, setMyTicketUnread] = useState(0)
  const [visibilityData, setVisibilityData] = useState<VisibilityData | null>(null)
  const [allTestCases, setAllTestCases] = useState<TestCasesData>({})

  const loadRunHistory = useCallback(async () => {
    try {
      const res = await fetch('/api/runs?limit=50')
      if (res.ok) {
        const data = await res.json()
        const mapped: RunSnapshot[] = (data as Array<{
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
        setRunHistory(mapped)
      }
    } catch {}
  }, [])

  const loadBugReports = useCallback(async () => {
    try {
      const reports = await getBugReports()
      setBugReportsList(reports.map((r) => ({
        id: r.id, testId: r.testId, desc: r.error || r.testDescription,
        status: r.status === 'open' ? 'Open' : r.status === 'in_progress' ? 'In Progress' : 'Fixed',
      })))
      const unread = reports.filter(r => !r.readByUser && (r.replies.length > 0 || r.status === 'open' || r.status === 'in-progress')).length
      setMyTicketUnread(unread)
    } catch {}
  }, [])

  const loadDashboardStats = useCallback(async () => {
    setDashboardLoading(true)
    try {
      const res = await fetch('/api/dashboard/stats')
      if (res.ok) { const data = await res.json(); setDashboardStats(data) }
    } catch {} finally { setDashboardLoading(false) }
  }, [])

  const loadVisibility = useCallback(async (): Promise<VisibilityData | null> => {
    try {
      const res = await fetch('/api/admin/tests/visibility')
      if (res.ok) {
        const data = await res.json()
        setVisibilityData(data)
        return data
      }
    } catch {}
    return null
  }, [])

  useEffect(() => {
    if (!user) return
    const timer = setTimeout(() => {
      fetchTestCases()
        .then((data) => {
          setAllTestCases(data)
          if (typeof window !== 'undefined') { (window as any).__ALL_TEST_CASES__ = data }
        })
        .catch(() => {})
    }, 200)
    return () => clearTimeout(timer)
  }, [user])

  useEffect(() => {
    if (selectedModule === 'dashboard') loadDashboardStats()
  }, [selectedModule, loadDashboardStats])

  useEffect(() => {
    if (!user) return
    const timer = setTimeout(() => {
      loadRunHistory()
      loadBugReports()
    }, 100)
    return () => clearTimeout(timer)
  }, [user, loadRunHistory, loadBugReports])

  return {
    dashboardStats,
    dashboardLoading,
    runHistory,
    bugReportsList,
    myTicketUnread,
    visibilityData,
    allTestCases,
    loadRunHistory,
    loadBugReports,
    loadDashboardStats,
    loadVisibility,
  }
}
