import { NextResponse } from 'next/server'
import { db } from '@/lib/db'

// GET /api/notifications/unread-count
export async function GET() {
  try {
    const count = await db.notification.count({
      where: { read: false },
    })

    return NextResponse.json({ count })
  } catch (error) {
    console.error('[Notifications] unread-count GET error:', error)
    return NextResponse.json({ error: 'Failed to get unread count' }, { status: 500 })
  }
}