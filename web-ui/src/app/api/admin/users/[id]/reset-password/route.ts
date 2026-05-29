// ─── /api/admin/users/[id]/reset-password ────────────────
// POST — Reset user password to a default or provided value
// GET  — Get password reset history for this user

import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import bcrypt from 'bcryptjs'
import { validateAdmin, createAuditLog } from '@/lib/admin-helpers'

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
        action: 'reset_password',
        targetType: 'user',
        targetId: id,
      },
      orderBy: { createdAt: 'desc' },
      take: 5,
    })

    const history = resetHistory.map((entry) => {
      // details format: "Password reset by admin to: <password>"
      const passwordMatch = entry.details.match(/to: (.+)$/)
      return {
        id: entry.id,
        resetBy: entry.userName,
        date: entry.createdAt,
        password: passwordMatch ? passwordMatch[1] : '—',
      }
    })

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
    const newPassword = body.password || 'changeme'

    const hashedPassword = await bcrypt.hash(newPassword, 12)
    await db.user.update({
      where: { id },
      data: { password: hashedPassword },
    })

    // Invalidate all sessions for this user so they have to re-login
    try {
      await db.session.deleteMany({ where: { userId: id } })
    } catch {}

    // Create audit log with the password so admin can see it in history
    await createAuditLog({
      userId: auth.user.id,
      userName: auth.user.name,
      action: 'reset_password',
      targetType: 'user',
      targetId: id,
      targetLabel: `${existing.name} (${existing.email})`,
      details: `Password reset by admin to: ${newPassword}`,
    })

    return NextResponse.json({ message: 'Password reset successfully', password: newPassword })
  } catch (err) {
    console.error('Reset password error:', err)
    return NextResponse.json({ error: 'Failed to reset password' }, { status: 500 })
  }
}
