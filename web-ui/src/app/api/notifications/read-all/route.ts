import { NextResponse } from 'next/server'
import { db } from '@/lib/db'

// PATCH /api/notifications/read-all — mark all notifications as read
export async function PATCH() {
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
