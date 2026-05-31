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

// ─── In-memory session cache (30s TTL) ──────────────────────
// Avoids hitting the DB for validateSession on every API call.
// On a typical page load, 6-8 API calls fire simultaneously —
// without caching, each one does a separate DB query just to
// validate the same session token.
const sessionCache = new Map<string, { user: SessionUser; expiresAt: number }>()
const SESSION_CACHE_TTL = 30_000 // 30 seconds

function getCachedSession(token: string): SessionUser | null {
  const cached = sessionCache.get(token)
  if (!cached) return null
  if (Date.now() > cached.expiresAt) {
    sessionCache.delete(token)
    return null
  }
  return cached.user
}

function setCachedSession(token: string, user: SessionUser): void {
  if (sessionCache.size > 500) {
    const now = Date.now()
    for (const [key, val] of sessionCache) {
      if (now > val.expiresAt) sessionCache.delete(key)
    }
  }
  sessionCache.set(token, { user, expiresAt: Date.now() + SESSION_CACHE_TTL })
}

function invalidateCachedSession(token: string): void {
  sessionCache.delete(token)
}

/**
 * Validate that the request comes from an authenticated user (any role).
 * Returns the user object if valid, or null if not.
 * Automatically cleans up expired sessions.
 * Uses in-memory cache to avoid repeated DB queries for the same token.
 */
export async function validateSession(req: NextRequest): Promise<SessionUser | null> {
  const token = req.cookies.get('session_token')?.value
  if (!token) return null

  // Check cache first — avoids DB hit for concurrent requests with same token
  const cached = getCachedSession(token)
  if (cached) return cached

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
      invalidateCachedSession(token)
      return null
    }

    const user: SessionUser = {
      id: session.user.id,
      email: session.user.email,
      name: session.user.name,
      role: session.user.role,
      status: session.user.status,
      moduleAccess: JSON.parse(session.user.moduleAccess || '[]'),
    }

    setCachedSession(token, user)
    return user
  } catch (err) {
    console.error('validateSession error:', err)
    return null
  }
}

/**
 * Validate that the request comes from an admin user.
 * Returns the user object if authorized, or null if not.
 */
export async function validateAdminSession(req: NextRequest): Promise<SessionUser | null> {
  const user = await validateSession(req)
  if (!user) return null
  if (user.role !== 'admin') return null
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