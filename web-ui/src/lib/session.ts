// ─── Shared Session Helpers ──────────────────────────────────
// Centralized session validation used across all API routes.
// Eliminates duplicate session-check code in proxy, dashboard, auth, etc.

import { NextRequest } from 'next/server'
import { db } from '@/lib/db'

export interface SessionUser {
  id: string
  email: string
  name: string
  role: string
  status: string
  moduleAccess: string[]
}

/**
 * Validate that the request comes from an authenticated user (any role).
 * Returns the user object if valid, or null if not.
 * Automatically cleans up expired sessions.
 */
export async function validateSession(req: NextRequest): Promise<SessionUser | null> {
  const token = req.cookies.get('session_token')?.value
  if (!token) return null

  try {
    const session = await db.session.findUnique({
      where: { token },
      include: { user: true },
    })

    if (!session || !session.user || session.expiresAt < new Date()) {
      // Clean up expired session
      if (session) {
        await db.session.delete({ where: { id: session.id } }).catch(() => {})
      }
      return null
    }

    return {
      id: session.user.id,
      email: session.user.email,
      name: session.user.name,
      role: session.user.role,
      status: session.user.status,
      moduleAccess: JSON.parse(session.user.moduleAccess || '[]'),
    }
  } catch (err) {
    console.error('validateSession error:', err)
    return null
  }
}

/**
 * Validate that the request comes from an admin or qa_lead user.
 * Returns the user object if authorized, or null if not.
 */
export async function validateAdminSession(req: NextRequest): Promise<SessionUser | null> {
  const user = await validateSession(req)
  if (!user) return null
  if (user.role !== 'admin' && user.role !== 'qa_lead') return null
  return user
}

/**
 * Check if the current environment is production (HTTPS expected).
 */
export function isProductionEnv(): boolean {
  return process.env.NODE_ENV === 'production'
}

/**
 * Get cookie options based on environment.
 * In production, set secure: true to require HTTPS.
 */
export function getCookieOptions() {
  return {
    httpOnly: true,
    secure: isProductionEnv(),
    sameSite: 'lax' as const,
    path: '/',
    maxAge: 7 * 24 * 60 * 60, // 7 days
  }
}

/**
 * Cleanup expired sessions from the database.
 * Call this periodically (e.g., on login or via a cron).
 */
export async function cleanupExpiredSessions(): Promise<number> {
  try {
    const result = await db.session.deleteMany({
      where: { expiresAt: { lt: new Date() } },
    })
    return result.count
  } catch {
    return 0
  }
}
