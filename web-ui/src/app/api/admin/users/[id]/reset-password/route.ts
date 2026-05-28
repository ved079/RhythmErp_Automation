// ─── /api/admin/users/[id]/reset-password ────────────────
// POST — Reset user password to a default or provided value

import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import bcrypt from 'bcryptjs'
import { validateAdmin, createAuditLog } from '@/lib/admin-helpers'

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
    await db.session.deleteMany({ where: { userId: id } })

    await createAuditLog({
      userId: auth.user.id,
      userName: auth.user.name,
      action: 'reset_password',
      targetType: 'user',
      targetId: id,
      targetLabel: `${existing.name} (${existing.email})`,
      details: 'Password reset by admin',
    })

    return NextResponse.json({ message: 'Password reset successfully' })
  } catch (err) {
    console.error('Reset password error:', err)
    return NextResponse.json({ error: 'Failed to reset password' }, { status: 500 })
  }
}
