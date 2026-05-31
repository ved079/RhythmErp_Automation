// ─── Next.js Middleware ──────────────────────────────────────
// Centralized route protection — runs before every API request.
//
// Security features:
// C1: Authentication check on all protected routes
// C5: /api/auth/seed blocked in production
// C6: CSRF validation on all state-changing requests (POST/PUT/PATCH/DELETE)
//
// Public routes (no auth required):
//   - /api/auth/login                (POST)
//   - /api/auth/forgot-password      (POST)
//   - /api/auth/reset-password-token (POST)
//   - /api/route.ts                  (health check)
//   - /api/runs/callback             (server-to-server, uses API key auth)
//   - /api/auth/seed                 (POST) — ONLY in non-production

import { NextRequest, NextResponse } from 'next/server'
import { validateCsrfToken, isStateChangingMethod, ensureCsrfCookie } from '@/lib/csrf'

// Routes that don't require authentication
const PUBLIC_ROUTES = new Set([
  '/api/auth/login',
  '/api/auth/forgot-password',
  '/api/auth/reset-password-token',
  '/api',
])

// Route prefixes that don't require authentication
const PUBLIC_PREFIXES = [
  '/api/auth/forgot-password',
  '/api/auth/reset-password-token',
  '/api/runs/callback',  // FastAPI server-to-server callback (uses API key auth)
]

// C5: /api/auth/seed is only public in non-production environments
function isSeedRoute(pathname: string): boolean {
  return pathname === '/api/auth/seed'
}

function isPublicRoute(pathname: string): boolean {
  if (PUBLIC_ROUTES.has(pathname)) return true
  for (const prefix of PUBLIC_PREFIXES) {
    if (pathname.startsWith(prefix)) return true
  }
  // C5: seed route is only public in development
  if (isSeedRoute(pathname) && process.env.NODE_ENV !== 'production') {
    return true
  }
  return false
}

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl

  // Only protect /api/* routes
  if (!pathname.startsWith('/api/')) {
    const response = NextResponse.next()
    return ensureCsrfCookie(req, response)
  }

  // C5: Block seed route in production
  if (isSeedRoute(pathname) && process.env.NODE_ENV === 'production') {
    return NextResponse.json(
      { error: 'This endpoint is not available in production' },
      { status: 404 }
    )
  }

  // Ensure CSRF cookie is set on all responses
  let response: NextResponse

  // Allow public routes through (but still validate CSRF on state-changing methods)
  if (isPublicRoute(pathname)) {
    response = NextResponse.next()
  } else {
    // C1: Check for session cookie on protected routes
    const token = req.cookies.get('session_token')?.value

    if (!token) {
      return NextResponse.json(
        { error: 'Not authenticated' },
        { status: 401 }
      )
    }

    // Token exists — let the route handler do full validation
    // (middleware runs on the Edge runtime, can't access Prisma directly)
    response = NextResponse.next()
  }

  // C6: Validate CSRF token on all state-changing requests
  // Skip CSRF for the callback route (server-to-server, uses API key)
  const isCallbackRoute = pathname.startsWith('/api/runs/callback')
  if (isStateChangingMethod(req.method) && !isCallbackRoute) {
    if (!validateCsrfToken(req)) {
      return NextResponse.json(
        { error: 'CSRF token validation failed' },
        { status: 403 }
      )
    }
  }

  return ensureCsrfCookie(req, response)
}

export const config = {
  // Match all API routes
  matcher: ['/api/:path*'],
}
