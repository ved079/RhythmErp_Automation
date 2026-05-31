// ─── /api/auth/forgot-password ──────────────────────────
// POST — Request a password reset OTP (sends via email)

import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { sendOtpEmail } from '@/lib/email'
import { checkRateLimit, getClientIp } from '@/lib/rate-limit'

export async function POST(request: NextRequest) {
  // C3: Rate limiting — 5 requests per minute per IP
  const clientIp = getClientIp(request)
  const rateCheck = checkRateLimit(clientIp, 'forgot-password', { maxRequests: 5, windowMs: 60_000 })
  if (rateCheck.limited) {
    return NextResponse.json(
      { error: 'Too many requests. Please try again later.' },
      {
        status: 429,
        headers: { 'Retry-After': String(Math.ceil((rateCheck.retryAfterMs || 60_000) / 1000)) }
      }
    )
  }

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
    try {
      await db.passwordReset.updateMany({
        where: { userId: user.id, used: false },
        data: { used: true },
      })
    } catch { /* empty */ }

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

    // Send OTP via email
    const emailSent = await sendOtpEmail(normalizedEmail, otp, user.name)

    if (!emailSent) {
      // C4: Do NOT return OTP in response — this was a security issue
      // Log warning for admin investigation instead
      console.warn('[ForgotPassword] Email send failed for:', normalizedEmail, '— OTP NOT returned in response for security')
      // Still return generic success message to avoid revealing system state
      return NextResponse.json({
        message: 'If your email exists in our system, an OTP has been sent.',
        emailSent: false,
      })
    }

    return NextResponse.json({
      message: 'OTP sent to your email address.',
      emailSent: true,
    })
  } catch (error) {
    console.error('Forgot password error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
