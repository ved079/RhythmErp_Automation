import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { validateAdmin } from '@/lib/admin-helpers'
import { stat } from 'fs/promises'
import path from 'path'

export async function GET(req: NextRequest) {
  const result = await validateAdmin(req)
  if ('error' in result) return result.error

  try {
    // DB Stats
    const [users, runs, bugs, modules, environments, notifications] = await Promise.all([
      db.user.count(),
      db.runHistory.count(),
      db.bugReport.count(),
      db.testModule.count(),
      db.environment.count(),
      db.notification.count(),
    ])

    // DB File Size
    let dbFileSize = '—'
    try {
      const dbPath = path.join(process.cwd(), 'db', 'custom.db')
      const info = await stat(dbPath)
      const mb = (info.size / (1024 * 1024)).toFixed(2)
      dbFileSize = `${mb} MB`
    } catch {
      // Try fallback locations
      try {
        const dbPath = path.join(process.cwd(), 'db', 'dev.db')
        const info = await stat(dbPath)
        const mb = (info.size / (1024 * 1024)).toFixed(2)
        dbFileSize = `${mb} MB`
      } catch {
        // Try prisma default location
        try {
          const dbPath = path.join(process.cwd(), 'prisma', 'dev.db')
          const info = await stat(dbPath)
          const mb = (info.size / (1024 * 1024)).toFixed(2)
          dbFileSize = `${mb} MB`
        } catch {
          // File not found, leave as "—"
        }
      }
    }

    // Last Run
    const lastRunRecord = await db.runHistory.findFirst({
      orderBy: { startedAt: 'desc' },
      take: 1,
    })
    const lastRun = lastRunRecord
      ? {
          id: lastRunRecord.id,
          moduleName: lastRunRecord.moduleName,
          status: lastRunRecord.status,
          completedAt: lastRunRecord.completedAt?.toISOString() || '',
        }
      : null

    // Active modules
    const activeModules = await db.testModule.count({
      where: { status: 'active' },
    })

    // Total test cases (sum of testCount from modules)
    const moduleAgg = await db.testModule.aggregate({
      _sum: { testCount: true },
    })
    const totalTestCases = moduleAgg._sum.testCount || 0

    const serverUptime = Math.floor(process.uptime())

    return NextResponse.json({
      dbStats: { users, runs, bugs, modules, environments, notifications },
      dbFileSize,
      lastRun,
      activeModules,
      totalTestCases,
      serverUptime,
    })
  } catch (error) {
    console.error('System health error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch system health' },
      { status: 500 }
    )
  }
}
