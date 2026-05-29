// ─── /api/auth/forgot-password ──────────────────────────
// POST — Request a password reset token

import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import crypto from 'crypto'

export async function POST(request: NextRequest) {
  try {
    const { email } = await request.json()
    if (!email || typeof email !== 'string') {
      return NextResponse.json({ error: 'Email is required' }, { status: 400 })
    }

    const normalizedEmail = email.toLowerCase().trim()

    // Check if user exists
    const user = await db.user.findUnique({ where: { email: normalizedEmail } })
    if (!user) {
      // Don't reveal whether the email exists — still return success
      return NextResponse.json({ message: 'If your email exists in our system, a reset token has been generated.' })
    }

    if (user.status !== 'active') {
      // Don't reveal account status
      return NextResponse.json({ message: 'If your email exists in our system, a reset token has been generated.' })
    }

    // Invalidate any existing reset tokens for this user
    await db.passwordReset.updateMany({
      where: { userId: user.id, used: false },
      data: { used: true },
    }).catch(() => {})

    // Generate a secure random token
    const token = crypto.randomBytes(32).toString('hex')
    const expiresAt = new Date(Date.now() + 60 * 60 * 1000) // 1 hour from now

    await db.passwordReset.create({
      data: {
        token,
        email: normalizedEmail,
        userId: user.id,
        expiresAt,
      },
    })

    // In production, you would send an email with the reset link.
    // For this internal tool, we return the token so it can be used directly.
    return NextResponse.json({
      message: 'Reset token generated successfully.',
      token,
      // Include the full reset URL for convenience
      resetUrl: `/reset-password?token=${token}`,
    })
  } catch (error) {
    console.error('Forgot password error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
