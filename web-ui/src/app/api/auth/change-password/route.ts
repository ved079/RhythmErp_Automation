import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import bcrypt from 'bcryptjs'
import { validateSession } from '@/lib/session'
import { getClientIp } from '@/lib/rate-limit'
import { createAuditLog } from '@/lib/admin-helpers'

export async function POST(request: NextRequest) {
  try {
    // Validate session using shared helper
    const user = await validateSession(request)

    if (!user) {
      return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
    }

    const body = await request.json()
    const { current_password, new_password } = body

    if (!current_password || !new_password) {
      return NextResponse.json({ error: 'Current password and new password are required' }, { status: 400 })
    }

    if (new_password.length < 6) {
      return NextResponse.json({ error: 'New password must be at least 6 characters' }, { status: 400 })
    }

    // Get the full user record with password hash
    const dbUser = await db.user.findUnique({ where: { id: user.id } })
    if (!dbUser) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }

    // Verify current password
    const isValid = await bcrypt.compare(current_password, dbUser.password)
    if (!isValid) {
      return NextResponse.json({ error: 'Current password is incorrect' }, { status: 400 })
    }

    // Hash and save new password
    const hashedPassword = await bcrypt.hash(new_password, 10)
    await db.user.update({
      where: { id: user.id },
      data: { password: hashedPassword },
    })

    // H1: Create audit log entry with IP — do NOT log passwords
    const clientIp = getClientIp(request)
    try {
      await createAuditLog({
        userId: user.id,
        userName: user.name,
        action: 'password_change',
        targetType: 'user',
        targetId: user.id,
        targetLabel: user.email,
        details: 'Password changed by user',
        ipAddress: clientIp,
      })
    } catch {} // non-critical

    return NextResponse.json({ message: 'Password changed successfully' })
  } catch (error) {
    console.error('Change password error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
