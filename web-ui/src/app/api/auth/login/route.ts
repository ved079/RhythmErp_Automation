import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import bcrypt from 'bcryptjs'
import crypto from 'crypto'
import { getCookieOptions, getDbSessionExpiry, cleanupExpiredSessions } from '@/lib/session'
import { checkRateLimit, getClientIp } from '@/lib/rate-limit'
import { createAuditLog } from '@/lib/admin-helpers'

export async function POST(request: NextRequest) {
  // C3: Rate limiting — 5 login attempts per minute per IP
  const clientIp = getClientIp(request)
  const rateCheck = checkRateLimit(clientIp, 'login', { maxRequests: 5, windowMs: 60_000 })
  if (rateCheck.limited) {
    return NextResponse.json(
      { error: 'Too many login attempts. Please try again later.' },
      {
        status: 429,
        headers: { 'Retry-After': String(Math.ceil((rateCheck.retryAfterMs || 60_000) / 1000)) }
      }
    )
  }

  try {
    const body = await request.json()
    const { email, password } = body

    if (!email || !password) {
      return NextResponse.json({ error: 'Email and password are required' }, { status: 400 })
    }

    const user = await db.user.findUnique({
      where: { email: email.toLowerCase().trim() },
    })

    if (!user) {
      // H1: Log failed login attempt with IP
      await createAuditLog({
        userId: 'unknown',
        userName: email.toLowerCase().trim(),
        action: 'failed_login',
        targetType: 'session',
        targetId: '',
        targetLabel: email.toLowerCase().trim(),
        details: 'Login failed: user not found',
        ipAddress: clientIp,
      }).catch(() => {})
      return NextResponse.json({ error: 'Invalid email or password' }, { status: 401 })
    }

    // Check if user is active
    if (user.status === 'inactive') {
      // H1: Log failed login attempt with IP
      await createAuditLog({
        userId: user.id,
        userName: user.name,
        action: 'failed_login',
        targetType: 'session',
        targetId: user.id,
        targetLabel: user.email,
        details: 'Login failed: account deactivated',
        ipAddress: clientIp,
      }).catch(() => {})
      return NextResponse.json({ error: 'Account is deactivated. Contact admin.' }, { status: 403 })
    }

    const isValid = await bcrypt.compare(password, user.password)

    if (!isValid) {
      // H1: Log failed login attempt with IP
      await createAuditLog({
        userId: user.id,
        userName: user.name,
        action: 'failed_login',
        targetType: 'session',
        targetId: user.id,
        targetLabel: user.email,
        details: 'Login failed: incorrect password',
        ipAddress: clientIp,
      }).catch(() => {})
      return NextResponse.json({ error: 'Invalid email or password' }, { status: 401 })
    }

    // Clean up old sessions for this user + expired sessions globally
    await Promise.all([
      db.session.deleteMany({ where: { userId: user.id } }),
      cleanupExpiredSessions(),
    ])

    // C7: Create new session with proper expiry
    const token = crypto.randomBytes(32).toString('hex')
    const expiresAt = getDbSessionExpiry() // 7 days in DB

    await db.session.create({
      data: {
        token,
        userId: user.id,
        expiresAt,
      },
    })

    // Update lastLogin timestamp
    await db.user.update({
      where: { id: user.id },
      data: { lastLogin: new Date() },
    }).catch(() => {}) // non-critical

    // Create audit log entry for login (with IP)
    try {
      await db.auditLog.create({
        data: {
          userId: user.id,
          userName: user.name,
          action: 'login',
          targetType: 'session',
          targetId: user.id,
          targetLabel: user.email,
          details: `User logged in with role: ${user.role}`,
          ipAddress: clientIp,
        },
      })
    } catch {} // non-critical

    const response = NextResponse.json({
      message: 'Login successful',
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
        role: user.role,
        status: user.status,
        moduleAccess: JSON.parse(user.moduleAccess || '[]'),
      },
    })

    response.cookies.set('session_token', token, getCookieOptions())

    return response
  } catch (error) {
    const isMissingTable = error instanceof Error && 'code' in error && (error as any).code === 'P2021'
    if (isMissingTable) {
      return NextResponse.json({ error: 'Database not initialized. Run: npx prisma db push' }, { status: 503 })
    }
    console.error('Login error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
