import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import bcrypt from 'bcryptjs'
import crypto from 'crypto'
import { getCookieOptions, cleanupExpiredSessions } from '@/lib/session'

export async function POST(request: NextRequest) {
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
      return NextResponse.json({ error: 'Invalid email or password' }, { status: 401 })
    }

    // Check if user is active
    if (user.status === 'inactive') {
      return NextResponse.json({ error: 'Account is deactivated. Contact admin.' }, { status: 403 })
    }

    const isValid = await bcrypt.compare(password, user.password)

    if (!isValid) {
      return NextResponse.json({ error: 'Invalid email or password' }, { status: 401 })
    }

    // Clean up old sessions for this user + expired sessions globally
    await Promise.all([
      db.session.deleteMany({ where: { userId: user.id } }),
      cleanupExpiredSessions(),
    ])

    // Create new session
    const token = crypto.randomBytes(32).toString('hex')
    const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000) // 7 days

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

    // Create audit log entry for login
    await db.auditLog.create({
      data: {
        userId: user.id,
        userName: user.name,
        action: 'login',
        targetType: 'session',
        targetId: user.id,
        targetLabel: user.email,
        details: `User logged in with role: ${user.role}`,
      },
    }).catch(() => {}) // non-critical

    const response = NextResponse.json({
      message: 'Login successful',
      user: { id: user.id, email: user.email, name: user.name, role: user.role },
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
