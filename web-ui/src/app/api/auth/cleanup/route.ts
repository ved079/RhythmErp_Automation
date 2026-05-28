// ─── /api/auth/cleanup ──────────────────────────────────────
// POST — Cleanup expired sessions (can be called by a cron job)

import { NextResponse } from 'next/server'
import { cleanupExpiredSessions, validateAdminSession } from '@/lib/session'
import type { NextRequest } from 'next/server'

export async function POST(req: NextRequest) {
  // Only admins can trigger cleanup
  const user = await validateAdminSession(req)
  if (!user) {
    return NextResponse.json({ error: 'Not authorized' }, { status: 401 })
  }

  try {
    const count = await cleanupExpiredSessions()
    return NextResponse.json({ message: `Cleaned up ${count} expired sessions`, count })
  } catch (error) {
    console.error('Session cleanup error:', error)
    return NextResponse.json({ error: 'Failed to cleanup sessions' }, { status: 500 })
  }
}
