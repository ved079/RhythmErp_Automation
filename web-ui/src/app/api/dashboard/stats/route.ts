// ─── /api/dashboard/stats ────────────────────────────────
// GET — Aggregated dashboard statistics

import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { validateSession } from '@/lib/session'

export async function GET(req: NextRequest) {
  // ── Auth check ──
  const user = await validateSession(req)
  if (!user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
  }

  const isAdmin = user.role === 'admin'
  const userId = user.id

  try {
    // ── Build where clauses based on user role ──
    const runWhere = isAdmin ? {} : { userId }
    const bugWhere = isAdmin ? {} : { userId }

    // ── Run all independent queries in parallel ──
    const [
      runHistoryAggregate,
      totalBugs,
      openBugs,
      inProgressBugs,
      fixedBugs,
      highPriorityBugs,
      totalRuns,
      completedRuns,
      failedRuns,
      activeUsers,
      activeModules,
      activeEnvs,
      recentRuns,
      recentBugs,
      allRunHistory,
      last7DaysBugs,
      bugsByPriority,
      bugsByStatus,
    ] = await Promise.all([
      // Aggregate passed/failed/total from RunHistory
      db.runHistory.aggregate({
        _sum: { passed: true, failed: true, total: true },
        _count: true,
        where: runWhere,
      }),

      // Total bugs
      db.bugReport.count({ where: bugWhere }),

      // Bugs by status
      db.bugReport.count({ where: { ...bugWhere, status: 'open' } }),
      db.bugReport.count({ where: { ...bugWhere, status: 'in_progress' } }),
      db.bugReport.count({ where: { ...bugWhere, status: 'fixed' } }),

      // High priority bugs
      db.bugReport.count({ where: { ...bugWhere, priority: 'high' } }),

      // Total runs (same as _count from aggregate, but explicit for clarity)
      db.runHistory.count({ where: runWhere }),

      // Runs by status
      db.runHistory.count({ where: { ...runWhere, status: 'completed' } }),
      db.runHistory.count({ where: { ...runWhere, status: 'failed' } }),

      // Active users
      db.user.count({ where: { status: 'active' } }),

      // Active modules
      db.testModule.count({ where: { status: 'active' } }),

      // Active environments
      db.environment.count({ where: { status: 'active' } }),

      // Recent 10 runs
      db.runHistory.findMany({
        where: runWhere,
        orderBy: { startedAt: 'desc' },
        take: 10,
        select: {
          id: true,
          moduleId: true,
          moduleName: true,
          passed: true,
          failed: true,
          total: true,
          rate: true,
          duration: true,
          status: true,
          startedAt: true,
          completedAt: true,
          createdBy: true,
        },
      }),

      // Recent 5 bugs
      db.bugReport.findMany({
        where: bugWhere,
        orderBy: { createdAt: 'desc' },
        take: 5,
        select: {
          id: true,
          testId: true,
          testDescription: true,
          moduleName: true,
          error: true,
          priority: true,
          status: true,
          reporterName: true,
          assignedToName: true,
          createdAt: true,
          updatedAt: true,
        },
      }),

      // All run history for moduleHealth & runTrend computation
      db.runHistory.findMany({
        where: runWhere,
        select: {
          moduleName: true,
          passed: true,
          failed: true,
          total: true,
          rate: true,
          startedAt: true,
          status: true,
        },
      }),

      // Bugs from the last 7 days for bugTrend
      db.bugReport.findMany({
        where: {
          ...bugWhere,
          createdAt: {
            gte: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
          },
        },
        select: {
          createdAt: true,
        },
      }),

      // Bug count grouped by priority
      db.bugReport.groupBy({
        by: ['priority'],
        _count: { _all: true },
        where: bugWhere,
      }),

      // Bug count grouped by status
      db.bugReport.groupBy({
        by: ['status'],
        _count: { _all: true },
        where: bugWhere,
      }),
    ])

    // ── Compute derived values ──

    const totalPassed = runHistoryAggregate._sum.passed ?? 0
    const totalFailed = runHistoryAggregate._sum.failed ?? 0
    const totalTests = runHistoryAggregate._sum.total ?? 0
    const passRate = totalTests > 0 ? Math.round((totalPassed / totalTests) * 10000) / 100 : 0

    // ── Bug Trend: last 7 days grouped by day ──
    const bugTrendMap = new Map<string, number>()
    // Initialize last 7 days with 0
    for (let i = 6; i >= 0; i--) {
      const d = new Date()
      d.setDate(d.getDate() - i)
      const key = d.toISOString().slice(0, 10) // YYYY-MM-DD
      bugTrendMap.set(key, 0)
    }
    for (const bug of last7DaysBugs) {
      const key = bug.createdAt.toISOString().slice(0, 10)
      if (bugTrendMap.has(key)) {
        bugTrendMap.set(key, (bugTrendMap.get(key) ?? 0) + 1)
      }
    }
    const bugTrend = Array.from(bugTrendMap.entries()).map(([date, count]) => ({ date, count }))

    // ── Run Trend: last 10 runs with passRate ──
    const runTrend = recentRuns.map((r) => ({
      id: r.id,
      moduleName: r.moduleName,
      passed: r.passed,
      failed: r.failed,
      total: r.total,
      passRate: r.rate,
      duration: r.duration,
      status: r.status,
      startedAt: r.startedAt.toISOString(),
    }))

    // ── Module Health: group by moduleName, compute passRate per module ──
    const moduleHealthMap = new Map<string, { passed: number; failed: number; total: number; runs: number }>()
    for (const run of allRunHistory) {
      const existing = moduleHealthMap.get(run.moduleName) ?? { passed: 0, failed: 0, total: 0, runs: 0 }
      existing.passed += run.passed
      existing.failed += run.failed
      existing.total += run.total
      existing.runs += 1
      moduleHealthMap.set(run.moduleName, existing)
    }
    const moduleHealth = Array.from(moduleHealthMap.entries()).map(([moduleName, data]) => ({
      moduleName,
      passed: data.passed,
      failed: data.failed,
      total: data.total,
      runs: data.runs,
      passRate: data.total > 0 ? Math.round((data.passed / data.total) * 10000) / 100 : 0,
    }))

    // ── Bug by Priority ──
    const bugByPriority: Record<string, number> = { low: 0, medium: 0, high: 0 }
    for (const entry of bugsByPriority) {
      bugByPriority[entry.priority] = entry._count._all
    }

    // ── Bug by Status ──
    const bugByStatus: Record<string, number> = { open: 0, in_progress: 0, fixed: 0, closed: 0, rejected: 0 }
    for (const entry of bugsByStatus) {
      bugByStatus[entry.status] = entry._count._all
    }

    // ── Build response ──
    return NextResponse.json({
      totalTests,
      totalPassed,
      totalFailed,
      passRate,
      totalBugs,
      openBugs,
      inProgressBugs,
      fixedBugs,
      highPriorityBugs,
      totalRuns,
      completedRuns,
      failedRuns,
      activeUsers,
      activeModules,
      activeEnvs,
      recentRuns: recentRuns.map((r) => ({
        id: r.id,
        moduleId: r.moduleId,
        moduleName: r.moduleName,
        passed: r.passed,
        failed: r.failed,
        total: r.total,
        rate: r.rate,
        duration: r.duration,
        status: r.status,
        startedAt: r.startedAt.toISOString(),
        completedAt: r.completedAt?.toISOString() ?? null,
        createdBy: r.createdBy,
      })),
      bugTrend,
      runTrend,
      moduleHealth,
      recentBugs: recentBugs.map((b) => ({
        id: b.id,
        testId: b.testId,
        testDescription: b.testDescription,
        moduleName: b.moduleName,
        error: b.error,
        priority: b.priority,
        status: b.status,
        reporterName: b.reporterName,
        assignedToName: b.assignedToName,
        createdAt: b.createdAt.toISOString(),
        updatedAt: b.updatedAt.toISOString(),
      })),
      bugByPriority,
      bugByStatus,
    })
  } catch (err) {
    console.error('Dashboard stats error:', err)
    return NextResponse.json({ error: 'Failed to load dashboard stats' }, { status: 500 })
  }
}
