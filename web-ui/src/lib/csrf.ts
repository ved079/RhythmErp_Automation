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
//
// Uses Web Crypto API (Edge Runtime compatible — no Node.js 'crypto')

import { NextRequest, NextResponse } from 'next/server'

const CSRF_COOKIE_NAME = 'csrf_token'
const CSRF_HEADER_NAME = 'x-csrf-token'

/** Generate a cryptographically random CSRF token (Edge Runtime safe) */
export function generateCsrfToken(): string {
  const bytes = new Uint8Array(32)
  crypto.getRandomValues(bytes)
  return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('')
}

/**
 * Timing-safe string comparison to prevent timing attacks.
 * Works in Edge Runtime without Node.js crypto.
 */
function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false
  let result = 0
  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i)
  }
  return result === 0
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
  return timingSafeEqual(cookieToken, headerToken)
}

/**
 * Check if a request method is state-changing (requires CSRF validation)
 */
export function isStateChangingMethod(method: string): boolean {
  return ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method.toUpperCase())
}
