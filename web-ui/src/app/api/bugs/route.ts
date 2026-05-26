import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'

// GET /api/bugs -” list all bug reports with replies
export async function GET() {
  try {
    const reports = await db.bugReport.findMany({
      orderBy: { createdAt: 'desc' },
      include: { replies: { orderBy: { createdAt: 'asc' } } },
    })

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
    console.error('[BugReports] GET error:', error)
    return NextResponse.json({ error: 'Failed to fetch bug reports' }, { status: 500 })
  }
}

// POST /api/bugs -” create a new bug report
export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { testId, testDescription, moduleName, error, userNote, priority, reporterName, reporterEmail } = body

    if (!testId || !testDescription || !reporterName || !reporterEmail) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 })
    }

    const dbPriority = priority === 'low' || priority === 'medium' || priority === 'high' ? priority : 'medium'

    const report = await db.bugReport.create({
      data: {
        testId,
        testDescription,
        moduleName: moduleName || '',
        error: error || '',
        userNote: userNote || '',
        priority: dbPriority,
        status: 'open',
        reporterName,
        reporterEmail,
        readByUser: true,
        readByAdmin: false,
      },
      include: { replies: true },
    })

    await db.notification.create({
      data: {
        type: 'schedule',
        title: 'New bug report filed',
        message: `${reporterName} filed ${report.id} for ${testDescription}`,
        ticketId: report.id,
      },
    })

    const mapped = {
      ...report,
      status: report.status === 'in_progress' ? 'in-progress' : report.status,
      replies: report.replies.map((rep) => ({ ...rep })),
    }

    return NextResponse.json(mapped, { status: 201 })
  } catch (error) {
    console.error('[BugReports] POST error:', error)
    return NextResponse.json({ error: 'Failed to create bug report' }, { status: 500 })
  }
}