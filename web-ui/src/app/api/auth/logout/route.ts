import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { getCookieOptions } from '@/lib/session'

export async function POST(request: NextRequest) {
  try {
    const token = request.cookies.get('session_token')?.value

    if (token) {
      // Get user info for audit log before deleting session
      const session = await db.session.findUnique({
        where: { token },
        include: { user: true },
      }).catch(() => null)

      await db.session.deleteMany({
        where: { token },
      })

      // Create audit log entry for logout
      if (session?.user) {
        await db.auditLog.create({
          data: {
            userId: session.user.id,
            userName: session.user.name,
            action: 'logout',
            targetType: 'session',
            targetId: session.user.id,
            targetLabel: session.user.email,
            details: 'User logged out',
          },
        }).catch(() => {}) // non-critical
      }
    }

    const response = NextResponse.json({ message: 'Logged out' })

    response.cookies.set('session_token', '', {
      ...getCookieOptions(),
      maxAge: 0, // Clear the cookie
    })

    return response
  } catch (error) {
    console.error('Logout error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
