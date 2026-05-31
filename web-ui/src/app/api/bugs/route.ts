import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { validateSession } from '@/lib/session'

function isMissingTableError(error: unknown): boolean {
  return error instanceof Error && 'code' in error && (error as any).code === 'P2021'
}

// GET /api/bugs — list all bug reports with replies
export async function GET(req: NextRequest) {
  try {
    // ── Auth check ──
    const user = await validateSession(req)
    if (!user) {
      return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
    }

    // Non-admin users only see their own bugs
    const where = user.role === 'admin' ? {} : { userId: user.id }

    const reports = await db.bugReport.findMany({
      where,
      orderBy: { createdAt: 'desc' },
      include: { replies: { orderBy: { createdAt: 'asc' } } },
    })

    // Map DB enums to client-friendly format
    const mapped = reports.map((r) => ({
      ...r,
      priority: r.priority,
      status: r.status === 'in_progress' ? 'in-progress' : r.status,
      replies: r.replies.map((rep) => ({
        ...rep,
        authorRole: rep.authorRole,
      })),
    }))

    return NextResponse.json(mapped)
  } catch (error) {
    if (isMissingTableError(error)) return NextResponse.json([])
    console.error('[BugReports] GET error:', error)
    return NextResponse.json({ error: 'Failed to fetch bug reports' }, { status: 500 })
  }
}

// POST /api/bugs — create a new bug report
export async function POST(req: NextRequest) {
  try {
    // ── Auth check ──
    const user = await validateSession(req)
    if (!user) {
      return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
    }

    const body = await req.json()
    const { testId, testDescription, moduleName, error, userNote, priority, reporterName, reporterEmail } = body

    if (!testId || !testDescription || !reporterName || !reporterEmail) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 })
    }

    const isAutoReport = userNote?.includes('Auto-reported')

    // Check for duplicate: if auto-reported, skip if an open bug already exists for this testId
    if (isAutoReport) {
      const existingOpen = await db.bugReport.findFirst({
        where: {
          testId,
          status: 'open',
        },
      })
      if (existingOpen) {
        // Already have an open bug for this test — skip duplicate
        return NextResponse.json({ skipped: true, reason: 'Duplicate open bug exists', existingId: existingOpen.id }, { status: 200 })
      }
    }

    // Map client status to DB enum
    const dbPriority = priority === 'low' || priority === 'medium' || priority === 'high' ? priority : 'medium'

    // Add [Auto] flag to description for auto-reported bugs
    const finalTestDescription = isAutoReport ? `${testDescription} [Auto]` : testDescription

    const report = await db.bugReport.create({
      data: {
        testId,
        testDescription: finalTestDescription,
        moduleName: moduleName || '',
        error: error || '',
        userNote: userNote || '',
        priority: dbPriority,
        status: 'open',
        reporterName,
        reporterEmail,
        readByUser: true,
        readByAdmin: false,
        userId: user.id,
      },
      include: { replies: true },
    })

    // Create notification
    if (isAutoReport) {
      // Auto-reported bug: notify admin specifically
      await db.notification.create({
        data: {
          type: 'status_change',
          title: 'Auto-reported bug',
          message: `Auto-reported bug ${report.id} for ${testDescription} in ${moduleName || 'unknown module'} — ${error?.slice(0, 80) || 'No error details'}`,
          ticketId: report.id,
          userId: null, // null = broadcast to all admins
        },
      })
    } else {
      // Manual bug report: general notification
      await db.notification.create({
        data: {
          type: 'schedule',
          title: 'New bug report filed',
          message: `${reporterName} filed ${report.id} for ${testDescription}`,
          ticketId: report.id,
        },
      })
    }

    const mapped = {
      ...report,
      testDescription: finalTestDescription,
      status: report.status === 'in_progress' ? 'in-progress' : report.status,
      replies: report.replies.map((rep) => ({ ...rep })),
      isAutoReport,
    }

    return NextResponse.json(mapped, { status: 201 })
  } catch (error) {
    console.error('[BugReports] POST error:', error)
    return NextResponse.json({ error: 'Failed to create bug report' }, { status: 500 })
  }
}
