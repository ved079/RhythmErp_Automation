import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { validateSession } from '@/lib/session'
import { checkRateLimit, getClientIp } from '@/lib/rate-limit'

function isMissingTableError(error: unknown): boolean {
  return error instanceof Error && 'code' in error && (error as any).code === 'P2021'
}

// GET /api/schedules — list all scheduled runs
// C1: Now requires authentication
export async function GET(req: NextRequest) {
  const user = await validateSession(req)
  if (!user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
  }

  try {
    const runs = await db.scheduledRun.findMany({
      orderBy: { createdAt: 'desc' },
    })

    // Map DB enums to client format
    const mapped = runs.map((r) => ({
      ...r,
      frequency: r.frequency === 'one_time' ? 'one-time' : r.frequency,
      testSelection: r.testSelection,
      selectedTestIds: r.selectedTestIds ? JSON.parse(r.selectedTestIds) : undefined,
    }))

    return NextResponse.json(mapped)
  } catch (error) {
    if (isMissingTableError(error)) return NextResponse.json([])
    console.error('[Schedules] GET error:', error)
    return NextResponse.json({ error: 'Failed to fetch scheduled runs' }, { status: 500 })
  }
}

// POST /api/schedules — create a scheduled run
// C1: Now requires authentication
export async function POST(req: NextRequest) {
  const user = await validateSession(req)
  if (!user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
  }

  // C3: Rate limiting — 10 schedule creations per minute per IP
  const clientIp = getClientIp(req)
  const rateCheck = checkRateLimit(clientIp, 'schedule-create', { maxRequests: 10, windowMs: 60_000 })
  if (rateCheck.limited) {
    return NextResponse.json(
      { error: 'Too many requests. Please try again later.' },
      {
        status: 429,
        headers: { 'Retry-After': String(Math.ceil((rateCheck.retryAfterMs || 60_000) / 1000)) }
      }
    )
  }

  try {
    const body = await req.json()
    const { moduleId, moduleName, frequency, scheduledTime, testSelection, selectedTestIds, enabled, createdBy } = body

    if (!moduleId || !moduleName || !scheduledTime || !createdBy) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 })
    }

    // Map client frequency to DB enum
    const freqMap: Record<string, string> = {
      'one-time': 'one_time',
      'one_time': 'one_time',
      'daily': 'daily',
      'weekly': 'weekly',
    }
    const dbFrequency = freqMap[frequency] || 'one_time'

    const validSelections = ['all', 'priority', 'selected']
    const dbSelection = validSelections.includes(testSelection) ? testSelection : 'all'

    const run = await db.scheduledRun.create({
      data: {
        moduleId,
        moduleName,
        frequency: dbFrequency,
        scheduledTime: new Date(scheduledTime),
        testSelection: dbSelection,
        selectedTestIds: selectedTestIds ? JSON.stringify(selectedTestIds) : null,
        enabled: enabled !== undefined ? enabled : true,
        createdBy,
      },
    })

    // Create notification
    await db.notification.create({
      data: {
        type: 'schedule',
        title: 'New schedule created',
        message: `Schedule created for ${moduleName} (${frequency})`,
      },
    })

    const mapped = {
      ...run,
      frequency: run.frequency === 'one_time' ? 'one-time' : run.frequency,
      selectedTestIds: run.selectedTestIds ? JSON.parse(run.selectedTestIds) : undefined,
    }

    return NextResponse.json(mapped, { status: 201 })
  } catch (error) {
    console.error('[Schedules] POST error:', error)
    return NextResponse.json({ error: 'Failed to create scheduled run' }, { status: 500 })
  }
}
