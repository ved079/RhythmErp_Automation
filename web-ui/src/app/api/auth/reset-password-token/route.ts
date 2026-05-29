// ─── /api/auth/reset-password-token ────────────────────
// POST — Reset password using an OTP (from forgot-password flow)

import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import bcrypt from 'bcryptjs'

export async function POST(request: NextRequest) {
  try {
    const { email, otp, new_password, confirm_password } = await request.json()

    if (!email || typeof email !== 'string') {
      return NextResponse.json({ error: 'Email is required' }, { status: 400 })
    }

    if (!otp || typeof otp !== 'string') {
      return NextResponse.json({ error: 'OTP is required' }, { status: 400 })
    }

    if (!new_password || typeof new_password !== 'string') {
      return NextResponse.json({ error: 'New password is required' }, { status: 400 })
    }

    if (!confirm_password || typeof confirm_password !== 'string') {
      return NextResponse.json({ error: 'Confirm password is required' }, { status: 400 })
    }

    if (new_password.length < 6) {
      return NextResponse.json({ error: 'New password must be at least 6 characters' }, { status: 400 })
    }

    if (new_password !== confirm_password) {
      return NextResponse.json({ error: 'Passwords do not match' }, { status: 400 })
    }

    const normalizedEmail = email.toLowerCase().trim()

    // Find the reset OTP record matching email and OTP
    const resetRecord = await db.passwordReset.findFirst({
      where: {
        email: normalizedEmail,
        otp,
        used: false,
      },
      orderBy: { createdAt: 'desc' },
    })

    if (!resetRecord) {
      return NextResponse.json({ error: 'Invalid OTP. Please check and try again.' }, { status: 400 })
    }

    if (resetRecord.expiresAt < new Date()) {
      // Mark as used so it can't be retried
      await db.passwordReset.update({ where: { id: resetRecord.id }, data: { used: true } }).catch(() => {})
      return NextResponse.json({ error: 'OTP has expired. Please request a new one.' }, { status: 400 })
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

    // Mark OTP as used
    await db.passwordReset.update({
      where: { id: resetRecord.id },
      data: { used: true },
    })

    // Invalidate all other pending OTPs for this user
    await db.passwordReset.updateMany({
      where: { userId: user.id, used: false },
      data: { used: true },
    }).catch(() => {})

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
          details: 'Password reset via forgot-password OTP',
        },
      })
    } catch {}

    return NextResponse.json({ message: 'Password has been reset successfully. You can now log in with your new password.' })
  } catch (error) {
    console.error('Reset password token error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
