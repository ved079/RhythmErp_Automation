// ─── /api/admin/users/[id]/reset-password ────────────────
// POST — Reset user password to a default or provided value
// GET  — Get password reset history for this user

import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import bcrypt from 'bcryptjs'
import { validateAdmin, createAuditLogWithRequest } from '@/lib/admin-helpers'

// GET — Fetch password reset history for a user (from audit log)
export async function GET(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const auth = await validateAdmin(req)
  if ('error' in auth) return auth.error
  const { id } = await params

  try {
    const user = await db.user.findUnique({ where: { id } })
    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }

    // Get last 5 reset_password audit entries for this user
    const resetHistory = await db.auditLog.findMany({
      where: {
        action: { in: ['reset_password', 'password_change'] },
        targetType: 'user',
        targetId: id,
      },
      orderBy: { createdAt: 'desc' },
      take: 5,
    })

    // H1: Do NOT expose passwords in audit history
    const history = resetHistory.map((entry) => ({
      id: entry.id,
      resetBy: entry.userName,
      date: entry.createdAt,
      ipAddress: entry.ipAddress || '—',
      details: entry.details.replace(/password:\s*\S+/i, 'password: [REDACTED]'),
    }))

    return NextResponse.json({ history })
  } catch (err) {
    console.error('Reset history error:', err)
    return NextResponse.json({ history: [] })
  }
}

// POST — Reset user password
export async function POST(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const auth = await validateAdmin(req)
  if ('error' in auth) return auth.error
  const { id } = await params

  try {
    const existing = await db.user.findUnique({ where: { id } })
    if (!existing) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }

    // Don't allow resetting own password this way
    if (existing.id === auth.user.id) {
      return NextResponse.json({ error: 'Use profile settings to change your own password' }, { status: 403 })
    }

    const body = await req.json().catch(() => ({}))
    // C4: Use env var for default password instead of hardcoded 'changeme'
    const defaultPassword = process.env.DEFAULT_USER_PASSWORD || 'changeme'
    const newPassword = body.password || defaultPassword

    const hashedPassword = await bcrypt.hash(newPassword, 12)
    await db.user.update({
      where: { id },
      data: { password: hashedPassword },
    })

    // Invalidate all sessions for this user so they have to re-login
    try {
      await db.session.deleteMany({ where: { userId: id } })
    } catch {}

    // H1: Create audit log — do NOT log the password in plaintext
    await createAuditLogWithRequest(req, {
      userId: auth.user.id,
      userName: auth.user.name,
      action: 'reset_password',
      targetType: 'user',
      targetId: id,
      targetLabel: `${existing.name} (${existing.email})`,
      details: 'Password reset by admin',
    })

    return NextResponse.json({ message: 'Password reset successfully', password: newPassword })
  } catch (err) {
    console.error('Reset password error:', err)
    return NextResponse.json({ error: 'Failed to reset password' }, { status: 500 })
  }
}
