// ─── /api/auth/reset-password-token ────────────────────
// POST — Reset password using a token (from forgot-password flow)

import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import bcrypt from 'bcryptjs'

export async function POST(request: NextRequest) {
  try {
    const { token, new_password } = await request.json()

    if (!token || typeof token !== 'string') {
      return NextResponse.json({ error: 'Reset token is required' }, { status: 400 })
    }

    if (!new_password || typeof new_password !== 'string') {
      return NextResponse.json({ error: 'New password is required' }, { status: 400 })
    }

    if (new_password.length < 6) {
      return NextResponse.json({ error: 'New password must be at least 6 characters' }, { status: 400 })
    }

    // Find the reset token
    const resetRecord = await db.passwordReset.findUnique({ where: { token } })

    if (!resetRecord) {
      return NextResponse.json({ error: 'Invalid or expired reset token' }, { status: 400 })
    }

    if (resetRecord.used) {
      return NextResponse.json({ error: 'This reset token has already been used' }, { status: 400 })
    }

    if (resetRecord.expiresAt < new Date()) {
      // Mark as used so it can't be retried
      await db.passwordReset.update({ where: { id: resetRecord.id }, data: { used: true } }).catch(() => {})
      return NextResponse.json({ error: 'Reset token has expired. Please request a new one.' }, { status: 400 })
    }

    // Find the user
    const user = await db.user.findUnique({ where: { id: resetRecord.userId } })
    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }

    // Hash and save the new password
    const hashedPassword = await bcrypt.hash(new_password, 12)
    await db.user.update({
      where: { id: user.id },
      data: { password: hashedPassword },
    })

    // Mark token as used
    await db.passwordReset.update({
      where: { id: resetRecord.id },
      data: { used: true },
    })

    // Invalidate all sessions for this user
    await db.session.deleteMany({ where: { userId: user.id } }).catch(() => {})

    // Create audit log (non-critical)
    try {
      await db.auditLog.create({
        data: {
          userId: user.id,
          userName: user.name,
          action: 'reset_password',
          targetType: 'user',
          targetId: user.id,
          targetLabel: user.email,
          details: 'Password reset via forgot-password token',
        },
      })
    } catch {}

    return NextResponse.json({ message: 'Password has been reset successfully. You can now log in with your new password.' })
  } catch (error) {
    console.error('Reset password token error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}

// GET — Validate a reset token (check if it's still valid)
export async function GET(request: NextRequest) {
  try {
    const token = new URL(request.url).searchParams.get('token')

    if (!token) {
      return NextResponse.json({ error: 'Token is required' }, { status: 400 })
    }

    const resetRecord = await db.passwordReset.findUnique({ where: { token } })

    if (!resetRecord) {
      return NextResponse.json({ valid: false, error: 'Invalid reset token' }, { status: 400 })
    }

    if (resetRecord.used) {
      return NextResponse.json({ valid: false, error: 'Token already used' }, { status: 400 })
    }

    if (resetRecord.expiresAt < new Date()) {
      return NextResponse.json({ valid: false, error: 'Token expired' }, { status: 400 })
    }

    return NextResponse.json({ valid: true, email: resetRecord.email })
  } catch (error) {
    console.error('Validate reset token error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
