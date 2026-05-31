// ─── CSRF Protection — Double-Submit Cookie Pattern ─────────
// Strategy:
// 1. Middleware sets a non-httpOnly `csrf_token` cookie (per session)
// 2. All state-changing requests (POST/PUT/PATCH/DELETE) must include
//    an `X-CSRF-Token` header matching the cookie value
// 3. Middleware validates the header matches the cookie before passing
//    the request through
//
// This prevents CSRF attacks because a malicious site cannot:
// - Read the csrf_token cookie (same-origin policy)
// - Set custom headers on cross-origin requests (CORS preflight)

import { NextRequest, NextResponse } from 'next/server'
import crypto from 'crypto'

const CSRF_COOKIE_NAME = 'csrf_token'
const CSRF_HEADER_NAME = 'x-csrf-token'

/** Generate a cryptographically random CSRF token */
export function generateCsrfToken(): string {
  return crypto.randomBytes(32).toString('hex')
}

/**
 * Ensure the request has a csrf_token cookie. If not, set one.
 * Called from middleware on every request (including GET) so the cookie
 * is always available for the frontend to read.
 */
export function ensureCsrfCookie(req: NextRequest, response: NextResponse): NextResponse {
  const existing = req.cookies.get(CSRF_COOKIE_NAME)?.value
  if (!existing) {
    const token = generateCsrfToken()
    response.cookies.set(CSRF_COOKIE_NAME, token, {
      httpOnly: false, // Must be readable by JavaScript
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      path: '/',
      maxAge: 60 * 60 * 24 * 7, // 7 days — matches session lifetime
    })
  }
  return response
}

/**
 * Validate CSRF token on state-changing requests.
 * Checks that the X-CSRF-Token header matches the csrf_token cookie.
 * Returns true if valid, false if missing or mismatched.
 */
export function validateCsrfToken(req: NextRequest): boolean {
  const cookieToken = req.cookies.get(CSRF_COOKIE_NAME)?.value
  const headerToken = req.headers.get(CSRF_HEADER_NAME)

  if (!cookieToken || !headerToken) {
    return false
  }

  // Use timing-safe comparison to prevent timing attacks
  try {
    const a = Buffer.from(cookieToken, 'hex')
    const b = Buffer.from(headerToken, 'hex')
    return a.length === b.length && crypto.timingSafeEqual(a, b)
  } catch {
    return false
  }
}

/**
 * Check if a request method is state-changing (requires CSRF validation)
 */
export function isStateChangingMethod(method: string): boolean {
  return ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method.toUpperCase())
}
