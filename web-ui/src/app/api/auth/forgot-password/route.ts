// ─── /api/auth/forgot-password ──────────────────────────
// POST — Request a password reset OTP

import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'

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
      return NextResponse.json({ message: 'If your email exists in our system, an OTP has been sent.' })
    }

    if (user.status !== 'active') {
      // Don't reveal account status
      return NextResponse.json({ message: 'If your email exists in our system, an OTP has been sent.' })
    }

    // Invalidate any existing OTPs for this user
    await db.passwordReset.updateMany({
      where: { userId: user.id, used: false },
      data: { used: true },
    }).catch(() => {})

    // Generate a 6-digit OTP
    const otp = Math.floor(100000 + Math.random() * 900000).toString()
    const expiresAt = new Date(Date.now() + 15 * 60 * 1000) // 15 minutes from now

    await db.passwordReset.create({
      data: {
        otp,
        email: normalizedEmail,
        userId: user.id,
        expiresAt,
      },
    })

    // In production, you would send an email with the OTP.
    // For this internal tool, we return the OTP so it can be used directly.
    return NextResponse.json({
      message: 'OTP sent successfully',
      otp,
    })
  } catch (error) {
    console.error('Forgot password error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
