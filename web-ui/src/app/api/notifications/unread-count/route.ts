import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { validateSession } from '@/lib/session'

function isMissingTableError(error: unknown): boolean {
  return error instanceof Error && 'code' in error && (error as any).code === 'P2021'
}

// GET /api/notifications/unread-count
// C1: Now requires authentication
export async function GET(req: NextRequest) {
  const user = await validateSession(req)
  if (!user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
  }

  try {
    const count = await db.notification.count({
      where: { read: false },
    })

    return NextResponse.json({ count })
  } catch (error) {
    if (isMissingTableError(error)) {
      // Table doesn't exist yet — return 0 instead of 500
      return NextResponse.json({ count: 0 })
    }
    console.error('[Notifications] unread-count GET error:', error)
    return NextResponse.json({ error: 'Failed to get unread count' }, { status: 500 })
  }
}
