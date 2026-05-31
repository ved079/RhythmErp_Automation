import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { validateSession } from '@/lib/session'

// PATCH /api/notifications/read-all — mark all notifications as read
// C1: Now requires authentication
export async function PATCH(req: NextRequest) {
  const user = await validateSession(req)
  if (!user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
  }

  try {
    await db.notification.updateMany({
      where: { read: false },
      data: { read: true },
    })

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('[Notifications] read-all PATCH error:', error)
    return NextResponse.json({ error: 'Failed to mark all as read' }, { status: 500 })
  }
}
