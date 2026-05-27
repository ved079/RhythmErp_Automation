import { NextResponse } from 'next/server'
import { db } from '@/lib/db'

function isMissingTableError(error: unknown): boolean {
  return error instanceof Error && 'code' in error && (error as any).code === 'P2021'
}

// GET /api/notifications/unread-count
export async function GET() {
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
