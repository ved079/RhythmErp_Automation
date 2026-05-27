import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'

// GET /api/runs — list run history
export async function GET(req: NextRequest) {
  try {
    const url = new URL(req.url)
    const moduleId = url.searchParams.get('moduleId')
    const limit = parseInt(url.searchParams.get('limit') || '50')

    const where = moduleId ? { moduleId } : {}

    const runs = await db.runHistory.findMany({
      where,
      orderBy: { startedAt: 'desc' },
      take: limit,
    })

    // Parse results JSON if present
    const mapped = runs.map((r) => ({
      ...r,
      results: r.results ? JSON.parse(r.results) : null,
    }))

    return NextResponse.json(mapped)
  } catch (error) {
    console.error('[RunHistory] GET error:', error)
    return NextResponse.json({ error: 'Failed to fetch run history' }, { status: 500 })
  }
}

// POST /api/runs — create a run history entry
export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { moduleId, moduleName, passed, failed, total, duration, rate, results, status, startedAt, completedAt, createdBy } = body

    if (!moduleId || !moduleName) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 })
    }

    const validStatuses = ['pending', 'running', 'completed', 'failed', 'stopped']
    const dbStatus = validStatuses.includes(status) ? status : 'pending'

    const run = await db.runHistory.create({
      data: {
        moduleId,
        moduleName,
        passed: passed || 0,
        failed: failed || 0,
        total: total || 0,
        duration: duration || '',
        rate: rate || 0,
        results: results ? JSON.stringify(results) : null,
        status: dbStatus,
        startedAt: startedAt ? new Date(startedAt) : new Date(),
        completedAt: completedAt ? new Date(completedAt) : null,
        createdBy: createdBy || null,
      },
    })

    const mapped = {
      ...run,
      results: run.results ? JSON.parse(run.results) : null,
    }

    return NextResponse.json(mapped, { status: 201 })
  } catch (error) {
    console.error('[RunHistory] POST error:', error)
    return NextResponse.json({ error: 'Failed to create run history' }, { status: 500 })
  }
}
