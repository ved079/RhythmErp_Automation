import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'

function isMissingTableError(error: unknown): boolean {
  return error instanceof Error && 'code' in error && (error as any).code === 'P2021'
}

// GET /api/notifications — list all notifications (newest first, capped at 50)
export async function GET() {
  try {
    const notifications = await db.notification.findMany({
      orderBy: { createdAt: 'desc' },
      take: 50,
    })
    return NextResponse.json(notifications)
  } catch (error) {
    if (isMissingTableError(error)) {
      // Table doesn't exist yet — return empty instead of 500
      return NextResponse.json([])
    }
    console.error('[Notifications] GET error:', error)
    return NextResponse.json({ error: 'Failed to fetch notifications' }, { status: 500 })
  }
}

// POST /api/notifications — create a notification
export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { type, title, message, ticketId, userId } = body

    if (!title || !message) {
      return NextResponse.json({ error: 'Missing required fields' }, { status: 400 })
    }

    const validTypes = ['status_change', 'reply', 'schedule', 'run_complete']
    const dbType = validTypes.includes(type) ? type : 'run_complete'

    const notification = await db.notification.create({
      data: {
        type: dbType,
        title,
        message,
        ticketId: ticketId || null,
        userId: userId || null,
      },
    })

    return NextResponse.json(notification, { status: 201 })
  } catch (error) {
    if (isMissingTableError(error)) {
      return NextResponse.json({ error: 'Database not initialized. Run: npx prisma db push' }, { status: 503 })
    }
    console.error('[Notifications] POST error:', error)
    return NextResponse.json({ error: 'Failed to create notification' }, { status: 500 })
  }
}
