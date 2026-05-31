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

// ─── Session timeout constants ────────────────────────────
// C7: Session cookie expires after 1 hour (access window).
// DB session can last up to 7 days (refresh window — renewed on activity).
const SESSION_COOKIE_MAX_AGE = 60 * 60         // 1 hour (access token equivalent)
const SESSION_DB_MAX_AGE = 7 * 24 * 60 * 60    // 7 days (refresh token equivalent)

/**
 * Validate that the request comes from an authenticated user (any role).
 * Returns the user object if valid, or null if not.
 * Automatically cleans up expired sessions.
 * Uses in-memory cache to avoid repeated DB queries for the same token.
 *
 * C7: Also renews the session expiry on each successful validation,
 * implementing a sliding window (similar to refresh token rotation).
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

    // C7: Renew session expiry on activity (sliding window / refresh token rotation)
    // Only renew if less than half the DB max age remains
    const remainingMs = session.expiresAt.getTime() - Date.now()
    const halfDbMaxAge = (SESSION_DB_MAX_AGE * 1000) / 2
    if (remainingMs < halfDbMaxAge) {
      const newExpiresAt = new Date(Date.now() + SESSION_DB_MAX_AGE * 1000)
      await db.session.update({
        where: { id: session.id },
        data: { expiresAt: newExpiresAt },
      }).catch(() => {}) // Non-critical
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
 * C7: Session cookie maxAge reduced to 1 hour.
 * The DB session can last 7 days and gets renewed on activity.
 * sameSite changed to 'strict' for C6 (CSRF hardening).
 */
export function getCookieOptions() {
  return {
    httpOnly: true,
    secure: isProductionEnv(),
    sameSite: 'strict' as const,  // C6: Changed from 'lax' to 'strict'
    path: '/',
    maxAge: SESSION_COOKIE_MAX_AGE, // C7: 1 hour (was 7 days)
  }
}

/**
 * Get cookie options for the DB session expiry (used when creating sessions).
 * The DB session lasts longer than the cookie — acts as a refresh token.
 */
export function getDbSessionExpiry(): Date {
  return new Date(Date.now() + SESSION_DB_MAX_AGE * 1000) // 7 days
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
